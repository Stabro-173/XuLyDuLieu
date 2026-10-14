"""Execute conditions x baselines x repetitions, writing raw JSONL rows. Resumable and OOM-safe."""
from __future__ import annotations

import logging
import random
import time
import traceback
from pathlib import Path

import torch

from src.baselines import REGISTRY
from src.benchmark.experiments import Condition, describe_positions
from src.cache import kv_utils
from src.cache.engine import CAGEngine, free_cuda
from src.evaluation.answer_metrics import evaluate
from src.utils import append_jsonl, read_jsonl

log = logging.getLogger("cag.runner")


def warmup(engine: CAGEngine, n: int = 3) -> None:
    ids = engine.tok("Khởi động mô hình. " * 40, add_special_tokens=False)["input_ids"]
    for _ in range(n):
        cache, _ = engine.prefill(ids)
        engine.answer(cache, len(ids), "Xin chào?", max_new_tokens=4)
        del cache
    free_cuda()


class TimeBudgetReached(Exception):
    """Raised between method runs when --max-minutes is exhausted; completed work is already saved."""


class Runner:
    def __init__(self, engine: CAGEngine, out_dir: str | Path, baselines: list[str], reps: int,
                 query_latency_subset: int = 3, run_tag: str = "", deadline: float | None = None):
        self.engine = engine
        self.out = Path(out_dir)
        self.out.mkdir(parents=True, exist_ok=True)
        self.baselines = baselines
        self.reps = reps
        self.q_subset = query_latency_subset
        self.run_tag = run_tag
        self.deadline = deadline  # time.perf_counter() value after which no new run is started
        done = read_jsonl(self.out / "runs.jsonl")
        self.done = {(r["condition_id"], r["baseline"], r["rep"]) for r in done
                     if r["status"] in ("ok", "vram_spill")}

    def _ctx(self, cond: Condition, pos: dict) -> dict:
        return {
            "condition_id": cond.condition_id, "budget": cond.budget, "seed": cond.seed,
            "scenario": cond.scenario, "position": cond.position,
            "stable_ratio_target": cond.stable_ratio_target, "n_sequential": cond.n_sequential,
            "stable_ratio_actual": pos["stable_ratio_actual"], "knowledge_tokens_v0": pos["knowledge_tokens_v0"],
            "edit_pos_norm_full": pos["edit_pos_norm_full"], "edit_pos_norm_dynamic": pos["edit_pos_norm_dynamic"],
            "edit_token_offset": pos["edit_token_offset"], "model": self.engine.info.model_name,
            "device": self.engine.info.device, "device_name": self.engine.info.device_name,
            "dtype": self.engine.info.dtype, "run_tag": self.run_tag,
        }

    def run_condition(self, cond: Condition) -> None:
        pos = describe_positions(cond, self.engine.tok, self.engine.template)
        ctx = self._ctx(cond, pos)
        known = {r["condition_id"] for r in read_jsonl(self.out / "conditions.jsonl")}
        if cond.condition_id not in known:
            append_jsonl(self.out / "conditions.jsonl", [{
                **ctx, **pos, "n_events": len(cond.events), "n_questions": len(cond.questions),
                "events": [e.to_dict() for e in cond.events], "meta": cond.meta,
                "doc_order_v0": [(d.doc_id, d.knowledge_type) for d in cond.snapshots[0].docs],
            }])
            append_jsonl(self.out / "questions_def.jsonl", [{"condition_id": cond.condition_id, **q}
                                                             for q in cond.questions])
        for rep in range(self.reps):
            order = list(self.baselines)
            random.Random(f"{cond.condition_id}-{rep}").shuffle(order)
            for b in order:
                if (cond.condition_id, b, rep) in self.done:
                    continue
                if self.deadline is not None and time.perf_counter() > self.deadline:
                    raise TimeBudgetReached()
                self._run_one(cond, b, rep, ctx)
                self.done.add((cond.condition_id, b, rep))

    def _run_one(self, cond: Condition, b: str, rep: int, ctx: dict) -> None:
        t0 = time.perf_counter()
        method = None
        status, err = "ok", None
        upd_rows, q_rows, init_row, final_stats = [], [], None, {}
        try:
            method = REGISTRY[b](self.engine)
            init_row = method.initialize(cond.snapshots[0])
            for i, ev in enumerate(cond.events):
                r = method.update(ev, cond.snapshots[i + 1])
                upd_rows.append({**ctx, "baseline": b, "rep": rep, "update_idx": i, "update_id": ev.update_id,
                                 "update_type": ev.update_type, "n_changes": len(ev.changes), **r})
            qs = cond.questions if rep == 0 else cond.questions[: self.q_subset]
            self.engine.mem_reset_peak()
            for q in qs:
                before = kv_utils.cache_len(method.cache)
                a = method.answer(q["question"])
                if kv_utils.cache_len(method.cache) != before:
                    raise RuntimeError("question KV leaked into the knowledge cache")
                ev_ = evaluate(q, a["answer"])
                q_rows.append({
                    **ctx, "baseline": b, "rep": rep, "question_id": q["question_id"], "group": q["group"],
                    "question_type": q["question_type"], "answer_type": q["answer_type"],
                    "question": q["question"], "expected_answer": q["expected_answer"],
                    "answer": a["answer"], "outcome": ev_["outcome"], "abstained": ev_["abstained"],
                    "generated_ids": a["generated_ids"], "ttft_s": a["ttft_s"], "generation_s": a["generation_s"],
                    "decode_tokens_per_s": a["decode_tokens_per_s"], "generated_tokens": a["generated_tokens"],
                    "question_tokens": a["question_tokens"], "knowledge_cache_tokens": before,
                })
            final_stats = {**method.get_cache_statistics(),
                           **{f"answer_{k}": v for k, v in self.engine.mem_stats().items()}}
        except torch.cuda.OutOfMemoryError as e:
            status, err = "oom", str(e)[:500]
            log.error("OOM in %s / %s rep %d", cond.condition_id, b, rep)
        except Exception as e:  # recorded, never silently skipped
            status, err = "error", f"{type(e).__name__}: {e}\n{traceback.format_exc()[-1500:]}"
            log.exception("failure in %s / %s rep %d", cond.condition_id, b, rep)
        finally:
            del method
            free_cuda()
        if status == "ok":
            spilled = [r for r in [init_row or {}, final_stats, *upd_rows]
                       if r.get("vram_spill_suspected") or r.get("answer_vram_spill_suspected")]
            if spilled:  # timings polluted by driver spill to system RAM: never report as GPU results
                status, err = "vram_spill", "peak reserved GPU memory exceeded the physical VRAM budget"
        if status in ("ok", "vram_spill"):
            append_jsonl(self.out / "updates.jsonl", [{**r, "run_status": status} for r in upd_rows])
            append_jsonl(self.out / "answers.jsonl", [{**r, "run_status": status} for r in q_rows])
        append_jsonl(self.out / "runs.jsonl", [{
            **ctx, "baseline": b, "rep": rep, "status": status, "error": err,
            "initialize": init_row, "final_cache": final_stats, "wall_s": time.perf_counter() - t0,
        }])
        log.info("%s %s rep%d -> %s (%.1fs)", cond.condition_id, b, rep, status, time.perf_counter() - t0)
