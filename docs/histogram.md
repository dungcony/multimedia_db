# Bước tính bộ đặc trưng của 1 ảnh sang vector

## **Tính Histogram**

### ***Đầu vào***

    Ảnh RGB định dạng jpg, png, ...

### ***Đầu ra***

    vector với số chiều cụ thể

### ***Chuyển sang HSV***

#### *B1. Đọc ảnh*

    Sử dụng thư viện Image để đọc ảnh và convert về dạng RGB

#### *B2. Reize*

- Đưa ảnh về cùng 1 size để dễ dàng xử lý
- Phương pháp sử dụng: nội suy từ 4 pixel lân cận

1. Xác định các biến
    - (x0, y0) = (⌊x⌋, ⌊y⌋) (pixel trên trái)
    - (x1, y1) = (x0 + 1, y0 + 1)
    - 4 pixel xung quanh
        - P₀₀ = P(x0, y0)    (trên trái)
        - P₁₀ = P(x1, y0)    (trên phải)
        - P₀₁ = P(x0, y1)    (dưới trái)
        - P₁₁ = P(x1, y1)    (dưới phải)

                    ```text
                    P₀₀ -------- P₁₀
                    |            |
                    |   (x, y)   |
                    |            |
                    P₀₁ -------- P₁₁
                    ```
    - [x]   : phần nguyên của x
    - [y]   : phần nguyên của y
    - dx    : phần thập phân của x
    - dy    : phần thập phân của y

2. Tính khoảng lệch
    - Ý nghĩa:
        - Là phép tính **trung bình có trọng số của 4 pixel lân cận**
            - pixel gần (x,y) sẽ có trọng số lớn
        - Giúp ảnh resize **mượt hơn, không bị ô vuông** so với nearest neighbor (hàng xóm gần nhất)

    - Công thức:

            pixel   = (1-dx)(1-dy)*P₀₀
                    + dx(1-dy)*P₁₀
                    + dy(1-dx)*P₀₁
                    + dxdy*P₁₁

#### *B3. Chuyển ảnh đã resize sang dạng HSV*

1. Xác định khoảng giá trị
    - H: [0-179]
    - S: [0-255]
    - V: [0-255]
2. Công thức biến đổi:
    - R',G',B'    = R,G,B/255
    - Cmax  = max(R',G',B')
    - Cmin  = min()
    - Δ     = Cmax - Cmin

3. Tính các thuộc tính của Hue
    - `Δ = 0` → `H = 0 (màu xám)`
    - `Cmax = R'` → `H = 60 × ((G'-B')/Δ mod 6)`
    - `Cmax = G'` → `H = 60 × ((B'-R')/Δ + 2)`
    - `Cmax = B'` → `H = 60 × ((R'-G')/Δ + 4)`
    - `S = Δ/Cmax × 255 (hoặc 0 nếu Cmax=0)`
    - `V = Cmax × 255`

### ***Tính Histogram***

#### *Histogram là gì?*

    Bảng đếm tần suất: mỗi pixel được phân loại vào 1 **bin** dựa trên giá trị, rồi đếm số pixel trong mỗi bin

#### *bin là gì?*

    - số bin là thứ để quyết định độ chi tiết của histogram
        + quá ít thì mất thông tin
        + quá nhiều thì nhiễu và chậm

    - H là đơn vị xác định màu sắc -> (16-36)
    - S,V ít nhạy hơn vì nó quyết định độ đậm, nhạt (4-8)
    - phổ biến nhất sẽ chọn 18,8,8

#### *Histogram 3D*

    - Với 3 kênh (H,S,V) và số bin (bH,bS,bV) ta có:
    - hist[i][j][k] = số pixel có H thuộc bin i, S thuộc bin j, V thuộc bin k

#### *B1. Xác định bH, bS, bV*

    - bH = 18
    - bS = 8
    - bV = 8

#### *B2. Tính bin_idx*

    - i = floor(h / 180 * bH)
    - j = floor(s / 256 * bS)
    - k = floor(v / 256 * bV)

    Tránh bị out of range
    - i = min(i, bH - 1)
    - j = min(j, bS - 1)
    - k = min(j, bV - 1)

    hist[i][j][k] += 1

### ***Chuẩn hóa***

#### *Tại sao cần chuẩn hóa?*

- Loại bỏ ảnh hưởng của **tổng số pixel** (ảnh to/nhỏ có tổng histogram khác nhau, nhưng **tỷ lệ** tương tự).
- Sau chuẩn hóa: `||v|| = 1` → cosine similarity = dot product (nhanh hơn).
- Công thức:

        ```
        ||v||₂ = √(v₁² + v₂² + ... + vₙ²)
        v_norm = v / ||v||₂
        ```

## **Tính độ tương đồng**

- Công thức:

        cos(v₁, v₂) = (v₁ · v₂) / (||v₁|| × ||v₂||)

- dải giá trị = {-1,1}
  - = 1 : giống hệt
  - = 0 : không liên quan
  - = -1: đối lập
