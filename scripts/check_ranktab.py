import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mtc.adb import AdbController

adb = AdbController(r'C:\Program Files\BlueStacks_nxt\HD-Adb.exe', '127.0.0.1:5555')
adb.ensure_device()

# Dismiss any open dialogs/screens
adb.go_back(); time.sleep(0.5)
adb.go_back(); time.sleep(0.5)

w, h = adb.screen_size()
print(f"Screen: {w}x{h}")

# Bottom nav - tap Xep Hang (3rd tab, 5/8 across)
xep_hang_x = int(w * 5 / 8)
xep_hang_y = int(h * 0.97)
print(f"Tapping Xep Hang at ({xep_hang_x}, {xep_hang_y})")
adb.tap(xep_hang_x, xep_hang_y)
time.sleep(2)

xml = adb.dump_ui()
texts = adb.get_all_text(xml)
print("Screen texts:", texts[:30])

books = adb.scan_visible_books()
print(f"\nVisible books: {len(books)}")
for b in books[:5]:
    t = b.get('title','?')
    c = b.get('center','?')
    print(f"  - {t[:50]} @ {c}")
