# Checkpoint — 2026-10-14

Status of the CAG dynamic-update benchmark when work was paused. Everything listed as "done" was
actually executed; nothing below "next" has been run yet.

## Environment (verified)

- GPU: **NVIDIA GTX 1650, 4 GB** (not a T4). Usable VRAM after CUDA context ≈ 3297 MB.
- Measured: fp16 matmul **0.34 TFLOPS**, fp32 matmul **1.84 TFLOPS**, memory bandwidth ≈ 135 GB/s.
- `.venv` (Python 3.11): torch 2.9.1+cu128 (installed from the NJU mirror wheel in `.wheels/`
  because download.pytorch.org resets connections here), transformers 5.19.0. Pins: `requirements.lock.txt`.
- Models (local, SHA-256 verified against HF LFS, `.complete` marker):
  - `models/Qwen2.5-1.5B-Instruct` rev `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`
  - `models/Qwen2.5-0.5B-Instruct`  rev `7ae557604adf67be50417f59c2c2f167def9a775`
  - The two tokenizers are byte-identical.

## Done

1. **Phase 1 data**: loader (read-only, hash-checked), HTML→text, 72 canonical documents, partition
   manifest, dataset profile (`data/processed/`). 10,605 tokens for all docs; default partition 40.5 % stable.
   Data-quality finding: some project descriptions contradict their own fields (e.g. #46) → such facts excluded.
2. **QA + synthetic updates**: generator for groups A–E, 14 scenario types; pilot grid = 49 conditions,
   66 events, 837 questions (`python scripts/generate_benchmark.py --config configs/pilot.yaml`).
3. **Methods** B0, B1, B2, B3 (exact), B3a (APPROXIMATE, RoPE re-rotation), B4 (layered), B5 (token LCP).
4. **Tests**: `python -m pytest -q tests` → **30 passed** (data, evaluators, 10 exactness cases on a tiny
   fp32 Qwen2, contamination, reuse ordering, RoPE re-rotation).
5. **Engine findings** (real model):
   - 1.5B fp16: 1K prefill 8.6 s, 2K 16.6 s, decode ≈ 8 tok/s; ≥4K exceeds VRAM.
   - Windows driver silently spills to system RAM instead of OOM → added **VRAM-spill guard**
     (`vram_spill_suspected`; runs flagged `vram_spill` are excluded from summaries).
   - Added **position-aligned chunked prefill** (`prefill_chunk`) to bound activation memory.
   - 0.5B fp32 + chunk 1024: 2K 1.1 s, 4K 2.4 s, 8K 5.7 s, no spill.
6. **Phase 4 cache validation, Qwen2.5-0.5B fp32, 2K** (`results/pilot_q05_fp32/cache_validation.json`):
   B3 10/10 PASS, B4 10/10 PASS, B5 10/10 PASS (max rel KV diff ≤ 4.3e-7, logits ≤ 3.2e-5,
   generated tokens 100 % identical). B3a 0/10 (rel KV dev 6.1e-2, logit dev ≈ 8.4, token agreement 0–50 %)
   — expected for the approximate method.

## Next (in order)

```bash
cd cag-benchmark
# 1. primary-model validation (≈30 min)
.venv/Scripts/python scripts/validate_cache.py --config configs/local_reduced_q15_fp16.yaml --budget 2048 --out results/reduced_q15_fp16/cache_validation.json
# 2. smoke end-to-end on the fast model, then check the report/figures pipeline
.venv/Scripts/python scripts/run_benchmark.py --config configs/local_smoke_q05_fp32.yaml --out results/smoke_q05_fp32
.venv/Scripts/python scripts/generate_report.py --results results/smoke_q05_fp32
# 3. pilot on 0.5B fp32 (≈2.5 h, resumable)
.venv/Scripts/python scripts/run_benchmark.py --config configs/local_pilot_q05_fp32.yaml --out results/pilot_q05_fp32
.venv/Scripts/python scripts/generate_report.py --results results/pilot_q05_fp32 --publish-summary
# 4. primary model 1.5B fp16, reduced grid ≤2K (≈3.5 h, resumable)
.venv/Scripts/python scripts/run_benchmark.py --config configs/local_reduced_q15_fp16.yaml --out results/reduced_q15_fp16
.venv/Scripts/python scripts/generate_report.py --results results/reduced_q15_fp16
```

Then: write `reports/benchmark_report.md` from the generated tables (`reports/*_tables.md`), add a
chunked-prefill case to `tests/test_cache.py`, run the Colab notebook (`notebooks/colab_benchmark.ipynb`,
1.5B on T4 with configs/smoke.yaml) if a T4 is available.

## Open caveats to report

- Hardware substitution: full grid uses Qwen2.5-0.5B fp32; the 1.5B primary model only runs ≤2K locally.
- 0.5B is noticeably less accurate (e.g. answers "5"/"8" instead of 50 for the project count at ≥2K).
- Stable-ratio 0 % target is 8.4 % actual (instruction header is always a stable prefix).
- `scripts/validate_cache.py` B3a failures are by design (no cross-document attention).
