"""B3 - Document-level caching.

B3  (exact)       Sequential cache with tracked document token boundaries. On an edit, keep the cache
                  up to the start of the first changed document and recompute that document and every
                  later one. Exact: the final token sequence equals full recompute's.

B3a (APPROXIMATE) Each document is prefilled independently, conditioned only on the shared
                  instruction header, and cached by its token ids. The knowledge cache is composed by
                  concatenating header KV + per-document KV, re-rotating each document's RoPE keys from
                  its prefill position to its final position. The token sequence equals the canonical
                  one, but documents cannot attend to earlier documents, so the KV values differ from a
                  jointly prefilled causal sequence. This is NOT equivalent to full recompute; its
                  deviation is measured, never assumed away.
"""
from __future__ import annotations

import torch

from src.baselines.base import Baseline, PrefixReuseBaseline
from src.cache import kv_utils
from src.cache.token_boundaries import TokenizedKnowledge
from src.data.knowledge import SerializedKnowledge
from src.utils import timed


class DocumentCacheExact(PrefixReuseBaseline):
    name = "B3_document_cache"
    label = "B3 Document Cache (exact)"

    def propose_reuse(self, new_ser, new_tk, new_types) -> int:
        i = self._first_change(new_ser, new_types)
        if i is None:
            return len(new_tk.ids)
        return self._doc_start_token(new_ser, new_tk, i)


def _chunks(ser: SerializedKnowledge, tk: TokenizedKnowledge) -> list[tuple[int, int]]:
    """Token ranges: chunk 0 = header, chunk i = doc i plus trailing separator/section header."""
    starts = [tk.doc_token_spans[d][0] for d in ser.doc_order]
    bounds = [0] + starts + [len(tk.ids)]
    return [(bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)]


class DocumentCacheApprox(Baseline):
    name = "B3a_document_cache_approx"
    label = "B3a Independent Doc Cache (APPROXIMATE)"
    exact = False

    def reset(self) -> None:
        super().reset()
        self.header_kv = None  # list of (k, v)
        self.header_ids: list[int] = []
        self.store: dict[tuple, list] = {}  # chunk token ids -> per-layer (k, v) at positions [h, h+len)

    def _prefill_chunk(self, ids: list[int]) -> list:
        base = kv_utils.from_kv([(k, v) for k, v in self.header_kv], None)
        cache, _ = self.engine.prefill(ids, base)
        h = len(self.header_ids)
        return [(k[..., h:, :].clone(), v[..., h:, :].clone()) for k, v in kv_utils.kv_pairs(cache)]

    def _build(self, ser, tk, t: dict) -> tuple[int, int]:
        ch = _chunks(ser, tk)
        hs, he = ch[0]
        header = tk.ids[hs:he]
        recomputed = 0
        with timed(t, "prefill_s"):
            if self.header_kv is None or header != self.header_ids:
                c, _ = self.engine.prefill(header)
                self.header_kv = [(k.clone(), v.clone()) for k, v in kv_utils.kv_pairs(c)]
                self.header_ids = header
                self.store.clear()
                recomputed += len(header)
            needed = {}
            for s, e in ch[1:]:
                key = tuple(tk.ids[s:e])
                if key not in self.store:
                    needed[key] = None
            for key in needed:
                self.store[key] = self._prefill_chunk(list(key))
                recomputed += len(key)
        with timed(t, "cache_management_s"):
            live = {tuple(tk.ids[s:e]) for s, e in ch[1:]}
            for key in [k for k in self.store if k not in live]:
                del self.store[key]  # evict versions no longer present
            h = len(self.header_ids)
            n_layers = len(self.header_kv)
            parts_k = [[self.header_kv[l][0]] for l in range(n_layers)]
            parts_v = [[self.header_kv[l][1]] for l in range(n_layers)]
            for s, e in ch[1:]:
                kv = self.store[tuple(tk.ids[s:e])]
                delta = torch.full((e - s,), float(s - h), device=self.engine.device)
                for l in range(n_layers):
                    k, v = kv[l]
                    parts_k[l].append(kv_utils.rerotate_keys(k, delta, self.engine.inv_freq, self.engine.rope_scaling)
                                      if s != h else k)
                    parts_v[l].append(v)
            self.cache = kv_utils.from_kv(
                [(torch.cat(parts_k[l], dim=-2), torch.cat(parts_v[l], dim=-2)) for l in range(n_layers)])
            if kv_utils.cache_len(self.cache) != len(tk.ids):
                raise RuntimeError("composed cache length mismatch")
        return len(tk.ids) - recomputed, recomputed

    def initialize(self, snapshot) -> dict:
        self.reset()
        t: dict = {}
        ser, tk = self._encode(snapshot, t)
        self.engine.mem_reset_peak()
        reused, recomputed = self._build(ser, tk, t)
        self._commit(snapshot, ser, tk)
        return self._stats_row(t, reused=0, recomputed=recomputed, kind="initialize", approximate=True)

    def update(self, event, snapshot) -> dict:
        t: dict = {}
        ser, tk = self._encode(snapshot, t)
        self.engine.mem_reset_peak()
        self.cache = None
        reused, recomputed = self._build(ser, tk, t)
        self._commit(snapshot, ser, tk)
        self.n_updates += 1
        # Reused chunk KV is *not* exact-valid reuse; reported separately from exact cache reuse.
        self.last_update = self._stats_row(t, reused=0, recomputed=recomputed, approximate=True,
                                           approx_reused_tokens=reused)
        return self.last_update

    def get_cache_statistics(self) -> dict:
        s = super().get_cache_statistics()
        s["store_chunks"] = len(self.store)
        s["store_mb"] = sum(k.numel() * k.element_size() * 2 for kv in self.store.values() for k, _ in kv) / 1024 ** 2
        return s
