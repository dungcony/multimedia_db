# Đặc trưng Texture (LBP + GLCM)

Đặc trưng texture mô tả **cấu trúc bề mặt** của ảnh — vằn, gồ ghề, mịn, vảy, lông — thay vì màu sắc hay hình dạng. Pipeline gồm 4 bước chính:

1. Chuẩn hóa ảnh sang grayscale
2. Tính LBP → histogram 256 bin
3. Tính GLCM → 4 chỉ số thống kê
4. Ghép thành vector đặc trưng 260 chiều

---

## Bước 1 — Chuẩn hóa sang Grayscale

Nếu ảnh đầu vào là RGB, chuyển sang grayscale theo trọng số cảm nhận của mắt người:

$$
\text{Gray} = 0.299R + 0.587G + 0.114B
$$

**Giải thích biến:**

- $R, G, B$: giá trị kênh màu, phạm vi $[0, 255]$
- $\text{Gray}$: giá trị pixel xám, phạm vi $[0, 255]$, kiểu `float` trước khi làm tròn

**Lưu ý khi code:** sau phép tính trên, làm tròn và ép về `uint8`. Nếu ảnh đã là grayscale thì bỏ qua bước này.

```python
gray = 0.299 * R + 0.587 * G + 0.114 * B  # shape (H, W), dtype float
gray = gray.astype(np.uint8)
```

---

## Bước 2 — LBP (Local Binary Pattern)

### Ý tưởng

LBP mô tả **cấu trúc cục bộ** xung quanh mỗi pixel bằng cách so sánh pixel trung tâm với 8 láng giềng của nó. Kết quả là một số 8-bit (0–255) — gọi là **mã LBP** — mã hóa pattern sáng/tối quanh điểm đó.

LBP bền vững trước **thay đổi độ sáng đơn điệu** (tăng/giảm đều toàn ảnh) vì chỉ dùng phép so sánh tương đối, không dùng giá trị tuyệt đối.

### Bước 2.1 — Xác định 8 láng giềng

Với mỗi pixel trung tâm tại $(x, y)$, xét 8 pixel xung quanh theo thứ tự **cố định** sau (ngược chiều kim đồng hồ, bắt đầu từ E):

```
p=3  p=2  p=1
p=4   c   p=0
p=5  p=6  p=7
```

| $p$ | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Hướng | E | NE | N | NW | W | SW | S | SE |
| Offset $(dx, dy)$ | $(0,+1)$ | $(-1,+1)$ | $(-1,0)$ | $(-1,-1)$ | $(0,-1)$ | $(+1,-1)$ | $(+1,0)$ | $(+1,+1)$ |

> **Quy ước offset:** $dx$ = dịch hàng (dương = xuống), $dy$ = dịch cột (dương = phải).

### Bước 2.2 — Tính mã LBP

Định nghĩa hàm ngưỡng:

$$
s(x) = \begin{cases} 1 & x \ge 0 \\ 0 & x < 0 \end{cases}
$$

Mã LBP của pixel trung tâm $I_c$:

$$
\text{LBP}(x, y) = \sum_{p=0}^{7} s\!\left(I_p - I_c\right) \cdot 2^p
$$

**Giải thích biến:**

- $I_c = \text{gray}[x, y]$: giá trị pixel trung tâm
- $I_p = \text{gray}[x + dx_p,\; y + dy_p]$: giá trị láng giềng thứ $p$
- $s(I_p - I_c)$: bằng 1 nếu láng giềng $\ge$ trung tâm, bằng 0 nếu ngược lại
- $2^p$: trọng số vị trí bit

Kết quả là một số nguyên trong $[0, 255]$.

### Ví dụ tính mã LBP

Patch 3×3, pixel trung tâm $I_c = 50$:

$$
\begin{bmatrix}
40 & 55 & 58 \\
45 & \mathbf{50} & 60 \\
35 & 48 & 52
\end{bmatrix}
$$

Tra bảng offset, lấy giá trị từng láng giềng và so sánh:

| $p$ | Hướng | $I_p$ | $I_p - I_c$ | $s(\cdot)$ | $s \cdot 2^p$ |
|:---:|:---:|:---:|:---:|:---:|:---:|
| 0 | E | 60 | +10 | 1 | 1 |
| 1 | NE | 58 | +8 | 1 | 2 |
| 2 | N | 55 | +5 | 1 | 4 |
| 3 | NW | 40 | −10 | 0 | 0 |
| 4 | W | 45 | −5 | 0 | 0 |
| 5 | SW | 35 | −15 | 0 | 0 |
| 6 | S | 48 | −2 | 0 | 0 |
| 7 | SE | 52 | +2 | 1 | 128 |

$$
\text{LBP} = 1 + 2 + 4 + 0 + 0 + 0 + 0 + 128 = \mathbf{135}
$$

Chuỗi bit (từ $p=7$ đến $p=0$): `10000111`

### Bước 2.3 — Xây dựng Histogram LBP

Duyệt toàn bộ ảnh, **bỏ viền 1 pixel** (vì pixel viền thiếu láng giềng), tính mã LBP cho từng pixel rồi đếm tần suất:

```
for x in range(1, H-1):
    for y in range(1, W-1):
        lbp_map[x, y] = tính LBP tại (x, y)

histogram h[k] = số pixel có mã LBP = k,  k ∈ {0, 1, ..., 255}
```

Chuẩn hóa L2 để bất biến với kích thước ảnh:

$$
\hat{h}_k = \frac{h_k}{\sqrt{\displaystyle\sum_{k=0}^{255} h_k^2}}
$$

**Kết quả:** vector $\hat{h}$ gồm **256 giá trị** `float`, tổng bình phương bằng 1.

### Ý nghĩa một số mã LBP

| Mã | Chuỗi bit | Pattern | Ý nghĩa hình học |
|:---:|:---:|:---:|:---|
| 0 | `00000000` | Tất cả tối hơn | Vùng sáng cô lập (đỉnh sáng) |
| 255 | `11111111` | Tất cả sáng hơn | Vùng tối cô lập (hố tối) |
| 15 | `00001111` | Nửa sáng nửa tối | Cạnh thẳng |
| 135 | `10000111` | Cụm sáng một góc | Góc hoặc điểm đặc trưng |

---

## Bước 3 — GLCM (Gray-Level Co-occurrence Matrix)

### Ý tưởng

GLCM mô tả **quan hệ không gian** giữa các cặp pixel — cụ thể là: mức xám nào hay xuất hiện cạnh mức xám nào. Từ đó rút ra 4 chỉ số thống kê mô tả tính chất texture.

### Bước 3.1 — Lượng tử hóa grayscale

Giảm số mức xám từ 256 xuống $L$ mức để ma trận GLCM nhỏ gọn hơn:

$$
q(x, y) = \left\lfloor \frac{\text{gray}[x, y]}{256 / L} \right\rfloor
$$

**Giải thích biến:**

- $L$: số mức xám rút gọn — tham số `glcm_levels`, mặc định 8
- $q(x,y)$: mức xám sau lượng tử hóa, phạm vi $[0, L-1]$

**Ví dụ** với $L = 8$: pixel có gray = 200 → $q = \lfloor 200/32 \rfloor = 6$

**Lưu ý khi code:** pixel có gray = 255 → $q = \lfloor 255/32 \rfloor = 7$ — đúng bằng $L-1$, không bị tràn.

### Bước 3.2 — Đếm cặp đồng xuất hiện

Với khoảng cách $d$ theo **hướng ngang** (pixel $(x,y)$ và $(x, y+d)$):

$$
G(i,\, j) = \#\bigl\{(x, y) \mid q(x, y) = i,\; q(x,\, y + d) = j\bigr\}
$$

**Đối xứng hóa** để GLCM không phụ thuộc chiều trái/phải — với mỗi cặp tìm được, tăng **cả hai**:

$$
G(i, j) \mathrel{+}= 1 \qquad \text{và} \qquad G(j, i) \mathrel{+}= 1
$$

**Chuẩn hóa** thành xác suất:

$$
P(i, j) = \frac{G(i, j)}{\displaystyle\sum_{i'=0}^{L-1}\sum_{j'=0}^{L-1} G(i', j')}
$$

```
Khởi tạo G[L][L] = 0

for x in range(H):
    for y in range(W - d):
        i = q[x, y]
        j = q[x, y + d]
        G[i][j] += 1
        G[j][i] += 1          # đối xứng hóa

P = G / G.sum()               # chuẩn hóa
```

### Ví dụ minh họa (L = 4, d = 1)

Ảnh đã lượng tử hóa:

$$
\begin{bmatrix}
0 & 1 & 1 & 2 \\
2 & 2 & 1 & 0 \\
1 & 0 & 0 & 1 \\
3 & 2 & 2 & 1
\end{bmatrix}
$$

Các cặp $(i, j)$ thu được khi duyệt hàng ngang:

| Hàng | Cặp gốc | Sau đối xứng |
|:---:|---|---|
| 0 | (0,1), (1,1), (1,2) | + (1,0), (1,1), (2,1) |
| 1 | (2,2), (2,1), (1,0) | + (2,2), (1,2), (0,1) |
| 2 | (1,0), (0,0), (0,1) | + (0,1), (0,0), (1,0) |
| 3 | (3,2), (2,2), (2,1) | + (2,3), (2,2), (1,2) |

Tổng cộng 24 lần đếm → chuẩn hóa để ra $P(i,j)$.

### Bước 3.3 — Tính các chỉ số thống kê

Trước hết tính kỳ vọng và độ lệch chuẩn (dùng $r, c$ làm biến lặp để tránh nhầm với chỉ số $i, j$):

$$
\mu_r = \sum_{r=0}^{L-1}\sum_{c=0}^{L-1} r \cdot P(r,c), \qquad
\mu_c = \sum_{r=0}^{L-1}\sum_{c=0}^{L-1} c \cdot P(r,c)
$$

$$
\sigma_r = \sqrt{\sum_{r,c} (r - \mu_r)^2 P(r,c)}, \qquad
\sigma_c = \sqrt{\sum_{r,c} (c - \mu_c)^2 P(r,c)}
$$

#### Contrast

$$
\text{Contrast} = \sum_{r,c} (r - c)^2 \, P(r,c)
$$

- **Phạm vi:** $[0,\; (L-1)^2]$
- **Cao** → nhiều cạnh sắc nét, bề mặt sần sùi (đá, vải thô).
- **Thấp** → bề mặt mịn, đồng đều (bầu trời, tường trơn).

#### Energy

$$
\text{Energy} = \sum_{r,c} P(r,c)^2
$$

- **Phạm vi:** $(0,\; 1]$; đạt 1 khi ảnh hoàn toàn đồng nhất.
- **Cao** → texture lặp lại đều đặn (vải kẻ sọc).
- **Thấp** → texture ngẫu nhiên, phức tạp.

#### Homogeneity

$$
\text{Homogeneity} = \sum_{r,c} \frac{P(r,c)}{1 + |r - c|}
$$

- **Phạm vi:** $(0,\; 1]$; đạt 1 khi mọi cặp pixel có cùng mức xám.
- **Cao** → các pixel cạnh nhau thường có mức xám gần nhau.
- **Thấp** → nhiều cặp pixel chênh lệch mức xám lớn.

#### Correlation

$$
\text{Correlation} = \frac{\displaystyle\sum_{r,c} (r - \mu_r)(c - \mu_c)\, P(r,c)}{\sigma_r \cdot \sigma_c}
$$

- **Phạm vi:** $[-1,\; 1]$
- **Gần 1** → pixel bên trái sáng thì bên phải cũng có xu hướng sáng.
- **Gần −1** → tương quan nghịch.
- **Gần 0** → không có xu hướng tuyến tính.
- **Edge case:** nếu $\sigma_r = 0$ hoặc $\sigma_c = 0$ (ảnh đồng nhất hoàn toàn) → gán Correlation = 1.

### Thứ tự 4 chỉ số trong vector

Ghép theo thứ tự cố định:

$$
\text{glcm\_stats} = [\,\text{Contrast},\; \text{Energy},\; \text{Homogeneity},\; \text{Correlation}\,]
$$

### Tóm tắt ý nghĩa đầu ra

| Chỉ số | Phạm vi | Texture mịn / đồng đều | Texture sần / ngẫu nhiên |
|---|:---:|:---:|:---:|
| Contrast | $[0,\,(L{-}1)^2]$ | Thấp | Cao |
| Energy | $(0,\,1]$ | Cao | Thấp |
| Homogeneity | $(0,\,1]$ | Cao | Thấp |
| Correlation | $[-1,\,1]$ | Gần 1 | Biến thiên |

---

## Bước 4 — Ghép Vector Đặc Trưng

$$
\mathbf{v} = \bigl[\,\underbrace{\hat{h}_0,\; \hat{h}_1,\; \ldots,\; \hat{h}_{255}}_{\text{LBP histogram — 256 chiều}},\;\; \underbrace{\text{Contrast},\; \text{Energy},\; \text{Homogeneity},\; \text{Correlation}}_{\text{GLCM stats — 4 chiều}}\,\bigr]
$$

**Tổng chiều: 260**

```python
feature_vector = np.concatenate([lbp_hist_normalized, glcm_stats])
# shape: (260,), dtype: float64
```

---

## Tham số

| Tham số | Mặc định | Mô tả |
|---|:---:|---|
| `lbp_bins` | 256 | Số bin LBP. Hiện tại chỉ hỗ trợ 256. |
| `glcm_levels` | 8 | Số mức lượng tử hóa $L$ cho GLCM. |
| `glcm_distance` | 1 | Khoảng cách pixel $d$ dùng cho GLCM (hướng ngang). |

---

## Cách dùng

```python
from src.models.texture import Texture

tex = Texture(img)        # img: numpy array, RGB hoặc grayscale
vec = tex.vec             # numpy array, shape (260,)
```

---

## Ghi chú khi implement

- **Viền ảnh trong LBP:** bỏ 1 pixel viền khi duyệt (hàng 1 đến H-2, cột 1 đến W-2). Pixel viền không có đủ 8 láng giềng.
- **Viền ảnh trong GLCM:** duyệt cột 0 đến W-2 (lấy cặp $(y, y+d)$ nên cột cuối là W-1-d).
- **Tràn số lượng tử hóa GLCM:** với $L=8$, pixel gray=255 → $q = \lfloor255/32\rfloor = 7 = L-1$, không bị tràn. Với các $L$ khác cần kiểm tra lại.
- **Edge case Correlation:** kiểm tra $\sigma_r \cdot \sigma_c < \epsilon$ trước khi chia.
- **Dtype:** giữ `float64` trong suốt quá trình tính; chỉ ép `uint8` ở bước grayscale.
