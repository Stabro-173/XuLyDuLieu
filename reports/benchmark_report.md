# Dynamic Knowledge Updating in Cache-Augmented Generation: Full Recompute, Append Correction, Document-Level Caching and Layered CAG

*All numbers in this report come from executions of the code in this repository on the hardware stated in §6.
Nothing is simulated. Sections that could not be run are marked **NOT RUN**.*

## 1. Abstract

Cache-Augmented Generation (CAG) prefills a knowledge base once and reuses its KV cache for every question,
which breaks when the knowledge changes. We built a reproducible benchmark on a real Vietnamese
architecture-company database export (49 projects, 17 news items, company profile, 4 taxonomies; 72
canonical documents, 10.6K tokens) and compared six update strategies plus one approximate variant:
stale cache (B0), full recompute (B1), append-only correction (B2), exact document-boundary reuse (B3),
approximate independent per-document caches with RoPE re-rotation (B3a), **Layered CAG** — a reusable stable
prefix followed by a recomputed dynamic suffix (B4) — and token-level longest-common-prefix reuse (B5).

Exact-cache validation on ten mandated edit scenarios shows that B3, B4 and B5 reproduce the full-prefill
cache of B1 within floating-point tolerance on both models tested (10/10 scenarios each; max relative KV
deviation 3.7e-7 in fp32 and 1.2e-3 in fp16), while B3a deviates strongly (0/10; first-token logits off by
up to 13.9). On the main comparison (33 conditions, 11 update types × 3 seeds, Qwen2.5-0.5B-Instruct fp32,
≈2K-token context) Layered CAG matched full recompute exactly in accuracy (81.1 % vs 81.1 % on updated
facts, identical generated tokens on 100 % of questions) while cutting update latency 2.4× (470 ms vs
1125 ms). It was, however, **slower than token-level prefix invalidation (293 ms) and exact document-level
reuse (327 ms)** in almost every condition, because it always recomputes the whole dynamic suffix; its
latency is flat in the edit position whereas B3/B5 approach zero cost for edits near the end. Its
benefit is governed by the stable-prefix ratio (1.2× speed-up at 9 % stable tokens, 7.1× at 89 %).
Append correction was the cheapest update (150 ms) but the model kept returning obsolete values
(21.6 % stale + 8.1 % mixed answers on updated facts) and accuracy degraded as corrections accumulated.
The central hypothesis is therefore **supported for correctness and partially supported for efficiency**:
Layered CAG preserves full-prefill behaviour and is cheaper than recomputation, but it is dominated by
finer-grained exact prefix reuse on this workload.

On the primary model, Qwen2.5-1.5B-Instruct in fp16 (19 conditions at ≤ 2K tokens), the picture is the
same: B4 matched B1 on every accuracy group (86.7 % on updated facts in the main comparison) and halved update
latency (8.2 s vs 16.7 s on this GPU), B5 (4.4 s) and B3 (5.0 s) were faster still, and B2 (1.6 s) was the
cheapest update. Because fp16 rounding differs between a full and a suffix prefill, exact methods produced
token-identical generations to B1 on 98.5 % (931/945) of answers; every divergence was a first-token near tie.

## 2. Research motivation

In CAG the knowledge cache is valid only for the exact token sequence it was computed from: causal
attention makes every KV entry a function of all earlier tokens. Editing a value in the middle of the
knowledge therefore invalidates every cached position from the edit onwards, and enterprise knowledge
(project areas, budgets, completion dates, company counts) does change. The trade-off is between
freshness, answer quality, update latency and cache reuse. Layered CAG is an evaluated application of a
known idea (prefix caching) as a *structuring* strategy: put rarely changing knowledge first so its cache
can be kept, and put volatile knowledge last. We do not claim it is a novel algorithm.

Research questions: RQ1 accuracy after updates vs full recompute; RQ2 update latency saved; RQ3 effect of
the stable-prefix ratio; RQ4 effect of the edit position; RQ5 preservation of unchanged facts; RQ6
latency/memory/reuse/quality trade-offs.

## 3. Dataset

Source: `database_export_2026-01-23T02-02-46.json` (PostgreSQL export, SHA-256
`b38e8cf0…a4007c598`, never modified; checked on every load).

| Table | Records | Used as |
|---|---|---|
| companyInfo | 1 | split into `company_profile` (descriptive) and `company_stats` (counts) |
| projects | 49 | one document each |
| news | 17 | one document each (excerpt; full HTML body excluded) |
| projectCategories / architectureTypes / interiorStyles / newsCategories | 12 / 15 / 10 / 4 | one taxonomy document per table |
| heroSlides / settings / users | 10 / 0 / 0 | excluded (UI content or empty) |

Preprocessing (`src/data/preprocessor.py`, log in `data/processed/dataset_profile.json`): HTML → plain
text with BeautifulSoup (entities decoded, tags/attributes/images removed, Vietnamese NFC preserved); project
titles such as *"Resort Hải Vân 2. Địa điểm: Đà Nẵng. Mức đầu tư: 20 tỷ"* split into a short name and a
parsed investment field (42/49 projects); nested category objects replaced by names; dates normalised to
ISO and rendered DD/MM/YYYY; image URLs, SEO fields, `structuredData` duplicates, view counts and
timestamps excluded; null fields omitted from the text, never filled. Every document is rendered
deterministically from its structured fields, so a synthetic update changes exactly one rendered line.

Data-quality findings: 4 projects have no area, 1 no investor, 11 no interior style, 36 no description;
some descriptions contradict their own structured fields (e.g. project #46: description says 135 m² in
Tân Phú, fields say 171.6 m² in Nhơn Hải). Facts contradicted inside their own document are excluded from
question generation and synthetic updates. 366 unambiguous facts remain. Token counts with the Qwen2.5
tokenizer: projects 6,255, news 3,710, company profile 312, taxonomies 273, company stats 55 (total 10,605).

**Partition.** Default rules (`configs/partition.yaml`): company profile, taxonomies and news are *stable*;
company stats and projects are *dynamic*; per-document overrides are supported. The stable-ratio ablation
instead moves non-target documents into the stable prefix until a target token share is reached, keeping
the document set identical. Manifest with order, token counts, hashes and rationale:
`data/processed/partition_manifest.json`.

## 4. Methodology

**Prompt layout.** `[chat-template system prefix][instruction][=== CƠ SỞ TRI THỨC === / PHẦN A: stable docs][PHẦN B: dynamic docs]`
is the cached knowledge; the system turn is left open so B2 can append inside it. Each question is
`<|im_end|>\n<|im_start|>user\n{q}<|im_end|>\n<|im_start|>assistant\n`, prefilled on top of the cache; after
greedy decoding (≤ 32 new tokens) the cache is cropped back to the knowledge length and this is asserted
after every answer, so question KV never leaks between questions. Tokenising knowledge and question
separately was verified to equal tokenising the full prompt.

**Synthetic updates** (`src/data/updates.py`): deterministic (seeded), flagged `is_synthetic`, applied to deep
copies of versioned snapshots: numeric (area ×0.55–0.85 or ×1.2–1.8; investment; company project count +3…15),
text (location / investor from pools that occur nowhere in the source), date (±90–500 days), multi-field,
multi-document, repeated (v0→v1→v2→v3 on one field), sequential k-update chains, document append, document
delete, and a *stable* document edit (company working hours).

**Questions** (`src/data/qa_generator.py`), generated from the final snapshot of each condition, ground
truth read from structured fields: A updated facts (with the obsolete values recorded), B unchanged facts
(including other fields of updated documents), C yes/no probes of the obsolete and of the current value,
D cross-document area comparisons (pairs whose answer flips because of the update are preferred), E
unanswerable (null source fields, non-existent project ids, absent attributes, deleted documents).
Projects are referenced by canonical id (`#77`) because several titles are duplicated.

**Evaluation** (`src/evaluation/answer_metrics.py`) is deterministic: Vietnamese number parsing
(`2.306`, `171,6`, `2,5 tỷ`), date parsing (`13/01/2026`, `ngày 13 tháng 1 năm 2026`), diacritic-tolerant
text matching with location/investor aliases, yes/no and abstention patterns, and first-mentioned-option
for comparisons. Outcomes are *correct*, *stale* (obsolete value only), *mixed* (both), *abstained*,
*wrong*. Agreement with B1 (identical generated token ids) is reported separately from correctness.

**Metrics.** Update latency = serialisation + tokenisation + cache management + prefill, CUDA-synchronised,
excluding answer generation and model loading. Query latency = time to first token and total generation.
Cache reuse ratio = verified reused knowledge tokens / tokens of the updated knowledge (reused-but-invalid
tensors of B0 and approximate chunks of B3a count as 0). GPU memory: peak allocated and peak reserved,
reset before each phase.

## 5. Baseline implementations

All methods implement `initialize / update / answer / get_cache_statistics / reset`
(`src/baselines/`). B1, B3, B4, B5 share one exact mechanism — keep a prefix of the old cache, crop, prefill
the rest — and differ only in how many tokens they propose to keep. Every proposal is clamped by
`verify_reuse` to the token-level common prefix of the old and new sequences, so no KV entry whose causal
history changed can be reused even if a document boundary falls inside a merged BPE token (observed: for an
appended document the boundary sits after a `\n\n` token and the proposal is shortened by 2 tokens).

| ID | Proposed reuse length |
|---|---|
| B0 | — (no update; original cache kept) |
| B1 | 0 |
| B2 | entire old sequence; a versioned Vietnamese "update notice" with explicit supersession is appended and prefilled |
| B3 | start token of the first changed document |
| B3a | approximate: header KV + independently prefilled per-document KV, keys re-rotated by Δposition with R(p+Δ)=R(Δ)R(p) |
| B4 | stable/dynamic boundary if only dynamic documents changed; otherwise start of the first changed stable document |
| B5 | full new sequence (→ clamped to the token LCP) |

B3a is labelled APPROXIMATE everywhere: its token sequence equals the canonical one, but no document can
attend to an earlier document, so it is not equivalent to a jointly prefilled causal sequence. The RoPE
re-rotation itself is unit-tested (layer-0 keys re-rotated from position p to p+37 equal keys computed at p+37).

## 6. Experimental setup

**Hardware actually used: NVIDIA GeForce GTX 1650, 4 GB (driver 610.62), Windows 11, Python 3.11.9,
torch 2.9.1+cu128, transformers 5.19.0** (`requirements.lock.txt`). The target T4 was not available; the
Colab notebook (`notebooks/colab_benchmark.ipynb`) runs the SMOKE profile on a T4 but was **NOT RUN** by us.

Measured hardware constraints and the adjustments they forced (all recorded in the configs):

1. fp16 GEMM on this GPU runs at 0.34 TFLOPS versus 1.84 TFLOPS for fp32. Qwen2.5-1.5B-Instruct only fits in
   fp16 (2.9 GB of weights in a 3.30 GB usable budget) and prefills 2K tokens in ≈16.7 s.
2. Windows' driver does not raise out-of-memory: it silently pages device allocations to system RAM. Without a
   guard, a 4K-token 1.5B prefill "succeeded" in 126 s at 5 GB peak. We added a **VRAM-spill guard**: the
   usable budget is measured before loading weights and every run whose peak reserved memory exceeds it is
   marked `vram_spill` and excluded from all summaries (rows are kept for transparency).
3. SDPA on sm75 materialises the full attention matrix for long prompts. We use **position-aligned chunked
   prefill** (chunks of 1024 tokens for 0.5B, 512 for 1.5B; boundaries at absolute multiples of the chunk
   size) for every method, which bounds activation memory and computes the same causal function.

Consequently two model configurations were run:

| Profile | Model (pinned revision) | dtype | Grid | Status |
|---|---|---|---|---|
| `pilot_q05_fp32` | Qwen2.5-0.5B-Instruct (`7ae5576`) — **substitute** | fp32 | full PILOT: 50 conditions, budgets 1K–8K, 7 methods × 3 reps | 1050/1050 runs, 0 failures |
| `reduced_q15_fp16` | Qwen2.5-1.5B-Instruct (`989aa79`) — **primary** | fp16 | 19 conditions at ≤ 2K tokens, 6 methods × 2 reps | 228/228 valid runs (+7 B3a runs flagged `vram_spill`), 0 errors |
| FULL profile (5 seeds, 4K/8K with 1.5B) | — | — | — | **NOT RUN** (does not fit this GPU) |

The two models share a byte-identical tokenizer, so conditions, token boundaries and questions are identical.
Generation: greedy, ≤ 32 new tokens, chat template, `torch.inference_mode`, seeds fixed, method order shuffled
per repetition, 3 warm-up passes, accuracy from repetition 0, latency from all repetitions.

PILOT grid (`configs/local_pilot_q05_fp32.yaml`): update types (11 types × 3 seeds, 2K, middle position);
edit position (begin/middle/end × 2 seeds); stable ratio (targets 0/25/50/75/90 %); context length (1K/2K/4K/8K);
sequential chains (k = 1/3/5/10); repeated update of one field (3 versions). Coverage: 50 conditions,
67 update events, 854 questions (A 74, B 380, C 106, D 144, E 150), 28+ distinct source documents.

## 7. Cache correctness validation

`scripts/validate_cache.py`, ten mandated scenarios at a 2K budget, each method initialised on v0 and updated
to v1, compared with a one-shot B1 prefill of v1. Tolerances were fixed before the runs (fp32: relative KV
≤ 1e-4, logits ≤ 1e-3; fp16: relative KV ≤ 1e-2, logits ≤ 0.5). Results:
`results/pilot_q05_fp32/cache_validation.json`, `results/reduced_q15_fp16/cache_validation.json`.

| Model | Method | PASS | max rel. KV dev. | max first-token logit dev. | generated-token agreement |
|---|---|---|---|---|---|
| 0.5B fp32 | B3 / B4 / B5 | 10/10 each | 3.4e-7 / 2.8e-7 / 3.7e-7 | ≤ 3.4e-5 | 100 % |
| 0.5B fp32 | B3a (approx.) | 0/10 | 5.8e-2 | 7.7 | 0 % |
| 1.5B fp16 | B3 / B4 / B5 | 10/10 each | 7.8e-4 / 1.2e-3 / 7.8e-4 | ≤ 0.061 | 100 % |
| 1.5B fp16 | B3a (approx.) | 0/10 | 6.1e-2 | 13.9 | 0 % |

Scenarios: no change; first / middle / last dynamic document; single numeric field; token-count-changing edit;
append; delete; multiple documents; **stable document edit** — where B4 correctly falls back to the edited
stable document (156 reused tokens instead of the 1,229-token stable prefix). The 30 unit tests
(`tests/`) repeat the same ten scenarios on a tiny random fp32 Qwen2 model and additionally check cache
non-contamination by questions, reuse ordering (B5 ≥ B3 ≥ B4 for dynamic edits) and RoPE re-rotation.

**Exact reuse ≠ bit-identical outputs in fp16.** In the 1.5B benchmark 11 of 589 exact-method answers
(1.9 %) differ from B1's. In every inspected case the cached token sequence was identical to B1's and the
first generated token was a near tie (top-1/top-2 logit margin 0.000–0.078, max logit difference 0.053):
chunk boundaries differ between a full prefill and a suffix prefill, and fp16 reassociation flips the tie.
Two of the divergent pairs ran in different processes, where even B1 alone is not bit-reproducible. The
effect is symmetric (correct→wrong and wrong→correct) and leaves mean accuracy unchanged. In fp32 (0.5B) the
agreement was 100 % on all 2,562 exact-method answers.

## 8. Performance results

### 8.1 Main comparison — Qwen2.5-0.5B fp32, 33 conditions (11 update types × 3 seeds, ≈2,040 tokens)

| Method | update latency (ms) | speed-up vs B1 | prefill share (ms) | valid reuse | final context | peak alloc. (MB) |
|---|---|---|---|---|---|---|
| B0 Stale | 0 | — | 0 | — (invalid) | 2,037 | 2,074 |
| B1 Full Recompute | 1,125 | 1.0× | 1,119 | 0 % | 2,041 | 2,074 |
| B2 Append Correction | 150 | 7.5× | 149 | 93.4 % | 2,183 | 1,980 |
| B3 Doc Cache (exact) | 327 | 3.4× | 321 | 72.8 % | 2,041 | 1,980 |
| B3a Doc Cache (APPROX) | 163 | 6.9× | 84 | 0 % (approx.) | 2,041 | 2,059 |
| **B4 Layered CAG** | **470** | **2.4×** | 464 | 55.5 % | 2,041 | 2,002 |
| B5 Prefix Invalidation | 293 | 3.8× | 287 | 75.9 % | 2,041 | 1,976 |

Serialisation + tokenisation + cache cropping cost ≈ 6 ms per update for every exact method; latency is
almost entirely prefill. Peak memory is dominated by the 1.98 GB of weights; the fp32 KV cache at 2K tokens is ≈ 48 MB.

By update type (mean of 3 seeds, ms): for edits of existing dynamic documents B4 costs 415–432 ms regardless
of the type, B5 158–390 ms and B3 232–416 ms (company-count edits hit the first dynamic document, where all
three coincide); for the **stable-document edit** all exact methods lose their advantage (B3 888, B4 890,
B5 922 vs B1 1,123 ms) because the edit sits 156 tokens into the sequence; for appends B3/B5 reuse the whole
old sequence (162 ms) while B4 still recomputes the suffix (517 ms).

### 8.2 Query latency

Mean time-to-first-token ≈ 96 ms and answer latency ≈ 840 ms (≈ 20–30 tok/s) for all methods on the
fixed-length context. **Known artefact:** the question prefill is also chunked at absolute 1,024-token
boundaries; for contexts of ≈2,040 tokens the question straddles position 2,048 and needs two forward passes,
whereas B2's longer context (≈2,180) does not. B2's lower TTFT (57 ms) is therefore an artefact, not a
property of append correction. Update latencies are unaffected.

### 8.3 End-to-end cost and break-even

For a cycle of one update followed by *q* questions, cost = update + q × query (measured means; we use the
same query latency for all methods because of §8.2). B4's saving over B1 per cycle is 655 ms; it falls below
10 % of the cycle cost once *q* > 6 questions per update on the 0.5B model.
On the 1.5B fp16 model the saving is 8.5 s per update against a 2.3 s answer, so B4 stays more than
10 % cheaper per cycle than B1 up to *q* ≈ 29 questions per update. Slower prefill (the 1.5B model on this GPU) makes cache reuse matter for much longer.

## 9. Accuracy results

### 9.1 Main comparison (33 conditions, per-condition means, %)

| Method | A updated | A stale | A mixed | B unchanged | C probes | D cross-doc | E unanswerable | agrees with B1 |
|---|---|---|---|---|---|---|---|---|
| B0 Stale | 1.7 | 73.3 | 0.0 | 64.7 | 24.1 | 67.7 | 0.0 | 84.6 |
| B1 Full Recompute | 82.2 | 1.7 | 0.0 | 63.9 | 65.7 | 69.7 | 0.0 | 100 |
| B2 Append Correction | 65.6 | 15.6 | 6.7 | 61.9 | 49.1 | 69.7 | 0.0 | 67.9 |
| B3 Doc Cache (exact) | 82.2 | 1.7 | 0.0 | 63.9 | 65.7 | 69.7 | 0.0 | 100 |
| B3a Doc Cache (APPROX) | 23.9 | 5.0 | 0.0 | 48.9 | 65.7 | 56.6 | 0.0 | 12.6 |
| **B4 Layered CAG** | **82.2** | **1.7** | 0.0 | **63.9** | 65.7 | 69.7 | 0.0 | **100** |
| B5 Prefix Invalidation | 82.2 | 1.7 | 0.0 | 63.9 | 65.7 | 69.7 | 0.0 | 100 |

Pooled over all 50 pilot conditions (question level, A n = 74): updated-fact accuracy B1 = B3 = B4 = B5 =
81.1 %, B2 58.1 % (21.6 % stale, 8.1 % mixed), B0 1.4 % (78.4 % stale), B3a 18.9 %.

Observations. (i) **RQ1/RQ5:** the exact methods are indistinguishable from B1 on every group — not because
they are "as good as" B1 but because they compute the same function. (ii) Full recompute is not an oracle:
B1 itself is wrong on 15 % of updated facts and 1.4 % of its answers still give an obsolete value (the
model confuses fields). (iii) Group E is 0 % for every method: the 0.5B model never abstains and invents
values (e.g. "dự án #101 có diện tích 1600 m²"); this is a model limitation, verified on the raw answers,
not an evaluator artefact. (iv) B3a's accuracy collapse shows that per-document caches without cross-document
attention are unusable here without further correction.

### 9.2 Primary model — Qwen2.5-1.5B fp16, 11 update-type conditions (seed 0, ≈2K tokens)

| Method | update latency (s) | speed-up | A updated | A stale | B unchanged | C probes | D cross-doc | E unanswerable | agrees with B1 |
|---|---|---|---|---|---|---|---|---|---|
| B0 Stale | 0 | — | 0.0 | 80.0 | 85.4 | 16.7 | 100 | 0.0 | 72.2 |
| B1 Full Recompute | 16.7 | 1.0× | 86.7 | 3.3 | 83.4 | 97.2 | 100 | 0.0 | 100 |
| B2 Append Correction | 1.6 | 10.5× | 81.7 | 3.3 | 76.4 | 91.7 | 100 | 9.1 | 57.6 |
| B3 Doc Cache (exact) | 5.0 | 3.3× | 86.7 | 3.3 | 83.5 | 97.2 | 100 | 0.0 | 99.0 |
| **B4 Layered CAG** | **8.2** | **2.0×** | **86.7** | **3.3** | **83.5** | **97.2** | 100 | 0.0 | **98.0** |
| B5 Prefix Invalidation | 4.4 | 3.8× | 86.7 | 3.3 | 83.5 | 97.2 | 100 | 0.0 | 98.0 |

Pooled over all 19 conditions (question level): updated facts (n = 22) B1 = B3 = B4 = B5 = 90.9 %, B2 86.4 %,
B0 0 % (86.4 % stale); unchanged facts (n = 144) 80.6 % for B1/B3/B4/B5 vs 75.7 % for B2; obsolete/current
value probes (n = 38) 94.7 % for every updating method vs 7.9 % for B0; cross-document comparisons (n = 54)
96.3 % for all methods (the compared areas rarely straddled the update); unanswerable (n = 57) 0 % for all
methods except B2 (12.3 %: it abstained on 4 non-existent-project and 3 absent-attribute questions — the
explicit update-notice section appears to make the model more cautious).

Compared with the 0.5B model, the larger model is more accurate overall and is **less confused by append
corrections** (3.3 % stale on updated facts vs 15.6 %), but appending still costs accuracy on *unchanged*
facts (−7 points) and on generation agreement with B1 (58 %). Peak memory during updates was ≈ 3.04 GB
allocated / 3.26 GB reserved for every method (weights 2.94 GB, KV cache 56 MB at 2K tokens), 30–40 MB below
the physical budget.

## 10. Ablation studies (0.5B fp32 unless stated)

### 10.1 Edit position (RQ4) — 2 seeds, update latency (ms)

| Position in dynamic suffix (normalised) | B1 | B2 | B3 | **B4** | B5 |
|---|---|---|---|---|---|
| begin (0.12) | 1,120 | 133 | 413 | **421** | 397 |
| middle (0.59) | 1,126 | 133 | 236 | **417** | 133 |
| end (0.87) | 1,120 | 135 | 81 | **416** | 63 |

B4 is flat in the edit position (it always recomputes all 807 dynamic tokens); B5 recomputes 634 → 249 → 35
tokens. For end-of-suffix edits B5 is 6.6× faster than B4; for edits at the start of the suffix the three
exact methods are equivalent. Figure `04_position_vs_latency`.

### 10.2 Stable-prefix ratio (RQ3) — target vs actual ratio, update latency (ms) and B4 speed-up

| Target | Actual | B1 | B4 | B4 speed-up | B5 | B3 |
|---|---|---|---|---|---|---|
| 0 % | 8.9 % | 1,161 | 993 | 1.2× | 138 | 243 |
| 25 % | 31.6 % | 1,121 | 752 | 1.5× | 132 | 242 |
| 50 % | 56.2 % | 1,117 | 399 | 2.8× | 132 | 236 |
| 75 % | 78.1 % | 1,126 | 278 | 4.1× | 124 | 153 |
| 90 % | 89.1 % | 1,142 | 162 | 7.1× | 63 | 82 |

The 0 % target cannot be reached: the 171-token instruction header is always a stable prefix. B4's speed-up
follows its reuse ratio almost exactly (reuse = actual stable ratio). Confound: at 78 % and 89 % more
documents precede the edited one, which moves the edit later in the sequence and is why B3/B5 also speed up
there. Figure `05_stable_ratio_vs_speedup`.

### 10.3 Context length — 1 seed, update latency (ms)

| Context | B1 | B2 | B3 | B4 | B5 |
|---|---|---|---|---|---|
| 1,020 | 560 | 95 | 67 | 176 | 99 |
| 2,035 | 1,122 | 133 | 237 | 418 | 134 |
| 4,049 | 2,410 | 169 | 618 | 1,132 | 529 |
| 8,117 | 5,713 | 237 | 1,471 | 3,219 | 1,289 |

B1 grows slightly super-linearly (attention); B4 stays 1.8–3.2× faster than B1 at every length. The 1.5B
model could not be run above 2K tokens on this GPU (spill guard).

### 10.4 Correction history and update frequency — sequential chains

| k updates | B1 total (ms) | B2 total | B3 | B4 | B5 | B2 context | B2 updated-fact acc. | exact methods acc. |
|---|---|---|---|---|---|---|---|---|
| 1 | 1,115 | 131 | 152 | 418 | 121 | 2,153 | 0/1 | 1/1 |
| 3 | 3,367 | 292 | 507 | 1,252 | 414 | 2,298 | 2/3 | 2/3 |
| 5 | 5,584 | 457 | 1,470 | 2,076 | 1,322 | 2,468 | 1/5 | 3/5 |
| 10 | 11,189 | 889 | 2,298 | 4,183 | 1,985 | 2,862 | 3/10 | 8/10 |

Append correction stays the cheapest per update but its context grows by ≈ 83 tokens per correction (+41 %
after ten) and its stale-answer rate on updated facts reaches 50 % at k = 10. Repeated updates of one field
(v0→v3): all exact methods and B2 answered the latest value; B2's context grew by 284 tokens. Counts are small
(1–10 updated-fact questions per row) and should be read as trends.

### 10.5 Primary model (1.5B fp16) ablations, seed 0, update latency (s)

| Edit position | B1 | B2 | B3 | **B4** | B5 |
|---|---|---|---|---|---|
| begin (0.07) | 16.70 | 1.33 | 6.44 | **7.45** | 6.21 |
| middle (0.60) | 16.74 | 1.33 | 3.30 | **7.49** | 2.19 |
| end (0.86) | 16.67 | 1.32 | 1.13 | **7.43** | 0.57 |

| Stable ratio (actual) | B1 | B4 | B4 speed-up | B5 | B3 |
|---|---|---|---|---|---|
| 8.9 % | 16.67 | 15.76 | 1.06× | 2.20 | 3.29 |
| 31.6 % | 16.68 | 11.70 | 1.43× | 2.19 | 3.29 |
| 56.2 % | 16.74 | 8.52 | 1.96× | 2.19 | 3.30 |
| 78.1 % | 16.74 | 4.25 | 3.94× | 1.64 | 2.17 |
| 89.1 % | 16.74 | 2.17 | 7.71× | 0.57 | 1.13 |

Context: at 1,020 tokens B1 8.19 s, B4 3.10 s, B5 0.54 s, B3 1.08 s, B2 1.26 s; 4K/8K not runnable (VRAM).
The orderings reproduce the 0.5B results exactly; only the absolute scale changes (×15 slower fp16 prefill).
Sequential/repeated chains were not run on 1.5B (**NOT RUN**, time budget).

## 11. Limitations

* **Hardware.** GTX 1650 4 GB instead of a T4. The full grid used a substitute model (0.5B fp32); the primary
  1.5B model was run on a reduced grid ≤ 2K tokens. Absolute latencies are specific to this GPU (fp16 is slow
  here) and to Windows; relative orderings are the transferable result.
* **B3a on 1.5B** exceeded the VRAM budget in every run (≈ 60–90 MB over) and was excluded from the 1.5B grid
  after session 8; its deviation on 1.5B is taken from the validation run.
* **Query latency** comparisons involving B2 are confounded by question-prefill chunk splitting (§8.2).
* **fp16 non-determinism**: exact methods agree with B1 on 98–99 % of 1.5B generations (§7).
* **Timing variance**: decoding speed varied between ≈ 7 and 34 tok/s across runs without any GPU throttling
  event (Python/launch overhead on Windows, Balanced power plan); method order was randomised per repetition.
* **Data**: synthetic updates are synthetic; questions are template-generated from structured fields and only
  cover facts that are not contradicted inside their own documents; one company, 72 documents.
* **Evaluation**: rule-based evaluators (numbers, dates, aliases, yes/no, first mentioned option) can mis-score
  paraphrases; answers are capped at 32 tokens per the specification, which truncated a few verbose answers.
* **Sample sizes**: ablation rows have 1–2 seeds and few updated-fact questions per cell.
* A first SMOKE attempt with an earlier instruction wording (answers frequently cut at 32 tokens) is archived in
  `results/_archive/` and not used.

## 12. Conclusion

1. **Correctness (RQ1, RQ5).** Keeping a token-verified causal prefix and recomputing the rest reproduces full
   recompute: B3, B4 and B5 passed all ten edit scenarios on both models and gave the same answers as B1
   (100 % of generations in fp32; 98.5 % in fp16, where the rest are numerical near ties). Layered CAG's
   design rule — reuse only an unchanged, positionally identical prefix — is sound, including its fallback
   when a "stable" document changes. Concatenating independently computed document caches (B3a) is not.
2. **Efficiency (RQ2, RQ6).** Layered CAG cut update latency 2.0–2.4× against full recompute at ≈2K tokens
   with the default partition (≈ 60 % stable tokens) and 1.8–3.2× from 1K to 8K tokens, with no memory
   overhead. Its cost is bounded by the size of the dynamic suffix, independent of where the edit is.
3. **The hypothesis does not make Layered CAG the best strategy.** Token-level prefix invalidation (B5),
   which needs nothing but the previous token sequence, was faster than B4 in every condition except edits
   at the very start of the suffix (where they tie) and stable-document edits (where all exact methods
   degrade to near-full recompute). Exact document-boundary reuse (B3) sits in between. B4's advantage is
   operational — a fixed, predictable recompute window and a single cached prefix — not speed.
4. **Stable ratio (RQ3) and position (RQ4)** are the levers: B4's speed-up rose from 1.1–1.2× at 9 % stable
   tokens to 7.1–7.7× at 89 %, and its latency did not change with edit position, while B5's fell by an
   order of magnitude from the start to the end of the suffix.
5. **Append correction** is the cheapest update and keeps most updated facts right on the larger model, but it
   grows the context with every correction, lowers accuracy on unchanged facts, and on the small model leaves
   21.6 % of updated-fact answers stale; after ten corrections half of them were stale.
6. **Practical guidance.** Use exact prefix reuse; prefer token-level LCP (B5) when the old token sequence is
   available, and structure the knowledge as Layered CAG when edits are concentrated in a small, volatile
   tail. Amortised over questions, update savings matter less as queries per update grow (below 10 % of the
   cycle cost beyond ≈ 6 questions per update on 0.5B and ≈ 29 on the slower 1.5B setting).

## 13. Reproduction

```bash
cd cag-benchmark
python -m venv .venv && .venv/Scripts/python -m pip install torch==2.9.1 --index-url https://download.pytorch.org/whl/cu128
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python scripts/prepare_dataset.py
.venv/Scripts/python -m pytest -q tests                                   # 30 tests
.venv/Scripts/python scripts/validate_cache.py --config configs/local_pilot_q05_fp32.yaml --budget 2048 --out results/pilot_q05_fp32/cache_validation.json
.venv/Scripts/python scripts/validate_cache.py --config configs/local_reduced_q15_fp16.yaml --budget 2048 --out results/reduced_q15_fp16/cache_validation.json
.venv/Scripts/python scripts/run_benchmark.py --config configs/local_pilot_q05_fp32.yaml --out results/pilot_q05_fp32 --max-minutes 35   # repeat until done
.venv/Scripts/python scripts/run_benchmark.py --config configs/local_reduced_q15_fp16.yaml --out results/reduced_q15_fp16 --max-minutes 35
.venv/Scripts/python scripts/generate_report.py --results results/pilot_q05_fp32 --publish-summary
.venv/Scripts/python scripts/generate_report.py --results results/reduced_q15_fp16
.venv/Scripts/python scripts/progress.py
```

Raw measurements: `results/<profile>/{runs,updates,answers,conditions,questions_def}.jsonl`; summaries:
`benchmark_summary.csv`, `cycle_cost.csv`, `failed_runs.csv`; figures: `results/<profile>/figures/*.png|pdf`;
auto-generated tables: `reports/<profile>_tables.md`. Git history records every session.
