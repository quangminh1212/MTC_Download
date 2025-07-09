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
   - Chọn trình duyệt (mặc định tự động)
5. Nhấn "Bắt đầu tải truyện"
6. Theo dõi tiến trình tải trên trang web

📁 CẤU TRÚC DỰ ÁN:
- web_server.py: Web server chính
- downloader.py: Logic tải truyện với Selenium
- templates/: Giao diện HTML
- run.bat: File khởi động
- config.json: Cấu hình truyện và trình duyệt

🌐 TÍNH NĂNG CHỌN TRÌNH DUYỆT:
- Auto: Tự động chọn (Edge → Firefox → Chrome → Brave)
- Edge: Microsoft Edge (mặc định Windows)
- Firefox: Mozilla Firefox
- Chrome: Google Chrome
- Brave: Brave Browser

✨ TÍNH NĂNG KHÁC:
- Giao diện web đơn giản, dễ sử dụng
- Theo dõi tiến trình tải real-time
- Tự động tạo thư mục theo tên truyện
- Mỗi chương được lưu thành file .txt riêng
- Sử dụng Selenium để xử lý JavaScript động

📝 CẤU HÌNH CONFIG.JSON:
{
    "story_url": "https://metruyencv.com/truyen/ten-truyen",
    "start_chapter": 1,
    "end_chapter": 3,
    "browser": "auto"
}

⚠️ LƯU Ý:
- Trình duyệt sẽ hiển thị khi tải (không headless)
- Nội dung có thể vẫn bị mã hóa (đang nghiên cứu giải pháp)
- Nhấn Ctrl+C trong terminal để dừng web server

📖 VÍ DỤ URL:
https://metruyencv.com/truyen/tan-the-chi-sieu-thi-he-thong
