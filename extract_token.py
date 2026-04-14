import os, sys, time
from pathlib import Path

# Thêm đường dẫn để chạy trực tiếp từ thư mục MTC_Download
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mtc.adb import AdbController

def extract_token_from_prefs(adb: AdbController) -> str:
    print("Vui lòng đảm bảo BlueStacks đang chạy và đã đăng nhập vào MTC App.")
    
    if not adb.ensure_device():
        print("Lỗi: Không thể kết nối với BlueStacks ADB.")
        return ""

    cmds = [
        "cat /data/data/com.novelfever.app.android/shared_prefs/FlutterSharedPreferences.xml",
        "cat /data/data/com.example.novelfeverx/shared_prefs/FlutterSharedPreferences.xml"
    ]
    
    xml_content = ""
    for cmd in cmds:
        out = adb.sh("su", "-c", f"'{cmd}'")
        if out and 'flutter.token' in out:
            xml_content = out
            break
            
    if not xml_content:
        print("Lỗi: Không tìm thấy file SharedPreferences hoặc chưa đăng nhập (không có token).")
        return ""
        
    # Trích xuất token
    import re
    match = re.search(r'<string name="flutter\.token">([^<]+)</string>', xml_content)
    if not match:
        match = re.search(r'<string name="flutter\.user_token">([^<]+)</string>', xml_content)
        
    if match:
        token = match.group(1)
        return token
        
    print("Lỗi: Tìm thấy file nhưng không thấy trường token.")
    return ""

def main():
    adb_path = AdbController.find_adb()
    if not adb_path:
        print("Lỗi: Không tìm thấy file ADB.exe. Bạn đã cài BlueStacks 5 chưa?")
        return
        
    adb = AdbController(adb_path, "127.0.0.1:5555")
    token = extract_token_from_prefs(adb)
    
    if token:
        token_file = Path("token.txt")
        token_file.write_text(token, encoding="utf-8")
        print(f"\nThành công! Đã trích xuất Token API và lưu vào: {token_file.absolute()}")
        print("Từ giờ bạn có thể dùng API trực tiếp mà không bị lỗi thiếu chữ VIP!")
        print("Thử chạy: python download_12.py")
    else:
        print("\nThất bại. Bạn vui lòng bật giả lập BlueStacks, mở ứng dụng MTC, đăng nhập vào tài khoản có VIP, rồi chạy lại script này.")

if __name__ == "__main__":
    main()
