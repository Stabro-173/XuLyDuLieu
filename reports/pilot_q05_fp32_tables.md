# Auto-generated tables — profile `pilot_q05_fp32`

Engine: `{'model_name': 'Qwen/Qwen2.5-0.5B-Instruct', 'revision': '7ae557604adf67be50417f59c2c2f167def9a775', 'device': 'cuda', 'device_name': 'NVIDIA GeForce GTX 1650', 'dtype': 'float32', 'attn_implementation': 'sdpa', 'torch_version': '2.9.1+cu128', 'transformers_version': '5.19.0', 'cuda_version': '12.8', 'load_seconds': 2.331615299999612, 'weights_bytes': 1976131072, 'prefill_chunk': 1024, 'vram_budget_mb': 3296.75, 'notes': []}`

Conditions: 25; completed method runs: 175; failed runs: 0; answered questions (rep 0): 2947


## Main comparison (25 conditions, mean over conditions)

| Method | upd lat (ms) | upd prefill (ms) | init prefill (ms) | TTFT (ms) | answer (ms) | reuse % | ctx final | peak alloc MB |
|---|---|---|---|---|---|---|---|---|
| B0 Stale | 0.0 | 0.0 | 1124.4 | 106.6 | 855.7 | — | 2036.5 | 2074.3 |
| B1 Full Recompute | 1122.4 | 1116.2 | 1124.6 | 97.0 | 837.7 | 0.0 | 2038.7 | 2074.3 |
| B2 Append Correction | 147.4 | 146.7 | 1123.1 | 56.4 | 728.1 | 93.5 | 2179.1 | 1980.3 |
| B3 Doc Cache (exact) | 326.8 | 320.8 | 1122.9 | 96.8 | 830.1 | 72.8 | 2038.7 | 1979.9 |
| B3a Doc Cache (APPROX) | 157.8 | 79.3 | 1143.4 | 96.6 | 804.8 | 0.0 | 2038.7 | 2058.3 |
| B4 Layered CAG | 463.2 | 457.0 | 1122.2 | 96.9 | 837.8 | 56.1 | 2038.7 | 2001.5 |
| B5 Prefix Invalidation | 290.1 | 283.9 | 1124.1 | 96.9 | 845.1 | 76.0 | 2038.7 | 1976.3 |


### Accuracy (%)

| Method | A updated | A stale | A mixed | B unchanged | C probes | D cross-doc | E unanswerable | overall | agree w/ B1 tokens |
|---|---|---|---|---|---|---|---|---|---|
| B0 Stale | 2.2 | 69.6 | 0.0 | 68.8 | 25.0 | 77.3 | 0.0 | 48.3 | 85.7 |
| B1 Full Recompute | 82.6 | 0.0 | 0.0 | 67.6 | 70.2 | 77.3 | 0.0 | 58.6 | 100.0 |
| B2 Append Correction | 59.4 | 18.1 | 8.7 | 63.1 | 48.8 | 78.7 | 0.0 | 52.5 | 70.5 |
| B3 Doc Cache (exact) | 82.6 | 0.0 | 0.0 | 67.6 | 70.2 | 77.3 | 0.0 | 58.6 | 100.0 |
| B3a Doc Cache (APPROX) | 21.0 | 0.0 | 0.0 | 51.1 | 67.9 | 57.3 | 0.0 | 42.5 | 11.7 |
| B4 Layered CAG | 82.6 | 0.0 | 0.0 | 67.6 | 70.2 | 77.3 | 0.0 | 58.6 | 100.0 |
| B5 Prefix Invalidation | 82.6 | 0.0 | 0.0 | 67.6 | 70.2 | 77.3 | 0.0 | 58.6 | 100.0 |


## Pooled question-level accuracy over all conditions (%)

| Method | A (n=31) | B (n=190) | C (n=50) | D (n=75) | E (n=75) |
|---|---|---|---|---|---|
| B0 Stale | 3.2 | 68.4 | 24.0 | 77.3 | 0.0 |
| B1 Full Recompute | 83.9 | 67.4 | 70.0 | 77.3 | 0.0 |
| B2 Append Correction | 54.8 | 62.6 | 48.0 | 78.7 | 0.0 |
| B3 Doc Cache (exact) | 83.9 | 67.4 | 70.0 | 77.3 | 0.0 |
| B3a Doc Cache (APPROX) | 19.4 | 51.1 | 68.0 | 57.3 | 0.0 |
| B4 Layered CAG | 83.9 | 67.4 | 70.0 | 77.3 | 0.0 |
| B5 Prefix Invalidation | 83.9 | 67.4 | 70.0 | 77.3 | 0.0 |


### Group A outcome breakdown (%)

| Method | correct | mixed | stale | wrong |
|---|---|---|---|---|
| B0 Stale | 3.2 | 0.0 | 71.0 | 25.8 |
| B1 Full Recompute | 83.9 | 0.0 | 0.0 | 16.1 |
| B2 Append Correction | 54.8 | 9.7 | 19.4 | 16.1 |
| B3 Doc Cache (exact) | 83.9 | 0.0 | 0.0 | 16.1 |
| B3a Doc Cache (APPROX) | 19.4 | 0.0 | 0.0 | 80.6 |
| B4 Layered CAG | 83.9 | 0.0 | 0.0 | 16.1 |
| B5 Prefix Invalidation | 83.9 | 0.0 | 0.0 | 16.1 |


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