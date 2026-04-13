import sys, time, subprocess
sys.path.insert(0, '.')
from mtc.adb import AdbController

ADB = r'C:\Program Files\BlueStacks_nxt\HD-Adb.exe'
DEVICE = '127.0.0.1:5555'

adb = AdbController(ADB, DEVICE)
adb.ensure_device()

def screencap(name):
    subprocess.run([ADB, '-s', DEVICE, 'shell', 'screencap', '-p', f'/sdcard/{name}'])
    subprocess.run([ADB, '-s', DEVICE, 'pull', f'/sdcard/{name}', name])

xml = adb.dump_ui()
texts = adb.get_all_text(xml)
print("== All texts ==")
for i, t in enumerate(texts):
    print(f"  [{i}] {repr(t)[:80]}")

print("\n== Clickable nodes ==")
import xml.etree.ElementTree as ET
root = ET.fromstring(xml)
for node in root.iter():
    if node.get('clickable') == 'true':
        txt = node.get('text','')
        desc = node.get('content-desc','')
        bounds = node.get('bounds','')
        cls = node.get('class','').split('.')[-1]
        info = txt or desc
        if info:
            print(f"  [{cls}] {repr(info[:60])} @ {bounds}")

print("\n== ALL bounds for first few nodes ==")
count = 0
for node in root.iter():
    bounds = node.get('bounds','')
    if bounds and '[329' in bounds:  # look for Cong cu dialog range
        print(f"  {node.get('class','').split('.')[-1]}: {node.get('text','')} / {node.get('content-desc','')} @ {bounds}")
