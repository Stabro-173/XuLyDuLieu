# Auto-generated tables — profile `smoke_q05_fp32`

Engine: `{'model_name': 'Qwen/Qwen2.5-0.5B-Instruct', 'revision': '7ae557604adf67be50417f59c2c2f167def9a775', 'device': 'cuda', 'device_name': 'NVIDIA GeForce GTX 1650', 'dtype': 'float32', 'attn_implementation': 'sdpa', 'torch_version': '2.9.1+cu128', 'transformers_version': '5.19.0', 'cuda_version': '12.8', 'load_seconds': 2.7040408000000014, 'weights_bytes': 1976131072, 'prefill_chunk': 1024, 'vram_budget_mb': 3296.75, 'notes': []}`

Conditions: 5; completed method runs: 35; failed runs: 0; answered questions (rep 0): 336


## Main comparison (5 conditions, mean over conditions)

| Method | upd lat (ms) | upd prefill (ms) | init prefill (ms) | TTFT (ms) | answer (ms) | reuse % | ctx final | peak alloc MB |
|---|---|---|---|---|---|---|---|---|
| B0 Stale | 0.0 | 0.0 | 560.8 | 73.1 | 757.9 | — | 1020.0 | 2074.1 |
| B1 Full Recompute | 560.3 | 557.8 | 558.6 | 72.4 | 722.3 | 0.0 | 1020.2 | 2074.1 |
| B2 Append Correction | 114.5 | 113.9 | 560.5 | 46.9 | 669.4 | 88.2 | 1157.0 | 1933.2 |
| B3 Doc Cache (exact) | 136.7 | 134.1 | 559.0 | 71.8 | 726.3 | 73.9 | 1020.2 | 1938.3 |
| B3a Doc Cache (APPROX) | 118.3 | 84.0 | 597.9 | 72.9 | 621.8 | 0.0 | 1020.2 | 1972.6 |
| B4 Layered CAG | 222.9 | 220.3 | 558.3 | 72.4 | 724.1 | 60.4 | 1020.2 | 1947.0 |
| B5 Prefix Invalidation | 113.7 | 111.1 | 561.9 | 73.4 | 729.8 | 82.2 | 1020.2 | 1935.5 |


### Accuracy (%)

| Method | A updated | A stale | A mixed | B unchanged | C probes | D cross-doc | E unanswerable | overall | agree w/ B1 tokens |
|---|---|---|---|---|---|---|---|---|---|
| B0 Stale | 0.0 | 60.0 | 0.0 | 50.0 | 30.0 | 0.0 | 0.0 | 27.4 | 64.5 |
| B1 Full Recompute | 60.0 | 0.0 | 0.0 | 50.0 | 60.0 | 0.0 | 0.0 | 41.7 | 100.0 |
| B2 Append Correction | 70.0 | 10.0 | 0.0 | 90.0 | 50.0 | 0.0 | 0.0 | 57.1 | 54.1 |
| B3 Doc Cache (exact) | 60.0 | 0.0 | 0.0 | 50.0 | 60.0 | 0.0 | 0.0 | 41.7 | 100.0 |
| B3a Doc Cache (APPROX) | 50.0 | 0.0 | 0.0 | 55.0 | 100.0 | 100.0 | 0.0 | 54.2 | 30.5 |
| B4 Layered CAG | 60.0 | 0.0 | 0.0 | 50.0 | 60.0 | 0.0 | 0.0 | 41.7 | 100.0 |
| B5 Prefix Invalidation | 60.0 | 0.0 | 0.0 | 50.0 | 60.0 | 0.0 | 0.0 | 41.7 | 100.0 |


## Pooled question-level accuracy over all conditions (%)

| Method | A (n=6) | B (n=20) | C (n=10) | D (n=2) | E (n=10) |
|---|---|---|---|---|---|
| B0 Stale | 0.0 | 50.0 | 30.0 | 0.0 | 0.0 |
| B1 Full Recompute | 66.7 | 50.0 | 60.0 | 0.0 | 0.0 |
| B2 Append Correction | 66.7 | 90.0 | 50.0 | 0.0 | 0.0 |
| B3 Doc Cache (exact) | 66.7 | 50.0 | 60.0 | 0.0 | 0.0 |
| B3a Doc Cache (APPROX) | 50.0 | 55.0 | 100.0 | 100.0 | 0.0 |
| B4 Layered CAG | 66.7 | 50.0 | 60.0 | 0.0 | 0.0 |
| B5 Prefix Invalidation | 66.7 | 50.0 | 60.0 | 0.0 | 0.0 |


### Group A outcome breakdown (%)

| Method | correct | stale | wrong |
|---|---|---|---|
| B0 Stale | 0.0 | 66.7 | 33.3 |
| B1 Full Recompute | 66.7 | 0.0 | 33.3 |
| B2 Append Correction | 66.7 | 16.7 | 16.7 |
| B3 Doc Cache (exact) | 66.7 | 0.0 | 33.3 |
| B3a Doc Cache (APPROX) | 50.0 | 0.0 | 50.0 |
| B4 Layered CAG | 66.7 | 0.0 | 33.3 |
| B5 Prefix Invalidation | 66.7 | 0.0 | 33.3 |


## Figures
- latency_vs_accuracy: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\smoke_q05_fp32\figures\01_latency_vs_accuracy.png`
- update_latency: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\smoke_q05_fp32\figures\02_update_latency.png`
- reuse: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\smoke_q05_fp32\figures\03_cache_reuse.png`
- updated_acc: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\smoke_q05_fp32\figures\06_updated_fact_accuracy.png`
- unchanged_acc: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\smoke_q05_fp32\figures\07_unchanged_fact_accuracy.png`
- stale: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\smoke_q05_fp32\figures\08_stale_answer_rate.png`
- cost: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\smoke_q05_fp32\figures\09_cost_vs_queries.png`
- memory: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\smoke_q05_fp32\figures\10_peak_gpu_memory.png`