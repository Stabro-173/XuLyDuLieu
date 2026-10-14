"""Token-level bookkeeping: offsets, char->token boundaries, verified reusable prefixes."""
from __future__ import annotations

import bisect
from dataclasses import dataclass

from src.data.knowledge import SerializedKnowledge


@dataclass
class TokenizedKnowledge:
    ids: list[int]
    offsets: list[tuple[int, int]]
    doc_token_spans: dict[str, tuple[int, int]]  # doc_id -> [start, end) token indices
    stable_token_end: int  # token index where the dynamic suffix starts
    header_token_end: int  # token index where the first document starts

    def __len__(self) -> int:
        return len(self.ids)


def tokenize_with_offsets(tokenizer, text: str) -> tuple[list[int], list[tuple[int, int]]]:
    enc = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)
    return list(enc["input_ids"]), [tuple(o) for o in enc["offset_mapping"]]


def char_to_token_boundary(offsets: list[tuple[int, int]], char_pos: int) -> int:
    """Largest i such that every token < i ends at or before char_pos (tokens spanning the
    boundary are assigned to the right-hand side, i.e. are *not* considered reusable)."""
    ends = [e for _, e in offsets]
    i = bisect.bisect_right(ends, char_pos)
    # ends are monotone for a left-to-right tokenizer; guard anyway
    while i > 0 and offsets[i - 1][1] > char_pos:
        i -= 1
    return i


def tokenize_knowledge(tokenizer, ser: SerializedKnowledge) -> TokenizedKnowledge:
    ids, offs = tokenize_with_offsets(tokenizer, ser.text)
    spans = {}
    for doc_id, (cs, ce) in ser.doc_spans.items():
        spans[doc_id] = (char_to_token_boundary(offs, cs), char_to_token_boundary(offs, ce))
    return TokenizedKnowledge(
        ids=ids, offsets=offs, doc_token_spans=spans,
        stable_token_end=char_to_token_boundary(offs, ser.stable_char_end),
        header_token_end=char_to_token_boundary(offs, ser.first_doc_char),
    )


def common_prefix_len(a: list[int], b: list[int]) -> int:
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


@dataclass
class ReuseDecision:
    proposed: int  # reuse length requested by the strategy
    verified: int  # after token-identity verification
    shortened: bool
    lcp: int


def verify_reuse(old_ids: list[int], new_ids: list[int], proposed: int) -> ReuseDecision:
    """Never reuse more than the verified identical token prefix of old and new sequences."""
    lcp = common_prefix_len(old_ids, new_ids)
    v = max(min(proposed, lcp), 0)
    return ReuseDecision(proposed=proposed, verified=v, shortened=v < proposed, lcp=lcp)
