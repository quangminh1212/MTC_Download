#!/usr/bin/env python3
"""
Tự động phân tích mitmproxy traffic để tìm APP_KEY.
Chạy script này trong khi mitmproxy đang chạy.
"""
import time
import requests
import json
from pathlib import Path

MITMPROXY_API = "http://127.0.0.1:8081/flows"
CHECK_INTERVAL = 2  # seconds

def check_for_key():
    """Kiểm tra traffic từ mitmproxy API."""
    try:
        resp = requests.get(MITMPROXY_API, timeout=5)
        flows = resp.json()
        
        for flow in flows:
            if 'request' not in flow:
                continue
            
            req = flow['request']
            host = req.get('host', '')
            
            # Chỉ xem API requests
            if 'lonoapp.net' not in host:
                continue
            
            url = req.get('url', '')
            method = req.get('method', '')
            
            print(f"\n{'='*60}")
            print(f"🔍 Found API request:")
            print(f"   URL: {url}")
            print(f"   Method: {method}")
            
            # Check request headers
            headers = req.get('headers', {})
            for header, value in headers.items():
                if any(kw in header.lower() for kw in ['key', 'auth', 'token', 'secret']):
                    print(f"   📝 Header: {header} = {value}")
                    
                    if 'key' in header.lower():
                        print(f"\n✅ POTENTIAL APP_KEY FOUND!")
                        print(f"   Header: {header}")
                        print(f"   Value: {value}")
                        
                        # Save to file
                        with open('APP_KEY.txt', 'w') as f:
                            f.write(f"Header: {header}\n")
                            f.write(f"Value: {value}\n")
                        
                        print(f"\n✅ Saved to APP_KEY.txt")
                        return True
            
            # Check response
            if 'response' in flow:
                resp_data = flow['response']
                
                # Check response headers
                resp_headers = resp_data.get('headers', {})
                for header, value in resp_headers.items():
                    if any(kw in header.lower() for kw in ['key', 'encrypt', 'secret']):
                        print(f"   📝 Response Header: {header} = {value}")
                        
                        if 'key' in header.lower():
                            print(f"\n✅ POTENTIAL APP_KEY FOUND IN RESPONSE!")
                            print(f"   Header: {header}")
                            print(f"   Value: {value}")
                            
                            with open('APP_KEY.txt', 'w') as f:
                                f.write(f"Response Header: {header}\n")
                                f.write(f"Value: {value}\n")
                            
                            print(f"\n✅ Saved to APP_KEY.txt")
                            return True
                
                # Check if content is decrypted
                content = resp_data.get('content', '')
                if content and not content.startswith('eyJ'):
                    # Not encrypted!
                    print(f"\n✅ FOUND DECRYPTED CONTENT!")
                    print(f"   Content length: {len(content)}")
                    print(f"   First 200 chars: {content[:200]}")
                    
                    with open('decrypted_sample.txt', 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    print(f"\n✅ Saved to decrypted_sample.txt")
                    print(f"\n💡 App decrypts content before displaying!")
                    print(f"   You can download directly from API without decryption.")
                    return True
        
        return False
        
    except requests.exceptions.ConnectionError:
        print("⚠️  mitmproxy not running. Start it with: start_mitmproxy.bat")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("="*60)
    print("Auto APP_KEY Finder")
    print("="*60)
    print("\nMonitoring mitmproxy traffic...")
    print("Waiting for API requests to api.lonoapp.net...")
    print("\nInstructions:")
    print("1. Make sure mitmproxy is running (start_mitmproxy.bat)")
    print("2. Open NovelFever app in BlueStacks")
    print("3. Read any chapter")
    print("4. This script will automatically detect APP_KEY")
    print("\nPress Ctrl+C to stop")
    print("="*60)
    
    found = False
    while not found:
        result = check_for_key()
        
        if result is None:
            # mitmproxy not running
            time.sleep(5)
            continue
        
        if result:
            found = True
            print("\n"+"="*60)
            print("✅ SUCCESS! APP_KEY found!")
            print("="*60)
            print("\nNext steps:")
            print("1. Check APP_KEY.txt for the key")
            print("2. Test with: python test_decrypt_with_key.py <key>")
            print("3. If it works, update mtc/api.py with the key")
            break
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nStopped by user")
