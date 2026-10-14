"""Versioned knowledge snapshots and their serialisation into the cached prompt prefix.

Layout of the cached knowledge sequence (all methods share it):

    <chat-template system prefix>{INSTRUCTION}
    === CƠ SỞ TRI THỨC ===
    ## PHẦN A ... (stable documents)
    ## PHẦN B ... (dynamic documents)
                                        <- knowledge cache ends here (system turn NOT closed)
    <|im_end|>\\n<|im_start|>user\\n{question}<|im_end|>\\n<|im_start|>assistant\\n   <- per question

The system turn is left open so append-only corrections (B2) can be added inside it.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.data.documents import KnowledgeDoc
from src.utils import sha256_text

INSTRUCTION = (
    "Bạn là trợ lý hỏi đáp của công ty kiến trúc Nguyen Minh Khang Architects. "
    "Chỉ trả lời dựa trên CƠ SỞ TRI THỨC bên dưới, không suy đoán. "
    "Trả lời trực tiếp bằng một câu ngắn tiếng Việt, nêu ngay giá trị được hỏi, không lặp lại câu hỏi. "
    "Nếu một mục được ghi nhận trong THÔNG BÁO CẬP NHẬT thì giá trị mới nhất thay thế giá trị cũ. "
    "Nếu cơ sở tri thức không có thông tin để trả lời, hãy trả lời: \"Không có thông tin.\""
)
KB_HEADER = "\n\n=== CƠ SỞ TRI THỨC ===\n\n## PHẦN A: KIẾN THỨC NỀN TẢNG\n"
DYN_HEADER = "\n\n## PHẦN B: DỮ LIỆU CẬP NHẬT THƯỜNG XUYÊN\n"
DOC_SEP = "\n\n"


@dataclass
class KnowledgeSnapshot:
    version: int
    docs: list[KnowledgeDoc]  # ordered: stable docs first, then dynamic

    def doc(self, doc_id: str) -> KnowledgeDoc:
        for d in self.docs:
            if d.doc_id == doc_id:
                return d
        raise KeyError(doc_id)

    def has(self, doc_id: str) -> bool:
        return any(d.doc_id == doc_id for d in self.docs)

    @property
    def stable_docs(self) -> list[KnowledgeDoc]:
        return [d for d in self.docs if d.knowledge_type == "stable"]

    @property
    def dynamic_docs(self) -> list[KnowledgeDoc]:
        return [d for d in self.docs if d.knowledge_type == "dynamic"]

    def validate_order(self) -> None:
        seen_dynamic = False
        for d in self.docs:
            if d.knowledge_type == "dynamic":
                seen_dynamic = True
            elif seen_dynamic:
                raise ValueError(f"stable doc {d.doc_id} after a dynamic doc")
        ids = [d.doc_id for d in self.docs]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate doc ids in snapshot")

    def clone(self) -> "KnowledgeSnapshot":
        return KnowledgeSnapshot(self.version, [d.clone() for d in self.docs])

    def to_dict(self) -> dict:
        return {"version": self.version, "docs": [d.to_dict() for d in self.docs]}

    @staticmethod
    def from_dict(d: dict) -> "KnowledgeSnapshot":
        return KnowledgeSnapshot(d["version"], [KnowledgeDoc.from_dict(x) for x in d["docs"]])


@dataclass
class SerializedKnowledge:
    text: str  # full knowledge prefix text (includes chat-template system prefix)
    doc_spans: dict[str, tuple[int, int]]  # doc_id -> (char_start, char_end) in text
    doc_order: list[str]
    stable_char_end: int  # char offset where the dynamic suffix (first dynamic doc) begins
    first_doc_char: int  # char offset of the first document (end of the instruction header)
    hashes: dict[str, str] = field(default_factory=dict)

    @property
    def text_hash(self) -> str:
        return sha256_text(self.text)


@dataclass
class PromptTemplate:
    """Pieces of the model chat template around the knowledge and the question."""
    pre: str  # before knowledge (e.g. '<|im_start|>system\\n')
    mid: str  # between knowledge and question
    post: str  # after question (generation prompt)

    @staticmethod
    def from_tokenizer(tokenizer) -> "PromptTemplate":
        kb, q = "\x00KB\x00", "\x00Q\x00"
        s = tokenizer.apply_chat_template(
            [{"role": "system", "content": kb}, {"role": "user", "content": q}],
            tokenize=False, add_generation_prompt=True,
        )
        i, j = s.index(kb), s.index(q)
        return PromptTemplate(pre=s[:i], mid=s[i + len(kb):j], post=s[j + len(q):])

    def question_text(self, question: str) -> str:
        return self.mid + question + self.post


def serialize(snapshot: KnowledgeSnapshot, template: PromptTemplate) -> SerializedKnowledge:
    snapshot.validate_order()
    parts: list[str] = [template.pre, INSTRUCTION, KB_HEADER]
    pos = sum(len(p) for p in parts)
    first_doc_char = pos
    spans, order, hashes = {}, [], {}
    stable_char_end = None
    for i, d in enumerate(snapshot.docs):
        if d.knowledge_type == "dynamic" and stable_char_end is None:
            parts.append(DYN_HEADER)
            pos += len(DYN_HEADER)
            stable_char_end = pos
            first_in_section = True
        else:
            first_in_section = i == 0
        if not first_in_section:
            parts.append(DOC_SEP)
            pos += len(DOC_SEP)
        t = d.text
        spans[d.doc_id] = (pos, pos + len(t))
        parts.append(t)
        pos += len(t)
        order.append(d.doc_id)
        hashes[d.doc_id] = d.content_hash
    if stable_char_end is None:  # no dynamic docs: header still emitted so the layout is constant
        parts.append(DYN_HEADER)
        pos += len(DYN_HEADER)
        stable_char_end = pos
    text = "".join(parts)
    assert len(text) == pos
    return SerializedKnowledge(text, spans, order, stable_char_end, first_doc_char, hashes)
