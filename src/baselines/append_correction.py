"""B2 - Append Correction: keep the original cache and append an explicit, versioned correction
notice after the knowledge, prefilling only the appended tokens. The sequence grows with every
update and contains contradictory historical values by construction."""
from __future__ import annotations

from src.baselines.base import Baseline
from src.cache.token_boundaries import tokenize_with_offsets
from src.data.documents import FIELD_LABELS, KnowledgeDoc, render_field
from src.utils import timed

UPDATES_HEADER = ("\n\n## THÔNG BÁO CẬP NHẬT (các thông báo dưới đây mới hơn và thay thế dữ liệu tương ứng "
                  "ở phần trên; thông báo sau thay thế thông báo trước)")


def _value_text(doc: KnowledgeDoc, field: str, value) -> str:
    tmp = doc.clone()
    tmp.metadata[field] = value
    line = render_field(tmp, field)
    return line.split(": ", 1)[1] if line else "(không có)"


def _subject(doc: KnowledgeDoc) -> str:
    if doc.doc_kind == "project":
        return f"Dự án #{doc.source_id} ({doc.title})"
    if doc.doc_kind == "news":
        return f"Bài viết #{doc.source_id} ({doc.title})"
    return doc.title


def correction_text(event, before_snapshot, n: int, first: bool) -> str:
    lines = [UPDATES_HEADER] if first else []
    lines.append(f"\n\n[CẬP NHẬT {n}] Thông báo cập nhật số {n} (phiên bản dữ liệu "
                 f"{event.version_before} → {event.version_after}):")
    for ch in event.changes:
        d = before_snapshot.doc(ch.doc_id)
        label = FIELD_LABELS.get(ch.field, ch.field)
        lines.append(f"\n- {_subject(d)}: {label} đã thay đổi từ {_value_text(d, ch.field, ch.old_value)} "
                     f"thành {_value_text(d, ch.field, ch.new_value)}. Giá trị mới thay thế giá trị cũ.")
    for doc_id in event.deleted_doc_ids:
        d = before_snapshot.doc(doc_id)
        lines.append(f"\n- {_subject(d)} [{doc_id}] đã bị gỡ khỏi cơ sở tri thức; mọi thông tin về nó "
                     "không còn hiệu lực.")
    for ad in event.added_docs:
        d = KnowledgeDoc.from_dict(ad)
        lines.append(f"\n- Bổ sung tài liệu mới:\n{d.text}")
    return "".join(lines)


class AppendCorrection(Baseline):
    name = "B2_append_correction"
    label = "B2 Append Correction"
    exact = False

    def reset(self) -> None:
        super().reset()
        self.corrections: list[str] = []
        self.base_tokens = 0

    def initialize(self, snapshot):
        row = super().initialize(snapshot)
        self.base_tokens = len(self.ids)
        return row

    def update(self, event, snapshot) -> dict:
        t: dict = {}
        before = self.snapshot  # logical knowledge the correction refers to
        with timed(t, "serialization_s", sync=False):
            txt = correction_text(event, before, len(self.corrections) + 1, first=not self.corrections)
        with timed(t, "tokenization_s", sync=False):
            add_ids, _ = tokenize_with_offsets(self.engine.tok, txt)
        self.engine.mem_reset_peak()
        reused = len(self.ids)
        with timed(t, "prefill_s"):
            self.cache, _ = self.engine.prefill(add_ids, self.cache)
        self.ids = self.ids + add_ids
        self.corrections.append(txt)
        self.snapshot = snapshot  # logical version tracked; physical cache still holds old values
        self.n_updates += 1
        self.last_update = self._stats_row(t, reused=reused, recomputed=len(add_ids),
                                           correction_tokens_total=len(self.ids) - self.base_tokens,
                                           n_corrections=len(self.corrections))
        return self.last_update

    def get_cache_statistics(self) -> dict:
        s = super().get_cache_statistics()
        s["cache_tokens_effective"] = len(self.ids)
        s["correction_tokens_total"] = len(self.ids) - self.base_tokens
        return s
