# Caro AI - Hướng dẫn chạy chương trình

README này tập trung vào cách cài đặt, chạy game, chạy kiểm thử và chạy thực nghiệm cho project Caro AI. Chương trình cài đặt trò chơi Caro giữa người chơi và máy tính, trong đó AI có thể chọn nước đi bằng Minimax hoặc Alpha-Beta pruning. Bàn cờ dùng luật thắng 4 quân liên tiếp theo hàng ngang, hàng dọc hoặc đường chéo, không xét luật chặn hai đầu.

\---

## 1\. Cấu trúc thư mục cần có

Khi nộp hoặc chạy project, nên giữ cấu trúc thư mục như sau:

```text
23021337\_23021307\_CaroAI/
│
├── source\\\\\\\_code/
│   ├── carogame.py
│   └── benchmark\\\\\\\_caro.py
│
├── tests/
│   └── test\\\\\\\_engine.py
│
├── results/
│   └── benchmark\\\\\\\_results.csv
│
├── requirements.txt
├── run\\\\\\\_tests\\\\\\\_manual.py
└── README.md
```

Ý nghĩa các file chính:

* `source\\\\\\\_code/carogame.py`: file chính để chạy game Caro có giao diện.
* `source\\\\\\\_code/benchmark\\\\\\\_caro.py`: file chạy thực nghiệm so sánh Minimax và Alpha-Beta.
* `tests/test\\\\\\\_engine.py`: bộ kiểm thử tự động bằng pytest.
* `run\\\\\\\_tests\\\\\\\_manual.py`: kiểm thử thủ công bằng lệnh Python thông thường.
* `requirements.txt`: danh sách thư viện cần cài.
* `results/benchmark\\\\\\\_results.csv`: file lưu kết quả thực nghiệm.

\---

## 2\. Yêu cầu môi trường

Máy cần cài Python 3.10 trở lên. Có thể kiểm tra bằng lệnh:

```bash
python --version
```

Hoặc trên một số máy:

```bash
python3 --version
```

Project dùng `tkinter` để hiển thị giao diện. Trên Windows, `tkinter` thường đã đi kèm Python. Nếu chạy trên Linux mà bị lỗi thiếu `tkinter`, cần cài thêm gói tương ứng của hệ điều hành.

\---

## 3\. Cài đặt thư viện

Mở terminal hoặc Command Prompt tại thư mục gốc của project, tức là thư mục có file `requirements.txt`.

Cài thư viện bằng lệnh:

```bash
pip install -r requirements.txt
```

Nếu máy dùng `python3`, có thể dùng:

```bash
python3 -m pip install -r requirements.txt
```

Trong project này, thư viện quan trọng nhất là `pytest`, dùng để chạy kiểm thử tự động.

\---

## 4\. Chạy chương trình game Caro

Từ thư mục gốc của project, chạy lệnh:

```bash
python source\\\\\\\_code/carogame.py
```

Nếu máy dùng `python3`, chạy:

```bash
python3 source\\\\\\\_code/carogame.py
```

Sau khi chạy, cửa sổ game sẽ hiện ra. Người chơi đánh quân `X`, AI đánh quân `O`.

Trên giao diện, người dùng có thể chọn các thông số sau:

1. **Ai đi trước**  
Chọn người chơi đi trước hoặc AI đi trước.
2. **Thuật toán AI**  
Chọn một trong hai chế độ:

   * `Minimax`
   * `Alpha-Beta`
3. **Độ sâu tìm kiếm**  
Chọn trực tiếp độ sâu tìm kiếm, ví dụ:

   * `1`: AI chạy nhanh, nhưng nhìn trước ít nước.
   * `2`: AI cân bằng hơn giữa tốc độ và chất lượng.
   * `3`: AI xét sâu hơn, nước đi thường tốt hơn nhưng tốn thời gian hơn.
   * `4`: AI xét nhiều trạng thái hơn, có thể chậm hơn tùy thế cờ.
4. **Giới hạn thời gian**  
Dùng để giới hạn thời gian AI suy nghĩ cho mỗi lượt. Nếu bàn cờ có nhiều nước đi hợp lệ và độ sâu lớn, AI có thể cần nhiều thời gian hơn.

Khi AI chọn nước đi, chương trình sẽ ghi log gồm:

* Nước đi AI đã chọn.
* Thuật toán đang sử dụng.
* Độ sâu tìm kiếm.
* Điểm đánh giá của nước đi.
* Số trạng thái đã xét.
* Thời gian chạy.

Các thông tin này dùng để chứng minh chương trình có đo đạc đúng yêu cầu thực nghiệm.

\---

## 5\. Cách chơi trong giao diện

Cách thao tác khi chạy game:

1. Chọn người đi trước.
2. Chọn thuật toán AI.
3. Chọn độ sâu tìm kiếm.
4. Bấm `New Game` nếu muốn bắt đầu lại với cấu hình mới.
5. Người chơi click chuột vào một ô trống trên bàn cờ để đánh quân `X`.
6. AI sẽ tự tính toán và đánh quân `O`.
7. Trò chơi kết thúc khi một bên có 4 quân liên tiếp hoặc bàn cờ đầy.

Lưu ý:

* Không thể đánh vào ô đã có quân.
* Nếu AI đang suy nghĩ, người chơi cần chờ AI đánh xong.
* Nếu chọn độ sâu lớn, thời gian phản hồi có thể tăng lên.

\---

## 6\. Chạy kiểm thử tự động

Để kiểm tra các hàm quan trọng như kiểm tra thắng/thua và khả năng AI chặn nước thắng ngay của người chơi, chạy:

```bash
python -m pytest tests/test\\\\\\\_engine.py
```

Nếu chạy thành công, terminal sẽ hiện kết quả dạng:

```text
passed
```

Điều này cho biết các test trong `tests/test\\\\\\\_engine.py` đã chạy qua.

\---

## 7\. Chạy kiểm thử thủ công

Ngoài pytest, project có thêm file kiểm thử thủ công. Chạy bằng lệnh:

```bash
python run\\\\\\\_tests\\\\\\\_manual.py
```

Nếu chương trình đúng, kết quả sẽ báo các test đã pass, ví dụ:

```text
TEST 1 PASS: winner detected for HUMAN
TEST 1 PASS: AI not winning
TEST 2 PASS: AI blocked the remaining winning flank
All manual tests passed
```

File này hữu ích khi muốn kiểm tra nhanh mà không cần đọc chi tiết pytest.

\---

## 8\. Chạy thực nghiệm Level 3

Để chạy thực nghiệm so sánh Minimax và Alpha-Beta, dùng lệnh:

```bash
python source\\\\\\\_code/benchmark\\\\\\\_caro.py
```

Script benchmark sẽ chạy hai thuật toán trên cùng các trạng thái bàn cờ. Các độ sâu được dùng trong thực nghiệm là:

```text
depth = 1
depth = 2
depth = 3
```

Mỗi trạng thái bàn cờ sẽ được chạy bằng cả hai thuật toán:

```text
Minimax
Alpha-Beta
```

Như vậy, chương trình đảm bảo khi so sánh thì hai thuật toán dùng cùng trạng thái, cùng độ sâu và cùng hàm đánh giá.

Sau khi chạy xong, kết quả được lưu vào:

```text
results/benchmark\\\\\\\_results.csv
```

File CSV này có thể mở bằng Excel. Các cột kết quả thường gồm:

* Tên trạng thái kiểm thử.
* Độ sâu tìm kiếm.
* Thuật toán.
* Nước đi được chọn.
* Điểm đánh giá.
* Số trạng thái đã xét.
* Thời gian chạy.
* Tỉ lệ giảm số trạng thái của Alpha-Beta so với Minimax.

Đây là file dùng để đưa vào báo cáo phần Level 3.

\---

## 9\. Một số lỗi thường gặp

### Lỗi không tìm thấy file `carogame.py`

Cần chắc chắn đang đứng tại thư mục gốc của project rồi chạy:

```bash
python source\\\\\\\_code/carogame.py
```

Không nên chạy từ bên trong thư mục khác nếu chưa điều chỉnh đường dẫn.

### Lỗi thiếu pytest

Cài lại thư viện:

```bash
pip install -r requirements.txt
```

Hoặc:

```bash
pip install pytest
```

### Lỗi giao diện không hiện

Kiểm tra lại Python có hỗ trợ `tkinter` không:

```bash
python -m tkinter
```

Nếu cửa sổ nhỏ hiện ra thì `tkinter` hoạt động bình thường.

### Chạy AI bị chậm

Có thể giảm độ sâu tìm kiếm xuống `1` hoặc `2`, hoặc tăng độ khó nếu muốn AI suy nghĩ lâu hơn.

\---

## 10\. Ghi chú khi nộp bài

Khi đưa project lên GitHub, đặt tên repository theo mẫu:

```text
mssv1\\\\\\\_mssv2\\\\\\\_mssv3\\\\\\\_CaroAI
```

Trong repository cần có:

```text
source\\\\\\\_code/
requirements.txt
README.md
```

README nên giữ trọng tâm vào cách chạy chương trình, cách chạy test và cách chạy benchmark để giảng viên có thể kiểm tra nhanh.

