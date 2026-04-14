#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kiểm tra trạng thái BlueStacks và app MTC."""
import subprocess
import sys
import os
from pathlib import Path

def find_adb():
    """Tìm BlueStacks ADB."""
    possible_paths = [
        r"C:\Program Files\BlueStacks_nxt\HD-Adb.exe",
        r"C:\Program Files\BlueStacks\HD-Adb.exe",
        r"C:\Program Files (x86)\BlueStacks_nxt\HD-Adb.exe",
        r"C:\Program Files (x86)\BlueStacks\HD-Adb.exe",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Thử system ADB
    try:
        subprocess.run(["adb", "version"], capture_output=True, check=True)
        return "adb"
    except:
        return None

def run_adb(adb_path, *args):
    """Chạy lệnh ADB."""
    try:
        result = subprocess.run(
            [adb_path] + list(args),
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

def main():
    print("="*60)
    print("KIỂM TRA TRẠNG THÁI BLUESTACKS")
    print("="*60)
    print()
    
    # Tìm ADB
    print("[1/5] Tìm ADB...")
    adb = find_adb()
    if not adb:
        print("❌ Không tìm thấy ADB")
        print("   Cài BlueStacks hoặc Android SDK")
        return
    print(f"✓ ADB: {adb}")
    print()
    
    # Kết nối
    print("[2/5] Kết nối với BlueStacks...")
    run_adb(adb, "kill-server")
    run_adb(adb, "start-server")
    
    connected = False
    for port in [5555, 5556, 5557]:
        result = run_adb(adb, "connect", f"127.0.0.1:{port}")
        if "connected" in result.lower():
            print(f"✓ Đã kết nối: 127.0.0.1:{port}")
            connected = True
            break
    
    if not connected:
        print("❌ Không kết nối được với BlueStacks")
        print("   Đảm bảo BlueStacks đang chạy")
        return
    print()
    
    # Kiểm tra proxy
    print("[3/5] Kiểm tra proxy...")
    proxy = run_adb(adb, "shell", "settings", "get", "global", "http_proxy")
    if proxy and proxy != "null" and "Error" not in proxy:
        print(f"✓ Proxy: {proxy}")
    else:
        print("⚠️  Proxy chưa được set")
    print()
    
    # Tìm app MTC
    print("[4/5] Tìm app MTC...")
    packages = run_adb(adb, "shell", "pm", "list", "packages")
    
    mtc_packages = []
    for line in packages.split('\n'):
        if any(kw in line.lower() for kw in ['mtc', 'novel', 'lono']):
            pkg = line.replace('package:', '').strip()
            mtc_packages.append(pkg)
    
    if mtc_packages:
        print(f"✓ Tìm thấy {len(mtc_packages)} app:")
        for pkg in mtc_packages:
            print(f"   - {pkg}")
    else:
        print("⚠️  Không tìm thấy app MTC")
        print("   Cài app MTC trong BlueStacks")
    print()
    
    # Kiểm tra certificate
    print("[5/5] Kiểm tra certificate...")
    certs = run_adb(adb, "shell", "ls", "/sdcard/Download/")
    if "mitmproxy" in certs.lower():
        print("✓ Certificate đã được push")
    else:
        print("⚠️  Certificate chưa được push")
    print()
    
    # Tổng kết
    print("="*60)
    print("TỔNG KẾT")
    print("="*60)
    
    if connected and mtc_packages:
        print("✅ BlueStacks sẵn sàng!")
        print()
        print("📋 Bước tiếp theo:")
        print("   1. Chạy: full_auto_setup.bat")
        print("   2. Hoặc: auto_config_bluestacks.bat")
        print()
        
        # Lưu package name
        if mtc_packages:
            with open('mtc_package_name.txt', 'w') as f:
                f.write(mtc_packages[0])
            print(f"✓ Đã lưu package name: {mtc_packages[0]}")
    else:
        print("⚠️  Cần khắc phục:")
        if not connected:
            print("   - Khởi động BlueStacks")
        if not mtc_packages:
            print("   - Cài app MTC trong BlueStacks")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Đã dừng")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
