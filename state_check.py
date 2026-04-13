import sys, time
sys.path.insert(0, '.')
from mtc.adb import AdbController

adb = AdbController(r'C:\Program Files\BlueStacks_nxt\HD-Adb.exe', '127.0.0.1:5555')
adb.ensure_device()

# Force back to home
for _ in range(5):
    adb.go_back()
    time.sleep(0.4)

time.sleep(1)
adb.take_screenshot('state_check.png')
w, h = adb.screen_size()
print(f"Screen: {w}x{h}")

xml = adb.dump_ui()
texts = adb.get_all_text(xml)
print("Texts:", texts[:20])
