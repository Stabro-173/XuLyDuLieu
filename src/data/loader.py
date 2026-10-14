"""Read-only loader and schema validator for the PostgreSQL JSON export."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from src.utils import sha256_file

REQUIRED_TOP_LEVEL = ("exportDate", "database", "tables")
REQUIRED_TABLES = (
    "companyInfo",
    "projects",
    "news",
    "projectCategories",
    "architectureTypes",
    "interiorStyles",
    "newsCategories",
)
REQUIRED_PROJECT_FIELDS = (
    "id", "title", "categoryId", "interiorStyleId", "architectureTypeId", "description",
    "content", "investor", "location", "area", "completedDate", "status",
    "category", "interiorStyle", "architectureType",
)
REQUIRED_NEWS_FIELDS = ("id", "title", "categoryId", "excerpt", "content", "status", "publishedAt")


class SchemaError(ValueError):
    pass


@dataclass
class RawExport:
    path: str
    sha256: str
    export_date: str
    database: str
    tables: dict
    record_counts: dict = field(default_factory=dict)


def load_export(path: str | Path) -> RawExport:
    """Load the export without modifying it and validate its structure."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    digest_before = sha256_file(path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    validate_export(data)
    counts = {k: len(v) for k, v in data["tables"].items() if isinstance(v, list)}
    if sha256_file(path) != digest_before:  # paranoia: the loader must be read-only
        raise RuntimeError("source file changed while loading")
    return RawExport(
        path=str(path),
        sha256=digest_before,
        export_date=data["exportDate"],
        database=data["database"],
        tables=data["tables"],
        record_counts=counts,
    )


def validate_export(data: dict) -> None:
    if not isinstance(data, dict):
        raise SchemaError("top level must be an object")
    for k in REQUIRED_TOP_LEVEL:
        if k not in data:
            raise SchemaError(f"missing top-level key: {k}")
    tables = data["tables"]
    if not isinstance(tables, dict):
        raise SchemaError("'tables' must be an object")
    for t in REQUIRED_TABLES:
        if t not in tables:
            raise SchemaError(f"missing table: {t}")
        if not isinstance(tables[t], list):
            raise SchemaError(f"table {t} must be a list")
    if len(tables["companyInfo"]) < 1:
        raise SchemaError("companyInfo is empty")
    ids = set()
    for p in tables["projects"]:
        for f in REQUIRED_PROJECT_FIELDS:
            if f not in p:
                raise SchemaError(f"project {p.get('id')} missing field {f}")
        if p["id"] in ids:
            raise SchemaError(f"duplicate project id {p['id']}")
        ids.add(p["id"])
    for n in tables["news"]:
        for f in REQUIRED_NEWS_FIELDS:
            if f not in n:
                raise SchemaError(f"news {n.get('id')} missing field {f}")
