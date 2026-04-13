import sys, time, subprocess
sys.path.insert(0, '.')
from mtc.adb import AdbController
import xml.etree.ElementTree as ET

ADB = r'C:\Program Files\BlueStacks_nxt\HD-Adb.exe'
DEVICE = '127.0.0.1:5555'

adb = AdbController(ADB, DEVICE)
adb.ensure_device()

def screencap(name):
    subprocess.run([ADB, '-s', DEVICE, 'shell', 'screencap', '-p', f'/sdcard/{name}'], timeout=10)
    subprocess.run([ADB, '-s', DEVICE, 'pull', f'/sdcard/{name}', name], timeout=10)

def dump_clickable(xml):
    root = ET.fromstring(xml)
    for node in root.iter():
        if node.get('clickable') == 'true':
            t = (node.get('text','') or node.get('content-desc',''))[:60]
            b = node.get('bounds','')
            if t:
                print(f"  {repr(t)} @ {b}")

# First: dismiss the bottom sheet by tapping scrim area
print("Dismissing bottom sheet...")
adb.tap(450, 600)
time.sleep(1)

xml = adb.dump_ui()
texts = adb.get_all_text(xml)
print("After dismiss:", texts[:10])

# Check if download notification exists somewhere (notification bar?)
screencap('after_dismiss.png')

# Now try tapping the BOOK TITLE area (left-center) not the 3-dot
print("\nTapping book title area at (400, 283)...")
# Row [12,216][888,351], title area ~ (200-700, 216-351)
adb.tap(400, 283)
time.sleep(2)

screencap('book_tap.png')
xml2 = adb.dump_ui()
texts2 = adb.get_all_text(xml2)
print("After tapping book title, texts:", texts2[:15])
print("\nClickable items:")
dump_clickable(xml2)
