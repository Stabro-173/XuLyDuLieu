"""Model wrapper: KV-cache prefill on top of an optional reused prefix, and greedy answering
that never leaks question tokens into the persistent knowledge cache."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, DynamicCache

from src.cache import kv_utils
from src.data.knowledge import PromptTemplate
from src.utils import cuda_sync, resolve_model_path  # noqa: F401 (re-export)


@dataclass
class EngineConfig:
    model_name: str = "Qwen/Qwen2.5-1.5B-Instruct"
    device: str = "auto"  # auto | cuda | cpu
    dtype: str = "auto"  # auto | float16 | bfloat16 | float32
    attn_implementation: str = "sdpa"
    max_new_tokens: int = 32
    allow_cpu: bool = False  # CPU runs must be requested explicitly (smoke-test mode)
    revision: str | None = None
    prefill_chunk: int | None = None  # bound activation memory: prefill in chunks of this many tokens


@dataclass
class EngineInfo:
    model_name: str
    revision: str | None
    device: str
    device_name: str
    dtype: str
    attn_implementation: str
    torch_version: str
    transformers_version: str
    cuda_version: str | None
    load_seconds: float
    weights_bytes: int
    prefill_chunk: int | None = None
    vram_budget_mb: float | None = None
    notes: list = field(default_factory=list)


def _pick_dtype(device: str, requested: str) -> torch.dtype:
    if requested != "auto":
        return getattr(torch, requested)
    if device == "cpu":
        return torch.float32
    major, _ = torch.cuda.get_device_capability()
    return torch.bfloat16 if major >= 8 else torch.float16  # T4 / GTX16xx (sm75): fp16


class CAGEngine:
    def __init__(self, cfg: EngineConfig, model=None, tokenizer=None):
        self.cfg = cfg
        import transformers

        if cfg.device == "auto":
            dev = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            dev = cfg.device
        if dev == "cpu" and not cfg.allow_cpu:
            raise RuntimeError("CUDA unavailable; pass allow_cpu=True for an explicitly labelled CPU smoke test")
        if dev == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("device=cuda requested but CUDA is not available")
        self.device = torch.device(dev)
        notes = []
        # Physically usable VRAM before weights are loaded. On Windows (WDDM) the driver may silently
        # spill allocations to system RAM instead of raising OOM; any measurement whose peak reserved
        # memory exceeds this budget is flagged so it is never reported as a GPU result.
        self.vram_budget_mb = torch.cuda.mem_get_info()[0] / 1024 ** 2 if dev == "cuda" else None
        t0 = time.perf_counter()
        local_rev = None
        if model is None:
            dtype = _pick_dtype(dev, cfg.dtype)
            path, local_rev = resolve_model_path(cfg.model_name)
            if local_rev is None and path != cfg.model_name:
                notes.append("local model copy without REVISION file")
            rev = None if path != cfg.model_name else cfg.revision
            tokenizer = AutoTokenizer.from_pretrained(path, revision=rev)
            model = AutoModelForCausalLM.from_pretrained(
                path, revision=rev, dtype=dtype, attn_implementation=cfg.attn_implementation,
            ).to(self.device)
        model.eval()
        self.model, self.tok = model, tokenizer
        self.dtype = next(model.parameters()).dtype
        cuda_sync()
        load_s = time.perf_counter() - t0
        self.template = PromptTemplate.from_tokenizer(tokenizer)
        eos = {tokenizer.eos_token_id, tokenizer.convert_tokens_to_ids("<|im_end|>"),
               tokenizer.convert_tokens_to_ids("<|endoftext|>")}
        self.eos_ids = {e for e in eos if isinstance(e, int) and e >= 0}
        rot = getattr(model.model, "rotary_emb", None)
        self.inv_freq = rot.inv_freq.detach() if rot is not None else None
        self.rope_scaling = float(getattr(rot, "attention_scaling", 1.0)) if rot is not None else 1.0
        rev = local_rev or getattr(model.config, "_commit_hash", None) or cfg.revision
        self.info = EngineInfo(
            model_name=cfg.model_name, revision=rev, device=dev,
            device_name=torch.cuda.get_device_name(0) if dev == "cuda" else "cpu",
            dtype=str(self.dtype).replace("torch.", ""),
            attn_implementation=getattr(model.config, "_attn_implementation", cfg.attn_implementation),
            torch_version=torch.__version__, transformers_version=transformers.__version__,
            cuda_version=torch.version.cuda, load_seconds=load_s,
            weights_bytes=sum(p.numel() * p.element_size() for p in model.parameters()),
            prefill_chunk=cfg.prefill_chunk, vram_budget_mb=self.vram_budget_mb, notes=notes,
        )

    # ------------------------------------------------------------------------- core ops
    def new_cache(self) -> DynamicCache:
        try:
            return DynamicCache(config=self.model.config)
        except TypeError:
            return DynamicCache()

    @torch.inference_mode()
    def prefill(self, ids: list[int], cache: DynamicCache | None = None,
                start_pos: int | None = None) -> tuple[DynamicCache, torch.Tensor | None]:
        """Run the model over `ids` appended to `cache` (positions continue from the cache length,
        or from `start_pos` if given). Returns the extended cache and last-token logits (fp32).

        With cfg.prefill_chunk set, the tokens are processed in chunks whose boundaries are aligned to
        absolute cache positions (multiples of the chunk size), so any two methods that end up with the
        same token sequence split it identically wherever their computations overlap. Chunked causal
        prefill computes the same function as one-shot prefill (up to floating-point reassociation)."""
        if cache is None:
            cache = self.new_cache()
        if not ids:
            return cache, None
        past = kv_utils.cache_len(cache)
        p0 = past if start_pos is None else start_pos
        C = self.cfg.prefill_chunk
        logits = None
        i = 0
        while i < len(ids):
            cur = past + i
            j = len(ids) if not C else min(len(ids), i + (C - cur % C))
            cache, logits = self._forward(ids[i:j], cache, cur, p0 + i)
            i = j
        return cache, logits

    def _forward(self, ids: list[int], cache, past: int, p0: int):
        m = len(ids)
        input_ids = torch.tensor([ids], dtype=torch.long, device=self.device)
        cache_position = torch.arange(past, past + m, device=self.device)
        position_ids = torch.arange(p0, p0 + m, device=self.device)[None]
        out = self.model(
            input_ids=input_ids, past_key_values=cache, use_cache=True,
            cache_position=cache_position, position_ids=position_ids,
            attention_mask=torch.ones(1, past + m, dtype=torch.long, device=self.device),
            logits_to_keep=1,
        )
        new_len = kv_utils.cache_len(out.past_key_values)
        if new_len != past + m:
            raise RuntimeError(f"cache length {new_len} != {past}+{m}")
        return out.past_key_values, out.logits[0, -1].float()

    @torch.inference_mode()
    def answer(self, cache: DynamicCache, knowledge_len: int, question: str,
               max_new_tokens: int | None = None, keep_logits: bool = False) -> dict:
        """Greedy decode on top of the knowledge cache; restores the cache to knowledge_len after."""
        if kv_utils.cache_len(cache) != knowledge_len:
            raise RuntimeError(f"knowledge cache has {kv_utils.cache_len(cache)} tokens, expected {knowledge_len}")
        max_new = max_new_tokens or self.cfg.max_new_tokens
        q_ids = self.tok(self.template.question_text(question), add_special_tokens=False)["input_ids"]
        gen: list[int] = []
        try:
            cuda_sync()
            t0 = time.perf_counter()
            cache, logits = self.prefill(q_ids, cache)
            first_logits = logits.detach().cpu() if keep_logits else None
            nxt = int(torch.argmax(logits))
            cuda_sync()
            t_first = time.perf_counter()
            gen.append(nxt)
            while len(gen) < max_new and nxt not in self.eos_ids:
                cache, logits = self.prefill([nxt], cache)
                nxt = int(torch.argmax(logits))
                gen.append(nxt)
            cuda_sync()
            t_end = time.perf_counter()
        finally:
            kv_utils.crop(cache, knowledge_len)  # drop question/answer KV: no contamination
        out_ids = [t for t in gen if t not in self.eos_ids]
        n_dec = len(gen)
        return {
            "answer": self.tok.decode(out_ids, skip_special_tokens=True).strip(),
            "generated_ids": gen,
            "question_tokens": len(q_ids),
            "generated_tokens": n_dec,
            "ttft_s": t_first - t0,
            "generation_s": t_end - t0,
            "decode_tokens_per_s": (n_dec - 1) / (t_end - t_first) if n_dec > 1 and t_end > t_first else None,
            "first_logits": first_logits,
        }

    # ------------------------------------------------------------------------- memory
    def mem_reset_peak(self) -> None:
        if self.device.type == "cuda":
            torch.cuda.reset_peak_memory_stats()

    def mem_stats(self) -> dict:
        if self.device.type != "cuda":
            return {"gpu_peak_allocated_mb": None, "gpu_peak_reserved_mb": None, "gpu_allocated_mb": None,
                    "vram_budget_mb": None, "vram_spill_suspected": None}
        mb = 1024 ** 2
        return {
            "gpu_peak_allocated_mb": torch.cuda.max_memory_allocated() / mb,
            "gpu_peak_reserved_mb": torch.cuda.max_memory_reserved() / mb,
            "gpu_allocated_mb": torch.cuda.memory_allocated() / mb,
            "vram_budget_mb": self.vram_budget_mb,
            "vram_spill_suspected": torch.cuda.max_memory_reserved() / mb > self.vram_budget_mb,
        }


def free_cuda() -> None:
    import gc

    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
