# Auto-generated tables — profile `reduced_q15_fp16`

Engine: `{'model_name': 'Qwen/Qwen2.5-1.5B-Instruct', 'revision': '989aa7980e4cf806f80c7fef2b1adb7bc71aa306', 'device': 'cuda', 'device_name': 'NVIDIA GeForce GTX 1650', 'dtype': 'float16', 'attn_implementation': 'sdpa', 'torch_version': '2.9.1+cu128', 'transformers_version': '5.19.0', 'cuda_version': '12.8', 'load_seconds': 8.331609500000923, 'weights_bytes': 3087428608, 'prefill_chunk': 512, 'vram_budget_mb': 3296.75, 'notes': []}`

Conditions: 4; completed method runs: 23; failed runs: 7; answered questions (rep 0): 459


## Main comparison (4 conditions, mean over conditions)

| Method | upd lat (ms) | upd prefill (ms) | init prefill (ms) | TTFT (ms) | answer (ms) | reuse % | ctx final | peak alloc MB |
|---|---|---|---|---|---|---|---|---|
| B0 Stale | 0.0 | 0.0 | 16736.0 | 558.1 | 2154.1 | — | 2035.0 | 3044.5 |
| B1 Full Recompute | 16740.2 | 16734.9 | 16741.9 | 554.4 | 2198.0 | 0.0 | 2035.0 | 3044.5 |
| B2 Append Correction | 1327.6 | 1327.0 | 16735.8 | 529.1 | 2101.2 | 94.4 | 2155.0 | 3068.0 |
| B3 Doc Cache (exact) | 4815.6 | 4810.0 | 16742.7 | 558.2 | 2213.3 | 75.2 | 2034.8 | 3039.6 |
| B4 Layered CAG | 7471.4 | 7459.9 | 16736.8 | 559.8 | 2217.5 | 60.4 | 2034.8 | 3044.4 |
| B5 Prefix Invalidation | 3822.1 | 3816.8 | 16735.7 | 558.2 | 2218.6 | 79.0 | 2034.8 | 3036.1 |


### Accuracy (%)

| Method | A updated | A stale | A mixed | B unchanged | C probes | D cross-doc | E unanswerable | overall | agree w/ B1 tokens |
|---|---|---|---|---|---|---|---|---|---|
| B0 Stale | 0.0 | 100.0 | 0.0 | 87.5 | 37.5 | 100.0 | 0.0 | 63.2 | 82.4 |
| B1 Full Recompute | 100.0 | 0.0 | 0.0 | 79.2 | 100.0 | 100.0 | 0.0 | 72.5 | 100.0 |
| B2 Append Correction | 100.0 | 0.0 | 0.0 | 71.9 | 100.0 | 100.0 | 8.3 | 70.6 | 64.7 |
| B3 Doc Cache (exact) | 100.0 | 0.0 | 0.0 | 84.4 | 100.0 | 100.0 | 0.0 | 75.0 | 100.0 |
| B4 Layered CAG | 100.0 | 0.0 | 0.0 | 84.4 | 100.0 | 100.0 | 0.0 | 75.0 | 100.0 |
| B5 Prefix Invalidation | 100.0 | 0.0 | 0.0 | 84.4 | 100.0 | 100.0 | 0.0 | 75.0 | 100.0 |


## Pooled question-level accuracy over all conditions (%)

| Method | A (n=4) | B (n=32) | C (n=8) | D (n=12) | E (n=12) |
|---|---|---|---|---|---|
| B0 Stale | 0.0 | 87.5 | 37.5 | 100.0 | 0.0 |
| B1 Full Recompute | 100.0 | 79.2 | 100.0 | 100.0 | 0.0 |
| B2 Append Correction | 100.0 | 71.9 | 100.0 | 100.0 | 8.3 |
| B3 Doc Cache (exact) | 100.0 | 84.4 | 100.0 | 100.0 | 0.0 |
| B3a Doc Cache (APPROX) | 50.0 | 46.9 | 87.5 | 91.7 | 0.0 |
| B4 Layered CAG | 100.0 | 84.4 | 100.0 | 100.0 | 0.0 |
| B5 Prefix Invalidation | 100.0 | 84.4 | 100.0 | 100.0 | 0.0 |


### Group A outcome breakdown (%)

| Method | correct | stale | wrong |
|---|---|---|---|
| B0 Stale | 0.0 | 100.0 | 0.0 |
| B1 Full Recompute | 100.0 | 0.0 | 0.0 |
| B2 Append Correction | 100.0 | 0.0 | 0.0 |
| B3 Doc Cache (exact) | 100.0 | 0.0 | 0.0 |
| B3a Doc Cache (APPROX) | 50.0 | 0.0 | 50.0 |
| B4 Layered CAG | 100.0 | 0.0 | 0.0 |
| B5 Prefix Invalidation | 100.0 | 0.0 | 0.0 |


## Ablation: position (1 conditions)

| update_position | baseline | edit_pos_norm_dynamic | recomputed_tokens | cache_reuse_ratio | context_tokens_final | updated_fact_accuracy | stale_answer_rate | unchanged_fact_accuracy | update_latency_ms | update_latency_std_ms | query_latency_ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
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