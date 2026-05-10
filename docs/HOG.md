# **Tìm hiểu về HOG - histogram of oriented gradients (biểu đồ độ dốc định hướng)**

## HOG là gì ?

    - là 1 dạng (feature descriptor/mô tả đặc trưng) sử dụng trong computer vision và xử lý hình ảnh, dùng để detec(phát hiện) 1 đối tượng.
    - Các khái niệm về HOG được nêu ra từ năm 1986 tuy nhiên cho đến năm 2005 HOG mới được sử dụng rộng rãi sau khi Navneet Dalal và Bill Triggs công bố những bổ sung về HOG.
    - Hog tương tự như các biểu đồ edge orientation, scale-invariant feature transform descriptors(như sift, surf,..), shape contexts nhưng HOG được tính toán trên một lưới dày đặc các cell và chuẩn hóa sự tương phản giữa các block để nâng cao độ chính xác.
    - Hog được sử dụng chủ yếu để mô tả hình dạng và sự xuất hiện của một object trong ảnh Bài toán tính toán Hog thường gồm 5 bước:
        1. Chuẩn hóa hình ảnh 
        2. Tính gradients theo cả x và y
        3. Lấy phiếu bầu cùng trọng số trong các cell
        4. Chuẩn hóa các block
        5. Thu thập tất cả các biểu đồ cường độ gradient định hướng để tạo ra feature vector cuối cùng

## **Chuẩn hóa hình ảnh**

### ***Đổi ảnh sang grayscale***

#### *Grayscale*

- là ảnh thang đo độ xám
- bao gồm các săc độ xám, chuyển từ đen(0) -> trắng(255)
- không chứa thông tin màu sắc
- Ảnh grayscale không phải là ảnh đen trắng vì có nhiều cấp độ xám.

#### *RGB sang Grayscale*

- Sử dụng tính chất mắt người nhìn sáng tối chủ yếu theo kênh xanh lá
- Công thức:

      Gray=0.299R+0.587G+0.114B

- Trong đó:
  - R (Red) ảnh hưởng ~29.9%
  - G (Green) ảnh hưởng ~58.7%
  - B (Blue) ảnh hưởng ~11.4%

## **Tính toán gradients theo trục X và Y**

### ***Tính Gradient***

- Đo mức độ thay đổi độ sáng giữa các pixel lân cận.
- pixel tối → pixel sáng = gradient lớn  (có cạnh)
- pixel tối → pixel tối  = gradient nhỏ  (không có cạnh)
- Công thức đơn giản nhất:

      Gx[i][j] = gray[i][j+1] - gray[i][j-1]   # thay đổi ngang
      Gy[i][j] = gray[i-1][j] - gray[i+1][j]   # thay đổi dọc

  - Ví dụ:
  
            ┌────┬────┬────┐
            │ 50 │ 80 │120 │
            ├────┼────┼────┤
            │ 60 │ 90 │130 │  ← pixel giữa (i=1, j=1)
            ├────┼────┼────┤
            │ 70 │100 │140 │
            └────┴────┴────┘

    - `Gx = gray[1][2] - gray[1][0] = 130 - 60 = 70   (thay đổi ngang)`
    - `Gy = gray[0][1] - gray[2][1] = 80  - 100 = -20  (thay đổi dọc)`

- Ý nghĩa:
  - Gx lớn  → cạnh dọc  │
  - Gy lớn  → cạnh ngang ─
  - cả hai  → cạnh chéo  /

### ***Tính magnitude and angle (độ lớn và góc)***

#### *Magnitude*

- Công thức

        magnitude   = sqrt(Gx² + Gy²)
                    = sqrt(70² + (-20)²)
                    = sqrt(4900 + 400)
                    = sqrt(5300) ≈ 72.8    ← độ mạnh của cạnh
- Ý nghĩa:
  - Là độ mạnh của cạnh
  - càng lớn -> pixel đó nằm trên cạnh  càng rõ

#### *Angle*

- HOG dùng dải 0°–180° (không phân biệt chiều):
- Công thức

        angle   = arctan(Gy / Gx)
                = arctan(-20 / 70)
                ≈ -16°

        angle < 0 → angle = angle + 180°
        -16° + 180° = 164°   ← hướng của cạnh
- Ý nghĩa:
  - Là hướng của cạnh

- Ví dụ:

        Gx=100, Gy=0    → angle=0°    → cạnh dọc   │
        Gx=0,   Gy=100  → angle=90°   → cạnh ngang ─
        Gx=100, Gy=100  → angle=45°   → cạnh chéo  /

### ***Đầu ra***

1. `Magnitude[i][j]` -> dùng làm trọng số khi đếm vào bin
2. `Angle[i][j]` -> dùng để xác định bin nào

## **Lấy votes trong mỗi cell**

### ***Cell***

- Là khi chia ảnh thành các ô vuông nhỏ, mỗi ô là 1 Cell
- Ví dụ:

        Ảnh 224x224, cell size = 8x8
        -> mỗi ô = 1 cell = 8x8 pixel 
        -> có 224x224 / 8x8 = 784 cell

### ***Tính histogram hướng cho mỗi cell***

#### *Bin*

- Là ngăn chứa dùng để đếm và phân loại
- Ta sử dụng bin = 9
- Dải góc là 0-180 độ

        bin 0:  góc 0°  – 20°    → đếm cạnh nằm ngang  ─
        bin 1:  góc 20° – 40°    → đếm cạnh hơi nghiêng
        ...
        bin 8:  góc 160°– 180°   → đếm cạnh gần ngang  ─

        → mỗi pixel rơi vào đúng 1 bin → bin đó += magnitude
- code với 1 cell 8x8:

        hist = [0] * 9   # 9 bin

        for i in range(8):
            for j in range(8):
                angle = orientation[i][j] # ví dụ 164°
                mag   = magnitude[i][j]   # ví dụ 72.8

                bin_idx = int(angle / 20) # 164/20 = 8
                bin_idx = min(bin_idx, 8) # clamp

                hist[bin_idx] += mag      # += 72.8, không phải += 1

## **Chuẩn hóa các block**

### ***Block***

- Là nhóm các cell gộp lại với nhau
- Nhóm để giúp loại bỏ ảnh hưởng của ánh sáng
- Ví dụ:

        Ảnh chụp buổi sáng:  magnitude = 80
        Ảnh chụp buổi tối:   magnitude = 20
        → histogram khác nhau dù hình dạng giống nhau ❌

### ***Phương pháp chuẩn hóa***

- Gộp histogram của 4 cell trong block thành 1 vector, rồi chia cho độ dài:

        block_vector = [hist_cell1, hist_cell2, hist_cell3, hist_cell4]
                    = 4 × 9 = 36 số
        ||v|| = sqrt(v1² + v2² + ... + v36²)
        block_norm = block_vector / ||v||

- Block trượt qua ảnh (sliding window):

        Block 1: cell(0,0) cell(0,1)    Block 2: cell(0,1) cell(0,2)
            cell(1,0) cell(1,1)             cell(1,1) cell(1,2)
            ↓                               ↓
            trượt sang phải 1 cell
        → Các cell được dùng lại nhiều lần ở các block khác nhau.

## Thu thập feature vector cuối cùng

- Block 2×2, trượt 1 cell:

      27×27 = 729 block
      mỗi block: 36 số

      vector HOG = flatten(tất cả block_norm)
                 = 729 × 36
                 = 26244 chiều
