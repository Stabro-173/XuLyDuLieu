"""Stable / dynamic partitioning of knowledge documents (config driven, with overrides)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from src.data.documents import KnowledgeDoc

DEFAULT_RULES = {
    "company_profile": ("stable", "company background / contact data changes rarely"),
    "taxonomy": ("stable", "category, architecture-type and style lists are structural vocabulary"),
    "news": ("stable", "published explanatory articles are not edited after publication"),
    "company_stats": ("dynamic", "headcount and project totals change as business grows"),
    "project": ("dynamic", "project area, investment, location and dates are business data that get revised"),
}
DEFAULT_KIND_ORDER = ["company_profile", "taxonomy", "news", "company_stats", "project"]


@dataclass
class PartitionConfig:
    rules: dict = field(default_factory=lambda: {k: v[0] for k, v in DEFAULT_RULES.items()})
    rationale: dict = field(default_factory=lambda: {k: v[1] for k, v in DEFAULT_RULES.items()})
    overrides: dict = field(default_factory=dict)  # doc_id -> "stable" | "dynamic"
    kind_order: list = field(default_factory=lambda: list(DEFAULT_KIND_ORDER))

    @staticmethod
    def from_dict(d: dict | None) -> "PartitionConfig":
        cfg = PartitionConfig()
        if not d:
            return cfg
        cfg.rules.update(d.get("rules", {}))
        cfg.rationale.update(d.get("rationale", {}))
        cfg.overrides.update(d.get("overrides", {}))
        if d.get("kind_order"):
            cfg.kind_order = list(d["kind_order"])
        return cfg


def _sort_key(doc: KnowledgeDoc, kind_order: list) -> tuple:
    kind_rank = kind_order.index(doc.doc_kind) if doc.doc_kind in kind_order else len(kind_order)
    sid = doc.source_id if isinstance(doc.source_id, int) else -1
    return (kind_rank, sid, doc.doc_id)


def partition(docs: list[KnowledgeDoc], cfg: PartitionConfig) -> tuple[list[KnowledgeDoc], list[dict]]:
    """Return docs ordered [stable..., dynamic...] with knowledge_type set, plus rationale rows."""
    out, why = [], {}
    for d in docs:
        d = d.clone()
        if d.doc_id in cfg.overrides:
            d.knowledge_type = cfg.overrides[d.doc_id]
            why[d.doc_id] = "manual override"
        else:
            d.knowledge_type = cfg.rules.get(d.doc_kind, "dynamic")
            why[d.doc_id] = cfg.rationale.get(d.doc_kind, "default: dynamic")
        if d.knowledge_type not in ("stable", "dynamic"):
            raise ValueError(f"bad knowledge_type {d.knowledge_type} for {d.doc_id}")
        out.append(d)
    out.sort(key=lambda d: (0 if d.knowledge_type == "stable" else 1, _sort_key(d, cfg.kind_order)))
    return out, [{"doc_id": d.doc_id, "rationale": why[d.doc_id]} for d in out]


def partition_to_target_ratio(docs: list[KnowledgeDoc], target_ratio: float, pinned_dynamic: set[str],
                              token_count: Callable[[KnowledgeDoc], int],
                              kind_order: list | None = None) -> list[KnowledgeDoc]:
    """Move non-pinned docs (in canonical order) into the stable prefix until the stable share of
    *document* tokens reaches `target_ratio`. The document set and content are unchanged; only the
    stable/dynamic assignment and therefore the ordering differ between ratio conditions."""
    kind_order = kind_order or DEFAULT_KIND_ORDER
    canon = sorted((d.clone() for d in docs), key=lambda d: _sort_key(d, kind_order))
    total = sum(token_count(d) for d in canon)
    stable, dynamic, acc = [], [], 0
    for d in canon:
        tc = token_count(d)
        # add while doing so brings us closer to the target
        if d.doc_id not in pinned_dynamic and abs((acc + tc) / total - target_ratio) < abs(acc / total - target_ratio):
            d.knowledge_type = "stable"
            stable.append(d)
            acc += tc
        else:
            d.knowledge_type = "dynamic"
            dynamic.append(d)
    return stable + dynamic
