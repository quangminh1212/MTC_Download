"""
1. Check network security config (can we MITM with mitmproxy?)
2. Try adb backup to extract app SQLite database
"""
import zipfile, re, xml.etree.ElementTree as ET, struct, subprocess, os, sys
sys.stdout.reconfigure(encoding='utf-8')

ADB = r'C:\Program Files\BlueStacks_nxt\HD-Adb.exe'
DEV = '127.0.0.1:5555'

def adb(cmd):
    r = subprocess.run([ADB, '-s', DEV, 'shell', cmd],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.stdout.strip(), r.stderr.strip()

# 1. Extract network_security_config from APK
print("=== Network Security Config ===")
with zipfile.ZipFile('base.apk') as z:
    # Find network_security_config.xml
    names = z.namelist()
    net_configs = [n for n in names if 'network_security' in n.lower() or 'res/xml' in n.lower()]
    print(f"Found: {net_configs}")
    
    # Check all res/xml files
    xml_files = [n for n in names if n.startswith('res/xml/')]
    print(f"res/xml files: {xml_files}")
    
    for f in xml_files:
        data = z.read(f)
        print(f"\n{f} ({len(data)} bytes):")
        print(f"  First 100: {repr(data[:100])}")
        # Extract strings from binary XML
        strings = re.findall(rb'[\x20-\x7e]{4,}', data)
        for s in strings:
            print(f"  str: {s!r}")

# 2. Check manifest allowBackup
print("\n=== Manifest allowBackup ===")
with zipfile.ZipFile('base.apk') as z:
    manifest = z.read('AndroidManifest.xml')
    # Find allowBackup mention
    idx = manifest.find(b'allowBackup')
    if idx != -1:
        ctx = manifest[max(0,idx-20):idx+40]
        print(f"allowBackup context: {repr(ctx)}")
    else:
        print("allowBackup not found in manifest")
        
    # Also check for backupAgent or backupRules
    for term in [b'backupAgent', b'backupRules', b'fullBackupContent']:
        pos = manifest.find(term)
        if pos != -1:
            ctx = manifest[max(0,pos-10):pos+30]
            print(f"{term}: {repr(ctx)}")

# 3. Try adb backup
print("\n=== Trying adb backup ===")
backup_file = 'novelfever_backup.ab'
if os.path.exists(backup_file):
    print(f"Backup file already exists: {os.path.getsize(backup_file)} bytes")
else:
    print("Starting adb backup...")
    # Non-interactive backup
    result = subprocess.run(
        [ADB, '-s', DEV, 'backup', '-noapk', '-nosystem', '-f', backup_file, 'com.novelfever.app.android'],
        capture_output=True, text=True, timeout=30
    )
    print(f"Backup result: {result.returncode}")
    print(f"stdout: {result.stdout[:200]}")
    print(f"stderr: {result.stderr[:200]}")
    if os.path.exists(backup_file):
        print(f"Backup file size: {os.path.getsize(backup_file)} bytes")
