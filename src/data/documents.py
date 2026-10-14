"""Canonical knowledge-document representation and deterministic text rendering.

A document's text is always *rendered* from its structured metadata, so a synthetic
update to a field changes exactly the rendered line(s) of that field and nothing else.
"""
from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any

from src.utils import sha256_text


@dataclass
class KnowledgeDoc:
    doc_id: str
    source_table: str
    source_id: Any
    title: str
    content: str  # free-text body (already cleaned), may be ""
    metadata: dict = field(default_factory=dict)
    knowledge_type: str = "dynamic"  # "stable" | "dynamic" (set by the partitioner)
    version: int = 0
    doc_kind: str = ""  # project | news | company_profile | company_stats | taxonomy

    def clone(self) -> "KnowledgeDoc":
        return copy.deepcopy(self)

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "KnowledgeDoc":
        return KnowledgeDoc(**d)

    @property
    def text(self) -> str:
        return render_doc(self)

    @property
    def content_hash(self) -> str:
        return sha256_text(self.text)


# --------------------------------------------------------------------------- formatting

def fmt_number(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, float) and x.is_integer():
        x = int(x)
    return str(x)


def fmt_date_vi(iso: str | None) -> str:
    """'2026-01-13' -> '13/01/2026' (Vietnamese day/month/year convention)."""
    if not iso:
        return ""
    d = date.fromisoformat(iso[:10])
    return f"{d.day:02d}/{d.month:02d}/{d.year:04d}"


def fmt_list(xs: list | None) -> str:
    return ", ".join(str(x) for x in xs) if xs else ""


# key, label, formatter, suffix
PROJECT_FIELDS = [
    ("category", "Danh mục", str, ""),
    ("architecture_type", "Loại kiến trúc", str, ""),
    ("interior_style", "Phong cách nội thất", str, ""),
    ("investor", "Chủ đầu tư", str, ""),
    ("location", "Địa điểm", str, ""),
    ("area_m2", "Diện tích", fmt_number, " m²"),
    ("investment", "Mức đầu tư", str, " đồng"),
    ("completed_date", "Ngày hoàn thành", fmt_date_vi, ""),
    ("description", "Mô tả", str, ""),
]
NEWS_FIELDS = [
    ("news_category", "Chuyên mục", str, ""),
    ("published_date", "Ngày đăng", fmt_date_vi, ""),
    ("related_project", "Dự án liên quan", lambda v: f"#{v}", ""),
]
COMPANY_PROFILE_FIELDS = [
    ("company_name", "Tên công ty", str, ""),
    ("slogan", "Khẩu hiệu", str, ""),
    ("main_address", "Địa chỉ chính", str, ""),
    ("secondary_address", "Địa chỉ phụ", str, ""),
    ("working_hours", "Giờ làm việc", str, ""),
    ("hotlines", "Hotline", fmt_list, ""),
    ("emails", "Email", fmt_list, ""),
    ("website", "Website", str, ""),
]
COMPANY_STATS_FIELDS = [
    ("total_employees", "Tổng số nhân viên", fmt_number, ""),
    ("total_engineers", "Số kỹ sư", fmt_number, ""),
    ("total_architects", "Số kiến trúc sư", fmt_number, ""),
    ("total_projects", "Tổng số dự án đã thực hiện", fmt_number, ""),
]

FIELD_SPECS = {
    "project": PROJECT_FIELDS,
    "news": NEWS_FIELDS,
    "company_profile": COMPANY_PROFILE_FIELDS,
    "company_stats": COMPANY_STATS_FIELDS,
    "taxonomy": [],
}

FIELD_LABELS = {k: lbl for spec in FIELD_SPECS.values() for k, lbl, _, _ in spec}


def is_missing(v: Any) -> bool:
    return v is None or (isinstance(v, str) and not v.strip()) or (isinstance(v, (list, dict)) and not v)


def render_field(doc: KnowledgeDoc, key: str) -> str | None:
    for k, label, fmt, suffix in FIELD_SPECS[doc.doc_kind]:
        if k == key:
            v = doc.metadata.get(k)
            if is_missing(v):
                return None
            return f"- {label}: {fmt(v)}{suffix}"
    raise KeyError(f"{doc.doc_kind} has no field {key}")


def render_doc(doc: KnowledgeDoc) -> str:
    """Deterministic plain-text rendering; missing/null fields are omitted, never invented."""
    if doc.doc_kind == "project":
        head = f"Dự án #{doc.source_id}: {doc.title}"
    elif doc.doc_kind == "news":
        head = f"Bài viết #{doc.source_id}: {doc.title}"
    else:
        head = doc.title
    lines = [f"[{doc.doc_id}]", head]
    for k, _, _, _ in FIELD_SPECS[doc.doc_kind]:
        line = render_field(doc, k)
        if line is not None:
            lines.append(line)
    if doc.content:
        lines.append(doc.content)
    return "\n".join(lines)
