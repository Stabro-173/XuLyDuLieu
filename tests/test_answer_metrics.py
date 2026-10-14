from src.evaluation.answer_metrics import evaluate, extract_dates, extract_numbers, is_abstention


def q(**kw):
    return {"answer_type": "numeric", "old_values": [], **kw}


def test_numbers_vietnamese_formats():
    assert 2306 in extract_numbers("Diện tích là 2.306 m²")
    assert 171.6 in extract_numbers("171,6 m2")
    assert 2.5e9 in extract_numbers("Mức đầu tư 2,5 tỷ đồng", with_multiplier=True)
    assert 77 not in extract_numbers("Dự án #77 có diện tích 2450 m²")


def test_numeric_outcomes():
    base = q(expected_value=2450.0, old_values=[2306.0])
    assert evaluate(base, "Diện tích là 2450 m².")["outcome"] == "correct"
    assert evaluate(base, "Diện tích là 2306 m².")["outcome"] == "stale"
    assert evaluate(base, "Trước 2306 m², nay 2450 m².")["outcome"] == "mixed"
    assert evaluate(base, "Khoảng 100 m².")["outcome"] == "wrong"
    assert evaluate(base, "Không có thông tin.")["outcome"] == "abstained"


def test_money_and_date():
    m = q(answer_type="money", expected_value=24_000_000_000, old_values=[20_000_000_000])
    assert evaluate(m, "24 tỷ đồng")["outcome"] == "correct"
    assert evaluate(m, "20 tỷ")["outcome"] == "stale"
    d = q(answer_type="date", expected_value="2026-01-13", old_values=["2025-03-02"])
    assert extract_dates("ngày 13 tháng 1 năm 2026") == {"2026-01-13"}
    assert evaluate(d, "Hoàn thành ngày 13/01/2026.")["outcome"] == "correct"
    assert evaluate(d, "02/03/2025")["outcome"] == "stale"


def test_text_choice_yesno_abstain():
    t = q(answer_type="text", expected_value="Cần Thơ", old_values=["Hải Vân, Đà Nẵng"], evidence_field="location")
    assert evaluate(t, "Dự án ở Cần Thơ.")["outcome"] == "correct"
    assert evaluate(t, "Dự án ở Hải Vân.")["outcome"] == "stale"
    c = q(answer_type="choice", expected_value=77, options=[77, 76], option_names={}, old_values=[76])
    assert evaluate(c, "Dự án #77 có diện tích lớn hơn dự án #76.")["outcome"] == "correct"
    assert evaluate(c, "#76")["outcome"] == "stale"
    y = q(answer_type="yesno", expected_value="no", stale_if="yes")
    assert evaluate(y, "Không, diện tích hiện tại là 2450 m².")["outcome"] == "correct"
    assert evaluate(y, "Có.")["outcome"] == "stale"
    a = q(answer_type="abstain", expected_value=None)
    assert evaluate(a, "Không có thông tin.")["outcome"] == "correct"
    assert evaluate(a, "Diện tích là 100 m².")["outcome"] == "wrong"
    assert is_abstention("Cơ sở tri thức không đề cập đến điều này.")
