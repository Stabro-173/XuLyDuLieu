# Cập nhật tri thức động trong Cache-Augmented Generation: so sánh Full Recompute, Append Correction, Document-Level Caching và Layered CAG

*Mọi con số trong báo cáo này đều đến từ việc chạy thật mã nguồn trong repository trên phần cứng nêu ở §6.
Không có số liệu nào được mô phỏng. Những phần không chạy được được đánh dấu **CHƯA CHẠY**.*

*Quy ước số: dấu phẩy là dấu thập phân (2,4×); số hàng nghìn viết liền (1125 ms).*

## 1. Tóm tắt

Cache-Augmented Generation (CAG) prefill cơ sở tri thức một lần rồi tái sử dụng KV cache của nó cho mọi câu hỏi.
Cách làm này không còn đúng khi tri thức thay đổi. Chúng tôi xây dựng một benchmark có thể tái lập trên dữ liệu
xuất từ cơ sở dữ liệu thật của một công ty kiến trúc Việt Nam (49 dự án, 17 bài viết, hồ sơ công ty, 4 bảng danh mục;
72 tài liệu chuẩn hoá, 10,6 nghìn token) và so sánh sáu chiến lược cập nhật cùng một biến thể xấp xỉ:
cache cũ không cập nhật (B0), tính lại toàn bộ (B1), nối thêm thông báo sửa đổi (B2), tái sử dụng chính xác theo
ranh giới tài liệu (B3), cache độc lập từng tài liệu với xoay lại RoPE — xấp xỉ (B3a), **Layered CAG** — tiền tố
ổn định được tái sử dụng cộng hậu tố động được tính lại (B4) — và tái sử dụng tiền tố chung dài nhất ở mức token (B5).

Kiểm chứng tính đúng của cache trên mười kịch bản chỉnh sửa bắt buộc cho thấy B3, B4 và B5 tái tạo đúng cache
full-prefill của B1 trong phạm vi sai số dấu phẩy động trên cả hai mô hình thử nghiệm (mỗi phương pháp 10/10 kịch bản;
sai lệch KV tương đối lớn nhất 3,7e-7 ở fp32 và 1,2e-3 ở fp16), trong khi B3a lệch rất mạnh (0/10; logit của token
đầu tiên lệch tới 13,9). Trong so sánh chính (33 điều kiện, 11 loại cập nhật × 3 seed, Qwen2.5-0.5B-Instruct fp32,
ngữ cảnh ≈2K token), Layered CAG cho độ chính xác đúng bằng Full Recompute (81,1 % so với 81,1 % trên dữ kiện đã cập
nhật, token sinh ra giống hệt trên 100 % câu hỏi) và giảm độ trễ cập nhật 2,4 lần (470 ms so với 1125 ms). Tuy nhiên,
nó **chậm hơn Prefix Invalidation mức token (293 ms) và tái sử dụng chính xác theo tài liệu (327 ms)** ở gần như mọi
điều kiện, vì nó luôn tính lại toàn bộ hậu tố động: độ trễ của nó không đổi theo vị trí chỉnh sửa, trong khi B3/B5 gần
như không tốn gì khi chỗ sửa nằm gần cuối. Lợi ích của nó do tỷ lệ tiền tố ổn định quyết định (nhanh hơn 1,2 lần khi
token ổn định chiếm 9 %, 7,1 lần khi chiếm 89 %). Append Correction có chi phí cập nhật rẻ nhất (150 ms) nhưng mô hình
vẫn trả về giá trị cũ (21,6 % câu trả lời cũ + 8,1 % câu trả lời trộn cũ/mới trên dữ kiện đã cập nhật) và độ chính
xác giảm dần khi các thông báo sửa đổi tích luỹ. Vì vậy, giả thuyết trung tâm **được xác nhận về tính đúng và được xác
nhận một phần về hiệu năng**: Layered CAG giữ nguyên hành vi của full prefill và rẻ hơn tính lại toàn bộ, nhưng trên
khối lượng công việc này nó bị các phương pháp tái sử dụng tiền tố chính xác ở mức chi tiết hơn vượt qua.

Trên mô hình chính, Qwen2.5-1.5B-Instruct ở fp16 (19 điều kiện với ngữ cảnh ≤ 2K token), bức tranh vẫn như vậy: B4 bằng
B1 ở mọi nhóm câu hỏi (86,7 % trên dữ kiện đã cập nhật trong so sánh chính) và giảm một nửa độ trễ cập nhật (8,2 s so
với 16,7 s trên GPU này); B5 (4,4 s) và B3 (5,0 s) còn nhanh hơn; B2 (1,6 s) có cập nhật rẻ nhất. Do làm tròn fp16 khác
nhau giữa prefill toàn bộ và prefill phần hậu tố, các phương pháp chính xác sinh ra token giống hệt B1 trên 98,5 %
(931/945) câu trả lời; mọi chỗ lệch đều là trường hợp token đầu tiên gần hoà.

## 2. Động cơ nghiên cứu

Trong CAG, cache tri thức chỉ hợp lệ với đúng chuỗi token đã dùng để tính nó: attention nhân quả khiến mỗi phần tử KV
là một hàm của mọi token đứng trước. Sửa một giá trị ở giữa phần tri thức vì thế làm mất hiệu lực mọi vị trí trong
cache kể từ chỗ sửa trở đi, mà tri thức doanh nghiệp (diện tích dự án, mức đầu tư, ngày hoàn thành, số liệu công ty)
thì có thay đổi. Đánh đổi nằm giữa độ tươi của tri thức, chất lượng câu trả lời, độ trễ cập nhật và mức tái sử dụng
cache. Layered CAG là việc đánh giá một ý tưởng đã biết (prefix caching) khi dùng làm chiến lược *tổ chức* tri thức:
đặt phần ít thay đổi lên trước để giữ được cache của nó, đặt phần hay thay đổi ở cuối. Chúng tôi không cho rằng đây là
một thuật toán mới.

Câu hỏi nghiên cứu: RQ1 độ chính xác sau cập nhật so với Full Recompute; RQ2 độ trễ cập nhật tiết kiệm được; RQ3 ảnh
hưởng của tỷ lệ tiền tố ổn định; RQ4 ảnh hưởng của vị trí chỉnh sửa; RQ5 khả năng giữ đúng các dữ kiện không đổi; RQ6
đánh đổi giữa độ trễ, bộ nhớ, mức tái sử dụng và chất lượng.

## 3. Dữ liệu

Nguồn: `database_export_2026-01-23T02-02-46.json` (dữ liệu xuất từ PostgreSQL, SHA-256 `b38e8cf0…a4007c598`, không bao
giờ bị sửa; được kiểm tra hash mỗi lần nạp).

| Bảng | Số bản ghi | Cách sử dụng |
|---|---|---|
| companyInfo | 1 | tách thành `company_profile` (mô tả) và `company_stats` (số liệu) |
| projects | 49 | mỗi dự án một tài liệu |
| news | 17 | mỗi bài một tài liệu (phần tóm tắt; bỏ thân bài HTML đầy đủ) |
| projectCategories / architectureTypes / interiorStyles / newsCategories | 12 / 15 / 10 / 4 | mỗi bảng một tài liệu danh mục |
| heroSlides / settings / users | 10 / 0 / 0 | loại bỏ (nội dung giao diện hoặc rỗng) |

Tiền xử lý (`src/data/preprocessor.py`, nhật ký trong `data/processed/dataset_profile.json`): chuyển HTML sang văn bản
thuần bằng BeautifulSoup (giải mã entity, bỏ thẻ/thuộc tính/ảnh, giữ chuẩn Unicode NFC tiếng Việt); tách tiêu đề dự án
như *"Resort Hải Vân 2. Địa điểm: Đà Nẵng. Mức đầu tư: 20 tỷ"* thành tên ngắn và trường mức đầu tư (42/49 dự án); thay
các đối tượng danh mục lồng nhau bằng tên; chuẩn hoá ngày về ISO và hiển thị DD/MM/YYYY; loại bỏ URL ảnh, trường SEO,
phần trùng lặp `structuredData`, lượt xem và dấu thời gian; trường null bị bỏ khỏi văn bản, không bao giờ tự điền. Mỗi
tài liệu được sinh văn bản một cách tất định từ các trường có cấu trúc, nên một cập nhật giả lập chỉ thay đổi đúng một dòng.

Phát hiện về chất lượng dữ liệu: 4 dự án không có diện tích, 1 không có chủ đầu tư, 11 không có phong cách nội thất,
36 không có mô tả; một số mô tả mâu thuẫn với chính các trường của nó (ví dụ dự án #46: mô tả ghi 135 m² ở Tân Phú,
trường dữ liệu ghi 171,6 m² ở Nhơn Hải). Các dữ kiện bị mâu thuẫn ngay trong tài liệu của nó được loại khỏi việc sinh câu
hỏi và cập nhật giả lập; còn lại 366 dữ kiện không mơ hồ. Số token theo tokenizer Qwen2.5: dự án 6255, bài viết 3710,
hồ sơ công ty 312, danh mục 273, số liệu công ty 55 (tổng 10605).

**Phân vùng.** Quy tắc mặc định (`configs/partition.yaml`): hồ sơ công ty, danh mục và bài viết là *ổn định*; số liệu
công ty và dự án là *động*; hỗ trợ ghi đè cho từng tài liệu. Riêng ablation tỷ lệ ổn định thì chuyển các tài liệu không
phải mục tiêu cập nhật vào tiền tố ổn định cho tới khi đạt tỷ lệ token mong muốn, giữ nguyên tập tài liệu. Manifest gồm
thứ tự, số token, hash và lý do phân vùng: `data/processed/partition_manifest.json`.

## 4. Phương pháp

**Bố cục prompt.** `[tiền tố system của chat template][chỉ dẫn][=== CƠ SỞ TRI THỨC === / PHẦN A: tài liệu ổn định][PHẦN B: tài liệu động]`
là phần tri thức được cache; lượt system được để mở để B2 có thể nối thêm vào bên trong. Mỗi câu hỏi có dạng
`<|im_end|>\n<|im_start|>user\n{q}<|im_end|>\n<|im_start|>assistant\n`, được prefill lên trên cache; sau khi giải mã
greedy (tối đa 32 token mới), cache được cắt về đúng độ dài phần tri thức và điều này được kiểm tra sau mỗi câu trả lời,
nên KV của câu hỏi không bao giờ lọt sang câu hỏi khác. Đã xác minh rằng tokenize phần tri thức và câu hỏi riêng rẽ cho
kết quả giống tokenize toàn bộ prompt.

**Cập nhật giả lập** (`src/data/updates.py`): tất định (có seed), gắn cờ `is_synthetic`, áp dụng trên bản sao sâu của
các snapshot có phiên bản: số (diện tích ×0,55–0,85 hoặc ×1,2–1,8; mức đầu tư; tổng số dự án của công ty +3…15), văn bản
(địa điểm / chủ đầu tư lấy từ danh sách không xuất hiện ở đâu trong dữ liệu gốc), ngày (±90–500 ngày), nhiều trường,
nhiều tài liệu, lặp lại (v0→v1→v2→v3 trên một trường), chuỗi k cập nhật liên tiếp, thêm tài liệu, xoá tài liệu, và sửa
một tài liệu *ổn định* (giờ làm việc của công ty).

**Câu hỏi** (`src/data/qa_generator.py`), sinh từ snapshot cuối của mỗi điều kiện, đáp án đúng đọc từ các trường có cấu
trúc: A dữ kiện đã cập nhật (có lưu các giá trị cũ), B dữ kiện không đổi (gồm cả các trường khác của tài liệu đã cập
nhật), C câu hỏi có/không kiểm tra giá trị cũ và giá trị hiện tại, D so sánh diện tích giữa hai dự án (ưu tiên các cặp mà
đáp án bị đảo do cập nhật), E câu không trả lời được (trường null trong nguồn, mã dự án không tồn tại, thuộc tính không
có, tài liệu đã bị xoá). Dự án được gọi bằng mã chuẩn (`#77`) vì có nhiều tiêu đề trùng nhau.

**Chấm điểm** (`src/evaluation/answer_metrics.py`) là tất định: đọc số kiểu Việt Nam (`2.306`, `171,6`, `2,5 tỷ`), đọc
ngày (`13/01/2026`, `ngày 13 tháng 1 năm 2026`), so khớp văn bản không phân biệt dấu kèm bí danh cho địa điểm/chủ đầu tư,
mẫu có/không và mẫu từ chối trả lời, và lấy phương án được nhắc đến đầu tiên cho câu so sánh. Kết quả gồm *correct*
(đúng), *stale* (chỉ có giá trị cũ), *mixed* (có cả cũ lẫn mới), *abstained* (từ chối), *wrong* (sai). Mức trùng với B1
(chuỗi token sinh ra giống hệt) được báo cáo riêng, tách khỏi tính đúng.

**Chỉ số.** Độ trễ cập nhật = serialize + tokenize + quản lý cache + prefill, có đồng bộ CUDA, không tính thời gian sinh
câu trả lời và nạp mô hình. Độ trễ truy vấn = thời gian tới token đầu tiên (TTFT) và tổng thời gian sinh. Tỷ lệ tái sử
dụng cache = số token tri thức được tái sử dụng hợp lệ (đã kiểm chứng) / số token của tri thức sau cập nhật (tensor cũ
nhưng không còn hợp lệ của B0 và các đoạn xấp xỉ của B3a được tính là 0). Bộ nhớ GPU: đỉnh allocated và đỉnh reserved,
được đặt lại trước mỗi pha.

## 5. Cài đặt các phương pháp

Mọi phương pháp đều cài đặt `initialize / update / answer / get_cache_statistics / reset` (`src/baselines/`). B1, B3,
B4, B5 dùng chung một cơ chế chính xác — giữ một tiền tố của cache cũ, cắt bỏ phần sau, prefill phần còn lại — và chỉ
khác nhau ở số token đề xuất giữ lại. Mọi đề xuất đều bị `verify_reuse` giới hạn về tiền tố chung ở mức token của chuỗi
cũ và chuỗi mới, nên không phần tử KV nào có lịch sử nhân quả đã thay đổi được tái sử dụng, kể cả khi ranh giới tài liệu
rơi vào giữa một token BPE đã gộp (quan sát thực tế: với tài liệu được thêm vào cuối, ranh giới nằm sau một token `\n\n`
và đề xuất bị rút ngắn 2 token).

| Mã | Độ dài tái sử dụng được đề xuất |
|---|---|
| B0 | — (không cập nhật; giữ nguyên cache ban đầu) |
| B1 | 0 |
| B2 | toàn bộ chuỗi cũ; nối thêm và prefill một "thông báo cập nhật" tiếng Việt có phiên bản, nêu rõ giá trị mới thay thế giá trị cũ |
| B3 | token đầu của tài liệu đầu tiên bị thay đổi |
| B3a | xấp xỉ: KV phần đầu + KV từng tài liệu được prefill độc lập, key được xoay lại theo Δvị trí với R(p+Δ)=R(Δ)R(p) |
| B4 | ranh giới ổn định/động nếu chỉ tài liệu động thay đổi; ngược lại là đầu tài liệu ổn định đầu tiên bị thay đổi |
| B5 | toàn bộ chuỗi mới (→ bị giới hạn về LCP mức token) |

B3a được gắn nhãn XẤP XỈ ở mọi nơi: chuỗi token của nó trùng với chuỗi chuẩn, nhưng không tài liệu nào được attend tới
tài liệu đứng trước, nên nó không tương đương với một chuỗi nhân quả được prefill chung. Bản thân phép xoay lại RoPE có
unit test (key của lớp 0 xoay từ vị trí p sang p+37 bằng đúng key tính trực tiếp tại p+37).

## 6. Thiết lập thực nghiệm

**Phần cứng thực tế: NVIDIA GeForce GTX 1650, 4 GB (driver 610.62), Windows 11, Python 3.11.9, torch 2.9.1+cu128,
transformers 5.19.0** (`requirements.lock.txt`). Không có T4 như mục tiêu ban đầu; notebook Colab
(`notebooks/colab_benchmark.ipynb`) chạy profile SMOKE trên T4 nhưng **CHƯA CHẠY**.

Các ràng buộc phần cứng đã đo được và những điều chỉnh bắt buộc (đều ghi trong file cấu hình):

1. Nhân ma trận fp16 trên GPU này chỉ đạt 0,34 TFLOPS, so với 1,84 TFLOPS ở fp32. Qwen2.5-1.5B-Instruct chỉ vừa bộ nhớ
   ở fp16 (2,9 GB trọng số trong ngân sách khả dụng 3,30 GB) và mất ≈16,7 s để prefill 2K token.
2. Driver Windows không báo hết bộ nhớ mà âm thầm đẩy vùng nhớ thiết bị sang RAM hệ thống. Khi chưa có cơ chế bảo vệ,
   một lần prefill 4K token với mô hình 1.5B vẫn "thành công" sau 126 s với đỉnh 5 GB. Chúng tôi thêm **cơ chế phát hiện
   tràn VRAM**: ngân sách khả dụng được đo trước khi nạp trọng số, và mọi lượt chạy có đỉnh bộ nhớ reserved vượt ngân
   sách đều bị gắn nhãn `vram_spill` và loại khỏi mọi bảng tổng hợp (dữ liệu thô vẫn được giữ để minh bạch).
3. SDPA trên sm75 tạo nguyên ma trận attention với prompt dài. Chúng tôi dùng **chunked prefill căn theo vị trí** (mỗi đoạn
   1024 token với 0.5B, 512 với 1.5B; ranh giới tại các bội số tuyệt đối của kích thước đoạn) cho mọi phương pháp, giúp
   giới hạn bộ nhớ activation mà vẫn tính đúng cùng một hàm nhân quả.

Do đó đã chạy hai cấu hình mô hình:

| Profile | Mô hình (revision cố định) | dtype | Lưới thí nghiệm | Trạng thái |
|---|---|---|---|---|
| `pilot_q05_fp32` | Qwen2.5-0.5B-Instruct (`7ae5576`) — **mô hình thay thế** | fp32 | PILOT đầy đủ: 50 điều kiện, ngữ cảnh 1K–8K, 7 phương pháp × 3 lần lặp | 1050/1050 lượt, 0 lỗi |
| `reduced_q15_fp16` | Qwen2.5-1.5B-Instruct (`989aa79`) — **mô hình chính** | fp16 | 19 điều kiện với ngữ cảnh ≤ 2K token, 6 phương pháp × 2 lần lặp | 228/228 lượt hợp lệ (+7 lượt B3a bị gắn `vram_spill`), 0 lỗi |
| Profile FULL (5 seed, 4K/8K với 1.5B) | — | — | — | **CHƯA CHẠY** (không vừa GPU này) |

Hai mô hình dùng tokenizer giống hệt nhau đến từng byte, nên các điều kiện, ranh giới token và câu hỏi là như nhau. Sinh
câu trả lời: greedy, tối đa 32 token mới, dùng chat template, `torch.inference_mode`, seed cố định, thứ tự phương pháp
được xáo trộn ở mỗi lần lặp, 3 lượt khởi động, độ chính xác lấy từ lần lặp 0, độ trễ lấy từ mọi lần lặp.

Lưới PILOT (`configs/local_pilot_q05_fp32.yaml`): các loại cập nhật (11 loại × 3 seed, 2K, vị trí giữa); vị trí sửa
(đầu/giữa/cuối × 2 seed); tỷ lệ ổn định (mục tiêu 0/25/50/75/90 %); độ dài ngữ cảnh (1K/2K/4K/8K); chuỗi cập nhật liên
tiếp (k = 1/3/5/10); cập nhật lặp lại một trường (3 phiên bản). Độ phủ: 50 điều kiện, 67 sự kiện cập nhật, 854 câu hỏi
(A 74, B 380, C 106, D 144, E 150), hơn 28 tài liệu nguồn khác nhau.

## 7. Kiểm chứng tính đúng của cache

`scripts/validate_cache.py`, mười kịch bản bắt buộc ở ngữ cảnh 2K: mỗi phương pháp được khởi tạo trên v0 rồi cập nhật
lên v1, sau đó so với một lần prefill trọn vẹn v1 của B1. Ngưỡng sai số được chốt trước khi chạy (fp32: KV tương đối
≤ 1e-4, logit ≤ 1e-3; fp16: KV tương đối ≤ 1e-2, logit ≤ 0,5). Kết quả:
`results/pilot_q05_fp32/cache_validation.json`, `results/reduced_q15_fp16/cache_validation.json`.

| Mô hình | Phương pháp | PASS | sai lệch KV tương đối lớn nhất | sai lệch logit token đầu lớn nhất | token sinh ra trùng B1 |
|---|---|---|---|---|---|
| 0.5B fp32 | B3 / B4 / B5 | mỗi cái 10/10 | 3,4e-7 / 2,8e-7 / 3,7e-7 | ≤ 3,4e-5 | 100 % |
| 0.5B fp32 | B3a (xấp xỉ) | 0/10 | 5,8e-2 | 7,7 | 0 % |
| 1.5B fp16 | B3 / B4 / B5 | mỗi cái 10/10 | 7,8e-4 / 1,2e-3 / 7,8e-4 | ≤ 0,061 | 100 % |
| 1.5B fp16 | B3a (xấp xỉ) | 0/10 | 6,1e-2 | 13,9 | 0 % |

Các kịch bản: không thay đổi; sửa tài liệu động đầu / giữa / cuối; sửa một trường số; sửa làm thay đổi số token; thêm tài
liệu; xoá tài liệu; nhiều tài liệu; **sửa tài liệu ổn định** — khi đó B4 lùi đúng về tài liệu ổn định bị sửa (tái sử dụng
156 token thay vì toàn bộ 1229 token tiền tố ổn định). 30 unit test (`tests/`) lặp lại mười kịch bản này trên một mô hình
Qwen2 ngẫu nhiên rất nhỏ ở fp32, đồng thời kiểm tra câu hỏi không làm bẩn cache, thứ tự mức tái sử dụng (B5 ≥ B3 ≥ B4 với
chỉnh sửa phần động) và phép xoay lại RoPE.

**Tái sử dụng chính xác ≠ đầu ra giống hệt từng bit ở fp16.** Trong benchmark 1.5B, 11 trên 589 câu trả lời của các phương
pháp chính xác (1,9 %) khác với B1. Ở mọi trường hợp đã kiểm tra, chuỗi token trong cache giống hệt của B1 và token sinh
ra đầu tiên là trường hợp gần hoà (chênh lệch logit giữa top-1 và top-2 từ 0,000 đến 0,078, chênh lệch logit lớn nhất
0,053): ranh giới đoạn khác nhau giữa prefill toàn bộ và prefill phần hậu tố, và thứ tự cộng khác nhau ở fp16 đủ để đảo
kết quả hoà. Hai cặp bị lệch chạy ở hai tiến trình khác nhau, nơi ngay cả B1 cũng không tái lập được từng bit. Ảnh hưởng là
đối xứng (đúng→sai và sai→đúng) và không làm thay đổi độ chính xác trung bình. Ở fp32 (0.5B), mức trùng là 100 % trên toàn
bộ 2562 câu trả lời của các phương pháp chính xác.

## 8. Kết quả hiệu năng

### 8.1 So sánh chính — Qwen2.5-0.5B fp32, 33 điều kiện (11 loại cập nhật × 3 seed, ≈2040 token)

| Phương pháp | độ trễ cập nhật (ms) | nhanh hơn B1 | phần prefill (ms) | tái sử dụng hợp lệ | ngữ cảnh cuối | đỉnh allocated (MB) |
|---|---|---|---|---|---|---|
| B0 Stale | 0 | — | 0 | — (không hợp lệ) | 2037 | 2074 |
| B1 Full Recompute | 1125 | 1,0× | 1119 | 0 % | 2041 | 2074 |
| B2 Append Correction | 150 | 7,5× | 149 | 93,4 % | 2183 | 1980 |
| B3 Doc Cache (chính xác) | 327 | 3,4× | 321 | 72,8 % | 2041 | 1980 |
| B3a Doc Cache (XẤP XỈ) | 163 | 6,9× | 84 | 0 % (xấp xỉ) | 2041 | 2059 |
| **B4 Layered CAG** | **470** | **2,4×** | 464 | 55,5 % | 2041 | 2002 |
| B5 Prefix Invalidation | 293 | 3,8× | 287 | 75,9 % | 2041 | 1976 |

Serialize + tokenize + cắt cache tốn ≈ 6 ms mỗi lần cập nhật với mọi phương pháp chính xác; độ trễ gần như toàn bộ là
prefill. Đỉnh bộ nhớ chủ yếu do 1,98 GB trọng số; KV cache fp32 ở 2K token chiếm ≈ 48 MB.

Theo loại cập nhật (trung bình 3 seed, ms): khi sửa tài liệu động đã có, B4 tốn 415–432 ms bất kể loại cập nhật, B5
158–390 ms và B3 232–416 ms (cập nhật tổng số dự án rơi vào tài liệu động đầu tiên, nơi cả ba trùng nhau); khi **sửa tài
liệu ổn định**, mọi phương pháp chính xác mất lợi thế (B3 888, B4 890, B5 922 so với B1 1123 ms) vì chỗ sửa chỉ cách đầu
chuỗi 156 token; khi thêm tài liệu, B3/B5 tái sử dụng toàn bộ chuỗi cũ (162 ms) còn B4 vẫn tính lại cả hậu tố (517 ms).

### 8.2 Độ trễ truy vấn

TTFT trung bình ≈ 96 ms và thời gian trả lời ≈ 840 ms (≈ 20–30 token/s) với mọi phương pháp trên ngữ cảnh có độ dài cố
định. **Sai lệch đo lường đã biết:** prefill câu hỏi cũng được chia đoạn tại các mốc tuyệt đối 1024 token; với ngữ cảnh
≈2040 token, câu hỏi vắt qua vị trí 2048 nên cần hai lượt forward, còn ngữ cảnh dài hơn của B2 (≈2180) thì không. TTFT
thấp hơn của B2 (57 ms) vì thế là sai lệch đo lường, không phải đặc tính của Append Correction. Độ trễ cập nhật không bị
ảnh hưởng.

### 8.3 Chi phí đầu-cuối và điểm hoà vốn

Với một chu kỳ gồm một lần cập nhật và *q* câu hỏi, chi phí = cập nhật + q × truy vấn (dùng giá trị trung bình đo được; do
§8.2, dùng cùng một độ trễ truy vấn cho mọi phương pháp). Mỗi chu kỳ B4 tiết kiệm 655 ms so với B1; mức tiết kiệm này
xuống dưới 10 % chi phí chu kỳ khi *q* > 6 câu hỏi cho mỗi lần cập nhật trên mô hình 0.5B. Trên mô hình 1.5B fp16, mức
tiết kiệm là 8,5 s mỗi lần cập nhật so với 2,3 s cho mỗi câu trả lời, nên B4 vẫn rẻ hơn B1 trên 10 % mỗi chu kỳ cho tới
*q* ≈ 29 câu hỏi mỗi lần cập nhật. Prefill càng chậm (như mô hình 1.5B trên GPU này) thì tái sử dụng cache càng đáng giá
trong phạm vi rộng hơn.

## 9. Kết quả độ chính xác

### 9.1 So sánh chính (33 điều kiện, trung bình theo điều kiện, %)

| Phương pháp | A đúng giá trị mới | A trả giá trị cũ | A trộn | B không đổi | C kiểm tra có/không | D so sánh chéo | E không trả lời được | trùng B1 |
|---|---|---|---|---|---|---|---|---|
| B0 Stale | 1,7 | 73,3 | 0,0 | 64,7 | 24,1 | 67,7 | 0,0 | 84,6 |
| B1 Full Recompute | 82,2 | 1,7 | 0,0 | 63,9 | 65,7 | 69,7 | 0,0 | 100 |
| B2 Append Correction | 65,6 | 15,6 | 6,7 | 61,9 | 49,1 | 69,7 | 0,0 | 67,9 |
| B3 Doc Cache (chính xác) | 82,2 | 1,7 | 0,0 | 63,9 | 65,7 | 69,7 | 0,0 | 100 |
| B3a Doc Cache (XẤP XỈ) | 23,9 | 5,0 | 0,0 | 48,9 | 65,7 | 56,6 | 0,0 | 12,6 |
| **B4 Layered CAG** | **82,2** | **1,7** | 0,0 | **63,9** | 65,7 | 69,7 | 0,0 | **100** |
| B5 Prefix Invalidation | 82,2 | 1,7 | 0,0 | 63,9 | 65,7 | 69,7 | 0,0 | 100 |

Gộp trên toàn bộ 50 điều kiện pilot (tính theo từng câu hỏi, nhóm A n = 74): độ chính xác trên dữ kiện đã cập nhật của
B1 = B3 = B4 = B5 = 81,1 %, B2 58,1 % (21,6 % giá trị cũ, 8,1 % trộn), B0 1,4 % (78,4 % giá trị cũ), B3a 18,9 %.

Nhận xét. (i) **RQ1/RQ5:** các phương pháp chính xác không thể phân biệt với B1 ở mọi nhóm — không phải vì chúng "tốt
ngang" B1 mà vì chúng tính đúng cùng một hàm. (ii) Full Recompute không phải là đáp án chuẩn tuyệt đối: chính B1 trả lời
sai 15 % dữ kiện đã cập nhật và 1,4 % câu trả lời của nó vẫn dùng giá trị cũ (mô hình nhầm lẫn giữa các trường). (iii)
Nhóm E đạt 0 % ở mọi phương pháp: mô hình 0.5B không bao giờ từ chối mà bịa ra giá trị (ví dụ "dự án #101 có diện tích
1600 m²"); đây là giới hạn của mô hình, đã được kiểm tra trên câu trả lời thô, không phải lỗi của bộ chấm điểm. (iv) Độ
chính xác của B3a sụp đổ cho thấy cache từng tài liệu không có attention chéo giữa các tài liệu là không dùng được ở đây
nếu không có bước hiệu chỉnh thêm.

### 9.2 Mô hình chính — Qwen2.5-1.5B fp16, 11 điều kiện loại cập nhật (seed 0, ≈2K token)

| Phương pháp | độ trễ cập nhật (s) | nhanh hơn B1 | A đúng giá trị mới | A trả giá trị cũ | B không đổi | C kiểm tra có/không | D so sánh chéo | E không trả lời được | trùng B1 |
|---|---|---|---|---|---|---|---|---|---|
| B0 Stale | 0 | — | 0,0 | 80,0 | 85,4 | 16,7 | 100 | 0,0 | 72,2 |
| B1 Full Recompute | 16,7 | 1,0× | 86,7 | 3,3 | 83,4 | 97,2 | 100 | 0,0 | 100 |
| B2 Append Correction | 1,6 | 10,5× | 81,7 | 3,3 | 76,4 | 91,7 | 100 | 9,1 | 57,6 |
| B3 Doc Cache (chính xác) | 5,0 | 3,3× | 86,7 | 3,3 | 83,5 | 97,2 | 100 | 0,0 | 99,0 |
| **B4 Layered CAG** | **8,2** | **2,0×** | **86,7** | **3,3** | **83,5** | **97,2** | 100 | 0,0 | **98,0** |
| B5 Prefix Invalidation | 4,4 | 3,8× | 86,7 | 3,3 | 83,5 | 97,2 | 100 | 0,0 | 98,0 |

Gộp trên toàn bộ 19 điều kiện (tính theo từng câu hỏi): dữ kiện đã cập nhật (n = 22) B1 = B3 = B4 = B5 = 90,9 %, B2
86,4 %, B0 0 % (86,4 % giá trị cũ); dữ kiện không đổi (n = 144) 80,6 % với B1/B3/B4/B5 so với 75,7 % của B2; câu kiểm tra
giá trị cũ/hiện tại (n = 38) 94,7 % với mọi phương pháp có cập nhật so với 7,9 % của B0; so sánh chéo (n = 54) 96,3 % với
mọi phương pháp (cặp diện tích được so sánh hiếm khi bị đảo bởi cập nhật); không trả lời được (n = 57) 0 % với mọi phương
pháp trừ B2 (12,3 %: nó từ chối ở 4 câu về dự án không tồn tại và 3 câu về thuộc tính không có — phần "thông báo cập nhật"
tường minh dường như khiến mô hình thận trọng hơn).

So với mô hình 0.5B, mô hình lớn hơn chính xác hơn nói chung và **ít bị nhiễu bởi thông báo sửa đổi được nối thêm hơn**
(3,3 % trả giá trị cũ trên dữ kiện đã cập nhật so với 15,6 %), nhưng việc nối thêm vẫn làm giảm độ chính xác trên dữ kiện
*không đổi* (−7 điểm) và giảm mức trùng với B1 (58 %). Đỉnh bộ nhớ khi cập nhật là ≈ 3,04 GB allocated / 3,26 GB reserved
với mọi phương pháp (trọng số 2,94 GB, KV cache 56 MB ở 2K token), thấp hơn ngân sách vật lý 30–40 MB.

## 10. Nghiên cứu ablation (0.5B fp32 trừ khi ghi khác)

### 10.1 Vị trí chỉnh sửa (RQ4) — 2 seed, độ trễ cập nhật (ms)

| Vị trí trong hậu tố động (chuẩn hoá) | B1 | B2 | B3 | **B4** | B5 |
|---|---|---|---|---|---|
| đầu (0,12) | 1120 | 133 | 413 | **421** | 397 |
| giữa (0,59) | 1126 | 133 | 236 | **417** | 133 |
| cuối (0,87) | 1120 | 135 | 81 | **416** | 63 |

Độ trễ của B4 không đổi theo vị trí sửa (nó luôn tính lại toàn bộ 807 token động); B5 tính lại 634 → 249 → 35 token. Với
chỗ sửa ở cuối hậu tố, B5 nhanh hơn B4 6,6 lần; với chỗ sửa ở đầu hậu tố, ba phương pháp chính xác tương đương nhau. Biểu
đồ `04_position_vs_latency`.

### 10.2 Tỷ lệ tiền tố ổn định (RQ3) — tỷ lệ mục tiêu và thực tế, độ trễ cập nhật (ms) và mức nhanh hơn của B4

| Mục tiêu | Thực tế | B1 | B4 | B4 nhanh hơn | B5 | B3 |
|---|---|---|---|---|---|---|
| 0 % | 8,9 % | 1161 | 993 | 1,2× | 138 | 243 |
| 25 % | 31,6 % | 1121 | 752 | 1,5× | 132 | 242 |
| 50 % | 56,2 % | 1117 | 399 | 2,8× | 132 | 236 |
| 75 % | 78,1 % | 1126 | 278 | 4,1× | 124 | 153 |
| 90 % | 89,1 % | 1142 | 162 | 7,1× | 63 | 82 |

Không thể đạt mục tiêu 0 %: phần chỉ dẫn 171 token luôn là tiền tố ổn định. Mức nhanh hơn của B4 bám gần như chính xác theo
tỷ lệ tái sử dụng của nó (tỷ lệ tái sử dụng = tỷ lệ ổn định thực tế). Yếu tố gây nhiễu: ở 78 % và 89 %, có nhiều tài liệu
đứng trước tài liệu bị sửa hơn, khiến chỗ sửa lùi về sau trong chuỗi — đó là lý do B3/B5 cũng nhanh lên ở đây. Biểu đồ
`05_stable_ratio_vs_speedup`.

### 10.3 Độ dài ngữ cảnh — 1 seed, độ trễ cập nhật (ms)

| Ngữ cảnh | B1 | B2 | B3 | B4 | B5 |
|---|---|---|---|---|---|
| 1020 | 560 | 95 | 67 | 176 | 99 |
| 2035 | 1122 | 133 | 237 | 418 | 134 |
| 4049 | 2410 | 169 | 618 | 1132 | 529 |
| 8117 | 5713 | 237 | 1471 | 3219 | 1289 |

B1 tăng hơi nhanh hơn tuyến tính (do attention); B4 luôn nhanh hơn B1 1,8–3,2 lần ở mọi độ dài. Mô hình 1.5B không chạy
được trên 2K token trên GPU này (bị cơ chế phát hiện tràn VRAM chặn).

### 10.4 Lịch sử sửa đổi và tần suất cập nhật — chuỗi cập nhật liên tiếp

| k cập nhật | B1 tổng (ms) | B2 tổng | B3 | B4 | B5 | ngữ cảnh B2 | B2 đúng giá trị mới | các phương pháp chính xác đúng |
|---|---|---|---|---|---|---|---|---|
| 1 | 1115 | 131 | 152 | 418 | 121 | 2153 | 0/1 | 1/1 |
| 3 | 3367 | 292 | 507 | 1252 | 414 | 2298 | 2/3 | 2/3 |
| 5 | 5584 | 457 | 1470 | 2076 | 1322 | 2468 | 1/5 | 3/5 |
| 10 | 11189 | 889 | 2298 | 4183 | 1985 | 2862 | 3/10 | 8/10 |

Append Correction luôn rẻ nhất cho mỗi lần cập nhật, nhưng ngữ cảnh của nó dài thêm ≈ 83 token sau mỗi lần sửa (+41 % sau
mười lần) và tỷ lệ trả giá trị cũ trên dữ kiện đã cập nhật lên tới 50 % ở k = 10. Cập nhật lặp lại một trường (v0→v3):
mọi phương pháp chính xác và B2 đều trả lời giá trị mới nhất; ngữ cảnh của B2 dài thêm 284 token. Số lượng mẫu nhỏ (1–10
câu hỏi về dữ kiện đã cập nhật mỗi dòng) nên chỉ nên đọc như xu hướng.

### 10.5 Ablation trên mô hình chính (1.5B fp16), seed 0, độ trễ cập nhật (s)

| Vị trí sửa | B1 | B2 | B3 | **B4** | B5 |
|---|---|---|---|---|---|
| đầu (0,07) | 16,70 | 1,33 | 6,44 | **7,45** | 6,21 |
| giữa (0,60) | 16,74 | 1,33 | 3,30 | **7,49** | 2,19 |
| cuối (0,86) | 16,67 | 1,32 | 1,13 | **7,43** | 0,57 |

| Tỷ lệ ổn định (thực tế) | B1 | B4 | B4 nhanh hơn | B5 | B3 |
|---|---|---|---|---|---|
| 8,9 % | 16,67 | 15,76 | 1,06× | 2,20 | 3,29 |
| 31,6 % | 16,68 | 11,70 | 1,43× | 2,19 | 3,29 |
| 56,2 % | 16,74 | 8,52 | 1,96× | 2,19 | 3,30 |
| 78,1 % | 16,74 | 4,25 | 3,94× | 1,64 | 2,17 |
| 89,1 % | 16,74 | 2,17 | 7,71× | 0,57 | 1,13 |

Độ dài ngữ cảnh: ở 1020 token, B1 8,19 s, B4 3,10 s, B5 0,54 s, B3 1,08 s, B2 1,26 s; 4K/8K không chạy được (VRAM). Thứ tự
giữa các phương pháp lặp lại đúng kết quả của 0.5B; chỉ có quy mô tuyệt đối thay đổi (prefill fp16 chậm hơn ≈15 lần). Chuỗi
cập nhật liên tiếp và lặp lại không chạy trên 1.5B (**CHƯA CHẠY**, do giới hạn thời gian).

## 11. Hạn chế

* **Phần cứng.** Dùng GTX 1650 4 GB thay vì T4. Lưới đầy đủ chạy trên mô hình thay thế (0.5B fp32); mô hình chính 1.5B chỉ
  chạy trên lưới thu gọn với ngữ cảnh ≤ 2K token. Độ trễ tuyệt đối phụ thuộc vào GPU này (fp16 chậm) và Windows; điều có thể
  khái quát hoá là thứ tự tương đối giữa các phương pháp.
* **B3a trên 1.5B** vượt ngân sách VRAM ở mọi lượt chạy (vượt ≈ 60–90 MB) và bị loại khỏi lưới 1.5B từ sau phiên 8; độ lệch
  của nó trên 1.5B lấy từ lần chạy kiểm chứng.
* **Độ trễ truy vấn**: so sánh có liên quan tới B2 bị nhiễu bởi việc chia đoạn khi prefill câu hỏi (§8.2).
* **Tính không tất định của fp16**: các phương pháp chính xác trùng B1 ở 98–99 % câu trả lời trên 1.5B (§7).
* **Dao động thời gian**: tốc độ giải mã dao động từ ≈ 7 đến 34 token/s giữa các lượt chạy dù GPU không hề bị giảm xung
  (overhead của Python/khởi chạy kernel trên Windows, chế độ nguồn Balanced); thứ tự phương pháp được xáo trộn ở mỗi lần lặp.
* **Dữ liệu**: cập nhật là giả lập; câu hỏi được sinh theo mẫu từ các trường có cấu trúc và chỉ bao phủ các dữ kiện không bị
  mâu thuẫn trong chính tài liệu của nó; chỉ có một công ty, 72 tài liệu.
* **Chấm điểm**: bộ chấm dựa trên quy tắc (số, ngày, bí danh, có/không, phương án nhắc đến đầu tiên) có thể chấm sai các
  cách diễn đạt khác; câu trả lời bị giới hạn 32 token theo đặc tả, làm một số câu trả lời dài bị cắt.
* **Cỡ mẫu**: các dòng ablation chỉ có 1–2 seed và ít câu hỏi về dữ kiện đã cập nhật trong mỗi ô.
* Lần chạy SMOKE đầu tiên với cách viết chỉ dẫn cũ (câu trả lời thường bị cắt ở 32 token) được lưu trong `results/_archive/`
  và không được sử dụng.

## 12. Kết luận

1. **Tính đúng (RQ1, RQ5).** Giữ một tiền tố nhân quả đã được kiểm chứng ở mức token và tính lại phần còn lại cho kết quả
   giống Full Recompute: B3, B4 và B5 vượt qua cả mười kịch bản chỉnh sửa trên cả hai mô hình và cho cùng câu trả lời với
   B1 (100 % câu trả lời ở fp32; 98,5 % ở fp16, phần còn lại là các trường hợp gần hoà về số học). Nguyên tắc thiết kế của
   Layered CAG — chỉ tái sử dụng tiền tố không đổi và giữ nguyên vị trí — là đúng, kể cả cơ chế lùi lại khi một tài liệu
   "ổn định" bị sửa. Việc ghép các cache tài liệu được tính độc lập (B3a) thì không đúng.
2. **Hiệu năng (RQ2, RQ6).** Layered CAG giảm độ trễ cập nhật 2,0–2,4 lần so với Full Recompute ở ≈2K token với phân vùng
   mặc định (≈ 60 % token ổn định), và 1,8–3,2 lần từ 1K đến 8K token, không tốn thêm bộ nhớ. Chi phí của nó bị chặn bởi
   kích thước hậu tố động, không phụ thuộc vào vị trí chỉnh sửa.
3. **Giả thuyết không khiến Layered CAG trở thành chiến lược tốt nhất.** Prefix Invalidation mức token (B5), vốn chỉ cần
   chuỗi token cũ, nhanh hơn B4 ở mọi điều kiện trừ chỗ sửa nằm ngay đầu hậu tố (khi đó chúng ngang nhau) và sửa tài liệu
   ổn định (khi đó mọi phương pháp chính xác đều gần như phải tính lại toàn bộ). Tái sử dụng chính xác theo ranh giới tài
   liệu (B3) nằm ở giữa. Lợi thế của B4 nằm ở mặt vận hành — một cửa sổ tính lại cố định, dễ dự đoán, và chỉ cần cache một
   tiền tố — chứ không nằm ở tốc độ.
4. **Tỷ lệ ổn định (RQ3) và vị trí (RQ4)** là hai yếu tố then chốt: mức nhanh hơn của B4 tăng từ 1,1–1,2 lần khi token ổn
   định chiếm 9 % lên 7,1–7,7 lần khi chiếm 89 %, và độ trễ của nó không đổi theo vị trí sửa, trong khi độ trễ của B5 giảm
   một bậc độ lớn từ đầu tới cuối hậu tố.
5. **Append Correction** có chi phí cập nhật rẻ nhất và vẫn giữ đúng phần lớn dữ kiện đã cập nhật trên mô hình lớn hơn,
   nhưng ngữ cảnh dài thêm sau mỗi lần sửa, độ chính xác trên dữ kiện không đổi giảm, và trên mô hình nhỏ 21,6 % câu trả lời
   về dữ kiện đã cập nhật vẫn dùng giá trị cũ; sau mười lần sửa thì một nửa là giá trị cũ.
6. **Khuyến nghị thực tế.** Dùng tái sử dụng tiền tố chính xác; ưu tiên LCP mức token (B5) khi còn giữ chuỗi token cũ, và tổ
   chức tri thức theo kiểu Layered CAG khi các chỉnh sửa tập trung ở một phần đuôi nhỏ, hay thay đổi. Khi tính gộp cả các
   câu hỏi, lợi ích của việc cập nhật rẻ giảm dần khi số câu hỏi sau mỗi lần cập nhật tăng (dưới 10 % chi phí chu kỳ khi
   vượt ≈ 6 câu hỏi mỗi lần cập nhật trên 0.5B và ≈ 29 câu trên cấu hình 1.5B chậm hơn).

## 13. Tái lập kết quả

```bash
cd cag-benchmark
python -m venv .venv && .venv/Scripts/python -m pip install torch==2.9.1 --index-url https://download.pytorch.org/whl/cu128
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python scripts/prepare_dataset.py
.venv/Scripts/python -m pytest -q tests                                   # 30 test
.venv/Scripts/python scripts/validate_cache.py --config configs/local_pilot_q05_fp32.yaml --budget 2048 --out results/pilot_q05_fp32/cache_validation.json
.venv/Scripts/python scripts/validate_cache.py --config configs/local_reduced_q15_fp16.yaml --budget 2048 --out results/reduced_q15_fp16/cache_validation.json
.venv/Scripts/python scripts/run_benchmark.py --config configs/local_pilot_q05_fp32.yaml --out results/pilot_q05_fp32 --max-minutes 35   # chạy lại cho tới khi xong
.venv/Scripts/python scripts/run_benchmark.py --config configs/local_reduced_q15_fp16.yaml --out results/reduced_q15_fp16 --max-minutes 35
.venv/Scripts/python scripts/generate_report.py --results results/pilot_q05_fp32 --publish-summary
.venv/Scripts/python scripts/generate_report.py --results results/reduced_q15_fp16
.venv/Scripts/python scripts/progress.py
```

Số đo thô: `results/<profile>/{runs,updates,answers,conditions,questions_def}.jsonl`; bảng tổng hợp:
`benchmark_summary.csv`, `cycle_cost.csv`, `failed_runs.csv`; biểu đồ: `results/<profile>/figures/*.png|pdf`; bảng sinh tự
động: `reports/<profile>_tables.md`. Lịch sử git ghi lại từng phiên chạy.
