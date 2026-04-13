import sys, time, subprocess
sys.path.insert(0, '.')
from mtc.adb import AdbController
import xml.etree.ElementTree as ET

ADB = r'C:\Program Files\BlueStacks_nxt\HD-Adb.exe'
DEVICE = '127.0.0.1:5555'

adb = AdbController(ADB, DEVICE)
adb.ensure_device()

def screencap(name):
    subprocess.run([ADB, '-s', DEVICE, 'shell', 'screencap', '-p', f'/sdcard/{name}'])
    subprocess.run([ADB, '-s', DEVICE, 'pull', f'/sdcard/{name}', name])

def dump_all(xml):
    root = ET.fromstring(xml)
    for node in root.iter():
        t = node.get('text','') or node.get('content-desc','')
        b = node.get('bounds','')
        if t and b:
            print(f"  {repr(t[:70])} @ {b}")

# Tap "Đồng ý" to confirm download with empty range (= all chapters)
print("Tapping 'Đồng ý' to start download...")
adb.tap(600, 1009)  # Center of Đồng ý button
time.sleep(2)

screencap('download_started.png')
xml = adb.dump_ui()
texts = adb.get_all_text(xml)
print("After confirming, texts:", texts[:20])
dump_all(xml)
