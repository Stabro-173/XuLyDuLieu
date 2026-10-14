# Auto-generated tables — profile `pilot_q05_fp32`

Engine: `{'model_name': 'Qwen/Qwen2.5-0.5B-Instruct', 'revision': '7ae557604adf67be50417f59c2c2f167def9a775', 'device': 'cuda', 'device_name': 'NVIDIA GeForce GTX 1650', 'dtype': 'float32', 'attn_implementation': 'sdpa', 'torch_version': '2.9.1+cu128', 'transformers_version': '5.19.0', 'cuda_version': '12.8', 'load_seconds': 2.829093099999227, 'weights_bytes': 1976131072, 'prefill_chunk': 1024, 'vram_budget_mb': 3296.75, 'notes': []}`

Conditions: 48; completed method runs: 331; failed runs: 0; answered questions (rep 0): 5583


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

| Method | A (n=58) | B (n=358) | C (n=96) | D (n=138) | E (n=141) |
|---|---|---|---|---|---|
| B0 Stale | 1.7 | 62.8 | 27.1 | 67.4 | 0.0 |
| B1 Full Recompute | 81.0 | 62.0 | 65.0 | 69.5 | 0.0 |
| B2 Append Correction | 65.5 | 61.7 | 49.0 | 68.1 | 0.0 |
| B3 Doc Cache (exact) | 81.0 | 62.0 | 65.0 | 69.5 | 0.0 |
| B3a Doc Cache (APPROX) | 20.7 | 45.5 | 68.8 | 52.2 | 0.0 |
| B4 Layered CAG | 82.8 | 62.3 | 65.6 | 68.8 | 0.0 |
| B5 Prefix Invalidation | 82.8 | 62.3 | 65.6 | 68.8 | 0.0 |


### Group A outcome breakdown (%)

| Method | correct | mixed | stale | wrong |
|---|---|---|---|---|
| B0 Stale | 1.7 | 0.0 | 77.6 | 20.7 |
| B1 Full Recompute | 81.0 | 1.6 | 1.6 | 15.9 |
| B2 Append Correction | 65.5 | 6.9 | 17.2 | 10.3 |
| B3 Doc Cache (exact) | 81.0 | 1.6 | 1.6 | 15.9 |
| B3a Doc Cache (APPROX) | 20.7 | 0.0 | 5.2 | 74.1 |
| B4 Layered CAG | 82.8 | 1.7 | 1.7 | 13.8 |
| B5 Prefix Invalidation | 82.8 | 1.7 | 1.7 | 13.8 |


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
| end | B4 Layered CAG | 0.865 | 807.000 | 0.604 | 2036.000 | 1.000 | 0.000 | 0.750 | 415.498 | 4.383 | 922.966 |
| end | B5 Prefix Invalidation | 0.865 | 35.000 | 0.983 | 2036.000 | 1.000 | 0.000 | 0.750 | 62.918 | 4.148 | 913.086 |
| middle | B0 Stale | 0.589 | 0.000 | — | 2036.000 | 0.000 | 1.000 | 0.750 | 0.000 | 0.000 | 946.145 |
| middle | B1 Full Recompute | 0.589 | 2036.000 | 0.000 | 2036.000 | 1.000 | 0.000 | 0.750 | 1125.932 | 8.973 | 929.385 |
| middle | B2 Append Correction | 0.589 | 123.000 | 0.943 | 2159.000 | 0.500 | 0.500 | 0.688 | 133.016 | 0.695 | 750.725 |
| middle | B3 Doc Cache (exact) | 0.589 | 332.000 | 0.837 | 2036.000 | 1.000 | 0.000 | 0.750 | 235.939 | 1.228 | 914.622 |
| middle | B3a Doc Cache (APPROX) | 0.589 | 118.500 | 0.000 | 2036.000 | 0.000 | 0.000 | 0.500 | 148.124 | 6.062 | 910.641 |
| middle | B4 Layered CAG | 0.589 | 807.000 | 0.604 | 2036.000 | 1.000 | 0.000 | 0.750 | 416.551 | 2.563 | 1033.201 |
| middle | B5 Prefix Invalidation | 0.589 | 248.500 | 0.878 | 2036.000 | 1.000 | 0.000 | 0.750 | 132.802 | 2.440 | 961.871 |


## Ablation: stable_ratio (5 conditions)

| stable_ratio_target | baseline | stable_ratio_actual | recomputed_tokens | cache_reuse_ratio | context_tokens_final | updated_fact_accuracy | stale_answer_rate | unchanged_fact_accuracy | update_latency_ms | update_latency_std_ms | query_latency_ms |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.000 | B0 Stale | 0.089 | 0.000 | — | 2035.000 | 0.000 | 1.000 | 0.750 | 0.000 | 0.000 | 884.653 |
| 0.000 | B1 Full Recompute | 0.089 | 2035.000 | 0.000 | 2035.000 | 1.000 | 0.000 | 0.750 | 1160.847 | 39.856 | 740.149 |
| 0.000 | B2 Append Correction | 0.089 | 124.000 | 0.943 | 2159.000 | 1.000 | 0.000 | 0.750 | 156.810 | 19.770 | 835.088 |
| 0.000 | B3 Doc Cache (exact) | 0.089 | 326.000 | 0.840 | 2035.000 | 1.000 | 0.000 | 0.750 | 242.713 | 3.946 | 861.532 |
| 0.000 | B3a Doc Cache (APPROX) | 0.089 | 118.000 | 0.000 | 2035.000 | 0.000 | 0.000 | 0.375 | 168.898 | 35.444 | 871.934 |
| 0.000 | B4 Layered CAG | 0.089 | 1853.000 | 0.089 | 2035.000 | 1.000 | 0.000 | 0.750 | 993.018 | 20.652 | 988.526 |
| 0.000 | B5 Prefix Invalidation | 0.089 | 243.000 | 0.881 | 2035.000 | 1.000 | 0.000 | 0.750 | 137.597 | 4.454 | 933.714 |
| 0.250 | B0 Stale | 0.316 | 0.000 | — | 2035.000 | 0.000 | 1.000 | 0.750 | 0.000 | 0.000 | 988.910 |
| 0.250 | B1 Full Recompute | 0.316 | 2035.000 | 0.000 | 2035.000 | 1.000 | 0.000 | 0.750 | 1121.498 | 11.922 | 828.703 |
| 0.250 | B2 Append Correction | 0.316 | 124.000 | 0.943 | 2159.000 | 1.000 | 0.000 | 0.625 | 157.081 | 42.368 | 781.836 |
| 0.250 | B3 Doc Cache (exact) | 0.316 | 326.000 | 0.840 | 2035.000 | 1.000 | 0.000 | 0.750 | 242.090 | 5.626 | 869.636 |
| 0.250 | B3a Doc Cache (APPROX) | 0.316 | 118.000 | 0.000 | 2035.000 | 0.000 | 0.000 | 0.375 | 146.681 | 17.419 | 863.957 |
| 0.250 | B4 Layered CAG | 0.316 | 1392.000 | 0.316 | 2035.000 | 1.000 | 0.000 | 0.750 | 751.564 | 7.378 | 860.406 |
| 0.250 | B5 Prefix Invalidation | 0.316 | 243.000 | 0.881 | 2035.000 | 1.000 | 0.000 | 0.750 | 131.731 | 1.426 | 840.502 |
| 0.500 | B0 Stale | 0.562 | 0.000 | — | 2035.000 | 0.000 | 1.000 | 0.750 | 0.000 | 0.000 | 1001.470 |
| 0.500 | B1 Full Recompute | 0.562 | 2035.000 | 0.000 | 2035.000 | 1.000 | 0.000 | 0.750 | 1116.845 | 2.871 | 939.475 |
| 0.500 | B2 Append Correction | 0.562 | 124.000 | 0.943 | 2159.000 | 1.000 | 0.000 | 0.625 | 132.780 | 0.482 | 794.532 |
| 0.500 | B3 Doc Cache (exact) | 0.562 | 326.000 | 0.840 | 2035.000 | 1.000 | 0.000 | 0.750 | 236.294 | 1.528 | 954.882 |
| 0.500 | B3a Doc Cache (APPROX) | 0.562 | 118.000 | 0.000 | 2035.000 | 0.000 | 0.000 | 0.250 | 141.505 | 14.615 | 869.897 |
| 0.500 | B4 Layered CAG | 0.562 | 892.000 | 0.562 | 2035.000 | 1.000 | 0.000 | 0.750 | 399.097 | 5.790 | 929.143 |
| 0.500 | B5 Prefix Invalidation | 0.562 | 243.000 | 0.881 | 2035.000 | 1.000 | 0.000 | 0.750 | 132.336 | 0.138 | 1031.202 |
| 0.750 | B0 Stale | 0.781 | 0.000 | — | 2035.000 | 0.000 | 1.000 | 0.375 | 0.000 | 0.000 | 840.669 |
| 0.750 | B1 Full Recompute | 0.781 | 2035.000 | 0.000 | 2035.000 | 1.000 | 0.000 | 0.375 | 1126.208 | 10.363 | 835.386 |
| 0.750 | B2 Append Correction | 0.781 | 121.000 | 0.944 | 2156.000 | 1.000 | 0.000 | 0.250 | 132.469 | 1.319 | 734.821 |
| 0.750 | B3 Doc Cache (exact) | 0.781 | 208.000 | 0.898 | 2035.000 | 1.000 | 0.000 | 0.375 | 153.373 | 1.157 | 840.246 |
| 0.750 | B3a Doc Cache (APPROX) | 0.781 | 98.000 | 0.000 | 2035.000 | 0.000 | 0.000 | 0.250 | 130.577 | 8.577 | 760.938 |
| 0.750 | B4 Layered CAG | 0.781 | 445.000 | 0.781 | 2035.000 | 1.000 | 0.000 | 0.375 | 277.701 | 2.512 | 846.329 |
| 0.750 | B5 Prefix Invalidation | 0.781 | 145.000 | 0.929 | 2035.000 | 1.000 | 0.000 | 0.375 | 123.511 | 2.650 | 779.847 |
| 0.900 | B0 Stale | 0.891 | 0.000 | — | 2035.000 | 0.000 | 1.000 | 0.750 | 0.000 | 0.000 | 846.191 |
| 0.900 | B1 Full Recompute | 0.891 | 2035.000 | 0.000 | 2035.000 | 1.000 | 0.000 | 0.750 | 1141.711 | 25.383 | 920.505 |
| 0.900 | B2 Append Correction | 0.891 | 121.000 | 0.944 | 2156.000 | 1.000 | 0.000 | 0.750 | 132.798 | 0.647 | 754.794 |
| 0.900 | B3 Doc Cache (exact) | 0.891 | 110.000 | 0.946 | 2035.000 | 1.000 | 0.000 | 0.750 | 82.053 | 5.275 | 879.537 |
| 0.900 | B3a Doc Cache (APPROX) | 0.891 | 110.000 | 0.000 | 2035.000 | 0.000 | 0.000 | 0.375 | 138.544 | 17.213 | 825.651 |
| 0.900 | B4 Layered CAG | 0.891 | 221.000 | 0.891 | 2035.000 | 1.000 | 0.000 | 0.750 | 162.249 | 3.719 | 1110.795 |
| 0.900 | B5 Prefix Invalidation | 0.891 | 35.000 | 0.983 | 2035.000 | 1.000 | 0.000 | 0.750 | 62.893 | 3.839 | 882.161 |


## Ablation: context_length (4 conditions)

| budget | baseline | recomputed_tokens | cache_reuse_ratio | context_tokens_final | updated_fact_accuracy | stale_answer_rate | unchanged_fact_accuracy | update_latency_ms | update_latency_std_ms | query_latency_ms |
|---|---|---|---|---|---|---|---|---|---|---|
| 1024 | B0 Stale | 0.000 | — | 1020.000 | 0.000 | 1.000 | 0.600 | 0.000 | 0.000 | 948.590 |
| 1024 | B1 Full Recompute | 1020.000 | 0.000 | 1020.000 | 1.000 | 0.000 | 0.600 | 559.641 | 0.842 | 961.133 |
| 1024 | B2 Append Correction | 124.000 | 0.892 | 1144.000 | 1.000 | 0.000 | 1.000 | 95.127 | 2.026 | 804.145 |
| 1024 | B3 Doc Cache (exact) | 117.000 | 0.885 | 1020.000 | 1.000 | 0.000 | 0.600 | 67.330 | 0.790 | 922.376 |
| 1024 | B3a Doc Cache (APPROX) | 117.000 | 0.000 | 1020.000 | 1.000 | 0.000 | 0.600 | 102.480 | 7.904 | 707.405 |
| 1024 | B4 Layered CAG | 289.000 | 0.717 | 1020.000 | 1.000 | 0.000 | 0.600 | 175.766 | 2.410 | 933.949 |
| 1024 | B5 Prefix Invalidation | 34.000 | 0.967 | 1020.000 | 1.000 | 0.000 | 0.600 | 98.971 | 82.408 | 1001.691 |
| 2048 | B0 Stale | 0.000 | — | 2035.000 | 0.000 | 1.000 | 0.750 | 0.000 | 0.000 | 1033.086 |
| 2048 | B1 Full Recompute | 2035.000 | 0.000 | 2035.000 | 1.000 | 0.000 | 0.750 | 1122.285 | 3.600 | 980.518 |
| 2048 | B2 Append Correction | 124.000 | 0.943 | 2159.000 | 1.000 | 0.000 | 0.750 | 133.366 | 0.891 | 844.919 |
| 2048 | B3 Doc Cache (exact) | 326.000 | 0.840 | 2035.000 | 1.000 | 0.000 | 0.750 | 237.008 | 2.028 | 985.306 |
| 2048 | B3a Doc Cache (APPROX) | 118.000 | 0.000 | 2035.000 | 0.000 | 0.000 | 0.375 | 159.978 | 8.370 | 1011.935 |
| 2048 | B4 Layered CAG | 806.000 | 0.604 | 2035.000 | 1.000 | 0.000 | 0.750 | 417.821 | 3.225 | 1213.935 |
| 2048 | B5 Prefix Invalidation | 243.000 | 0.881 | 2035.000 | 1.000 | 0.000 | 0.750 | 134.365 | 3.889 | 1067.731 |
| 4096 | B0 Stale | 0.000 | — | 4049.000 | 0.000 | 1.000 | 0.500 | 0.000 | 0.000 | 1280.095 |
| 4096 | B1 Full Recompute | 4049.000 | 0.000 | 4049.000 | 1.000 | 0.000 | 0.500 | 2409.973 | 3.235 | 1135.969 |
| 4096 | B2 Append Correction | 120.000 | 0.971 | 4169.000 | 0.000 | 1.000 | 0.750 | 169.047 | 1.340 | 899.749 |
| 4096 | B3 Doc Cache (exact) | 911.000 | 0.775 | 4049.000 | 1.000 | 0.000 | 0.500 | 617.651 | 4.803 | 1346.223 |
| 4096 | B3a Doc Cache (APPROX) | 121.000 | 0.000 | 4049.000 | 0.000 | 0.000 | 0.125 | 217.224 | 16.358 | 1164.090 |
| 4096 | B4 Layered CAG | 1856.000 | 0.542 | 4049.000 | 1.000 | 0.000 | 0.500 | 1132.414 | 12.613 | 1161.582 |
| 4096 | B5 Prefix Invalidation | 825.000 | 0.796 | 4049.000 | 1.000 | 0.000 | 0.500 | 529.174 | 5.583 | 1167.569 |
| 8192 | B0 Stale | 0.000 | — | 8117.000 | 0.000 | 0.000 | 0.250 | 0.000 | 0.000 | 1525.757 |
| 8192 | B1 Full Recompute | 8117.000 | 0.000 | 8117.000 | 1.000 | 0.000 | 0.250 | 5713.275 | 5.967 | 1589.099 |
| 8192 | B2 Append Correction | 124.000 | 0.985 | 8241.000 | 1.000 | 0.000 | 0.500 | 236.941 | 0.813 | 1411.555 |
| 8192 | B3 Doc Cache (exact) | 1540.000 | 0.810 | 8117.000 | 1.000 | 0.000 | 0.250 | 1471.421 | 13.875 | 1623.550 |
| 8192 | B3a Doc Cache (APPROX) | 118.000 | 0.000 | 8117.000 | 0.000 | 0.000 | 0.125 | 383.082 | 47.925 | 1501.672 |
| 8192 | B4 Layered CAG | 3897.000 | 0.520 | 8117.000 | 1.000 | 0.000 | 0.250 | 3219.355 | 4.286 | 1588.962 |
| 8192 | B5 Prefix Invalidation | 1455.000 | 0.821 | 8117.000 | 1.000 | 0.000 | 0.250 | 1288.634 | 7.373 | 1591.565 |


## Ablation: sequential (3 conditions)

| n_sequential | baseline | recomputed_tokens | cache_reuse_ratio | context_tokens_final | updated_fact_accuracy | stale_answer_rate | unchanged_fact_accuracy | update_latency_ms | update_latency_std_ms | query_latency_ms |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | B0 Stale | 0.000 | — | 2035.000 | 0.000 | 1.000 | 0.500 | 0.000 | 0.000 | 789.155 |
| 1 | B1 Full Recompute | 2037.000 | 0.000 | 2037.000 | 1.000 | 0.000 | 0.500 | 1114.762 | 0.222 | 729.938 |
| 1 | B2 Append Correction | 118.000 | 0.945 | 2153.000 | 0.000 | 1.000 | 0.500 | 131.478 | 1.028 | 740.823 |
| 1 | B3 Doc Cache (exact) | 210.000 | 0.897 | 2037.000 | 1.000 | 0.000 | 0.500 | 152.375 | 1.389 | 799.806 |
| 1 | B3a Doc Cache (APPROX) | 100.000 | 0.000 | 2037.000 | 0.000 | 0.000 | 0.250 | 127.142 | 3.525 | 741.588 |
| 1 | B4 Layered CAG | 808.000 | 0.603 | 2037.000 | 1.000 | 0.000 | 0.500 | 418.042 | 4.549 | 736.156 |
| 1 | B5 Prefix Invalidation | 133.000 | 0.935 | 2037.000 | 1.000 | 0.000 | 0.500 | 121.167 | 3.986 | 781.904 |
| 3 | B0 Stale | 0.000 | — | 2035.000 | 0.000 | 0.667 | 0.625 | 0.000 | 0.000 | 681.579 |
| 3 | B1 Full Recompute | 6114.000 | 0.000 | 2038.000 | 0.667 | 0.000 | 0.625 | 3367.116 | 24.023 | 710.339 |
| 3 | B2 Append Correction | 263.000 | 0.961 | 2298.000 | 0.667 | 0.333 | 0.625 | 292.060 | 1.085 | 585.040 |
| 3 | B3 Doc Cache (exact) | 769.000 | 0.874 | 2038.000 | 0.667 | 0.000 | 0.625 | 507.052 | 1.979 | 830.045 |
| 3 | B3a Doc Cache (APPROX) | 330.000 | 0.000 | 2038.000 | 0.333 | 0.000 | 0.875 | 472.291 | 93.198 | 612.207 |
| 3 | B4 Layered CAG | 2427.000 | 0.603 | 2038.000 | 0.667 | 0.000 | 0.625 | 1252.435 | 7.059 | 718.440 |
| 3 | B5 Prefix Invalidation | 602.000 | 0.902 | 2038.000 | 0.667 | 0.000 | 0.625 | 413.669 | 15.922 | 710.367 |
| 5 | B1 Full Recompute | 10181.000 | 0.000 | 2036.000 | 0.600 | 0.000 | 0.500 | 5594.335 | 0.000 | 887.247 |
| 5 | B3 Doc Cache (exact) | 2474.000 | 0.757 | 2036.000 | 0.600 | 0.000 | 0.500 | 1481.106 | 0.000 | 835.716 |


## Figures
- latency_vs_accuracy: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\pilot_q05_fp32\figures\01_latency_vs_accuracy.png`
- update_latency: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\pilot_q05_fp32\figures\02_update_latency.png`
- reuse: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\pilot_q05_fp32\figures\03_cache_reuse.png`
- position: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\pilot_q05_fp32\figures\04_position_vs_latency.png`
- stable_ratio: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\pilot_q05_fp32\figures\05_stable_ratio_vs_speedup.png`
- updated_acc: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\pilot_q05_fp32\figures\06_updated_fact_accuracy.png`
- unchanged_acc: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\pilot_q05_fp32\figures\07_unchanged_fact_accuracy.png`
- stale: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\pilot_q05_fp32\figures\08_stale_answer_rate.png`
- cost: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\pilot_q05_fp32\figures\09_cost_vs_queries.png`
- memory: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\pilot_q05_fp32\figures\10_peak_gpu_memory.png`