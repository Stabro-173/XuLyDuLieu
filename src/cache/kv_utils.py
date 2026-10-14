"""Version-tolerant helpers around transformers' DynamicCache."""
from __future__ import annotations

import torch
from transformers import DynamicCache


def _layers(cache) -> list:
    if hasattr(cache, "layers"):  # transformers >= 4.56
        return [(l.keys, l.values) for l in cache.layers]
    return list(zip(cache.key_cache, cache.value_cache))


def kv_pairs(cache) -> list[tuple[torch.Tensor, torch.Tensor]]:
    return _layers(cache)


def cache_len(cache) -> int:
    return 0 if cache is None else int(cache.get_seq_length())


def crop(cache, n: int) -> None:
    """Truncate to the first n positions. Slices (views) are taken, original tensors are not
    written to, so caches sharing storage with this one are not mutated."""
    cur = cache_len(cache)
    if cur > n:
        cache.crop(n - cur)  # negative = number of trailing positions to drop (transformers >= 5)


def from_kv(pairs: list[tuple[torch.Tensor, torch.Tensor]], config=None) -> DynamicCache:
    c = DynamicCache(config=config) if config is not None else DynamicCache()
    for i, (k, v) in enumerate(pairs):
        c.update(k, v, i)
    return c


def clone(cache, config=None) -> DynamicCache:
    return from_kv([(k.clone(), v.clone()) for k, v in kv_pairs(cache)], config)


def kv_bytes(cache) -> int:
    if cache is None:
        return 0
    return sum(k.numel() * k.element_size() + v.numel() * v.element_size() for k, v in kv_pairs(cache))


def compare(a, b, n: int | None = None) -> dict:
    """Per-layer max/mean absolute differences over the first n positions."""
    pa, pb = kv_pairs(a), kv_pairs(b)
    assert len(pa) == len(pb), "layer count mismatch"
    n = n if n is not None else min(cache_len(a), cache_len(b))
    per_layer, gmax, gsum, cnt = [], 0.0, 0.0, 0
    for (ka, va), (kb, vb) in zip(pa, pb):
        dk = (ka[..., :n, :].float() - kb[..., :n, :].float()).abs()
        dv = (va[..., :n, :].float() - vb[..., :n, :].float()).abs()
        mx = max(dk.max().item(), dv.max().item())
        per_layer.append({"k_max": dk.max().item(), "v_max": dv.max().item(),
                          "k_mean": dk.mean().item(), "v_mean": dv.mean().item()})
        gmax = max(gmax, mx)
        gsum += dk.sum().item() + dv.sum().item()
        cnt += dk.numel() + dv.numel()
    return {"max_abs": gmax, "mean_abs": gsum / max(cnt, 1), "n_positions": n, "per_layer": per_layer}


def rerotate_keys(k: torch.Tensor, delta: torch.Tensor, inv_freq: torch.Tensor,
                  attention_scaling: float = 1.0) -> torch.Tensor:
    """Shift RoPE-rotated keys k (B,H,T,D) by `delta` positions (per token, shape (T,)).
    Uses R(p+d) = R(d) R(p) for the rotate_half RoPE convention (Llama/Qwen2).
    Only valid for the default (unscaled, attention_scaling == 1) rotary embedding."""
    if attention_scaling != 1.0:
        raise NotImplementedError("re-rotation assumes attention_scaling == 1")
    freqs = delta.to(torch.float32)[:, None] * inv_freq.to(torch.float32)[None, :]  # (T, D/2)
    emb = torch.cat([freqs, freqs], dim=-1)
    cos, sin = emb.cos()[None, None], emb.sin()[None, None]
    kf = k.float()
    half = kf.shape[-1] // 2
    rot = torch.cat([-kf[..., half:], kf[..., :half]], dim=-1)
    return (kf * cos + rot * sin).to(k.dtype)
