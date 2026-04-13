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

def get_node_center(xml, text):
    root = ET.fromstring(xml)
    for node in root.iter():
        if text in (node.get('text','') or node.get('content-desc','')):
            bounds = node.get('bounds','')
            if bounds:
                nums = [int(x) for x in bounds.replace('][',',').replace('[','').replace(']','').split(',')]
                return ((nums[0]+nums[2])//2, (nums[1]+nums[3])//2, bounds)
    return None

# Get current state
xml = adb.dump_ui()
result = get_node_center(xml, 'Tải truyện')
print(f"'Tải truyện' location: {result}")

if result:
    cx, cy, bounds = result
    print(f"Tapping 'Tải truyện' at ({cx}, {cy})")
    adb.tap(cx, cy)
    time.sleep(3)
    
    screencap('after_tai_truyen.png')
    xml2 = adb.dump_ui()
    texts2 = adb.get_all_text(xml2)
    print("After tapping 'Tải truyện', texts:", texts2[:30])
    
    root2 = ET.fromstring(xml2)
    for node in root2.iter():
        b = node.get('bounds','')
        t = node.get('text','') or node.get('content-desc','')
        if t and b:
            print(f"  {repr(t[:60])} @ {b}")
