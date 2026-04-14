#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tự động cài certificate và chạy mitmproxy."""
import subprocess
import time
import os
import sys
import socket

def get_local_ip():
    """Lấy IP máy tính."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def run_adb(*args):
    """Chạy lệnh ADB."""
    adb = r"C:\Program Files\BlueStacks_nxt\HD-Adb.exe"
    device = "emulator-5554"  # BlueStacks device
    
    try:
        result = subprocess.run(
            [adb, "-s", device] + list(args),
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout
    except Exception as e:
        return False, str(e)

def main():
    print("="*60)
    print("TỰ ĐỘNG CÀI CERTIFICATE VÀ CHẠY MITMPROXY")
    print("="*60)
    print()
    
    # Lấy IP
    ip = get_local_ip()
    print(f"✓ IP máy tính: {ip}")
    print()
    
    # Bước 1: Set proxy
    print("[1/6] Cấu hình proxy...")
    success, output = run_adb("shell", "settings", "put", "global", "http_proxy", f"{ip}:8080")
    if success:
        print(f"✓ Đã set proxy: {ip}:8080")
    else:
        print(f"⚠️  Lỗi set proxy: {output}")
    print()
    
    # Bước 2: Tải certificate
    print("[2/6] Tải certificate từ mitmproxy...")
    cert_path = os.path.expanduser("~/.mitmproxy/mitmproxy-ca-cert.cer")
    
    if os.path.exists(cert_path):
        print(f"✓ Tìm thấy certificate: {cert_path}")
        # Copy ra thư mục hiện tại
        import shutil
        shutil.copy(cert_path, "mitmproxy-ca-cert.cer")
        print("✓ Đã copy certificate")
    else:
        print("⚠️  Certificate chưa có, sẽ tạo khi chạy mitmproxy lần đầu")
    print()
    
    # Bước 3: Push certificate
    print("[3/6] Push certificate vào BlueStacks...")
    if os.path.exists("mitmproxy-ca-cert.cer"):
        success, output = run_adb("push", "mitmproxy-ca-cert.cer", "/sdcard/Download/mitmproxy-ca-cert.cer")
        if success:
            print("✓ Đã push certificate vào /sdcard/Download/")
        else:
            print(f"⚠️  Lỗi push: {output}")
    else:
        print("⚠️  Không có certificate để push")
    print()
    
    # Bước 4: Cài certificate tự động
    print("[4/6] Cài certificate...")
    print("ℹ️  Đang thử cài tự động...")
    
    # Thử cài qua intent
    success, output = run_adb("shell", "am", "start", "-a", "android.credentials.INSTALL")
    if success:
        print("✓ Đã mở màn hình cài certificate")
        print()
        print("⚠️  QUAN TRỌNG: Trong BlueStacks, làm theo:")
        print("   1. Chọn 'Install from storage'")
        print("   2. Tìm: Download/mitmproxy-ca-cert.cer")
        print("   3. Đặt tên: mitmproxy")
        print("   4. Chọn: VPN and apps")
        print()
        print("Đợi 10 giây để bạn cài...")
        time.sleep(10)
    else:
        print("⚠️  Không mở được màn hình cài certificate")
    print()
    
    # Bước 5: Mở app
    print("[5/6] Mở app NovelFever...")
    success, output = run_adb("shell", "monkey", "-p", "com.novelfever.app.android", "1")
    if success:
        print("✓ Đã mở app")
    else:
        print("⚠️  Không mở được app")
    print()
    
    # Restart app để áp dụng proxy
    print("Restart app để áp dụng proxy...")
    run_adb("shell", "am", "force-stop", "com.novelfever.app.android")
    time.sleep(2)
    run_adb("shell", "monkey", "-p", "com.novelfever.app.android", "1")
    print("✓ Đã restart app")
    print()
    
    # Bước 6: Khởi động mitmproxy
    print("[6/6] Khởi động mitmproxy...")
    print("✓ Đang khởi động mitmproxy...")
    
    # Tìm mitmweb
    mitmweb_paths = [
        r"C:\Users\GHC\AppData\Roaming\Python\Python314\Scripts\mitmweb.exe",
        r"C:\Python314\Scripts\mitmweb.exe",
        "mitmweb"
    ]
    
    mitmweb_cmd = None
    for path in mitmweb_paths:
        if os.path.exists(path) or path == "mitmweb":
            mitmweb_cmd = path
            break
    
    if not mitmweb_cmd:
        print("❌ Không tìm thấy mitmweb")
        print("   Chạy: pip install mitmproxy")
        return
    
    # Khởi động mitmproxy trong background
    try:
        subprocess.Popen(
            [mitmweb_cmd, "--listen-host", "0.0.0.0", "--listen-port", "8080", 
             "--web-host", "127.0.0.1", "--web-port", "8081"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
        )
    except Exception as e:
        print(f"❌ Lỗi khởi động mitmproxy: {e}")
        return
    
    print("⏳ Đợi mitmproxy khởi động...")
    time.sleep(5)
    
    # Mở web interface
    import webbrowser
    webbrowser.open("http://127.0.0.1:8081")
    print("✓ mitmproxy web: http://127.0.0.1:8081")
    print()
    
    # Hoàn tất
    print("="*60)
    print("HOÀN TẤT CÀI ĐẶT!")
    print("="*60)
    print()
    print("✅ Đã cấu hình:")
    print(f"   - Proxy: {ip}:8080")
    print("   - Certificate: Đã push vào BlueStacks")
    print("   - App: Đã mở")
    print("   - mitmproxy: Đang chạy")
    print()
    print("📋 BÂY GIỜ:")
    print("   1. Trong BlueStacks, đọc MỘT CHƯƠNG bất kỳ")
    print("   2. Chạy: python auto_find_key.py")
    print("   3. Hoặc xem traffic tại: http://127.0.0.1:8081")
    print()
    print("⏳ Bắt đầu tự động tìm APP_KEY...")
    print()
    
    # Chạy auto finder
    try:
        subprocess.run(["python", "auto_find_key.py"])
    except KeyboardInterrupt:
        print("\n\n⚠️  Đã dừng")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Đã dừng bởi người dùng")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
