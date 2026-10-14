import copy

import pytest

from src.data.documents import render_doc
from src.data.knowledge import KnowledgeSnapshot
from src.data.loader import SchemaError, load_export, validate_export
from src.data.partitioner import PartitionConfig, partition, partition_to_target_ratio
from src.data.preprocessor import build_documents, html_to_text, parse_investment, short_project_name
from src.data.qa_generator import QAGenerator, eligible_fields
from src.data.updates import UpdateFactory, apply_update, money_to_vnd
from src.utils import PROJECT_ROOT, sha256_file

RAW = PROJECT_ROOT / "data" / "raw" / "database_export_2026-01-23T02-02-46.json"


@pytest.fixture(scope="module")
def raw():
    return load_export(RAW)


@pytest.fixture(scope="module")
def docs(raw):
    return build_documents(raw)[0]


def test_record_counts(raw):
    c = raw.record_counts
    assert (c["companyInfo"], c["projects"], c["news"]) == (1, 49, 17)
    assert (c["projectCategories"], c["architectureTypes"], c["interiorStyles"], c["newsCategories"]) == (12, 15, 10, 4)


def test_loader_is_read_only(raw):
    assert sha256_file(RAW) == raw.sha256


def test_schema_validation_rejects_bad_input():
    with pytest.raises(SchemaError):
        validate_export({"exportDate": "x", "database": "y"})
    with pytest.raises(SchemaError):
        validate_export({"exportDate": "x", "database": "y", "tables": {"projects": []}})


def test_html_cleaning_keeps_vietnamese():
    s = html_to_text('<h2 data-start="1">Năm mới</h2> <p>kh&ocirc;ng để trống &ndash; m&atilde;i</p><img src="a.jpg">')
    assert s == "Năm mới\nkhông để trống – mãi"


def test_title_and_investment_parsing():
    t = "Resort Hải Vân 2. Địa điểm: Đà Nẵng. Mức đầu tư: 20 tỷ"
    assert short_project_name(t) == "Resort Hải Vân 2"
    assert parse_investment(t) == ("20 tỷ", 20_000_000_000)
    assert parse_investment("Nhà ở Gia đình 4x17. Địa điểm: Lào Cai. Mức đầu tư: 1,5 tỷ")[1] == 1_500_000_000
    assert parse_investment("Khách sạn nghỉ dưỡng. Địa điểm: Quận 9. Mức đầu tư:5 tỷ")[1] == 5_000_000_000
    assert parse_investment("Nhà ở gia đình 4x20m. Mức đầu tư 450 triệu")[1] == 450_000_000
    assert parse_investment("Căn hộ Phúc Đạt mẫu 1") == (None, None)


def test_documents_and_nulls(docs):
    ids = [d.doc_id for d in docs]
    assert len(ids) == len(set(ids)) == 72
    p77 = next(d for d in docs if d.doc_id == "project_77")
    assert p77.metadata["area_m2"] == 2306 and p77.metadata["location"] == "Hải Vân, Đà Nẵng"
    assert "Mức đầu tư: 20 tỷ đồng" in p77.text and "Diện tích: 2306 m²" in p77.text
    assert "Ngày hoàn thành: 13/01/2026" in p77.text
    p72 = next(d for d in docs if d.doc_id == "project_72")  # area is null in the source
    assert p72.metadata["area_m2"] is None and "Diện tích" not in p72.text
    assert "http" not in "".join(d.text for d in docs if d.doc_kind == "project")  # no image URLs


def test_conflicting_description_excluded(docs):
    p46 = next(d for d in docs if d.doc_id == "project_46")  # description says 135m², field says 171.6
    assert "area_m2" not in eligible_fields(p46)


def test_partition_and_ratio(docs):
    ordered, why = partition(docs, PartitionConfig())
    snap = KnowledgeSnapshot(0, ordered)
    snap.validate_order()
    assert {d.doc_kind for d in snap.stable_docs} == {"company_profile", "taxonomy", "news"}
    cfg = PartitionConfig.from_dict({"overrides": {"news_46": "dynamic"}})
    o2, _ = partition(docs, cfg)
    assert next(d for d in o2 if d.doc_id == "news_46").knowledge_type == "dynamic"
    tc = lambda d: len(d.text)
    for target in (0.0, 0.5, 0.9):
        o = partition_to_target_ratio(docs, target, {"project_77"}, tc)
        KnowledgeSnapshot(0, o).validate_order()
        st = sum(tc(d) for d in o if d.knowledge_type == "stable") / sum(tc(d) for d in o)
        assert abs(st - target) < 0.1
        assert next(d for d in o if d.doc_id == "project_77").knowledge_type == "dynamic"
        assert sorted(d.doc_id for d in o) == sorted(d.doc_id for d in docs)  # same content


def test_updates_are_versioned_and_non_mutating(docs):
    ordered, _ = partition(docs, PartitionConfig())
    s0 = KnowledgeSnapshot(0, ordered)
    before = copy.deepcopy(s0.to_dict())
    fac = UpdateFactory(0, "")
    ev = fac.field_update(s0, [("project_77", "area_m2"), ("project_77", "investment")], "multi")
    s1 = apply_update(s0, ev)
    assert s0.to_dict() == before
    assert s1.version == 1 and s1.doc("project_77").version == 1
    assert s1.doc("project_77").metadata["area_m2"] != 2306
    assert s1.doc("project_77").metadata["investment_vnd"] == money_to_vnd(s1.doc("project_77").metadata["investment"])
    assert all(c.old_value != c.new_value for c in ev.changes) and ev.is_synthetic
    with pytest.raises(ValueError):  # replaying against the wrong version is rejected
        apply_update(s1, ev)
    # determinism
    ev2 = UpdateFactory(0, "").field_update(s0, [("project_77", "area_m2"), ("project_77", "investment")], "multi")
    assert [c.new_value for c in ev.changes] == [c.new_value for c in ev2.changes]


def test_qa_ground_truth_from_snapshot(docs):
    ordered, _ = partition(docs, PartitionConfig())
    s0 = KnowledgeSnapshot(0, ordered)
    fac = UpdateFactory(1, "")
    ev = fac.field_update(s0, [("project_77", "area_m2")], "numeric_area")
    s1 = apply_update(s0, ev)
    qs = QAGenerator(1).generate(s1, [ev], {})
    a = [q for q in qs if q["group"] == "A"]
    assert len(a) == 1 and a[0]["expected_value"] == float(s1.doc("project_77").metadata["area_m2"])
    assert a[0]["old_values"] == [2306.0]
    assert {q["group"] for q in qs} == {"A", "B", "C", "D", "E"}
    for q in qs:
        if q["group"] == "B" and q["answer_type"] == "numeric" and q["source_doc_id"].startswith("project"):
            d = s1.doc(q["source_doc_id"])
            assert q["expected_value"] == float(d.metadata[q["evidence_field"]])


def test_render_is_deterministic(docs):
    d = docs[10]
    assert render_doc(d) == render_doc(d.clone())
