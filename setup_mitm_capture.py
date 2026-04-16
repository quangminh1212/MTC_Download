#!/usr/bin/env python3
"""
Setup mitmproxy to capture encryption key from MTC app.
This script helps automate the mitmproxy setup process.
"""
import subprocess
import sys
from pathlib import Path

def check_mitmproxy():
    """Check if mitmproxy is installed."""
    try:
        result = subprocess.run(['mitmproxy', '--version'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("[OK] mitmproxy is installed")
            print(f"  Version: {result.stdout.strip()}")
            return True
    except:
        pass

    print("[X] mitmproxy is not installed")
    return False

def install_mitmproxy():
    """Install mitmproxy."""
    print("\nInstalling mitmproxy...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'mitmproxy'],
                      check=True)
        print("[OK] mitmproxy installed successfully")
        return True
    except Exception as e:
        print(f"[X] Failed to install mitmproxy: {e}")
        return False

def create_mitm_script():
    """Create mitmproxy addon script to capture encryption key."""
    script_content = '''"""
mitmproxy addon to capture MTC encryption key.
Usage: mitmproxy -s capture_key.py
"""
import json
import re

class KeyCapture:
    def __init__(self):
        self.keys_found = []

    def response(self, flow):
        """Intercept responses to find encryption key."""
        # Check headers for encryption key
        for header, value in flow.response.headers.items():
            if 'key' in header.lower() or 'encrypt' in header.lower():
                print(f"[KEY] Found in header {header}: {value}")
                self.keys_found.append(('header', header, value))

        # Check response body
        try:
            if flow.response.content:
                content = flow.response.content.decode('utf-8', errors='ignore')

                # Look for base64 keys
                base64_pattern = r'base64:([A-Za-z0-9+/=]{40,})'
                matches = re.findall(base64_pattern, content)
                for match in matches:
                    print(f"[KEY] Found base64 key in response: base64:{match[:50]}...")
                    self.keys_found.append(('body', 'base64', f"base64:{match}"))

                # Look for JSON with key field
                try:
                    data = json.loads(content)
                    if isinstance(data, dict):
                        for key in ['key', 'encryption_key', 'app_key', 'secret']:
                            if key in data:
                                print(f"[KEY] Found in JSON field '{key}': {data[key][:50]}...")
                                self.keys_found.append(('json', key, data[key]))
                except:
                    pass
        except:
            pass

    def done(self):
        """Save found keys."""
        if self.keys_found:
            print(f"\\n[SUMMARY] Found {len(self.keys_found)} potential keys")
            with open('captured_keys.txt', 'w', encoding='utf-8') as f:
                f.write("Captured Encryption Keys\\n")
                f.write("=" * 60 + "\\n\\n")
                for source, field, value in self.keys_found:
                    f.write(f"Source: {source}\\n")
                    f.write(f"Field: {field}\\n")
                    f.write(f"Value: {value}\\n")
                    f.write("-" * 60 + "\\n")
            print("[SAVED] Keys saved to captured_keys.txt")
        else:
            print("\\n[INFO] No encryption keys found in traffic")

addons = [KeyCapture()]
'''

    script_path = Path('capture_key.py')
    script_path.write_text(script_content, encoding='utf-8')
    print(f"[OK] Created mitmproxy script: {script_path}")
    return script_path

def print_instructions():
    """Print setup instructions."""
    print("\n" + "=" * 60)
    print("MITMPROXY SETUP INSTRUCTIONS")
    print("=" * 60)
    print("""
1. Start mitmproxy with the capture script:
   mitmweb -s capture_key.py --listen-port 8080

2. Configure BlueStacks proxy:
   - Open BlueStacks Settings
   - Go to Network → Proxy
   - Set Manual Proxy:
     * Host: 127.0.0.1
     * Port: 8080
   - Save and restart BlueStacks

3. Install mitmproxy certificate:
   - Open browser in BlueStacks
   - Go to: http://mitm.it
   - Download and install Android certificate
   - Trust the certificate in Settings → Security

4. Run MTC app and read a chapter:
   - Open MTC app
   - Login if needed
   - Open any novel and read a chapter
   - Watch mitmproxy web interface at http://127.0.0.1:8081

5. Check for captured keys:
   - Look for requests to /chapters/ endpoint
   - Check captured_keys.txt file
   - Look for X-Encryption-Key header or similar

6. Test the captured key:
   python test_decrypt_with_key.py "base64:YOUR_KEY_HERE"

7. If key works, save it:
   echo "base64:YOUR_KEY_HERE" > WORKING_KEY.txt

8. Download novels with decryption:
   python download_and_decrypt.py "Tên Truyện"
""")
    print("=" * 60)

def main():
    print("MTC Encryption Key Capture Setup")
    print("=" * 60)

    # Check if mitmproxy is installed
    if not check_mitmproxy():
        print("\nDo you want to install mitmproxy? (y/n): ", end='')
        response = input().strip().lower()
        if response == 'y':
            if not install_mitmproxy():
                print("\nPlease install manually: pip install mitmproxy")
                return
        else:
            print("\nPlease install mitmproxy first: pip install mitmproxy")
            return

    # Create capture script
    create_mitm_script()

    # Print instructions
    print_instructions()

    print("\nReady to capture! Run: mitmweb -s capture_key.py --listen-port 8080")

if __name__ == "__main__":
    main()
