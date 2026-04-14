#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tự động phân tích mitmproxy traffic để tìm APP_KEY.
Chạy script này trong khi mitmproxy đang chạy.
"""
import time
import requests
import json
import base64
from pathlib import Path

MITMPROXY_API = "http://127.0.0.1:8081/flows"
CHECK_INTERVAL = 2  # seconds
CHECKED_FLOWS = set()  # Track đã check

def check_for_key():
    """Kiểm tra traffic từ mitmproxy API."""
    try:
        resp = requests.get(MITMPROXY_API, timeout=5)
        flows = resp.json()
        
        for flow in flows:
            if 'request' not in flow:
                continue
            
            # Skip nếu đã check flow này
            flow_id = flow.get('id', '')
            if flow_id in CHECKED_FLOWS:
                continue
            CHECKED_FLOWS.add(flow_id)
            
            req = flow['request']
            host = req.get('host', '')
            
            # Chỉ xem API requests
            if 'lonoapp.net' not in host and 'api' not in host.lower():
                continue
            
            url = req.get('url', '')
            method = req.get('method', '')
            
            print(f"\n{'='*60}")
            print(f"🔍 Phát hiện API request:")
            print(f"   URL: {url}")
            print(f"   Method: {method}")
            
            # Check request headers
            headers = req.get('headers', [])
            found_interesting = False
            for header_pair in headers:
                if isinstance(header_pair, list) and len(header_pair) >= 2:
                    header = header_pair[0]
                    value = header_pair[1]
                    
                    if any(kw in header.lower() for kw in ['key', 'auth', 'token', 'secret', 'x-']):
                        print(f"   📝 Header: {header} = {value[:100]}...")
                        found_interesting = True
                        
                        if 'key' in header.lower():
                            print(f"\n✅ TÌM THẤY APP_KEY TIỀM NĂNG!")
                            print(f"   Header: {header}")
                            print(f"   Value: {value}")
                            
                            # Save to file
                            with open('APP_KEY.txt', 'w', encoding='utf-8') as f:
                                f.write(f"Header: {header}\n")
                                f.write(f"Value: {value}\n")
                                f.write(f"\nURL: {url}\n")
                                f.write(f"Method: {method}\n")
                            
                            print(f"\n✅ Đã lưu vào APP_KEY.txt")
                            return True
            
            # Check response
            if 'response' in flow:
                resp_data = flow['response']
                
                # Check response headers
                resp_headers = resp_data.get('headers', [])
                for header_pair in resp_headers:
                    if isinstance(header_pair, list) and len(header_pair) >= 2:
                        header = header_pair[0]
                        value = header_pair[1]
                        
                        if any(kw in header.lower() for kw in ['key', 'encrypt', 'secret', 'x-']):
                            print(f"   📝 Response Header: {header} = {value[:100]}...")
                            found_interesting = True
                            
                            if 'key' in header.lower():
                                print(f"\n✅ TÌM THẤY APP_KEY TRONG RESPONSE!")
                                print(f"   Header: {header}")
                                print(f"   Value: {value}")
                                
                                with open('APP_KEY.txt', 'w', encoding='utf-8') as f:
                                    f.write(f"Response Header: {header}\n")
                                    f.write(f"Value: {value}\n")
                                    f.write(f"\nURL: {url}\n")
                                    f.write(f"Method: {method}\n")
                                
                                print(f"\n✅ Đã lưu vào APP_KEY.txt")
                                return True
                
                # Check if content is decrypted
                content_raw = resp_data.get('content')
                if content_raw:
                    try:
                        # Decode base64 nếu cần
                        if isinstance(content_raw, str):
                            content = content_raw
                        else:
                            content = base64.b64decode(content_raw).decode('utf-8', errors='ignore')
                        
                        # Check nếu là plain text (không phải encrypted JSON)
                        if content and len(content) > 100:
                            # Kiểm tra xem có phải encrypted không
                            is_encrypted = False
                            try:
                                data = json.loads(content)
                                if isinstance(data, dict) and 'iv' in data and 'value' in data:
                                    is_encrypted = True
                                    print(f"   🔒 Nội dung bị mã hóa (Laravel encryption)")
                            except:
                                pass
                            
                            if not is_encrypted and any(c in content for c in ['Chương', 'chương', 'Chapter']):
                                print(f"\n✅ TÌM THẤY NỘI DUNG ĐÃ GIẢI MÃ!")
                                print(f"   Độ dài: {len(content)} ký tự")
                                print(f"   200 ký tự đầu: {content[:200]}")
                                
                                with open('decrypted_sample.txt', 'w', encoding='utf-8') as f:
                                    f.write(f"URL: {url}\n")
                                    f.write(f"Method: {method}\n")
                                    f.write(f"{'='*60}\n\n")
                                    f.write(content)
                                
                                print(f"\n✅ Đã lưu vào decrypted_sample.txt")
                                print(f"\n💡 App tự giải mã nội dung trước khi hiển thị!")
                                print(f"   Có thể tải trực tiếp từ API mà không cần giải mã.")
                                return True
                    except Exception as e:
                        pass
            
            if found_interesting:
                print(f"   ℹ️  Đã ghi nhận request này")
        
        return False
        
    except requests.exceptions.ConnectionError:
        print("⚠️  mitmproxy chưa chạy. Đang chờ khởi động...")
        return None
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return False

def main():
    print("="*60)
    print("TỰ ĐỘNG TÌM APP_KEY")
    print("="*60)
    print("\n🔍 Đang theo dõi mitmproxy traffic...")
    print("⏳ Chờ API requests đến api.lonoapp.net...")
    print("\n📋 Hướng dẫn:")
    print("1. Đảm bảo mitmproxy đang chạy")
    print("2. Mở app MTC trong BlueStacks")
    print("3. Đọc bất kỳ chương truyện nào")
    print("4. Script sẽ tự động phát hiện APP_KEY")
    print("\n⚠️  Nhấn Ctrl+C để dừng")
    print("="*60)
    
    found = False
    wait_count = 0
    while not found:
        result = check_for_key()
        
        if result is None:
            # mitmproxy chưa chạy
            wait_count += 1
            if wait_count % 3 == 0:
                print(f"⏳ Vẫn đang chờ mitmproxy khởi động... ({wait_count * 5}s)")
            time.sleep(5)
            continue
        
        if result:
            found = True
            print("\n"+"="*60)
            print("✅ THÀNH CÔNG! Đã tìm thấy APP_KEY!")
            print("="*60)
            print("\n📋 Bước tiếp theo:")
            print("1. Kiểm tra file APP_KEY.txt")
            print("2. Test với: python test_decrypt_with_key.py <key>")
            print("3. Nếu thành công, cập nhật mtc/api.py với key")
            break
        
        # Hiển thị dấu chấm để biết script đang chạy
        print(".", end="", flush=True)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Đã dừng bởi người dùng")
        print("\n💡 Tip: Nếu chưa tìm thấy key, hãy:")
        print("   1. Kiểm tra proxy settings trong BlueStacks")
        print("   2. Đảm bảo đã cài certificate từ mitm.it")
        print("   3. Thử đọc thêm vài chương trong app")
