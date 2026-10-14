# Bảng sinh tự động — profile `reduced_q15_fp16`

Engine (mô hình, phần cứng, phiên bản): `{'model_name': 'Qwen/Qwen2.5-1.5B-Instruct', 'revision': '989aa7980e4cf806f80c7fef2b1adb7bc71aa306', 'device': 'cuda', 'device_name': 'NVIDIA GeForce GTX 1650', 'dtype': 'float16', 'attn_implementation': 'sdpa', 'torch_version': '2.9.1+cu128', 'transformers_version': '5.19.0', 'cuda_version': '12.8', 'load_seconds': 5.126511999998911, 'weights_bytes': 3087428608, 'prefill_chunk': 512, 'vram_budget_mb': 3296.75, 'notes': []}`

Số điều kiện: 19; số cặp điều kiện × phương pháp hoàn tất: 114; số lượt lỗi/bị loại: 7; số câu đã trả lời (lần lặp 0): 1958


## So sánh chính (11 điều kiện, trung bình theo điều kiện)

| Phương pháp | trễ cập nhật (ms) | prefill cập nhật (ms) | prefill ban đầu (ms) | TTFT (ms) | trả lời (ms) | tái sử dụng % | ngữ cảnh cuối | đỉnh allocated MB |
|---|---|---|---|---|---|---|---|---|
| B0 Stale | 0.0 | 0.0 | 16720.6 | 563.2 | 2152.3 | — | 2035.0 | 3044.5 |
| B1 Full Recompute | 16715.2 | 16709.5 | 16717.2 | 562.8 | 2317.9 | 0.0 | 2032.9 | 3045.7 |
| B2 Append Correction | 1588.9 | 1588.3 | 16721.9 | 542.5 | 2112.9 | 93.5 | 2177.3 | 3068.7 |
| B3 Doc Cache (exact) | 5021.0 | 5015.6 | 16718.7 | 563.0 | 2301.7 | 73.2 | 2032.9 | 3041.1 |
| B4 Layered CAG | 8215.1 | 8207.5 | 16723.0 | 563.8 | 2312.5 | 55.7 | 2032.9 | 3045.7 |
| B5 Prefix Invalidation | 4400.6 | 4395.3 | 16720.2 | 563.2 | 2307.5 | 76.5 | 2032.9 | 3038.2 |


### Độ chính xác (%)

| Phương pháp | A đúng giá trị mới | A giá trị cũ | A trộn | B không đổi | C có/không | D so sánh chéo | E không trả lời được | tổng | trùng token B1 |
|---|---|---|---|---|---|---|---|---|---|
| B0 Stale | 0.0 | 80.0 | 0.0 | 85.4 | 16.7 | 100.0 | 0.0 | 58.5 | 72.2 |
| B1 Full Recompute | 86.7 | 3.3 | 0.0 | 83.4 | 97.2 | 100.0 | 0.0 | 72.8 | 100.0 |
| B2 Append Correction | 81.7 | 3.3 | 0.0 | 76.4 | 91.7 | 100.0 | 9.1 | 69.9 | 57.6 |
| B3 Doc Cache (exact) | 86.7 | 3.3 | 0.0 | 83.5 | 97.2 | 100.0 | 0.0 | 73.0 | 99.0 |
| B4 Layered CAG | 86.7 | 3.3 | 0.0 | 83.5 | 97.2 | 100.0 | 0.0 | 73.0 | 98.0 |
| B5 Prefix Invalidation | 86.7 | 3.3 | 0.0 | 83.5 | 97.2 | 100.0 | 0.0 | 73.0 | 98.0 |


## Độ chính xác gộp theo từng câu hỏi trên mọi điều kiện (%)

| Phương pháp | A (n=22) | B (n=144) | C (n=38) | D (n=54) | E (n=57) |
|---|---|---|---|---|---|
| B0 Stale | 0.0 | 81.2 | 7.9 | 96.3 | 0.0 |
| B1 Full Recompute | 90.9 | 80.6 | 94.7 | 96.3 | 0.0 |
| B2 Append Correction | 86.4 | 75.7 | 94.7 | 96.3 | 12.3 |
| B3 Doc Cache (exact) | 90.9 | 80.6 | 94.7 | 96.3 | 0.0 |
| B3a Doc Cache (APPROX) | 50.0 | 46.9 | 87.5 | 91.7 | 0.0 |
| B4 Layered CAG | 90.9 | 80.6 | 94.7 | 96.3 | 0.0 |
| B5 Prefix Invalidation | 90.9 | 80.6 | 94.7 | 96.3 | 0.0 |


### Phân loại kết quả nhóm A (%)

| Phương pháp | đúng | giá trị cũ | sai |
|---|---|---|---|
| B0 Stale | 0.0 | 86.4 | 13.6 |
| B1 Full Recompute | 90.9 | 4.5 | 4.5 |
| B2 Append Correction | 86.4 | 4.5 | 9.1 |
| B3 Doc Cache (exact) | 90.9 | 4.5 | 4.5 |
| B3a Doc Cache (APPROX) | 50.0 | 0.0 | 50.0 |
| B4 Layered CAG | 90.9 | 4.5 | 4.5 |
| B5 Prefix Invalidation | 90.9 | 4.5 | 4.5 |


## Ablation: vị trí chỉnh sửa (3 điều kiện)

| vị trí sửa | phương pháp | vị trí sửa chuẩn hoá | token tính lại | tỷ lệ tái sử dụng | ngữ cảnh cuối | A đúng giá trị mới | A giá trị cũ | B không đổi | trễ cập nhật (ms) | độ lệch chuẩn trễ (ms) | trễ truy vấn (ms) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| begin | B0 Stale | 0.069 | 0.000 | — | 2035.000 | 0.000 | 1.000 | 0.750 | 0.000 | 0.000 | 2043.173 |
| begin | B1 Full Recompute | 0.069 | 2035.000 | 0.000 | 2035.000 | 1.000 | 0.000 | 0.875 | 16702.859 | 57.436 | 2143.578 |
| begin | B2 Append Correction | 0.069 | 129.000 | 0.940 | 2164.000 | 1.000 | 0.000 | 0.750 | 1325.417 | 4.066 | 1915.391 |
| begin | B3 Doc Cache (exact) | 0.069 | 750.000 | 0.631 | 2035.000 | 1.000 | 0.000 | 0.875 | 6435.473 | 1.064 | 2122.796 |
| begin | B4 Layered CAG | 0.069 | 806.000 | 0.604 | 2035.000 | 1.000 | 0.000 | 0.875 | 7446.698 | 28.690 | 2143.646 |
| begin | B5 Prefix Invalidation | 0.069 | 670.000 | 0.671 | 2035.000 | 1.000 | 0.000 | 0.875 | 6206.073 | 21.253 | 2143.070 |
| end | B0 Stale | 0.864 | 0.000 | — | 2035.000 | 0.000 | 1.000 | 0.750 | 0.000 | 0.000 | 2312.477 |
| end | B1 Full Recompute | 0.864 | 2035.000 | 0.000 | 2035.000 | 1.000 | 0.000 | 0.750 | 16672.816 | 5.002 | 2287.629 |
| end | B2 Append Correction | 0.864 | 121.000 | 0.944 | 2156.000 | 1.000 | 0.000 | 0.750 | 1322.364 | 0.585 | 1966.577 |
| end | B3 Doc Cache (exact) | 0.864 | 110.000 | 0.946 | 2035.000 | 1.000 | 0.000 | 0.750 | 1126.006 | 0.231 | 2288.470 |
| end | B4 Layered CAG | 0.864 | 806.000 | 0.604 | 2035.000 | 1.000 | 0.000 | 0.750 | 7431.980 | 1.635 | 2287.871 |
| end | B5 Prefix Invalidation | 0.864 | 35.000 | 0.983 | 2035.000 | 1.000 | 0.000 | 0.750 | 572.425 | 0.076 | 2287.651 |
| middle | B0 Stale | 0.596 | 0.000 | — | 2035.000 | 0.000 | 1.000 | 0.750 | 0.000 | 0.000 | 2218.701 |
| middle | B1 Full Recompute | 0.596 | 2035.000 | 0.000 | 2035.000 | 1.000 | 0.000 | 0.750 | 16741.753 | 0.291 | 2217.209 |
| middle | B2 Append Correction | 0.596 | 124.000 | 0.943 | 2159.000 | 1.000 | 0.000 | 0.750 | 1327.349 | 0.012 | 2321.766 |
| middle | B3 Doc Cache (exact) | 0.596 | 326.000 | 0.840 | 2035.000 | 1.000 | 0.000 | 0.750 | 3302.794 | 0.731 | 2216.030 |
| middle | B4 Layered CAG | 0.596 | 806.000 | 0.604 | 2035.000 | 1.000 | 0.000 | 0.750 | 7492.592 | 39.899 | 2239.374 |
| middle | B5 Prefix Invalidation | 0.596 | 243.000 | 0.881 | 2035.000 | 1.000 | 0.000 | 0.750 | 2193.169 | 0.508 | 2218.867 |


## Ablation: tỷ lệ tiền tố ổn định (5 điều kiện)

| tỷ lệ ổn định mục tiêu | phương pháp | tỷ lệ ổn định thực tế | token tính lại | tỷ lệ tái sử dụng | ngữ cảnh cuối | A đúng giá trị mới | A giá trị cũ | B không đổi | trễ cập nhật (ms) | độ lệch chuẩn trễ (ms) | trễ truy vấn (ms) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.000 | B0 Stale | 0.089 | 0.000 | — | 2035.000 | 0.000 | 1.000 | 0.750 | 0.000 | 0.000 | 2509.111 |
| 0.000 | B1 Full Recompute | 0.089 | 2035.000 | 0.000 | 2035.000 | 1.000 | 0.000 | 0.750 | 16674.243 | 1.545 | 2509.330 |
| 0.000 | B2 Append Correction | 0.089 | 124.000 | 0.943 | 2159.000 | 1.000 | 0.000 | 0.750 | 1324.237 | 0.174 | 2232.622 |
| 0.000 | B3 Doc Cache (exact) | 0.089 | 326.000 | 0.840 | 2035.000 | 1.000 | 0.000 | 0.750 | 3288.400 | 1.807 | 2502.896 |
| 0.000 | B4 Layered CAG | 0.089 | 1853.000 | 0.089 | 2035.000 | 1.000 | 0.000 | 0.750 | 15758.064 | 5.865 | 2501.177 |
| 0.000 | B5 Prefix Invalidation | 0.089 | 243.000 | 0.881 | 2035.000 | 1.000 | 0.000 | 0.750 | 2199.813 | 21.948 | 2513.862 |
| 0.250 | B0 Stale | 0.316 | 0.000 | — | 2035.000 | 0.000 | 1.000 | 0.750 | 0.000 | 0.000 | 2449.199 |
| 0.250 | B1 Full Recompute | 0.316 | 2035.000 | 0.000 | 2035.000 | 1.000 | 0.000 | 0.750 | 16679.721 | 4.470 | 2446.578 |
| 0.250 | B2 Append Correction | 0.316 | 124.000 | 0.943 | 2159.000 | 1.000 | 0.000 | 0.750 | 1323.418 | 0.480 | 2233.922 |
| 0.250 | B3 Doc Cache (exact) | 0.316 | 326.000 | 0.840 | 2035.000 | 1.000 | 0.000 | 0.750 | 3287.504 | 0.072 | 2450.086 |
| 0.250 | B4 Layered CAG | 0.316 | 1392.000 | 0.316 | 2035.000 | 1.000 | 0.000 | 0.750 | 11699.713 | 1.206 | 2452.716 |
| 0.250 | B5 Prefix Invalidation | 0.316 | 243.000 | 0.881 | 2035.000 | 1.000 | 0.000 | 0.750 | 2187.785 | 0.822 | 2450.877 |
| 0.500 | B0 Stale | 0.562 | 0.000 | — | 2035.000 | 0.000 | 1.000 | 0.625 | 0.000 | 0.000 | 2718.933 |
| 0.500 | B1 Full Recompute | 0.562 | 2035.000 | 0.000 | 2035.000 | 1.000 | 0.000 | 0.625 | 16744.492 | 0.465 | 2711.645 |
| 0.500 | B2 Append Correction | 0.562 | 124.000 | 0.943 | 2159.000 | 1.000 | 0.000 | 0.625 | 1327.228 | 4.974 | 2476.466 |
| 0.500 | B3 Doc Cache (exact) | 0.562 | 326.000 | 0.840 | 2035.000 | 1.000 | 0.000 | 0.625 | 3295.169 | 11.745 | 2720.020 |
| 0.500 | B4 Layered CAG | 0.562 | 892.000 | 0.562 | 2035.000 | 1.000 | 0.000 | 0.625 | 8517.633 | 1.064 | 2714.987 |
| 0.500 | B5 Prefix Invalidation | 0.562 | 243.000 | 0.881 | 2035.000 | 1.000 | 0.000 | 0.625 | 2189.396 | 6.616 | 2714.066 |
| 0.750 | B0 Stale | 0.781 | 0.000 | — | 2035.000 | 0.000 | 1.000 | 0.750 | 0.000 | 0.000 | 2206.705 |
| 0.750 | B1 Full Recompute | 0.781 | 2035.000 | 0.000 | 2035.000 | 1.000 | 0.000 | 0.750 | 16743.375 | 1.713 | 2209.313 |
| 0.750 | B2 Append Correction | 0.781 | 121.000 | 0.944 | 2156.000 | 1.000 | 0.000 | 0.875 | 1328.238 | 0.741 | 2286.221 |
| 0.750 | B3 Doc Cache (exact) | 0.781 | 208.000 | 0.898 | 2035.000 | 1.000 | 0.000 | 0.750 | 2170.495 | 1.407 | 2211.939 |
| 0.750 | B4 Layered CAG | 0.781 | 445.000 | 0.781 | 2035.000 | 1.000 | 0.000 | 0.750 | 4253.106 | 4.907 | 2207.481 |
| 0.750 | B5 Prefix Invalidation | 0.781 | 145.000 | 0.929 | 2035.000 | 1.000 | 0.000 | 0.750 | 1635.592 | 1.003 | 2222.081 |
| 0.900 | B0 Stale | 0.891 | 0.000 | — | 2035.000 | 0.000 | 1.000 | 0.875 | 0.000 | 0.000 | 2138.413 |
| 0.900 | B1 Full Recompute | 0.891 | 2035.000 | 0.000 | 2035.000 | 1.000 | 0.000 | 0.875 | 16740.948 | 0.622 | 2136.472 |
| 0.900 | B2 Append Correction | 0.891 | 121.000 | 0.944 | 2156.000 | 1.000 | 0.000 | 0.875 | 1329.354 | 0.573 | 2183.028 |
| 0.900 | B3 Doc Cache (exact) | 0.891 | 110.000 | 0.946 | 2035.000 | 1.000 | 0.000 | 0.875 | 1132.558 | 1.500 | 2128.515 |
| 0.900 | B4 Layered CAG | 0.891 | 221.000 | 0.891 | 2035.000 | 1.000 | 0.000 | 0.875 | 2170.554 | 1.026 | 2132.769 |
| 0.900 | B5 Prefix Invalidation | 0.891 | 35.000 | 0.983 | 2035.000 | 1.000 | 0.000 | 0.875 | 573.748 | 0.213 | 2131.590 |


## Ablation: độ dài ngữ cảnh (2 điều kiện)

| ngân sách token | phương pháp | token tính lại | tỷ lệ tái sử dụng | ngữ cảnh cuối | A đúng giá trị mới | A giá trị cũ | B không đổi | trễ cập nhật (ms) | độ lệch chuẩn trễ (ms) | trễ truy vấn (ms) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1024 | B0 Stale | 0.000 | — | 1020.000 | 0.000 | 1.000 | 0.800 | 0.000 | 0.000 | 1603.900 |
| 1024 | B1 Full Recompute | 1020.000 | 0.000 | 1020.000 | 1.000 | 0.000 | 0.800 | 8193.087 | 0.748 | 1594.500 |
| 1024 | B2 Append Correction | 124.000 | 0.892 | 1144.000 | 1.000 | 0.000 | 0.600 | 1260.092 | 3.037 | 1558.730 |
| 1024 | B3 Doc Cache (exact) | 117.000 | 0.885 | 1020.000 | 1.000 | 0.000 | 0.800 | 1079.820 | 0.135 | 1593.491 |
| 1024 | B4 Layered CAG | 289.000 | 0.717 | 1020.000 | 1.000 | 0.000 | 0.800 | 3095.434 | 3.385 | 1596.833 |
| 1024 | B5 Prefix Invalidation | 34.000 | 0.967 | 1020.000 | 1.000 | 0.000 | 0.800 | 544.339 | 0.448 | 1594.524 |
| 2048 | B0 Stale | 0.000 | — | 2035.000 | 0.000 | 1.000 | 0.750 | 0.000 | 0.000 | 2218.701 |
| 2048 | B1 Full Recompute | 2035.000 | 0.000 | 2035.000 | 1.000 | 0.000 | 0.750 | 16741.753 | 0.291 | 2217.209 |
| 2048 | B2 Append Correction | 124.000 | 0.943 | 2159.000 | 1.000 | 0.000 | 0.750 | 1327.349 | 0.012 | 2321.766 |
| 2048 | B3 Doc Cache (exact) | 326.000 | 0.840 | 2035.000 | 1.000 | 0.000 | 0.750 | 3302.794 | 0.731 | 2216.030 |
| 2048 | B4 Layered CAG | 806.000 | 0.604 | 2035.000 | 1.000 | 0.000 | 0.750 | 7492.592 | 39.899 | 2239.374 |
| 2048 | B5 Prefix Invalidation | 243.000 | 0.881 | 2035.000 | 1.000 | 0.000 | 0.750 | 2193.169 | 0.508 | 2218.867 |


## Các lượt chạy lỗi hoặc bị loại

| mã điều kiện | phương pháp | lần lặp | trạng thái | lỗi |
|---|---|---|---|---|
| b2048_s0_numeric_area_middle_rdef_k1 | B3a_document_cache_approx | 0 | vram_spill | đỉnh bộ nhớ GPU reserved vượt ngân sách VRAM vật lý (tràn sang RAM) |
| b2048_s0_numeric_area_middle_rdef_k1 | B3a_document_cache_approx | 1 | vram_spill | đỉnh bộ nhớ GPU reserved vượt ngân sách VRAM vật lý (tràn sang RAM) |
| b2048_s0_numeric_investment_middle_rdef_k1 | B3a_document_cache_approx | 0 | vram_spill | đỉnh bộ nhớ GPU reserved vượt ngân sách VRAM vật lý (tràn sang RAM) |
| b2048_s0_numeric_investment_middle_rdef_k1 | B3a_document_cache_approx | 1 | vram_spill | đỉnh bộ nhớ GPU reserved vượt ngân sách VRAM vật lý (tràn sang RAM) |
| b2048_s0_company_count_middle_rdef_k1 | B3a_document_cache_approx | 0 | vram_spill | đỉnh bộ nhớ GPU reserved vượt ngân sách VRAM vật lý (tràn sang RAM) |
| b2048_s0_company_count_middle_rdef_k1 | B3a_document_cache_approx | 1 | vram_spill | đỉnh bộ nhớ GPU reserved vượt ngân sách VRAM vật lý (tràn sang RAM) |
| b2048_s0_text_location_middle_rdef_k1 | B3a_document_cache_approx | 0 | vram_spill | đỉnh bộ nhớ GPU reserved vượt ngân sách VRAM vật lý (tràn sang RAM) |


## Biểu đồ
- latency_vs_accuracy: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\reduced_q15_fp16\figures\01_latency_vs_accuracy.png`
- update_latency: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\reduced_q15_fp16\figures\02_update_latency.png`
- reuse: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\reduced_q15_fp16\figures\03_cache_reuse.png`
- position: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\reduced_q15_fp16\figures\04_position_vs_latency.png`
- stable_ratio: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\reduced_q15_fp16\figures\05_stable_ratio_vs_speedup.png`
- updated_acc: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\reduced_q15_fp16\figures\06_updated_fact_accuracy.png`
- unchanged_acc: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\reduced_q15_fp16\figures\07_unchanged_fact_accuracy.png`
- stale: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\reduced_q15_fp16\figures\08_stale_answer_rate.png`
- cost: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\reduced_q15_fp16\figures\09_cost_vs_queries.png`
- memory: `D:\THANHTUNG\HOC_KI_7\XLDL\cag-benchmark\results\reduced_q15_fp16\figures\10_peak_gpu_memory.png`