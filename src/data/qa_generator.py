"""Generate Vietnamese evaluation questions directly from structured fields of a snapshot.

Ground truth is always read from the snapshot (source record values or explicitly synthetic
update values). No facts are invented. Question groups:
  A updated_fact      - directly targets a value changed by an update (expected = latest value)
  B unchanged_fact    - targets a value no update touched (incl. other fields of updated docs)
  C old_value_probe   - yes/no verification of an obsolete value (expect "no") or the new value ("yes")
  D cross_document    - comparison between two projects (answer = project id)
  E unanswerable      - information absent from the knowledge base (expect abstention)
"""
from __future__ import annotations

import random
import re
from collections import defaultdict
from datetime import date

from src.data.documents import KnowledgeDoc, fmt_date_vi, fmt_number, is_missing
from src.data.knowledge import KnowledgeSnapshot
from src.data.updates import UpdateEvent, money_to_vnd

PROJECT_Q = {
    "area_m2": ("numeric", "Diện tích của dự án #{id} ({name}) là bao nhiêu mét vuông?"),
    "investment": ("money", "Mức đầu tư của dự án #{id} ({name}) là bao nhiêu?"),
    "location": ("text", "Dự án #{id} ({name}) được thực hiện ở địa điểm nào?"),
    "investor": ("text", "Chủ đầu tư của dự án #{id} ({name}) là ai?"),
    "completed_date": ("date", "Dự án #{id} ({name}) hoàn thành vào ngày nào?"),
    "category": ("text", "Dự án #{id} ({name}) thuộc danh mục dự án nào?"),
    "architecture_type": ("text", "Dự án #{id} ({name}) thuộc loại hình kiến trúc nào?"),
    "interior_style": ("text", "Dự án #{id} ({name}) theo phong cách nội thất nào?"),
}
COMPANY_Q = {
    "total_projects": ("numeric", "Công ty đã thực hiện tổng cộng bao nhiêu dự án?"),
    "total_employees": ("numeric", "Công ty có tổng cộng bao nhiêu nhân viên?"),
    "total_engineers": ("numeric", "Công ty có bao nhiêu kỹ sư?"),
    "total_architects": ("numeric", "Công ty có bao nhiêu kiến trúc sư?"),
    "working_hours": ("time_range", "Giờ làm việc của công ty là khi nào?"),
    "main_address": ("text", "Địa chỉ chính của công ty ở đâu?"),
}
NEWS_Q = {
    "published_date": ("date", "Bài viết #{id} (\"{name}\") được đăng vào ngày nào?"),
    "news_category": ("text", "Bài viết #{id} (\"{name}\") thuộc chuyên mục tin tức nào?"),
    "related_project": ("id", "Bài viết #{id} (\"{name}\") liên quan đến dự án nào? Hãy nêu mã dự án."),
}
YESNO_PHRASE = {
    "area_m2": ("diện tích", lambda v: f"{fmt_number(v)} m²"),
    "investment": ("mức đầu tư", lambda v: f"{v} đồng"),
    "location": ("địa điểm", str),
    "investor": ("chủ đầu tư", str),
    "completed_date": ("ngày hoàn thành", fmt_date_vi),
    "total_projects": ("tổng số dự án đã thực hiện", fmt_number),
    "total_employees": ("tổng số nhân viên", fmt_number),
    "working_hours": ("giờ làm việc", str),
}
UNANSWERABLE_FIELD_Q = [
    ("Số điện thoại của chủ đầu tư dự án #{id} ({name}) là gì?", "điện thoại chủ đầu tư"),
    ("Dự án #{id} ({name}) có bao nhiêu phòng ngủ?", "phòng ngủ"),
    ("Ai là kiến trúc sư trưởng phụ trách dự án #{id} ({name})?", "kiến trúc sư phụ trách"),
    ("Nhà thầu điện nước của dự án #{id} ({name}) là đơn vị nào?", "nhà thầu điện nước"),
]
NONEXISTENT_PROJECT_IDS = [101, 137, 158, 199, 212, 250]


def _area_mentions(text: str) -> list[float]:
    return [float(x.replace(",", ".")) for x in re.findall(r"(\d+(?:[.,]\d+)?)\s*m(?:²|2)\b", text)]


def eligible_fields(doc: KnowledgeDoc) -> list[str]:
    """Fields usable as unambiguous facts (present, and not contradicted inside the same document)."""
    if doc.doc_kind == "project":
        out = []
        desc = doc.metadata.get("description") or ""
        for f in PROJECT_Q:
            v = doc.metadata.get(f)
            if is_missing(v):
                continue
            if f == "area_m2" and any(abs(a - float(v)) > 1e-6 for a in _area_mentions(desc)):
                continue  # description states a different area
            if f == "investment" and re.search(r"\d\s*(tỷ|triệu)", desc) and \
                    money_to_vnd(v) not in {money_to_vnd(m.group(0)) for m in re.finditer(r"[\d.,]+\s*(?:tỷ|triệu)", desc)}:
                continue
            if f == "location" and desc:
                continue  # free-text descriptions mention other places; be conservative
            out.append(f)
        return out
    if doc.doc_kind == "company_stats":
        return [f for f in ("total_projects", "total_employees", "total_engineers", "total_architects")
                if not is_missing(doc.metadata.get(f))]
    if doc.doc_kind == "company_profile":
        return [f for f in ("working_hours", "main_address") if not is_missing(doc.metadata.get(f))]
    if doc.doc_kind == "news":
        return [f for f in NEWS_Q if not is_missing(doc.metadata.get(f))]
    return []


def _qspec(doc: KnowledgeDoc, field: str):
    if doc.doc_kind == "project":
        return PROJECT_Q[field]
    if doc.doc_kind in ("company_stats", "company_profile"):
        return COMPANY_Q[field]
    return NEWS_Q[field]


def _expected(doc: KnowledgeDoc, field: str, value):
    t = _qspec(doc, field)[0]
    if t == "money":
        return money_to_vnd(value), f"{value} đồng"
    if t == "numeric":
        return float(value), fmt_number(value) + (" m²" if field == "area_m2" else "")
    if t == "date":
        return value, fmt_date_vi(value)
    if t == "id":
        return int(value), f"#{value}"
    return value, str(value)


def _value_for_type(doc, field, v):
    t = _qspec(doc, field)[0]
    return money_to_vnd(v) if t == "money" else (float(v) if t == "numeric" else v)


class QAGenerator:
    def __init__(self, seed: int):
        self.rng = random.Random(seed)
        self.n = 0

    def _q(self, group: str, qtype: str, doc_ids: list[str], question: str, answer_type: str,
           expected_value, expected_answer: str, field: str, version: int, **kw) -> dict:
        self.n += 1
        return {
            "question_id": f"q_{self.n:04d}", "group": group, "question_type": qtype,
            "source_doc_id": doc_ids[0] if doc_ids else None, "source_doc_ids": doc_ids,
            "question": question, "expected_answer": expected_answer, "expected_value": expected_value,
            "answer_type": answer_type, "evidence_field": field, "knowledge_version": version, **kw,
        }

    def fact_question(self, doc: KnowledgeDoc, field: str, group: str, qtype: str, version: int,
                      history: list | None = None) -> dict:
        at, tmpl = _qspec(doc, field)
        exp_v, exp_s = _expected(doc, field, doc.metadata[field])
        olds = [_value_for_type(doc, field, h) for h in (history or [])]
        return self._q(group, qtype, [doc.doc_id], tmpl.format(id=doc.source_id, name=doc.title), at,
                       exp_v, exp_s, field, version, old_values=olds)

    def generate(self, final: KnowledgeSnapshot, events: list[UpdateEvent], sizes: dict) -> list[dict]:
        v = final.version
        history: dict = defaultdict(list)  # (doc_id, field) -> list of obsolete values, oldest first
        deleted: list[str] = []
        for ev in events:
            for ch in ev.changes:
                history[(ch.doc_id, ch.field)].append(ch.old_value)
            deleted += ev.deleted_doc_ids
        changed = [(d, f) for (d, f) in history if final.has(d)]
        qs: list[dict] = []

        # A: updated facts
        for d_id, f in changed:
            d = final.doc(d_id)
            if f in eligible_fields(d) or f == "working_hours":
                qs.append(self.fact_question(d, f, "A", "updated_fact", v, history[(d_id, f)]))
        for ad in [x for ev in events for x in ev.added_docs]:
            if final.has(ad["doc_id"]):
                d = final.doc(ad["doc_id"])
                for f in eligible_fields(d)[:2]:
                    qs.append(self.fact_question(d, f, "A", "appended_doc_fact", v))

        # B: unchanged facts (other fields of updated docs first, then other docs)
        touched = {d for d, _ in changed}
        same_doc = [(d, f) for d in touched for f in eligible_fields(final.doc(d)) if (d, f) not in history]
        self.rng.shuffle(same_doc)
        for d_id, f in same_doc[: sizes.get("same_doc_unchanged", 2)]:
            qs.append(self.fact_question(final.doc(d_id), f, "B", "same_doc_unchanged", v))
        pool = [(d.doc_id, f) for d in final.docs if d.doc_id not in touched for f in eligible_fields(d)]
        self.rng.shuffle(pool)
        per_doc = defaultdict(int)
        picked = 0
        for d_id, f in pool:  # spread across documents
            if picked >= sizes.get("unchanged", 6):
                break
            if per_doc[d_id] >= 1:
                continue
            per_doc[d_id] += 1
            picked += 1
            qs.append(self.fact_question(final.doc(d_id), f, "B", "unchanged_fact", v))

        # C: obsolete-value probes (yes/no)
        probes = []
        for d_id, f in changed:
            if f not in YESNO_PHRASE:
                continue
            d = final.doc(d_id)
            phrase, fmt = YESNO_PHRASE[f]
            subj = f"dự án #{d.source_id} ({d.title})" if d.doc_kind == "project" else "công ty"
            old = history[(d_id, f)][-1]
            probes.append(self._q("C", "old_value_probe", [d_id],
                                  f"Hiện tại, {phrase} của {subj} có phải là {fmt(old)} không? Trả lời Có hoặc Không.",
                                  "yesno", "no", "Không", f, v, stale_if="yes", probed_value=old))
            probes.append(self._q("C", "new_value_probe", [d_id],
                                  f"Hiện tại, {phrase} của {subj} có phải là {fmt(d.metadata[f])} không? Trả lời Có hoặc Không.",
                                  "yesno", "yes", "Có", f, v, stale_if="no", probed_value=d.metadata[f]))
        qs += probes[: sizes.get("old_value_probe", 4)]

        # D: cross-document comparisons
        qs += self._cross_doc(final, history, sizes.get("cross_document", 3), v)

        # E: unanswerable
        qs += self._unanswerable(final, deleted, sizes.get("unanswerable", 3), v)
        return qs

    def _cross_doc(self, final, history, n, v) -> list[dict]:
        projs = [d for d in final.docs if d.doc_kind == "project"]
        area_ok = [d for d in projs if "area_m2" in eligible_fields(d)]
        out = []
        # pairs whose answer flips because of an area update come first
        for (d_id, f), olds in history.items():
            if f != "area_m2" or not final.has(d_id) or len(out) >= n:
                continue
            a = final.doc(d_id)
            new, old = float(a.metadata["area_m2"]), float(olds[0])
            lo, hi = min(new, old), max(new, old)
            mids = [b for b in area_ok if b.doc_id != d_id and b.doc_id not in {k[0] for k in history}
                    and lo * 1.05 < float(b.metadata["area_m2"]) < hi / 1.05]
            if mids:
                b = self.rng.choice(mids)
                out.append(self._area_cmp(a, b, v, old_area_a=old))
        others = [d for d in area_ok if d.doc_id not in {k[0] for k in history}]
        tries = 0
        while len(out) < n and len(others) >= 2 and tries < 200:
            tries += 1
            a, b = self.rng.sample(others, 2)
            xa, xb = float(a.metadata["area_m2"]), float(b.metadata["area_m2"])
            if max(xa, xb) / min(xa, xb) >= 1.15:
                out.append(self._area_cmp(a, b, v))
        return out[:n]

    def _area_cmp(self, a, b, v, old_area_a=None) -> dict:
        xa, xb = float(a.metadata["area_m2"]), float(b.metadata["area_m2"])
        if self.rng.random() < 0.5:
            a, b, xa, xb = b, a, xb, xa
            first_is_updated = False
        else:
            first_is_updated = True
        win = a if xa > xb else b
        olds = []
        if old_area_a is not None:
            upd, other = (a, b) if first_is_updated else (b, a)
            old_win = upd if old_area_a > float(other.metadata["area_m2"]) else other
            if old_win.source_id != win.source_id:
                olds = [old_win.source_id]
        q = (f"Giữa dự án #{a.source_id} ({a.title}) và dự án #{b.source_id} ({b.title}), dự án nào có diện tích "
             f"lớn hơn? Trả lời bằng mã dự án.")
        return self._q("D", "cross_document_area", [a.doc_id, b.doc_id], q, "choice", win.source_id,
                       f"#{win.source_id}", "area_m2", v, options=[a.source_id, b.source_id],
                       option_names={str(a.source_id): a.title, str(b.source_id): b.title}, old_values=olds)

    def _unanswerable(self, final, deleted, n, v) -> list[dict]:
        out = []
        projs = [d for d in final.docs if d.doc_kind == "project"]
        for d in projs:  # genuinely null area in the source record
            if is_missing(d.metadata.get("area_m2")):
                out.append(self._q("E", "null_field", [d.doc_id],
                                   PROJECT_Q["area_m2"][1].format(id=d.source_id, name=d.title),
                                   "abstain", None, "Không có thông tin", "area_m2", v))
                break
        for doc_id in deleted:
            sid = int(doc_id.split("_")[1])
            out.append(self._q("E", "deleted_document", [doc_id],
                               f"Diện tích của dự án #{sid} là bao nhiêu mét vuông?", "abstain", None,
                               "Không có thông tin", "area_m2", v))
        present = {d.source_id for d in projs}
        fake = [i for i in NONEXISTENT_PROJECT_IDS if i not in present]
        out.append(self._q("E", "nonexistent_entity", [], f"Diện tích của dự án #{fake[0]} là bao nhiêu mét vuông?",
                           "abstain", None, "Không có thông tin", "area_m2", v))
        tmpls = list(UNANSWERABLE_FIELD_Q)
        self.rng.shuffle(tmpls)
        for tmpl, key in tmpls:
            if len(out) >= n or not projs:
                break
            d = self.rng.choice(projs)
            if key.split()[0] in d.text.lower():
                continue
            out.append(self._q("E", "absent_field", [d.doc_id], tmpl.format(id=d.source_id, name=d.title),
                               "abstain", None, "Không có thông tin", key, v))
        return out[:n]
