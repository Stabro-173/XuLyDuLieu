# Auto-generated tables — profile `pilot_q05_fp32`

Engine: `{'model_name': 'Qwen/Qwen2.5-0.5B-Instruct', 'revision': '7ae557604adf67be50417f59c2c2f167def9a775', 'device': 'cuda', 'device_name': 'NVIDIA GeForce GTX 1650', 'dtype': 'float32', 'attn_implementation': 'sdpa', 'torch_version': '2.9.1+cu128', 'transformers_version': '5.19.0', 'cuda_version': '12.8', 'load_seconds': 3.322523099999671, 'weights_bytes': 1976131072, 'prefill_chunk': 1024, 'vram_budget_mb': 3296.75, 'notes': []}`

Conditions: 37; completed method runs: 259; failed runs: 0; answered questions (rep 0): 4361


## Main comparison (33 conditions, mean over conditions)

| Method | upd lat (ms) | upd prefill (ms) | init prefill (ms) | TTFT (ms) | answer (ms) | reuse % | ctx final | peak alloc MB |
|---|---|---|---|---|---|---|---|---|
| B0 Stale | 0.0 | 0.0 | 1125.0 | 103.9 | 861.9 | — | 2037.3 | 2074.3 |
| B1 Full Recompute | 1125.1 | 1119.0 | 1124.9 | 96.3 | 855.5 | 0.0 | 2041.2 | 2074.3 |
| B2 Append Correction | 149.6 | 148.9 | 1123.2 | 56.6 | 720.8 | 93.4 | 2183.2 | 1980.4 |
| B3 Doc Cache (exact) | 327.0 | 320.8 | 1122.6 | 95.8 | 843.6 | 72.8 | 2041.2 | 1979.5 |
| B3a Doc Cache (APPROX) | 162.9 | 83.7 | 1143.7 | 95.4 | 801.4 | 0.0 | 2041.2 | 2058.8 |
| B4 Layered CAG | 469.9 | 463.8 | 1122.3 | 95.5 | 834.2 | 55.5 | 2041.2 | 2001.6 |
| B5 Prefix Invalidation | 293.4 | 287.1 | 1124.1 | 95.6 | 844.8 | 75.9 | 2041.2 | 1976.1 |


### Accuracy (%)

| Method | A updated | A stale | A mixed | B unchanged | C probes | D cross-doc | E unanswerable | overall | agree w/ B1 tokens |
|---|---|---|---|---|---|---|---|---|---|
| B0 Stale | 1.7 | 73.3 | 0.0 | 64.7 | 24.1 | 67.7 | 0.0 | 44.5 | 84.6 |
| B1 Full Recompute | 82.2 | 1.7 | 0.0 | 63.9 | 65.7 | 69.7 | 0.0 | 54.8 | 100.0 |
| B2 Append Correction | 65.6 | 15.6 | 6.7 | 61.9 | 49.1 | 69.7 | 0.0 | 50.7 | 67.9 |
| B3 Doc Cache (exact) | 82.2 | 1.7 | 0.0 | 63.9 | 65.7 | 69.7 | 0.0 | 54.8 | 100.0 |
| B3a Doc Cache (APPROX) | 23.9 | 5.0 | 0.0 | 48.9 | 65.7 | 56.6 | 0.0 | 41.5 | 12.6 |
| B4 Layered CAG | 82.2 | 1.7 | 0.0 | 63.9 | 65.7 | 69.7 | 0.0 | 54.8 | 100.0 |
| B5 Prefix Invalidation | 82.2 | 1.7 | 0.0 | 63.9 | 65.7 | 69.7 | 0.0 | 54.8 | 100.0 |


## Pooled question-level accuracy over all conditions (%)

| Method | A (n=46) | B (n=281) | C (n=74) | D (n=111) | E (n=111) |
|---|---|---|---|---|---|
| B0 Stale | 2.2 | 64.1 | 24.3 | 67.6 | 0.0 |
| B1 Full Recompute | 80.4 | 63.3 | 66.2 | 69.4 | 0.0 |
| B2 Append Correction | 63.0 | 61.6 | 48.6 | 69.4 | 0.0 |
| B3 Doc Cache (exact) | 80.4 | 63.3 | 66.2 | 69.4 | 0.0 |
| B3a Doc Cache (APPROX) | 21.7 | 48.4 | 67.6 | 55.0 | 0.0 |
| B4 Layered CAG | 80.4 | 63.3 | 66.2 | 69.4 | 0.0 |
| B5 Prefix Invalidation | 80.4 | 63.3 | 66.2 | 69.4 | 0.0 |


### Group A outcome breakdown (%)

| Method | correct | mixed | stale | wrong |
|---|---|---|---|---|
| B0 Stale | 2.2 | 0.0 | 76.1 | 21.7 |
| B1 Full Recompute | 80.4 | 2.2 | 2.2 | 15.2 |
| B2 Append Correction | 63.0 | 8.7 | 15.2 | 13.0 |
| B3 Doc Cache (exact) | 80.4 | 2.2 | 2.2 | 15.2 |
| B3a Doc Cache (APPROX) | 21.7 | 0.0 | 6.5 | 71.7 |
| B4 Layered CAG | 80.4 | 2.2 | 2.2 | 15.2 |
| B5 Prefix Invalidation | 80.4 | 2.2 | 2.2 | 15.2 |


## Ablation: position (6 conditions)

| update_position | baseline | edit_pos_norm_dynamic | recomputed_tokens | cache_reuse_ratio | context_tokens_final | updated_fact_accuracy | stale_answer_rate | unchanged_fact_accuracy | update_latency_ms | update_latency_std_ms | query_latency_ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| begin | B0 Stale | 0.118 | 0.000 | — | 2036.000 | 0.000 | 1.000 | 0.500 | 0.000 | 0.000 | 855.509 |
| begin | B1 Full Recompute | 0.118 | 2036.000 | 0.000 | 2036.000 | 0.500 | 0.000 | 0.500 | 1119.749 | 6.870 | 884.998 |
| begin | B2 Append Correction | 0.118 | 127.000 | 0.941 | 2163.000 | 0.500 | 0.000 | 0.562 | 133.198 | 1.201 | 688.070 |
| begin | B3 Doc Cache (exact) | 0.118 | 712.000 | 0.650 | 2036.000 | 0.500 | 0.000 | 0.500 | 413.173 | 4.066 | 889.041 |
| begin | B3a Doc Cache (APPROX) | 0.118 | 113.500 | 0.000 | 2036.000 | 0.000 | 0.500 | 0.375 | 145.570 | 11.782 | 908.647 |
| begin | B4 Layered CAG | 0.118 | 807.000 | 0.604 | 2036.000 | 0.500 | 0.000 | 0.500 | 420.973 | 4.472 | 900.364 |
| begin | B5 Prefix Invalidation | 0.118 | 633.500 | 0.689 | 2036.000 | 0.500 | 0.000 | 0.500 | 396.651 | 1.752 | 912.116 |
| end | B0 Stale | 0.865 | 0.000 | — | 2036.000 | 0.000 | 1.000 | 0.750 | 0.000 | 0.000 | 871.787 |
| end | B1 Full Recompute | 0.865 | 2036.000 | 0.000 | 2036.000 | 1.000 | 0.000 | 0.750 | 1119.619 | 3.168 | 899.550 |
| end | B2 Append Correction | 0.865 | 121.000 | 0.944 | 2157.000 | 1.000 | 0.000 | 0.688 | 135.390 | 3.419 | 792.660 |
| end | B3 Doc Cache (exact) | 0.865 | 109.000 | 0.946 | 2036.000 | 1.000 | 0.000 | 0.750 | 81.443 | 2.639 | 894.311 |
| end | B3a Doc Cache (APPROX) | 0.865 | 109.000 | 0.000 | 2036.000 | 0.500 | 0.000 | 0.500 | 138.875 | 16.773 | 834.841 |
| end | B4 Layered CAG | 0.865 | 807.000 | 0.604 | 2036.000 | 1.000 | 0.000 | 0.750 | 415.890 | 4.307 | 922.966 |
| end | B5 Prefix Invalidation | 0.865 | 35.000 | 0.983 | 2036.000 | 1.000 | 0.000 | 0.750 | 64.716 | 3.527 | 913.086 |
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