MeTruyenCV Downloader - Web Interface
=====================================

🚀 HƯỚNG DẪN SỬ DỤNG:

1. Cài đặt Python 3.7+ trên máy tính
2. Chạy file run.bat
3. Trình duyệt sẽ tự động mở tại http://localhost:3000
4. Nhập thông tin truyện vào form:
   - URL truyện từ metruyencv.com
   - Chương bắt đầu (mặc định 1)
   - Chương kết thúc (để trống = tải hết)
   - HOẶC sử dụng tính năng "Tìm kiếm truyện trực tiếp"
5. Nhấn "Bắt đầu tải truyện"
6. Theo dõi tiến trình tải trên trang web

📁 CẤU TRÚC DỰ ÁN:
- web_server.py: Web server chính
- downloader.py: Logic tải truyện với Selenium
- config.json: Cấu hình truyện và trình duyệt
- run.bat: File khởi động
- test.py: Test trình duyệt
- templates/: Giao diện HTML

🔍 TÍNH NĂNG TÌM KIẾM TRUYỆN:
- Tìm kiếm trực tiếp trên localhost
- Không cần biết URL chính xác
- Hiển thị kết quả với mô tả và thông tin
- Tải truyện ngay từ kết quả tìm kiếm
- Tự động chọn trình duyệt phù hợp

✨ TÍNH NĂNG KHÁC:
- Giao diện web đơn giản, dễ sử dụng
- Tìm kiếm truyện trực tiếp trên localhost
- Theo dõi tiến trình tải real-time
- Tự động tạo thư mục theo tên truyện
- Mỗi chương được lưu thành file .txt riêng
- Sử dụng Selenium để xử lý JavaScript động
- Tự động chọn trình duyệt phù hợp

📝 CẤU HÌNH CONFIG.JSON:
{
    "story_url": "https://metruyencv.com/truyen/ten-truyen",
    "start_chapter": 1,
    "end_chapter": 3,
    "browser": "auto"
}

🆕 CÁCH SỬ DỤNG MỚI:
1. Chạy run.bat
2. Mở http://localhost:3000
3. Chọn "Tìm kiếm truyện trực tiếp"
4. Nhập tên truyện cần tìm
5. Chọn truyện từ kết quả và nhấn "Tải truyện này"

🧪 TEST TRÌNH DUYỆT:
Chạy: python test.py

⚠️ LƯU Ý:
- Trình duyệt sẽ hiển thị khi tải (không headless)
- Nội dung có thể vẫn bị mã hóa (đang nghiên cứu giải pháp)
- Nhấn Ctrl+C trong terminal để dừng web server

📖 VÍ DỤ URL:
https://metruyencv.com/truyen/tan-the-chi-sieu-thi-he-thong
