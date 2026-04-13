import sys, time, subprocess
sys.path.insert(0, '.')
from mtc.adb import AdbController

ADB = r'C:\Program Files\BlueStacks_nxt\HD-Adb.exe'
DEVICE = '127.0.0.1:5555'

adb = AdbController(ADB, DEVICE)
adb.ensure_device()

print("Polling download progress (max 2 mins)...")
for i in range(60):
    xml = adb.dump_ui()
    texts = adb.get_all_text(xml)
    # Find progress indicator
    for t in texts:
        if 'Tải truyện' in t or 'tải' in t.lower() or '%' in t:
            print(f"  [{i*2:3d}s] {repr(t)}")
    time.sleep(2)
    
    # Check if download completed (100% or no longer showing progress)
    has_progress = any('%' in t for t in texts)
    if not has_progress and i > 3:
        print(f"  [{i*2}s] No progress indicator - may be done!")
        print("  All texts:", texts[:15])
        break

print("Done polling")
