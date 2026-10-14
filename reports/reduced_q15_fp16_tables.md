# Auto-generated tables — profile `reduced_q15_fp16`

Engine: `{'model_name': 'Qwen/Qwen2.5-1.5B-Instruct', 'revision': '989aa7980e4cf806f80c7fef2b1adb7bc71aa306', 'device': 'cuda', 'device_name': 'NVIDIA GeForce GTX 1650', 'dtype': 'float16', 'attn_implementation': 'sdpa', 'torch_version': '2.9.1+cu128', 'transformers_version': '5.19.0', 'cuda_version': '12.8', 'load_seconds': 4.860720099997707, 'weights_bytes': 3087428608, 'prefill_chunk': 512, 'vram_budget_mb': 3296.75, 'notes': []}`

Conditions: 12; completed method runs: 70; failed runs: 7; answered questions (rep 0): 1246


## Main comparison (11 conditions, mean over conditions)

| Method | upd lat (ms) | upd prefill (ms) | init prefill (ms) | TTFT (ms) | answer (ms) | reuse % | ctx final | peak alloc MB |
|---|---|---|---|---|---|---|---|---|
| B0 Stale | 0.0 | 0.0 | 16720.6 | 563.2 | 2152.3 | — | 2035.0 | 3044.5 |
| B1 Full Recompute | 16715.2 | 16709.5 | 16717.2 | 562.8 | 2317.9 | 0.0 | 2032.9 | 3045.7 |
| B2 Append Correction | 1588.9 | 1588.3 | 16721.9 | 542.5 | 2112.9 | 93.5 | 2177.3 | 3068.7 |
| B3 Doc Cache (exact) | 5021.0 | 5015.6 | 16718.7 | 563.0 | 2301.7 | 73.2 | 2032.9 | 3041.1 |
| B4 Layered CAG | 8215.1 | 8207.5 | 16723.0 | 563.8 | 2312.5 | 55.7 | 2032.9 | 3045.7 |
| B5 Prefix Invalidation | 4400.6 | 4395.3 | 16720.2 | 563.2 | 2307.5 | 76.5 | 2032.9 | 3038.2 |


### Accuracy (%)

| Method | A updated | A stale | A mixed | B unchanged | C probes | D cross-doc | E unanswerable | overall | agree w/ B1 tokens |
|---|---|---|---|---|---|---|---|---|---|
| B0 Stale | 0.0 | 80.0 | 0.0 | 85.4 | 16.7 | 100.0 | 0.0 | 58.5 | 72.2 |
| B1 Full Recompute | 86.7 | 3.3 | 0.0 | 83.4 | 97.2 | 100.0 | 0.0 | 72.8 | 100.0 |
| B2 Append Correction | 81.7 | 3.3 | 0.0 | 76.4 | 91.7 | 100.0 | 9.1 | 69.9 | 57.6 |
| B3 Doc Cache (exact) | 86.7 | 3.3 | 0.0 | 83.5 | 97.2 | 100.0 | 0.0 | 73.0 | 99.0 |
| B4 Layered CAG | 86.7 | 3.3 | 0.0 | 83.5 | 97.2 | 100.0 | 0.0 | 73.0 | 98.0 |
| B5 Prefix Invalidation | 86.7 | 3.3 | 0.0 | 83.5 | 97.2 | 100.0 | 0.0 | 73.0 | 98.0 |


## Pooled question-level accuracy over all conditions (%)

| Method | A (n=14) | B (n=83) | C (n=22) | D (n=33) | E (n=33) |
|---|---|---|---|---|---|
| B0 Stale | 0.0 | 85.5 | 13.6 | 100.0 | 0.0 |
| B1 Full Recompute | 86.7 | 83.5 | 91.7 | 97.2 | 0.0 |
| B2 Append Correction | 80.0 | 75.8 | 91.7 | 97.2 | 8.3 |
| B3 Doc Cache (exact) | 85.7 | 83.1 | 95.5 | 100.0 | 0.0 |
| B3a Doc Cache (APPROX) | 50.0 | 46.9 | 87.5 | 91.7 | 0.0 |
| B4 Layered CAG | 86.7 | 83.5 | 91.7 | 97.2 | 0.0 |
| B5 Prefix Invalidation | 86.7 | 83.5 | 91.7 | 97.2 | 0.0 |


### Group A outcome breakdown (%)

| Method | correct | stale | wrong |
|---|---|---|---|
| B0 Stale | 0.0 | 78.6 | 21.4 |
| B1 Full Recompute | 86.7 | 6.7 | 6.7 |
| B2 Append Correction | 80.0 | 6.7 | 13.3 |
| B3 Doc Cache (exact) | 85.7 | 7.1 | 7.1 |
| B3a Doc Cache (APPROX) | 50.0 | 0.0 | 50.0 |
| B4 Layered CAG | 86.7 | 6.7 | 6.7 |
| B5 Prefix Invalidation | 86.7 | 6.7 | 6.7 |


## Ablation: position (2 conditions)

| update_position | baseline | edit_pos_norm_dynamic | recomputed_tokens | cache_reuse_ratio | context_tokens_final | updated_fact_accuracy | stale_answer_rate | unchanged_fact_accuracy | update_latency_ms | update_latency_std_ms | query_latency_ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| begin | B1 Full Recompute | 0.069 | 2035.000 | 0.000 | 2035.000 | 1.000 | 0.000 | 0.875 | 16743.472 | 0.000 | 2143.578 |
| begin | B2 Append Correction | 0.069 | 129.000 | 0.940 | 2164.000 | 1.000 | 0.000 | 0.750 | 1328.292 | 0.000 | 1915.391 |
| begin | B4 Layered CAG | 0.069 | 806.000 | 0.604 | 2035.000 | 1.000 | 0.000 | 0.875 | 7466.985 | 0.000 | 2143.646 |
| begin | B5 Prefix Invalidation | 0.069 | 670.000 | 0.671 | 2035.000 | 1.000 | 0.000 | 0.875 | 6221.101 | 0.000 | 2143.070 |
| middle | B0 Stale | 0.596 | 0.000 | — | 2035.000 | 0.000 | 1.000 | 0.750 | 0.000 | 0.000 | 2218.701 |
| middle | B1 Full Recompute | 0.596 | 2035.000 | 0.000 | 2035.000 | 1.000 | 0.000 | 0.750 | 16741.753 | 0.291 | 2217.209 |
| middle | B2 Append Correction | 0.596 | 124.000 | 0.943 | 2159.000 | 1.000 | 0.000 | 0.750 | 1327.349 | 0.012 | 2321.766 |
| middle | B3 Doc Cache (exact) | 0.596 | 326.000 | 0.840 | 2035.000 | 1.000 | 0.000 | 0.750 | 3302.794 | 0.731 | 2216.030 |
| middle | B4 Layered CAG | 0.596 | 806.000 | 0.604 | 2035.000 | 1.000 | 0.000 | 0.750 | 7492.592 | 39.899 | 2239.374 |
| middle | B5 Prefix Invalidation | 0.596 | 243.000 | 0.881 | 2035.000 | 1.000 | 0.000 | 0.750 | 2193.169 | 0.508 | 2218.867 |


## Ablation: context_length (1 conditions)

| budget | baseline | recomputed_tokens | cache_reuse_ratio | context_tokens_final | updated_fact_accuracy | stale_answer_rate | unchanged_fact_accuracy | update_latency_ms | update_latency_std_ms | query_latency_ms |
|---|---|---|---|---|---|---|---|---|---|---|
| 2048 | B0 Stale | 0.000 | — | 2035.000 | 0.000 | 1.000 | 0.750 | 0.000 | 0.000 | 2218.701 |
| 2048 | B1 Full Recompute | 2035.000 | 0.000 | 2035.000 | 1.000 | 0.000 | 0.750 | 16741.753 | 0.291 | 2217.209 |
| 2048 | B2 Append Correction | 124.000 | 0.943 | 2159.000 | 1.000 | 0.000 | 0.750 | 1327.349 | 0.012 | 2321.766 |
| 2048 | B3 Doc Cache (exact) | 326.000 | 0.840 | 2035.000 | 1.000 | 0.000 | 0.750 | 3302.794 | 0.731 | 2216.030 |
| 2048 | B4 Layered CAG | 806.000 | 0.604 | 2035.000 | 1.000 | 0.000 | 0.750 | 7492.592 | 39.899 | 2239.374 |
| 2048 | B5 Prefix Invalidation | 243.000 | 0.881 | 2035.000 | 1.000 | 0.000 | 0.750 | 2193.169 | 0.508 | 2218.867 |


## Failed runs

| condition_id | baseline | rep | status | error |
|---|---|---|---|---|
| b2048_s0_numeric_area_middle_rdef_k1 | B3a_document_cache_approx | 0 | vram_spill | peak reserved GPU memory exceeded the physical VRAM budget |
| b2048_s0_numeric_area_middle_rdef_k1 | B3a_document_cache_approx | 1 | vram_spill | peak reserved GPU memory exceeded the physical VRAM budget |
| b2048_s0_numeric_investment_middle_rdef_k1 | B3a_document_cache_approx | 0 | vram_spill | peak reserved GPU memory exceeded the physical VRAM budget |
| b2048_s0_numeric_investment_middle_rdef_k1 | B3a_document_cache_approx | 1 | vram_spill | peak reserved GPU memory exceeded the physical VRAM budget |
| b2048_s0_company_count_middle_rdef_k1 | B3a_document_cache_approx | 0 | vram_spill | peak reserved GPU memory exceeded the physical VRAM budget |
| b2048_s0_company_count_middle_rdef_k1 | B3a_document_cache_approx | 1 | vram_spill | peak reserved GPU memory exceeded the physical VRAM budget |
| b2048_s0_text_location_middle_rdef_k1 | B3a_document_cache_approx | 0 | vram_spill | peak reserved GPU memory exceeded the physical VRAM budget |


## Figures
- latency_vs_accuracy: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\reduced_q15_fp16\figures\01_latency_vs_accuracy.png`
- update_latency: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\reduced_q15_fp16\figures\02_update_latency.png`
- reuse: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\reduced_q15_fp16\figures\03_cache_reuse.png`
- position: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\reduced_q15_fp16\figures\04_position_vs_latency.png`
- updated_acc: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\reduced_q15_fp16\figures\06_updated_fact_accuracy.png`
- unchanged_acc: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\reduced_q15_fp16\figures\07_unchanged_fact_accuracy.png`
- stale: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\reduced_q15_fp16\figures\08_stale_answer_rate.png`
- cost: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\reduced_q15_fp16\figures\09_cost_vs_queries.png`
- memory: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\reduced_q15_fp16\figures\10_peak_gpu_memory.png`