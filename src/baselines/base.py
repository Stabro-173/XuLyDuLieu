"""Common baseline interface and the shared exact prefix-reuse machinery.

Every baseline implements: initialize(snapshot), update(event, snapshot), answer(question),
get_cache_statistics(), reset().  `update` receives both the UpdateEvent (needed by append-only
correction) and the new canonical KnowledgeSnapshot (identical for all methods).
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from src.cache import kv_utils
from src.cache.engine import CAGEngine
from src.cache.token_boundaries import TokenizedKnowledge, tokenize_knowledge, verify_reuse
from src.data.knowledge import KnowledgeSnapshot, SerializedKnowledge, serialize
from src.data.updates import UpdateEvent
from src.utils import timed


def first_changed_doc_index(old: SerializedKnowledge, new: SerializedKnowledge,
                            old_types: list[str], new_types: list[str]) -> int | None:
    """Index of the first document whose id, content hash or partition differs (None if identical)."""
    n = min(len(old.doc_order), len(new.doc_order))
    for i in range(n):
        a, b = old.doc_order[i], new.doc_order[i]
        if a != b or old.hashes[a] != new.hashes[b] or old_types[i] != new_types[i]:
            return i
    if len(old.doc_order) != len(new.doc_order):
        return n
    return None


class Baseline(ABC):
    name = "base"
    label = ""
    exact = True  # produces the same token sequence/cache as full recompute (up to fp numerics)

    def __init__(self, engine: CAGEngine):
        self.engine = engine
        self.reset()

    def reset(self) -> None:
        self.cache = None
        self.ids: list[int] = []
        self.ser: SerializedKnowledge | None = None
        self.tk: TokenizedKnowledge | None = None
        self.snapshot: KnowledgeSnapshot | None = None
        self.types: list[str] = []
        self.last_update: dict = {}
        self.n_updates = 0

    # ------------------------------------------------------------------ helpers
    def _encode(self, snap: KnowledgeSnapshot, t: dict) -> tuple[SerializedKnowledge, TokenizedKnowledge]:
        with timed(t, "serialization_s", sync=False):
            ser = serialize(snap, self.engine.template)
        with timed(t, "tokenization_s", sync=False):
            tk = tokenize_knowledge(self.engine.tok, ser)
        return ser, tk

    def _commit(self, snap, ser, tk, ids=None) -> None:
        self.snapshot, self.ser, self.tk = snap, ser, tk
        self.ids = list(tk.ids) if ids is None else ids
        self.types = [d.knowledge_type for d in snap.docs]

    def initialize(self, snapshot: KnowledgeSnapshot) -> dict:
        self.reset()
        t: dict = {}
        ser, tk = self._encode(snapshot, t)
        self.engine.mem_reset_peak()
        with timed(t, "prefill_s"):
            self.cache, _ = self.engine.prefill(tk.ids)
        self._commit(snapshot, ser, tk)
        return self._stats_row(t, reused=0, recomputed=len(tk.ids), kind="initialize")

    @abstractmethod
    def update(self, event: UpdateEvent, snapshot: KnowledgeSnapshot) -> dict: ...

    def answer(self, question: str, keep_logits: bool = False) -> dict:
        return self.engine.answer(self.cache, len(self.ids), question, keep_logits=keep_logits)

    def get_cache_statistics(self) -> dict:
        return {
            "cache_tokens": kv_utils.cache_len(self.cache),
            "kv_cache_mb": kv_utils.kv_bytes(self.cache) / 1024 ** 2,
            "canonical_tokens": len(self.tk.ids) if self.tk else 0,
            "stable_tokens": self.tk.stable_token_end if self.tk else 0,
            "n_updates": self.n_updates,
        }

    def _stats_row(self, t: dict, reused: int, recomputed: int, kind: str = "update", **extra) -> dict:
        total = len(self.ids)
        row = {
            "kind": kind,
            "serialization_s": t.get("serialization_s", 0.0),
            "tokenization_s": t.get("tokenization_s", 0.0),
            "cache_management_s": t.get("cache_management_s", 0.0),
            "prefill_s": t.get("prefill_s", 0.0),
            "reused_tokens": reused,
            "recomputed_tokens": recomputed,
            "total_knowledge_tokens": total,
            "cache_reuse_ratio": reused / total if total else None,
            "kv_cache_mb": kv_utils.kv_bytes(self.cache) / 1024 ** 2,
            **self.engine.mem_stats(),
            **extra,
        }
        row["update_total_s"] = row["serialization_s"] + row["tokenization_s"] + row["cache_management_s"] + row["prefill_s"]
        return row


class PrefixReuseBaseline(Baseline):
    """Exact reuse: keep a verified token-identical prefix of the old cache, crop, prefill the rest.
    Subclasses only decide the *proposed* reuse length."""

    def propose_reuse(self, new_ser: SerializedKnowledge, new_tk: TokenizedKnowledge,
                      new_types: list[str]) -> int:
        raise NotImplementedError

    def update(self, event: UpdateEvent, snapshot: KnowledgeSnapshot) -> dict:
        t: dict = {}
        ser, tk = self._encode(snapshot, t)
        new_types = [d.knowledge_type for d in snapshot.docs]
        self.engine.mem_reset_peak()
        with timed(t, "cache_management_s"):
            proposed = self.propose_reuse(ser, tk, new_types)
            dec = verify_reuse(self.ids, tk.ids, proposed)
            if dec.verified == 0:
                self.cache = None  # nothing reusable: release before re-prefill
            else:
                kv_utils.crop(self.cache, dec.verified)
        with timed(t, "prefill_s"):
            self.cache, _ = self.engine.prefill(tk.ids[dec.verified:], self.cache)
        self._commit(snapshot, ser, tk)
        self.n_updates += 1
        self.last_update = self._stats_row(
            t, reused=dec.verified, recomputed=len(tk.ids) - dec.verified,
            proposed_reuse=dec.proposed, reuse_shortened=dec.shortened, token_lcp=dec.lcp,
        )
        return self.last_update

    # shared helpers for document-boundary strategies
    def _first_change(self, ser, new_types) -> int | None:
        return first_changed_doc_index(self.ser, ser, self.types, new_types)

    @staticmethod
    def _doc_start_token(ser: SerializedKnowledge, tk: TokenizedKnowledge, i: int) -> int:
        if i >= len(ser.doc_order):
            return len(tk.ids)
        return tk.doc_token_spans[ser.doc_order[i]][0]
