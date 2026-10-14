"""Deterministic structured answer evaluators.

Each evaluator returns an outcome label:
  correct      - the expected (current) value is present and no obsolete value is
  stale        - an obsolete value is present and the current one is not
  mixed        - both current and obsolete values are present
  abstained    - the model said the information is unavailable
  wrong        - anything else
For 'abstain' questions, 'abstained' is the correct outcome and is mapped to correct.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date

ABSTAIN_PATTERNS = [
    "không có thông tin", "không được cung cấp", "không có dữ liệu", "chưa có thông tin",
    "không tìm thấy", "không được đề cập", "không đề cập", "không rõ", "không biết",
    "không có trong", "không được nêu", "không nêu", "không xác định", "chưa được cung cấp",
    "không có thông tin về", "không có số liệu", "không thể trả lời", "không thể xác định",
]
HONORIFICS = ("anh ", "chị ", "chi ", "bác ", "ông ", "bà ", "cô ", "chú ")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFC", s or "").lower()
    s = s.replace("đ", "đ")
    s = re.sub(r"[\"'“”‘’`*_]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def strip_diacritics(s: str) -> str:
    s = unicodedata.normalize("NFD", s).replace("đ", "d").replace("Đ", "D")
    return "".join(ch for ch in s if unicodedata.category(ch) != "Mn")


def is_abstention(answer: str) -> bool:
    a = norm(answer)
    return any(p in a for p in ABSTAIN_PATTERNS)


# ----------------------------------------------------------------------------- numbers

_NUM = re.compile(r"(?<![\w#])(\d+(?:[.,]\d+)*)(\s*(?:tỷ|triệu|nghìn|ngàn|k\b))?", re.IGNORECASE)
_DATE_LIKE = re.compile(r"\b\d{1,4}[/-]\d{1,2}[/-]\d{1,4}\b")
_PROJECT_REF = re.compile(r"#\s*\d+")
_MULT = {"tỷ": 1e9, "triệu": 1e6, "nghìn": 1e3, "ngàn": 1e3, "k": 1e3}


def number_interpretations(tok: str) -> set[float]:
    out = set()
    seps = re.findall(r"[.,]", tok)
    digits = re.sub(r"[.,]", "", tok)
    if not seps:
        return {float(tok)}
    out.add(float(digits))  # all separators are thousands separators
    if len(seps) == 1:
        out.add(float(tok.replace(",", ".")))  # single separator as decimal mark
    else:
        last = seps[-1]
        head, tail = tok.rsplit(last, 1)
        if all(s != last for s in seps[:-1]):  # mixed: 1.234,5 or 1,234.5
            out.add(float(re.sub(r"[.,]", "", head) + "." + tail))
    return out


def extract_numbers(text: str, with_multiplier: bool = False) -> set[float]:
    text = _PROJECT_REF.sub(" ", text)
    text = _DATE_LIKE.sub(" ", text)
    vals = set()
    for m in _NUM.finditer(text):
        base = number_interpretations(m.group(1))
        mult = 1.0
        if with_multiplier and m.group(2):
            mult = _MULT[m.group(2).strip().lower()]
        for b in base:
            vals.add(b * mult)
            vals.add(b)
    return vals


def _num_in(target: float, vals: set[float]) -> bool:
    return any(abs(v - float(target)) <= 1e-6 * max(1.0, abs(float(target))) for v in vals)


# ----------------------------------------------------------------------------- dates

_VI_DATE = re.compile(r"ngày\s*(\d{1,2})\s*tháng\s*(\d{1,2})\s*(?:năm|,)?\s*(\d{4})", re.IGNORECASE)
_DMY = re.compile(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})\b")
_YMD = re.compile(r"\b(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})\b")


def extract_dates(text: str) -> set[str]:
    out = set()

    def add(y, m, d):
        try:
            out.add(date(int(y), int(m), int(d)).isoformat())
        except ValueError:
            pass

    for d, m, y in _VI_DATE.findall(text):
        add(y, m, d)
    for d, m, y in _DMY.findall(text):
        add(y, m, d)
    for y, m, d in _YMD.findall(text):
        add(y, m, d)
    return out


# ----------------------------------------------------------------------------- text

def text_aliases(value: str, kind: str = "") -> list[str]:
    v = norm(value)
    al = {v}
    if kind == "location" and "," in v:
        first = v.split(",")[0].strip()
        if len(first) >= 3:
            al.add(first)
    if kind == "investor":
        for part in re.split(r",| và ", v):
            p = part.strip()
            al.add(p)
            for h in HONORIFICS:
                if p.startswith(h) and len(p) > len(h) + 1:
                    al.add(p[len(h):].strip())
    return sorted(a for a in al if a)


def _contains(answer_n: str, alias: str) -> bool:
    if alias in answer_n:
        return True
    return strip_diacritics(alias) in strip_diacritics(answer_n)


def _times(text: str) -> set[str]:
    return {f"{int(h)}:{m}" for h, m in re.findall(r"(\d{1,2})\s*[:hg]\s*(\d{2})", text)}


# ----------------------------------------------------------------------------- dispatcher

def _label(cur: bool, old: bool) -> str:
    if cur and old:
        return "mixed"
    if cur:
        return "correct"
    if old:
        return "stale"
    return "wrong"


def evaluate(question: dict, answer: str) -> dict:
    t = question["answer_type"]
    exp = question.get("expected_value")
    olds = question.get("old_values") or []
    abst = is_abstention(answer)

    if t == "abstain":
        return {"outcome": "correct" if abst else "wrong", "abstained": abst}
    if t == "numeric":
        vals = extract_numbers(answer)
        lab = _label(_num_in(exp, vals), any(_num_in(o, vals) for o in olds))
    elif t == "money":
        vals = extract_numbers(answer, with_multiplier=True)
        lab = _label(_num_in(exp, vals), any(_num_in(o, vals) for o in olds))
    elif t == "date":
        ds = extract_dates(answer)
        lab = _label(exp in ds, any(o in ds for o in olds))
    elif t == "text":
        a = norm(answer)
        kind = question.get("evidence_field", "")
        cur = any(_contains(a, x) for x in text_aliases(exp, kind))
        old = any(_contains(a, x) for o in olds for x in text_aliases(o, kind))
        lab = _label(cur, old)
    elif t == "time_range":
        ts = _times(answer)
        cur = _times(exp) <= ts and bool(_times(exp))
        old = any(_times(o) <= ts and bool(_times(o)) for o in olds)
        lab = _label(cur, old)
    elif t == "id":
        ids = {int(x) for x in re.findall(r"#?\s*(\d+)", answer)}
        lab = "correct" if int(exp) in ids else "wrong"
    elif t == "choice":
        opts = question["options"]  # list of project ids; expected_value is one of them
        names = question.get("option_names", {})
        a = norm(answer)
        pos = {}
        for o in opts:
            ps = [m.start() for m in re.finditer(rf"#\s*{o}\b|\bdự án {o}\b|^{o}\b", a)]
            nm = names.get(str(o))
            if nm and norm(nm) in a:
                ps.append(a.index(norm(nm)))
            if ps:
                pos[o] = min(ps)
        pred = min(pos, key=pos.get) if pos else None
        lab = "correct" if pred == exp else ("wrong" if pred is None or not olds else
                                             ("stale" if pred in olds else "wrong"))
    elif t == "yesno":
        a = norm(answer)
        if abst:
            pred = None
        elif re.match(r"^(không|sai|chưa)\b", a) or "không phải" in a or "không đúng" in a:
            pred = "no"
        elif re.match(r"^(có|đúng|phải|vâng|chính xác)\b", a):
            pred = "yes"
        else:
            pred = None
        lab = "correct" if pred == exp else ("stale" if pred is not None and question.get("stale_if") == pred else "wrong")
    else:
        raise ValueError(f"unknown answer_type {t}")
    if abst and lab == "wrong":
        lab = "abstained"
    return {"outcome": lab, "abstained": abst}
