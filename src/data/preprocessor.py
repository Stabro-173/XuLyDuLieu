"""Turn the raw export into canonical KnowledgeDocs, logging every transformation."""
from __future__ import annotations

import re
import unicodedata
import warnings
from collections import Counter
from dataclasses import dataclass, field

from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning

from src.data.documents import KnowledgeDoc
from src.data.loader import RawExport

warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

# Title fragments like ". Địa điểm: Đà Nẵng. Mức đầu tư: 20 tỷ" are metadata, not the name.
_TITLE_META = re.compile(
    r"[.\s]*(?:Địa\s*đi[ểệ]m(?:\s*thiết\s*kế)?|Địa\s*chỉ|Tổng\s*mức\s*đầu\s*tư|Mức\s*đầu\s*tư)\b.*$",
    re.IGNORECASE,
)
_INVEST = re.compile(r"(?:Tổng\s+)?mức\s+đầu\s+tư\s*:?\s*([\d][\d.,]*)\s*(tỷ|triệu)", re.IGNORECASE)
_UNIT = {"tỷ": 1_000_000_000, "triệu": 1_000_000}


@dataclass
class PreprocessReport:
    transformations: list[str] = field(default_factory=list)
    counters: Counter = field(default_factory=Counter)
    excluded_tables: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def log(self, msg: str) -> None:
        if msg not in self.transformations:
            self.transformations.append(msg)

    def to_dict(self) -> dict:
        return {
            "transformations": self.transformations,
            "counters": dict(self.counters),
            "excluded_tables": self.excluded_tables,
            "warnings": self.warnings,
        }


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def clean_whitespace(s: str) -> str:
    s = s.replace(" ", " ")
    s = re.sub(r"[ \t\r\f\v]+", " ", s)
    s = re.sub(r"\s*\n\s*", "\n", s)
    s = re.sub(r"\n{2,}", "\n", s)
    return s.strip()


def html_to_text(html: str | None) -> str:
    """HTML -> plain text. Entities are decoded, tags/attributes/scripts dropped, Unicode kept."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "header", "footer", "img", "figure", "iframe"]):
        tag.decompose()
    text = soup.get_text("\n")
    return nfc(clean_whitespace(text))


def short_project_name(title: str) -> str:
    name = _TITLE_META.sub("", title).strip().rstrip(".").strip()
    return nfc(name or title.strip())


def parse_investment(title: str) -> tuple[str | None, int | None]:
    """Extract 'Mức đầu tư: 1,5 tỷ' -> ('1,5 tỷ', 1500000000). Returns (None, None) if absent."""
    m = _INVEST.search(title)
    if not m:
        return None, None
    num_s, unit = m.group(1).rstrip(".,"), m.group(2).lower()
    value = float(num_s.replace(",", "."))  # in these titles both ',' and '.' are decimal marks
    return f"{num_s} {unit}", int(round(value * _UNIT[unit]))


def iso_date(v: str | None) -> str | None:
    return v[:10] if v else None


def _num(v):
    if v is None:
        return None
    f = float(v)
    return int(f) if f.is_integer() else f


def build_documents(raw: RawExport, include_project_content: bool = False,
                    include_news_content: bool = False) -> tuple[list[KnowledgeDoc], PreprocessReport]:
    rep = PreprocessReport()
    t = raw.tables
    docs: list[KnowledgeDoc] = []

    for name in ("heroSlides", "settings", "users"):
        if name in t:
            rep.excluded_tables[name] = f"{len(t[name])} records; marketing/UI or empty, not business knowledge"

    # ---- company ---------------------------------------------------------------------
    c = t["companyInfo"][0]
    if len(t["companyInfo"]) > 1:
        rep.warnings.append("companyInfo has >1 record; only the first is used")
    slogan = (c.get("companySlogan") or "").strip().strip('"“”').strip()
    docs.append(KnowledgeDoc(
        doc_id="company_profile", source_table="companyInfo", source_id=c["id"],
        title=f"Hồ sơ công ty {nfc(c['companyName'])}", doc_kind="company_profile",
        content="Giới thiệu: " + html_to_text(c.get("companyDescription")) if c.get("companyDescription") else "",
        metadata={
            "company_name": nfc(c["companyName"]),
            "slogan": nfc(slogan) or None,
            "main_address": c.get("mainAddress"),
            "secondary_address": c.get("secondaryAddress"),
            "working_hours": c.get("workingHours"),
            "hotlines": c.get("hotlines") or None,
            "emails": c.get("emails") or None,
            "website": c.get("website"),
        },
    ))
    docs.append(KnowledgeDoc(
        doc_id="company_stats", source_table="companyInfo", source_id=c["id"],
        title=f"Số liệu hoạt động của {nfc(c['companyName'])}", doc_kind="company_stats", content="",
        metadata={
            "total_employees": c.get("totalEmployees"),
            "total_engineers": c.get("totalEngineers"),
            "total_architects": c.get("totalArchitects"),
            "total_projects": c.get("totalProjects"),
        },
    ))
    rep.log("companyInfo split into company_profile (descriptive) and company_stats (counts)")
    rep.log("companyInfo: socialLinks, thumbnail*, seo*, structuredData, timestamps excluded")

    # ---- taxonomies (one doc per table; avoids repeating nested objects per project) --------
    tax = [
        ("projectCategories", "taxonomy_project_categories", "Danh mục dự án"),
        ("architectureTypes", "taxonomy_architecture_types", "Các loại hình kiến trúc"),
        ("interiorStyles", "taxonomy_interior_styles", "Các phong cách nội thất"),
        ("newsCategories", "taxonomy_news_categories", "Chuyên mục tin tức"),
    ]
    for table, doc_id, title in tax:
        rows = sorted((r for r in t[table] if r.get("isActive", True)), key=lambda r: (r.get("order") or 0, r["id"]))
        items = []
        for r in rows:
            d = html_to_text(r.get("description"))
            items.append(nfc(r["name"]) + (f" ({d})" if d and d != r["name"] else ""))
        docs.append(KnowledgeDoc(
            doc_id=doc_id, source_table=table, source_id=None, title=title, doc_kind="taxonomy",
            content="Gồm: " + "; ".join(items) + ".", metadata={"items": [nfc(r["name"]) for r in rows]},
        ))
        rep.counters[f"{table}_items"] = len(rows)
    rep.log("taxonomy tables rendered once each (name list); slug/icon/imageUrl/seo/timestamps excluded")
    rep.log("nested category/interiorStyle/architectureType objects inside projects replaced by their names")

    # ---- projects ----------------------------------------------------------------------
    for p in sorted(t["projects"], key=lambda r: r["id"]):
        if p.get("status") != "PUBLISHED":
            rep.counters["projects_skipped_unpublished"] += 1
            continue
        invest_s, invest_v = parse_investment(p["title"])
        if invest_s:
            rep.counters["projects_with_investment_parsed"] += 1
        content = html_to_text(p.get("content")) if include_project_content else ""
        loc = p.get("location")
        if loc and loc != loc.strip():
            rep.counters["project_location_whitespace_trimmed"] += 1
        md = {
            "source_title": nfc(p["title"]),
            "category": (p.get("category") or {}).get("name"),
            "architecture_type": (p.get("architectureType") or {}).get("name"),
            "interior_style": (p.get("interiorStyle") or {}).get("name"),
            "investor": nfc(p["investor"].strip()) if p.get("investor") and p["investor"].strip() else None,
            "location": nfc(loc.strip()) if loc and loc.strip() else None,
            "area_m2": _num(p.get("area")),
            "investment": invest_s,
            "investment_vnd": invest_v,
            "completed_date": iso_date(p.get("completedDate")),
            "completed_date_source": p.get("completedDate"),
            "description": html_to_text(p.get("description")) or None,
        }
        for k in ("investor", "area_m2", "description", "interior_style", "architecture_type"):
            if md[k] is None:
                rep.counters[f"projects_missing_{k}"] += 1
        docs.append(KnowledgeDoc(
            doc_id=f"project_{p['id']}", source_table="projects", source_id=p["id"],
            title=short_project_name(p["title"]), content=content, metadata=md, doc_kind="project",
        ))
    rep.log("project title split: short name kept as title; 'Địa điểm/Mức đầu tư' fragments removed "
            "(full title preserved in metadata.source_title)")
    rep.log("project investment parsed from title into metadata.investment / investment_vnd")
    rep.log("dates normalised to ISO YYYY-MM-DD in metadata and rendered as DD/MM/YYYY; source value kept")
    rep.log("project fields excluded: slug, thumbnail*, seo*, structuredData (duplicates fields), viewCount, "
            "isFeatured, order, status (publication state), timestamps")
    rep.log(f"project HTML content {'included' if include_project_content else 'excluded (long marketing text)'}; "
            "project description converted from HTML")

    # ---- news ----------------------------------------------------------------------------
    news_cat = {r["id"]: nfc(r["name"]) for r in t["newsCategories"]}
    for n in sorted(t["news"], key=lambda r: r["id"]):
        if n.get("status") != "PUBLISHED":
            rep.counters["news_skipped_unpublished"] += 1
            continue
        body = html_to_text(n.get("content")) if include_news_content else html_to_text(n.get("excerpt"))
        docs.append(KnowledgeDoc(
            doc_id=f"news_{n['id']}", source_table="news", source_id=n["id"], title=nfc(n["title"].strip()),
            content=("Tóm tắt: " + body) if body else "", doc_kind="news",
            metadata={
                "news_category": news_cat.get(n["categoryId"]),
                "published_date": iso_date(n.get("publishedAt")),
                "related_project": n.get("projectId"),
            },
        ))
    rep.log(f"news: {'full content' if include_news_content else 'excerpt only'} (HTML stripped); "
            "author, thumbnail*, seo*, structuredData, readingTime, viewCount excluded")
    rep.counters["documents_total"] = len(docs)
    rep.counters.update(Counter(f"docs_{d.doc_kind}" for d in docs))
    return docs, rep
