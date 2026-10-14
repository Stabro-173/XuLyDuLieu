# Checkpoint — 2026-10-14 (benchmark complete)

All GPU work is finished; every number below was produced by real runs on this machine.

| Item | Result | Where |
|---|---|---|
| Tests | 30/30 pass | `tests/` |
| Cache validation, 0.5B fp32 | B3/B4/B5 10/10, B3a 0/10 | `results/pilot_q05_fp32/cache_validation.json` |
| Cache validation, 1.5B fp16 | B3/B4/B5 10/10, B3a 0/10 | `results/reduced_q15_fp16/cache_validation.json` |
| SMOKE, 0.5B fp32 | 70/70 runs | `results/smoke_q05_fp32/` |
| PILOT, 0.5B fp32 (substitute model) | 1050/1050 runs, 50 conditions | `results/pilot_q05_fp32/`, `results/benchmark_summary.csv` |
| Reduced grid, 1.5B fp16 (primary model) | 228/228 runs, 19 conditions (+7 B3a runs flagged `vram_spill`, excluded) | `results/reduced_q15_fp16/` |
| Report | written from the above | `reports/benchmark_report.md` (+ auto tables `reports/*_tables.md`) |

Hardware: GTX 1650 4 GB (fp16 GEMM 0.34 TFLOPS vs fp32 1.84), Windows driver spills VRAM silently →
spill guard + position-aligned chunked prefill. Session logs: `results/session*_*.log`; one git commit per session.

## Not run

- Colab notebook on a T4 (`notebooks/colab_benchmark.ipynb`) — written, not executed here.
- FULL profile (5 seeds, 1.5B at 4K/8K) — does not fit this GPU.
- Sequential/repeated chains on 1.5B.

## Known caveats (see report §11)

- Query-latency comparison of B2 is confounded by question-prefill chunk splitting at 1024/512-token boundaries.
- fp16: exact methods agree with B1 on 98.5 % of 1.5B generations (near-tie first tokens).
