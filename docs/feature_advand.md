# Tài liệu bộ đặc trưng ảnh

---

# 1. Histogram màu HSV (Spatial Grid)

## Đầu vào / Đầu ra

- **Đầu vào:** Ảnh HSV, shape `(H, W, 3)`
- **Đầu ra:** Vector `grid_h × grid_w × (bH × bS × bV)` chiều  
  Ví dụ: `grid=(3,3)`, `bins=(8,4,4)` → `9 × 128 = 1152` chiều

## Tham số

| Tham số | Mặc định | Mô tả |
|---|:---:|---|
| `bins` | `(8, 4, 4)` | Số bin cho kênh H, S, V |
| `center_ratio` | `0.75` | Tỷ lệ vùng trung tâm giữ lại (0 < ratio ≤ 1.0) |
| `grid` | `(3, 3)` | Chia ảnh thành `gh × gw` ô |

## Cải tiến so với histogram đơn giản

### 1. Center Crop

- Cắt bỏ phần rìa ảnh trước khi tính histogram
- Object thường nằm giữa, nền thường ở rìa
- `center_ratio=0.75` → giữ 75% vùng giữa, cắt 12.5% mỗi phía

```
center_ratio = 0.75
mh = int(H * (1 - 0.75) / 2) = int(H * 0.125)
mw = int(W * (1 - 0.75) / 2) = int(W * 0.125)
crop = img[mh : H-mh, mw : W-mw]
```

### 2. Spatial Grid Histogram

- Chia ảnh (sau crop) thành `gh × gw` ô
- Tính histogram riêng từng ô → L2-normalize từng ô → nối lại
- Phân biệt được phân bố màu theo không gian:
  - "nền xám ở trên, vật thể nâu ở dưới" ≠ "nền xám ở dưới, vật thể nâu ở trên"

## Quy trình tính

### B1. Center Crop

```
mh = int(H * (1 - center_ratio) / 2)
mw = int(W * (1 - center_ratio) / 2)
cropped = img[mh : H-mh, mw : W-mw]
```

### B2. Chia grid và tính histogram từng ô

Với mỗi ô `(r, c)` trong grid `gh × gw`:

```
ch = H // gh     (chiều cao mỗi ô)
cw = W // gw     (chiều rộng mỗi ô)

patch = cropped[r*ch : (r+1)*ch, c*cw : (c+1)*cw]
```

### B3. Tính histogram 3D cho từng ô

Với mỗi pixel `(r, c)` trong patch:

```
i = min(floor(H_channel / 180 * bH), bH - 1)
j = min(floor(S_channel / 256 * bS), bS - 1)
k = min(floor(V_channel / 256 * bV), bV - 1)

hist3D[i][j][k] += 1
```

### B4. L2-normalize từng ô rồi nối lại

```
patch_vec = hist3D.flatten()          # (bH*bS*bV,)
patch_vec = patch_vec / ||patch_vec|| # L2-normalize từng ô

# Nối tất cả gh*gw ô
vec = concat([patch_vec_00, patch_vec_01, ..., patch_vec_GhGw])
vec = vec / ||vec||                   # L2-normalize toàn bộ
```

---

# 2. HOG — Histogram of Oriented Gradients

## Đầu vào / Đầu ra

- **Đầu vào:** Ảnh grayscale, shape `(H, W)`
- **Đầu ra:** Vector HOG đã L2-normalize  
  Ví dụ: ảnh `224×224`, `cell_size=8`, `block_size=2`, `bins=9` → `27×27×36 = 26244` chiều  
  *(sau center crop `0.75`: ảnh còn `168×168` → `20×20` cell → `19×19×36 = 12996` chiều)*

## Tham số

| Tham số | Mặc định | Mô tả |
|---|:---:|---|
| `bins` | `9` | Số bin góc (0°–180°, mỗi bin 20°) |
| `cell_size` | `8` | Kích thước ô pixel |
| `block_size` | `2` | Số ô mỗi block |
| `mag_threshold_percentile` | `30` | Bỏ gradient yếu dưới percentile này |
| `center_ratio` | `0.75` | Tỷ lệ vùng trung tâm |

## Cải tiến so với HOG gốc

### 1. Center Crop

Tương tự Histogram — chỉ tính HOG trên vùng trung tâm, giảm ảnh hưởng của background ở rìa.

### 2. Magnitude Threshold

Loại bỏ pixel có gradient yếu trước khi tích lũy vào histogram:

```
threshold = percentile(magnitude_toàn_ảnh, mag_threshold_percentile)

nếu magnitude[pixel] < threshold → bỏ qua pixel đó
```

- Nền phẳng (bầu trời, cát, đất) tạo gradient yếu nhưng nhiều
- Loại bỏ chúng giúp histogram phản ánh đúng hình dạng object

## Quy trình tính

### B0. Center Crop

```
work_img = crop_center(img, center_ratio)
```

### B1. Tính Gradient Gx, Gy

Pad ảnh thêm 1 pixel (zero-padding), dùng kernel `[-1, 0, 1]`:

```
Gx[h, w] = pad[h+1, w+2] - pad[h+1, w]     (gradient ngang)
Gy[h, w] = pad[h,   w+1] - pad[h+2, w+1]   (gradient dọc)
```

### B2. Tính Magnitude và Angle

```
magnitude[h, w] = sqrt(Gx² + Gy²)
angle[h, w]     = atan2(Gy, Gx) → đổi sang độ → [0, 180)

nếu angle < 0: angle += 180
```

### B3. Tính histogram từng Cell (có threshold)

```
threshold = percentile(magnitude, mag_threshold_percentile)

với mỗi cell (ci, cj):
    với mỗi pixel (pi, pj) trong cell:
        nếu magnitude[pi, pj] < threshold → bỏ qua
        bin_idx = min(int(angle[pi, pj] / 20), bins - 1)
        his_cell[ci, cj, bin_idx] += magnitude[pi, pj]
```

### B4. Chuẩn hóa Block

```
số block = (n_cell_h - block_size + 1) × (n_cell_w - block_size + 1)

với mỗi block (ci, cj):
    his_bloc = concat(his_cell[ci+i, cj+j] với i,j ∈ [0, block_size))
               → block_size² × bins số (ví dụ 2²×9 = 36 số)
    his_bloc = his_bloc / ||his_bloc||   (L2-normalize)
```

### B5. Ghép vector cuối

```
vec = flatten(tất cả his_bloc đã normalize)
vec = vec / ||vec||   (L2-normalize lần cuối)
```

---

# 3. Texture (LBP + GLCM + Edge Density)

## Đầu vào / Đầu ra

- **Đầu vào:** Ảnh RGB hoặc grayscale, shape `(H, W, 3)` hoặc `(H, W)`
- **Đầu ra:** Vector `lbp_bins + 4 + (gh × gw)` chiều  
  Với defaults: `256 + 4 + 16 = 276` chiều

## Tham số

| Tham số | Mặc định | Mô tả |
|---|:---:|---|
| `lbp_bins` | `256` | Số bin histogram LBP |
| `glcm_levels` | `8` | Số mức lượng tử hóa $L$ cho GLCM |
| `glcm_distance` | `1` | Khoảng cách pixel $d$ cho GLCM (hướng ngang) |
| `edge_grid` | `(4, 4)` | Grid tính mật độ cạnh |

## Bước 1 — Grayscale

```
Gray = 0.299R + 0.587G + 0.114B
```

Nếu ảnh đã là grayscale thì bỏ qua.

---

## Bước 2 — LBP Histogram (256 chiều)

### Ý tưởng

LBP mã hóa cấu trúc cục bộ xung quanh mỗi pixel bằng cách so sánh với 8 láng giềng → số 8-bit (0–255). Bền vững với thay đổi độ sáng đơn điệu.

### 8 láng giềng (thứ tự cố định)

```
p=3  p=2  p=1
p=4   c   p=0
p=5  p=6  p=7
```

| p | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Hướng | E | NE | N | NW | W | SW | S | SE |
| Offset (dx, dy) | (0,+1) | (-1,+1) | (-1,0) | (-1,-1) | (0,-1) | (+1,-1) | (+1,0) | (+1,+1) |

### Công thức mã LBP

$$\text{LBP}(x, y) = \sum_{p=0}^{7} s(I_p - I_c) \cdot 2^p$$

Với $s(x) = 1$ nếu $x \ge 0$, $s(x) = 0$ nếu $x < 0$.

**Triển khai vectorized (không dùng vòng lặp pixel):**

```python
pad = zeros(H+2, W+2)
pad[1:-1, 1:-1] = gray

center  = pad[1:-1, 1:-1]       # (H, W)
lbp_map = zeros(H, W, uint8)

for p, (dx, dy) in enumerate(OFFSET):
    neighbor  = pad[1+dx : H+1+dx, 1+dy : W+1+dy]
    lbp_map  += (neighbor >= center).astype(uint8) * (1 << p)
```

### Histogram và chuẩn hóa

```
hist[k] = số pixel có mã LBP = k,  k ∈ {0, ..., 255}
hist    = hist / ||hist||           (L2-normalize)
```

---

## Bước 3 — GLCM Stats (4 chiều)

### B3.1 Lượng tử hóa

```
q(x, y) = floor(gray[x, y] / (256 / L))
q        = clip(q, 0, L-1)
```

### B3.2 Đếm cặp đồng xuất hiện (hướng ngang, khoảng cách d)

```
với mỗi (x, y):
    i = q[x, y]
    j = q[x, y+d]
    G[i, j] += 1    (cặp gốc)
    G[j, i] += 1    (đối xứng)

P = G / G.sum()     (chuẩn hóa thành xác suất)
```

### B3.3 Các chỉ số thống kê

$$\mu_r = \sum_{r,c} r \cdot P(r,c), \quad \sigma_r = \sqrt{\sum_{r,c}(r-\mu_r)^2 P(r,c)}$$

| Chỉ số | Công thức | Ý nghĩa |
|---|---|---|
| Contrast | $\sum_{r,c}(r-c)^2 P(r,c)$ | Cao = texture sần sùi, cạnh sắc |
| Energy | $\sum_{r,c} P(r,c)^2$ | Cao = texture lặp đều đặn |
| Homogeneity | $\sum_{r,c} \frac{P(r,c)}{1+\|r-c\|}$ | Cao = pixel lân cận giống nhau |
| Correlation | $\frac{\sum_{r,c}(r-\mu_r)(c-\mu_c)P(r,c)}{\sigma_r \sigma_c}$ | Tương quan mức xám lân cận |

**Edge case:** nếu $\sigma_r < 10^{-10}$ hoặc $\sigma_c < 10^{-10}$ → Correlation = 1.

**Thứ tự trong vector:** `[Contrast, Energy, Homogeneity, Correlation]`

---

## Bước 4 — Edge Density Map (gh × gw chiều)

### Ý tưởng

Phân bố mật độ cạnh theo vùng không gian phân biệt hình dạng tổng thể mà LBP/GLCM toàn cục bỏ qua:

- **Sư tử:** bờm tạo edges dày ở vùng trên-giữa, thân nhỏ ở dưới
- **Voi:** thân khổng lồ trải đều, vòi dài tạo đường thẳng

### Quy trình

```
# B1: Tính gradient magnitude toàn ảnh (vectorized)
pad = zeros(H+2, W+2);  pad[1:-1, 1:-1] = gray
gx  = pad[1:-1, 2:]  - pad[1:-1, :-2]   # (H, W)
gy  = pad[:-2, 1:-1] - pad[2:, 1:-1]    # (H, W)
mag = sqrt(gx² + gy²)                   # (H, W)

# B2: Chia grid gh × gw, tính mean magnitude mỗi vùng
ch = H // gh
cw = W // gw

density[r*gw + c] = mean(mag[r*ch:(r+1)*ch, c*cw:(c+1)*cw])

# B3: L2-normalize
density = density / ||density||
```

**Kết quả:** vector `(gh × gw,)` = `(16,)` với `edge_grid=(4,4)`

---

## Bước 5 — Ghép vector cuối

$$\mathbf{v} = [\underbrace{\text{LBP hist}}_{256}, \underbrace{\text{Contrast, Energy, Homogeneity, Correlation}}_{4}, \underbrace{\text{Edge density}}_{gh \times gw}]$$

```python
vec = concat([lbp_hist, glcm_stats, edge_density])
# shape: (276,) với defaults
vec = vec / ||vec||   # L2-normalize lần cuối
```

---

## Tóm tắt chiều vector toàn bộ pipeline

| Đặc trưng | Chiều | Ghi chú |
|---|:---:|---|
| Histogram HSV (spatial grid 3×3) | 1152 | `bins=(8,4,4)`, `grid=(3,3)` |
| HOG | 12996 | Sau center crop 0.75 trên ảnh 224×224 |
| LBP histogram | 256 | |
| GLCM stats | 4 | Contrast, Energy, Homogeneity, Correlation |
| Edge Density Map | 16 | `edge_grid=(4,4)` |
| **Texture tổng** | **276** | LBP + GLCM + Edge Density |

---

# 4. CNN — Trích đặc trưng bằng DINOv2

## Tại sao cần CNN

Pipeline thủ công (Histogram + HOG + Texture) có giới hạn cơ bản không thể vượt qua bằng cách thêm feature:

- Mọi feature thủ công đều mô tả **pixel-level statistics** — màu sắc, cạnh, texture vi mô
- CNN học được **semantic concepts** — "đây là mặt động vật", "đây là bầu trời"
- Kết quả thực tế: feature thủ công tốt nhất ~0.65 cosine similarity cho 2 ảnh sư tử khác góc, DINOv2 đạt ~0.82

## Đầu vào / Đầu ra

- **Đầu vào:** Ảnh BGR, shape `(H, W, 3)`, dtype `uint8` — format OpenCV
- **Đầu ra:** Vector `(768,)`, dtype `float32`, đã L2-normalize

## Quy trình xử lý

### B1. Chuyển màu BGR → RGB

```python
img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
```

OpenCV đọc ảnh theo thứ tự BGR, model ImageNet yêu cầu RGB.

### B2. Transform chuẩn ImageNet

```python
transform = Compose([
    Resize((224, 224)),       # đưa về kích thước cố định
    ToTensor(),               # (H,W,3) uint8 → (3,H,W) float [0,1]
    Normalize(
        mean=[0.485, 0.456, 0.406],   # mean ImageNet theo kênh R,G,B
        std =[0.229, 0.224, 0.225],   # std  ImageNet theo kênh R,G,B
    )
])
# Output: tensor (3, 224, 224)
```

Normalize đưa pixel về phân phối chuẩn mà model đã thấy lúc train — bỏ bước này làm feature vector vô nghĩa.

### B3. Forward pass qua DINOv2

```python
tensor = transform(pil_img).unsqueeze(0)   # (1, 3, 224, 224)

with torch.no_grad():                      # không cần gradient
    vec = model(tensor)                    # (1, 768)

vec = vec.squeeze().cpu().numpy()          # (768,)
```

DINOv2 chia ảnh thành các patch 14×14 pixel → `224/14 = 16×16 = 256 patch` → mỗi patch được encode → gộp lại thành vector 768 chiều đại diện toàn ảnh.

### B4. L2-normalize

```python
norm = np.linalg.norm(vec)
if norm > 1e-10:
    vec /= norm
# ||vec|| = 1 → cosine similarity = dot product đơn giản
```

## Tính cosine similarity

Vì vector đã L2-normalize, cosine similarity chỉ cần dot product:

```python
cosine = float(np.dot(vec1, vec2))   # kết quả trong [-1, 1]
```

## Kết quả kỳ vọng

| Cặp ảnh | Feature thủ công | DINOv2 |
|---|:---:|:---:|
| Sư tử vs sư tử (khác góc, khác nền) | ~0.56–0.65 | ~0.78–0.88 |
| Anime girl vs sư tử | ~0.60–0.67 | ~0.10–0.20 |
| Sư tử vs voi | ~0.70–0.80 | ~0.40–0.55 |

---

# 5. Giới hạn và kết quả thực tế

## Tại sao không thể đạt chính xác tuyệt đối

### Semantic gap

Bài toán image retrieval về bản chất là ánh xạ từ pixel (số) sang khái niệm ngữ nghĩa (ý nghĩa). Không có thuật toán nào ánh xạ hoàn hảo — kể cả model lớn nhất thế giới. Cosine similarity ~0.9 với cùng loài và ~0.3 với khác loài đã là kết quả rất tốt trong thực tế.

### Curse of dimensionality

Vector càng nhiều chiều, cosine similarity giữa 2 vector ngẫu nhiên càng tiệm cận về một giá trị dương. Đây là hiện tượng toán học thuần túy, không phải lỗi thuật toán.

```python
# Minh chứng: 2 vector ngẫu nhiên 30000 chiều
a = np.random.rand(30000)
b = np.random.rand(30000)
cosine = np.dot(a / np.linalg.norm(a), b / np.linalg.norm(b))
# → cosine ≈ 0.65–0.70 dù hoàn toàn ngẫu nhiên
```

### Intra-class variation

Sư tử chụp ban đêm có thể khác sư tử ban ngày nhiều hơn sư tử vs voi trong cùng điều kiện ánh sáng. Không có feature nào — thủ công hay CNN — hoàn toàn bất biến với góc chụp, ánh sáng, scale.

## Giới hạn của từng phương pháp

| Phương pháp | Phân biệt tốt | Không phân biệt được |
|---|---|---|
| Histogram HSV | Màu sắc chủ đạo | Cùng màu nền, khác nội dung |
| HOG | Cạnh, hướng gradient | Ảnh "mềm" có gradient tương tự |
| LBP + GLCM | Texture vi mô | Texture tổng thể giống nhau |
| Edge Density | Phân bố cạnh theo vùng | Nội dung ngữ nghĩa |
| Gabor Filter | Tần số + hướng texture | Vị trí không gian của object |
| DINOv2 pretrained | Ngữ nghĩa tổng quát | Domain rất đặc thù (ảnh y tế, công nghiệp) |

## Tại sao không nên tự train CNN từ đầu

DINOv2 được train trên 142 triệu ảnh với hàng nghìn GPU trong nhiều tuần. Tự train từ đầu với ít data hơn sẽ cho kết quả tệ hơn pretrained vì:

- **Thiếu data:** CNN cần tối thiểu hàng chục nghìn ảnh có nhãn. Ít hơn → overfit nghiêm trọng
- **Thiếu tài nguyên:** Train từ đầu cần GPU mạnh chạy nhiều ngày đến nhiều tuần
- **Loss function phức tạp:** Image retrieval cần Triplet Loss hoặc Contrastive Loss, không phải classification loss thông thường — cần thuật toán hard negative mining để chọn đúng cặp ảnh huấn luyện
