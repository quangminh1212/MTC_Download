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

# The first book row: [12,216][888,351]
# Tap at center of title area (not the 3-dot area)
# Center = (450, 283)
# Try the 3-dot icon at far right ~ (848, 283)

print("=== Test 1: Tap on three-dot icon of first book ===")
adb.tap(848, 283)
time.sleep(1.5)
screencap('tap_threedot.png')

xml = adb.dump_ui()
texts = adb.get_all_text(xml)
print("After 3-dot tap, texts:", texts[:20])
