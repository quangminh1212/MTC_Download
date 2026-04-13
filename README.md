# MTC_Download

Bộ script phục vụ tải truyện, phân tích APK và kiểm tra luồng giải mã cho ứng dụng MTC/NovelFever.

## Ghi chú về `frida-server`

File `frida-server` không được lưu trong Git vì vượt quá giới hạn kích thước 100 MB của GitHub.

Khi cần dùng lại, hãy tải đúng bản khớp với phiên bản `frida` trong môi trường hiện tại:

```powershell
.\.venv\Scripts\python.exe get_frida.py
```

Script trên sẽ tải và giải nén ra file `frida-server` tại thư mục gốc của project. Sau đó có thể push file này vào thiết bị giả lập, ví dụ với BlueStacks:

```powershell
& "C:\Program Files\BlueStacks_nxt\HD-Adb.exe" -s 127.0.0.1:5555 push ".\frida-server" /data/local/tmp/frida-server
```

`frida-server` đã được thêm vào `.gitignore`, nên file này sẽ luôn là local-only và không được commit lên remote.