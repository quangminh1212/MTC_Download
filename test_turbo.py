"""Test turbo advance+read speed - explore fastest approach."""
import time, sys
sys.path.insert(0, '.')
from mtc.adb import AdbController
adb = AdbController(r'C:\Program Files\BlueStacks_nxt\HD-Adb.exe', '127.0.0.1:5555')
adb.ensure_device()

w, h = adb.screen_size()
print(f'Screen: {w}x{h}')

# Should still be in reader from last test
xml = adb.dump_ui()
p = adb._extract_reader_payload(xml)
print(f'Starting at: {p.get("title") if p else "N/A"}')

if not p:
    print('Not in reader, need to navigate first')
    sys.exit(1)

# Test A: tap right side without menu (direct advance?)
print('\n=== Test A: Direct right-tap (no menu) ===')
for i in range(3):
    before = adb._extract_reader_payload(adb.dump_ui())
    before_title = before.get('title', '?') if before else '?'
    
    t0 = time.perf_counter()
    # Just tap right side of screen
    adb.tap(int(w * 0.85), h // 2)
    time.sleep(0.5)
    xml = adb.dump_ui()
    after = adb._extract_reader_payload(xml)
    t1 = time.perf_counter()
    
    after_title = after.get('title', '?') if after else '?'
    changed = before_title != after_title
    print(f'  #{i+1}: {(t1-t0)*1000:.0f}ms | {before_title} -> {after_title} | changed={changed}')

# Test B: open menu with longer sleep, tap "next", close
print('\n=== Test B: Menu with 0.3s sleep ===')
for i in range(3):
    before = adb._extract_reader_payload(adb.dump_ui())
    before_title = before.get('title', '?') if before else '?'
    
    t0 = time.perf_counter()
    adb.reader_open_menu()
    time.sleep(0.3)
    adb.tap(*adb._reader_nav_point("next"))
    time.sleep(0.35)
    adb.reader_close_menu()
    time.sleep(0.15)
    xml = adb.dump_ui()
    after = adb._extract_reader_payload(xml)
    t1 = time.perf_counter()
    
    after_title = after.get('title', '?') if after else '?'
    changed = before_title != after_title
    print(f'  #{i+1}: {(t1-t0)*1000:.0f}ms | {before_title} -> {after_title} | changed={changed}')
