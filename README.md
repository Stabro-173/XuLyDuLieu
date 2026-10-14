# Dynamic Knowledge Updating in Cache-Augmented Generation (CAG)

A reproducible benchmark comparing how a causal LM's **knowledge KV cache** can be kept fresh when the
underlying enterprise data changes: Full Recompute, Append Correction, Document-level caching
(exact and approximate), **Layered CAG** (stable prefix + dynamic suffix) and token-level Prefix
Invalidation — plus a deliberately stale control.

Everything reported in `reports/benchmark_report.md` comes from real executions of this code.

## Methods

| ID | Method | Update procedure | Exact w.r.t. full prefill? |
|---|---|---|---|
| B0 | Stale CAG | data changes, cache untouched | no (stale by design) |
| B1 | Full Recompute | drop cache, prefill whole updated knowledge | reference |
| B2 | Append Correction | keep cache, append a versioned "update notice" and prefill only it | no (sequence grows, old values remain) |
| B3 | Document Cache (exact) | keep cache up to the first changed **document boundary**, recompute the rest | yes |
| B3a | Independent Doc Cache | per-document KV prefilled independently after the instruction header; composed by concatenation with **RoPE key re-rotation** to final positions | **APPROXIMATE** (no cross-document attention) |
| B4 | Layered CAG | `[instruction][stable prefix][dynamic suffix]`; dynamic change → keep stable-prefix KV, recompute the *whole* suffix; stable change → fall back to the first changed stable document | yes |
| B5 | Prefix Invalidation | keep the longest common **token** prefix of old/new sequences | yes |

Every reuse length is verified against the actual token-ID common prefix of the old and new
sequences (`src/cache/token_boundaries.py::verify_reuse`); a strategy can never reuse a KV entry whose
causal history changed. Exactness of B3/B4/B5 is validated against one-shot B1 on the real model
(`scripts/validate_cache.py`) and on a tiny fp32 model in the unit tests.

## Layout

```
configs/            smoke|pilot|full.yaml (benchmark grids), partition.yaml (stable/dynamic rules)
data/raw/           source export (read-only copy; SHA-256 checked on every load)
data/processed/     documents.json, dataset_profile.json, partition_manifest.json
data/benchmark/     generated conditions: versioned snapshots, synthetic updates, questions
src/data/           loader, preprocessor (HTML→text), documents (rendering), partitioner,
                    knowledge (snapshots + prompt layout), updates (synthetic events), qa_generator
src/cache/          engine (prefill / greedy answering), kv_utils, token_boundaries, cache_validation
src/baselines/      B0–B5, B3a
src/evaluation/     answer_metrics (deterministic evaluators), performance_metrics (aggregation)
src/benchmark/      experiments (conditions), experiment_manager, runner (resumable, OOM-safe)
src/visualization/  plots.py (10 figures, PNG + PDF)
scripts/            prepare_dataset, generate_benchmark, validate_cache, run_benchmark, run_smoke,
                    generate_report, make_notebook
tests/              data, evaluator and cache-correctness tests
results/<profile>/  raw JSONL (runs, updates, answers, conditions), summary CSVs, figures
reports/            benchmark_report.md and auto-generated tables
notebooks/          colab_benchmark.ipynb
```

## Installation (local)

Python 3.11. CUDA PyTorch must be installed first (pinned version used for the reported runs:
`torch==2.9.1+cu128`).

```bash
python -m venv .venv
.venv/Scripts/python -m pip install torch==2.9.1 --index-url https://download.pytorch.org/whl/cu128
.venv/Scripts/python -m pip install -r requirements.txt
```

If `download.pytorch.org` is unreachable, any PyTorch wheel mirror works, e.g.
`-f https://mirrors.nju.edu.cn/pytorch/whl/cu128/torch/`.

### Model

`Qwen/Qwen2.5-1.5B-Instruct`, pinned to revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`
(in every config). It is downloaded from the Hugging Face Hub automatically. Alternatively place the
files in `models/Qwen2.5-1.5B-Instruct/` together with a `REVISION` file and a `.complete` marker;
the engine then loads the local copy.

### Dataset

Put `database_export_2026-01-23T02-02-46.json` in `data/raw/`. It is never written to.

## Running

```bash
python scripts/prepare_dataset.py                                   # Phase 1: documents, profile, manifest
python -m pytest -q tests                                           # data, evaluators, cache logic
python scripts/generate_benchmark.py --config configs/pilot.yaml   # conditions + coverage report
python scripts/validate_cache.py --budget 2048 --out results/cache_validation.json   # Phase 4
python scripts/run_benchmark.py --config configs/smoke.yaml        # SMOKE
python scripts/run_benchmark.py --config configs/pilot.yaml        # PILOT (resumable)
python scripts/generate_report.py --results results/pilot --publish-summary
python scripts/run_smoke.py                                         # all SMOKE steps in one go
```

`run_benchmark.py` appends to `results/<profile>/*.jsonl` and skips (condition, method, repetition)
triples that already completed, so an interrupted run can be resumed by re-running the command.
Failures (OOM, exceptions) are recorded in `runs.jsonl` with `status` and `error`, never skipped silently.

**CPU smoke mode.** Without a GPU the engine refuses to start unless `--device cpu --allow-cpu` is
given; such rows carry `device=cpu` and the run tag `<profile>_CPU_SMOKE`.

### Google Colab

Open `notebooks/colab_benchmark.ipynb` with a T4 runtime, upload the project folder as
`cag-benchmark.zip` (without `.venv`, `.wheels`, `models`) or mount Drive, and run all cells. It runs the
SMOKE profile: install → data → QA/updates → tests → cache validation → 7 methods → tables → figures →
zip export. `requirements-colab.txt` omits torch because Colab ships a CUDA build.

## Measurement protocol (short)

* Same model, tokenizer, dtype, attention implementation, greedy decoding (≤ 32 new tokens), knowledge
  snapshots, update events and questions for every method within a condition.
* The knowledge cache ends *inside* the open system turn; each question is
  `<|im_end|>\n<|im_start|>user\n{q}<|im_end|>\n<|im_start|>assistant\n`, prefilled on top of the cache,
  and the cache is cropped back afterwards (checked after every answer — question KV never leaks).
* Update latency = serialization + tokenization + cache management + prefill, with CUDA synchronisation;
  answer generation and model loading are excluded. Query latency (TTFT, total, tokens/s) is measured
  separately. Warm-up runs precede measurement; method order is shuffled per repetition.
* Accuracy is computed from repetition 0 (greedy decoding is deterministic); later repetitions re-measure
  latency and answer a small question subset for query-latency samples.

## Known limitations

See `reports/benchmark_report.md` §11. Most importantly: the reported runs used a **GTX 1650 (4 GB)**,
not a T4; synthetic updates are synthetic; the QA set is template-generated from structured fields;
evaluators are rule-based; fp16 reuse is equivalent to full prefill only up to numerical tolerance.
