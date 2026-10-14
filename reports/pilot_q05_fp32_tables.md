# Auto-generated tables — profile `pilot_q05_fp32`

Engine: `{'model_name': 'Qwen/Qwen2.5-0.5B-Instruct', 'revision': '7ae557604adf67be50417f59c2c2f167def9a775', 'device': 'cuda', 'device_name': 'NVIDIA GeForce GTX 1650', 'dtype': 'float32', 'attn_implementation': 'sdpa', 'torch_version': '2.9.1+cu128', 'transformers_version': '5.19.0', 'cuda_version': '12.8', 'load_seconds': 2.3321452999998655, 'weights_bytes': 1976131072, 'prefill_chunk': 1024, 'vram_budget_mb': 3296.75, 'notes': []}`

Conditions: 13; completed method runs: 88; failed runs: 0; answered questions (rep 0): 1482


## Main comparison (13 conditions, mean over conditions)

| Method | upd lat (ms) | upd prefill (ms) | init prefill (ms) | TTFT (ms) | answer (ms) | reuse % | ctx final | peak alloc MB |
|---|---|---|---|---|---|---|---|---|
| B0 Stale | 0.0 | 0.0 | 1120.0 | 108.6 | 859.2 | — | 2035.2 | 2074.3 |
| B1 Full Recompute | 1114.2 | 1108.1 | 1122.5 | 99.5 | 833.5 | 0.0 | 2033.7 | 2074.3 |
| B2 Append Correction | 149.4 | 148.7 | 1120.5 | 56.2 | 721.6 | 93.6 | 2175.8 | 1980.1 |
| B3 Doc Cache (exact) | 314.0 | 308.1 | 1120.5 | 98.9 | 834.7 | 74.1 | 2033.2 | 1978.1 |
| B3a Doc Cache (APPROX) | 155.9 | 78.3 | 1141.5 | 99.3 | 819.8 | 0.0 | 2033.7 | 2058.0 |
| B4 Layered CAG | 459.9 | 454.0 | 1119.1 | 100.3 | 843.0 | 56.4 | 2033.7 | 2001.4 |
| B5 Prefix Invalidation | 267.4 | 261.1 | 1123.2 | 99.4 | 833.5 | 77.8 | 2033.7 | 1974.3 |


### Accuracy (%)

| Method | A updated | A stale | A mixed | B unchanged | C probes | D cross-doc | E unanswerable | overall | agree w/ B1 tokens |
|---|---|---|---|---|---|---|---|---|---|
| B0 Stale | 4.5 | 72.7 | 0.0 | 68.7 | 17.5 | 77.8 | 0.0 | 47.9 | 85.3 |
| B1 Full Recompute | 87.5 | 0.0 | 0.0 | 66.9 | 75.0 | 79.5 | 0.0 | 59.5 | 100.0 |
| B2 Append Correction | 53.0 | 24.2 | 13.6 | 63.1 | 47.5 | 77.8 | 0.0 | 52.1 | 70.0 |
| B3 Doc Cache (exact) | 86.4 | 0.0 | 0.0 | 66.2 | 77.5 | 77.8 | 0.0 | 59.0 | 100.0 |
| B3a Doc Cache (APPROX) | 20.8 | 0.0 | 0.0 | 46.3 | 68.2 | 61.5 | 0.0 | 41.1 | 10.0 |
| B4 Layered CAG | 87.5 | 0.0 | 0.0 | 66.9 | 75.0 | 79.5 | 0.0 | 59.5 | 100.0 |
| B5 Prefix Invalidation | 87.5 | 0.0 | 0.0 | 66.9 | 75.0 | 79.5 | 0.0 | 59.5 | 100.0 |


## Pooled question-level accuracy over all conditions (%)

| Method | A (n=15) | B (n=91) | C (n=24) | D (n=36) | E (n=36) |
|---|---|---|---|---|---|
| B0 Stale | 6.7 | 68.1 | 16.7 | 77.8 | 0.0 |
| B1 Full Recompute | 87.5 | 66.7 | 73.1 | 79.5 | 0.0 |
| B2 Append Correction | 53.3 | 62.6 | 45.8 | 77.8 | 0.0 |
| B3 Doc Cache (exact) | 86.7 | 65.9 | 75.0 | 77.8 | 0.0 |
| B3a Doc Cache (APPROX) | 18.8 | 46.5 | 69.2 | 61.5 | 0.0 |
| B4 Layered CAG | 87.5 | 66.7 | 73.1 | 79.5 | 0.0 |
| B5 Prefix Invalidation | 87.5 | 66.7 | 73.1 | 79.5 | 0.0 |


### Group A outcome breakdown (%)

| Method | correct | mixed | stale | wrong |
|---|---|---|---|---|
| B0 Stale | 6.7 | 0.0 | 73.3 | 20.0 |
| B1 Full Recompute | 87.5 | 0.0 | 0.0 | 12.5 |
| B2 Append Correction | 53.3 | 13.3 | 26.7 | 6.7 |
| B3 Doc Cache (exact) | 86.7 | 0.0 | 0.0 | 13.3 |
| B3a Doc Cache (APPROX) | 18.8 | 0.0 | 0.0 | 81.2 |
| B4 Layered CAG | 87.5 | 0.0 | 0.0 | 12.5 |
| B5 Prefix Invalidation | 87.5 | 0.0 | 0.0 | 12.5 |


## Ablation: position (2 conditions)

| update_position | baseline | edit_pos_norm_dynamic | recomputed_tokens | cache_reuse_ratio | context_tokens_final | updated_fact_accuracy | stale_answer_rate | unchanged_fact_accuracy | update_latency_ms | update_latency_std_ms | query_latency_ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| middle | B0 Stale | 0.589 | 0.000 | — | 2036.000 | 0.000 | 1.000 | 0.750 | 0.000 | 0.000 | 946.145 |
| middle | B1 Full Recompute | 0.589 | 2036.000 | 0.000 | 2036.000 | 1.000 | 0.000 | 0.750 | 1125.932 | 8.973 | 929.385 |
| middle | B2 Append Correction | 0.589 | 123.000 | 0.943 | 2159.000 | 0.500 | 0.500 | 0.688 | 133.016 | 0.695 | 750.725 |
| middle | B3 Doc Cache (exact) | 0.589 | 332.000 | 0.837 | 2036.000 | 1.000 | 0.000 | 0.750 | 235.939 | 1.228 | 914.622 |
| middle | B3a Doc Cache (APPROX) | 0.589 | 118.500 | 0.000 | 2036.000 | 0.000 | 0.000 | 0.500 | 148.124 | 6.062 | 910.641 |
| middle | B4 Layered CAG | 0.589 | 807.000 | 0.604 | 2036.000 | 1.000 | 0.000 | 0.750 | 416.551 | 2.563 | 1033.201 |
| middle | B5 Prefix Invalidation | 0.589 | 248.500 | 0.878 | 2036.000 | 1.000 | 0.000 | 0.750 | 132.802 | 2.440 | 961.871 |


## Ablation: context_length (1 conditions)

| budget | baseline | recomputed_tokens | cache_reuse_ratio | context_tokens_final | updated_fact_accuracy | stale_answer_rate | unchanged_fact_accuracy | update_latency_ms | update_latency_std_ms | query_latency_ms |
|---|---|---|---|---|---|---|---|---|---|---|
| 2048 | B0 Stale | 0.000 | — | 2035.000 | 0.000 | 1.000 | 0.750 | 0.000 | 0.000 | 1033.086 |
| 2048 | B1 Full Recompute | 2035.000 | 0.000 | 2035.000 | 1.000 | 0.000 | 0.750 | 1122.285 | 3.600 | 980.518 |
| 2048 | B2 Append Correction | 124.000 | 0.943 | 2159.000 | 1.000 | 0.000 | 0.750 | 133.366 | 0.891 | 844.919 |
| 2048 | B3 Doc Cache (exact) | 326.000 | 0.840 | 2035.000 | 1.000 | 0.000 | 0.750 | 237.008 | 2.028 | 985.306 |
| 2048 | B3a Doc Cache (APPROX) | 118.000 | 0.000 | 2035.000 | 0.000 | 0.000 | 0.375 | 159.978 | 8.370 | 1011.935 |
| 2048 | B4 Layered CAG | 806.000 | 0.604 | 2035.000 | 1.000 | 0.000 | 0.750 | 417.821 | 3.225 | 1213.935 |
| 2048 | B5 Prefix Invalidation | 243.000 | 0.881 | 2035.000 | 1.000 | 0.000 | 0.750 | 134.365 | 3.889 | 1067.731 |


## Figures
- latency_vs_accuracy: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\pilot_q05_fp32\figures\01_latency_vs_accuracy.png`
- update_latency: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\pilot_q05_fp32\figures\02_update_latency.png`
- reuse: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\pilot_q05_fp32\figures\03_cache_reuse.png`
- position: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\pilot_q05_fp32\figures\04_position_vs_latency.png`
- updated_acc: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\pilot_q05_fp32\figures\06_updated_fact_accuracy.png`
- unchanged_acc: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\pilot_q05_fp32\figures\07_unchanged_fact_accuracy.png`
- stale: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\pilot_q05_fp32\figures\08_stale_answer_rate.png`
- cost: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\pilot_q05_fp32\figures\09_cost_vs_queries.png`
- memory: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\pilot_q05_fp32\figures\10_peak_gpu_memory.png`