# 🌐 MeTruyenCV Web Interface

Giao diện web hiện đại cho MeTruyenCV Downloader với real-time progress tracking và quản lý cấu hình trực quan.

## 🚀 Cách sử dụng

### **Khởi động Web Interface:**
```bash
run_web.bat
```

Hoặc chạy thủ công:
```bash
pip install -r requirements_web.txt
python app.py
```

### **Truy cập:**
- 🏠 **Dashboard**: http://localhost:5000
- ⚙️ **Cấu hình**: http://localhost:5000/config
- 📥 **Download**: http://localhost:5000/download
- 📋 **Logs**: http://localhost:5000/logs

## ✨ Tính năng

### 📊 Dashboard
- Hiển thị trạng thái download real-time
- Thống kê tiến độ và tốc độ
- Logs gần đây
- Tóm tắt cấu hình hiện tại

### 📥 Download Manager
- Form nhập URL và chapter range thân thiện
- Validation URL tự động
- Progress bar real-time với WebSocket
- Live logs streaming
- Tính toán tốc độ và thời gian còn lại
- Nút dừng download an toàn

### ⚙️ Configuration Manager
- Giao diện cấu hình trực quan
- Validation form tự động
- Lưu/tải cấu hình
- Test kết nối
- Khôi phục cài đặt mặc định

### 📋 Log Viewer
- Real-time log streaming
- Lọc theo level (info, warning, error, debug)
- Tìm kiếm logs
- Export logs
- Fullscreen mode
- Auto-scroll toggle

## 🎨 Giao diện

### Responsive Design
- ✅ Desktop friendly
- ✅ Mobile responsive
- ✅ Tablet optimized

### Modern UI/UX
- 🎨 Bootstrap 5 + Custom CSS
- 🌈 Gradient backgrounds
- ⚡ Smooth animations
- 🔔 Toast notifications
- 📱 Progressive Web App ready

### Real-time Features
- 🔄 WebSocket connections
- 📊 Live progress updates
- 📝 Streaming logs
- 🔔 Desktop notifications
- 📡 Connection status indicator

## 🛠️ Cấu trúc Files

```
MTC_Download/
├── app.py                    # Flask main application
├── web_downloader.py         # Web wrapper cho existing code
├── requirements_web.txt      # Web dependencies
├── run_web.bat              # Web server launcher
├── templates/               # HTML templates
│   ├── base.html           # Base template với sidebar
│   ├── index.html          # Dashboard
│   ├── config.html         # Configuration page
│   ├── download.html       # Download manager
│   └── logs.html           # Log viewer
└── static/                 # Static assets
    ├── css/
    │   └── custom.css      # Custom styles
    └── js/
        └── utils.js        # JavaScript utilities
```

## 🔧 API Endpoints

### REST API
- `GET /api/config` - Lấy cấu hình hiện tại
- `POST /api/config` - Lưu cấu hình mới
- `POST /api/start_download` - Bắt đầu download
- `POST /api/stop_download` - Dừng download
- `GET /api/status` - Lấy trạng thái hiện tại

### WebSocket Events
- `connect` - Client kết nối
- `disconnect` - Client ngắt kết nối
- `status_update` - Cập nhật trạng thái
- `progress_update` - Cập nhật tiến độ
- `new_log` - Log mới
- `download_started` - Bắt đầu download
- `download_completed` - Hoàn thành download
- `download_error` - Lỗi download
- `download_stopped` - Dừng download

## 🎯 Tính năng nâng cao

### Progress Tracking
- Real-time chapter progress
- Download speed calculation
- ETA estimation
- Success/failure statistics

### Log Management
- Level-based filtering
- Search functionality
- Export to JSON
- Auto-cleanup (max 1000 entries)
- Fullscreen viewer

### Configuration
- Form validation
- Default value restoration
- Connection testing
- Auto-save options

### Notifications
- Desktop notifications
- Toast messages
- Connection status
- Download completion alerts

## 🔒 Bảo mật

- ✅ Input sanitization
- ✅ CSRF protection
- ✅ Safe file operations
- ✅ Error handling
- ✅ Resource limits

## 📱 Mobile Support

- ✅ Responsive sidebar
- ✅ Touch-friendly buttons
- ✅ Mobile-optimized forms
- ✅ Swipe gestures
- ✅ Viewport optimization

## 🚀 Performance

- ⚡ Async operations
- 🔄 WebSocket efficiency
- 📦 Resource optimization
- 🗜️ Gzip compression
- 🎯 Lazy loading

## 🐛 Troubleshooting

### Port đã được sử dụng
```bash
# Thay đổi port trong app.py
socketio.run(app, host='0.0.0.0', port=5001, debug=True)
```

### Dependencies lỗi
```bash
pip install --upgrade pip
pip install -r requirements_web.txt --force-reinstall
```

### WebSocket không hoạt động
- Kiểm tra firewall
- Thử browser khác
- Disable ad blockers

### Lỗi kết nối database
- Kiểm tra config.txt
- Restart web server
- Clear browser cache

## 📝 Development

### Thêm tính năng mới
1. Tạo route trong `app.py`
2. Thêm template trong `templates/`
3. Update navigation trong `base.html`
4. Thêm CSS/JS nếu cần

### Debugging
```bash
# Enable debug mode
export FLASK_DEBUG=1
python app.py
```

### Testing
```bash
# Test API endpoints
curl http://localhost:5000/api/status
curl -X POST http://localhost:5000/api/config -H "Content-Type: application/json" -d "{}"
```

## 🤝 Contributing

1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📄 License

MIT License - xem file LICENSE để biết thêm chi tiết.

---

**Phát triển bởi**: MeTruyenCV Team  
**Version**: 1.0.0  
**Last Updated**: 2024-07-08
