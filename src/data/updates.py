"""Synthetic, versioned knowledge updates. The source JSON is never touched: updates are applied to
deep copies of KnowledgeSnapshots and every new value is flagged is_synthetic."""
from __future__ import annotations

import random
import re
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from typing import Any

from src.data.documents import KnowledgeDoc, is_missing
from src.data.knowledge import KnowledgeSnapshot

# Synthetic replacement values. Chosen to not occur anywhere in the source export (checked at runtime).
SYNTH_LOCATIONS = ["Cần Thơ", "Hải Phòng", "Vũng Tàu", "Long An", "Tây Ninh", "Đà Lạt", "Phan Thiết",
                   "Hội An", "Rạch Giá", "Bến Tre", "Sóc Trăng", "Thanh Hóa", "Nam Định", "Pleiku"]
SYNTH_INVESTORS = ["Anh Bảo Long", "Chị Thu Trang", "Anh Quang Huy", "Chị Ngọc Lan", "Anh Đức Thịnh",
                   "Chị Mỹ Duyên", "Anh Hoàng Phúc", "Chị Thanh Thảo", "Anh Minh Triết", "Chị Kim Oanh"]
SYNTH_HOURS = ["Thứ 2 - Chủ nhật: 7:30 - 18:00", "Thứ 2 - Thứ 6: 8:30 - 17:00", "Thứ 2 - Thứ 7: 7:00 - 16:30"]


@dataclass
class FieldChange:
    doc_id: str
    field: str
    old_value: Any
    new_value: Any


@dataclass
class UpdateEvent:
    update_id: str
    update_type: str
    changes: list[FieldChange] = field(default_factory=list)
    added_docs: list[dict] = field(default_factory=list)  # KnowledgeDoc dicts
    deleted_doc_ids: list[str] = field(default_factory=list)
    is_synthetic: bool = True
    version_before: int = 0
    version_after: int = 1

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "UpdateEvent":
        d = dict(d)
        d["changes"] = [FieldChange(**c) for c in d.get("changes", [])]
        return UpdateEvent(**d)

    @property
    def touched_doc_ids(self) -> list[str]:
        ids = [c.doc_id for c in self.changes] + [d["doc_id"] for d in self.added_docs] + list(self.deleted_doc_ids)
        return list(dict.fromkeys(ids))


def apply_update(snapshot: KnowledgeSnapshot, event: UpdateEvent) -> KnowledgeSnapshot:
    if event.version_before != snapshot.version:
        raise ValueError(f"event expects v{event.version_before}, snapshot is v{snapshot.version}")
    new = snapshot.clone()
    new.version = event.version_after
    for ch in event.changes:
        d = new.doc(ch.doc_id)
        if d.metadata.get(ch.field) != ch.old_value:
            raise ValueError(f"{ch.doc_id}.{ch.field}: expected old {ch.old_value!r}, found {d.metadata.get(ch.field)!r}")
        d.metadata[ch.field] = ch.new_value
        if ch.field == "investment":  # keep the numeric twin consistent
            d.metadata["investment_vnd"] = money_to_vnd(ch.new_value)
        d.version = event.version_after
    if event.deleted_doc_ids:
        new.docs = [d for d in new.docs if d.doc_id not in set(event.deleted_doc_ids)]
    for ad in event.added_docs:
        doc = KnowledgeDoc.from_dict(ad)
        doc.version = event.version_after
        if new.has(doc.doc_id):
            raise ValueError(f"doc {doc.doc_id} already present")
        if doc.knowledge_type == "stable":
            idx = len(new.stable_docs)
            new.docs.insert(idx, doc)
        else:
            new.docs.append(doc)
    new.validate_order()
    return new


# --------------------------------------------------------------------------- value generators

def money_to_vnd(s: str | None) -> int | None:
    if not s:
        return None
    m = re.match(r"\s*([\d.,]+)\s*(tỷ|triệu)", s)
    if not m:
        return None
    return int(round(float(m.group(1).replace(",", ".")) * (1e9 if m.group(2) == "tỷ" else 1e6)))


def vnd_to_money(v: int) -> str:
    if v >= 1_000_000_000:
        x = v / 1e9
        return (f"{x:.1f}".rstrip("0").rstrip(".").replace(".", ",")) + " tỷ"
    return f"{int(round(v / 1e6))} triệu"


def _scale(rng: random.Random) -> float:
    return rng.choice([rng.uniform(0.55, 0.85), rng.uniform(1.2, 1.8)])


def new_area(old: float, rng: random.Random) -> float | int:
    for _ in range(100):
        v = old * _scale(rng)
        v = int(round(v)) if float(old).is_integer() or v >= 100 else round(v, 1)
        if v > 0 and abs(v - old) / old >= 0.1:
            return v
    raise RuntimeError("could not draw area")


def new_investment(old_s: str, rng: random.Random) -> str:
    old = money_to_vnd(old_s)
    for _ in range(100):
        v = old * _scale(rng)
        v = round(v / 1e8) * 1e8 if v >= 1e9 else round(v / 1e7) * 1e7
        s = vnd_to_money(int(v))
        if money_to_vnd(s) != old and abs(money_to_vnd(s) - old) / old >= 0.1:
            return s
    raise RuntimeError("could not draw investment")


def new_count(old: int, rng: random.Random) -> int:
    return old + rng.randint(3, 15)


def new_date(old_iso: str, rng: random.Random) -> str:
    d = date.fromisoformat(old_iso) + timedelta(days=rng.choice([-1, 1]) * rng.randint(90, 500))
    return d.isoformat()


def _unused(pool: list[str], forbidden_text: str, used: set, rng: random.Random) -> str:
    cands = [p for p in pool if p not in used and p.lower() not in forbidden_text.lower()]
    if not cands:
        raise RuntimeError("synthetic pool exhausted")
    v = rng.choice(cands)
    used.add(v)
    return v


class UpdateFactory:
    """Generates deterministic synthetic UpdateEvents against an evolving snapshot."""

    def __init__(self, seed: int, corpus_text: str):
        self.rng = random.Random(seed)
        self.corpus_text = corpus_text  # all source text, so synthetic strings never collide with real ones
        self.used: set = set()
        self.counter = 0

    def _id(self) -> str:
        self.counter += 1
        return f"u_{self.counter:03d}"

    def field_value(self, doc: KnowledgeDoc, fld: str, history: list | None = None) -> Any:
        old = doc.metadata[fld]
        history = set(map(str, history or [])) | {str(old)}
        for _ in range(50):
            if fld == "area_m2":
                v = new_area(old, self.rng)
            elif fld == "investment":
                v = new_investment(old, self.rng)
            elif fld in ("total_projects", "total_employees", "total_engineers", "total_architects"):
                v = new_count(old, self.rng)
            elif fld == "completed_date":
                v = new_date(old, self.rng)
            elif fld == "location":
                v = _unused(SYNTH_LOCATIONS, self.corpus_text, self.used, self.rng)
            elif fld == "investor":
                v = _unused(SYNTH_INVESTORS, self.corpus_text, self.used, self.rng)
            elif fld == "working_hours":
                v = _unused(SYNTH_HOURS, self.corpus_text, self.used, self.rng)
            else:
                raise ValueError(f"no generator for field {fld}")
            if str(v) not in history and str(v) not in doc.text:
                return v
        raise RuntimeError(f"could not draw a fresh value for {doc.doc_id}.{fld}")

    def field_update(self, snap: KnowledgeSnapshot, items: list[tuple[str, str]], update_type: str,
                     history: dict | None = None) -> UpdateEvent:
        changes = []
        for doc_id, fld in items:
            d = snap.doc(doc_id)
            if is_missing(d.metadata.get(fld)):
                raise ValueError(f"{doc_id}.{fld} is null in source; cannot update")
            hist = (history or {}).get((doc_id, fld), [])
            changes.append(FieldChange(doc_id, fld, d.metadata[fld], self.field_value(d, fld, hist)))
        return UpdateEvent(self._id(), update_type, changes=changes,
                           version_before=snap.version, version_after=snap.version + 1)

    def add_doc(self, snap: KnowledgeSnapshot, doc: KnowledgeDoc) -> UpdateEvent:
        doc = doc.clone()
        doc.knowledge_type = "dynamic"
        return UpdateEvent(self._id(), "append_document", added_docs=[doc.to_dict()],
                           version_before=snap.version, version_after=snap.version + 1)

    def delete_doc(self, snap: KnowledgeSnapshot, doc_id: str) -> UpdateEvent:
        snap.doc(doc_id)
        return UpdateEvent(self._id(), "delete_document", deleted_doc_ids=[doc_id],
                           version_before=snap.version, version_after=snap.version + 1)
