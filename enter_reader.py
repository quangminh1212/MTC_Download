"""Enter reader and explore reader menu to find XUAT EBOOK."""
import subprocess, time, re

ADB = r'C:\Program Files\BlueStacks_nxt\HD-Adb.exe'
DEV = '127.0.0.1:5555'

def adb(*args):
    return subprocess.run([ADB, '-s', DEV] + list(args), capture_output=True)

def adb_text(*args):
    r = subprocess.run([ADB, '-s', DEV] + list(args), capture_output=True)
    return r.stdout.decode('utf-8', errors='replace')

def tap(x, y, delay=1.5):
    adb('shell', 'input', 'tap', str(x), str(y))
    time.sleep(delay)

def screenshot(name):
    adb('shell', 'screencap', '-p', f'/sdcard/{name}.png')
    adb('pull', f'/sdcard/{name}.png', f'{name}.png')
    print(f'Screenshot: {name}.png')

def dump_ui():
    adb('shell', 'uiautomator', 'dump', '/sdcard/ui.xml')
    raw = adb_text('shell', 'cat', '/sdcard/ui.xml')
    texts = re.findall(r'text="([^"]+)"', raw)
    bounds = re.findall(r'text="([^"]+)"[^>]+bounds="(\[\d+,\d+\]\[\d+,\d+\])"', raw)
    return texts, bounds, raw

def back():
    adb('shell', 'input', 'keyevent', 'KEYCODE_BACK')
    time.sleep(1.0)

# ============================================================
# Navigate: back to library screen first
# ============================================================
print('=== Going back to library ===')
for _ in range(5):
    back()
    time.sleep(0.5)

screenshot('back_to_library')
texts, bounds, raw = dump_ui()
print('After backs:', texts[:10])

# ============================================================
# Check if we're on library screen, tap first history book
# ============================================================
print('\n=== Tap first history book row (400, 283) ===')
tap(400, 283, delay=2.0)
screenshot('book_detail_again')

# Look for "Doc truyen" button in the UI
texts, bounds, raw = dump_ui()
print('Book detail texts:', texts[:20])
print()
for t, b in bounds[:15]:
    print(f'  {repr(t)} @ {b}')

# ============================================================
# Tap "Doc truyen" button
# ============================================================
# The "Doc truyen" should be in the detail page header  
# Based on UIAutomator: 'Doc truyen' @ [245,320][371,356] center=(308, 338) 
doc_btn = None
for t, b in bounds:
    if 'truyện' in t.lower() and ('đọc' in t.lower() or 'doc' in t.lower()):
        doc_btn = b
        print(f'Found Doc truyen: {repr(t)} @ {b}')
        # Parse center from bounds
        nums = re.findall(r'\d+', b)
        if len(nums) == 4:
            cx = (int(nums[0]) + int(nums[2])) // 2
            cy = (int(nums[1]) + int(nums[3])) // 2
            print(f'  Center: ({cx}, {cy})')
            break

print('\n=== Tapping Doc truyen at known position (308, 338) ===')
tap(308, 338, delay=3.0)
screenshot('reader_attempt')

texts, bounds, raw = dump_ui()
print('After tapping Doc truyen:')
print('Texts:', texts[:20])
print()
for t, b in bounds[:15]:
    print(f'  {repr(t)} @ {b}')

# Check if we entered the reader (reader has payload with many newlines in content-desc)
in_reader = False
for node_text in [raw] if raw else []:
    if 'D.S Chương' in raw and 'Tải lại nội dung' in raw:
        in_reader = True
        print('\n** IN READER MENU VIEW! **')

# If in reader, look for export option
if in_reader or True:
    print('\n=== Checking reader menu (tap center) ===')
    tap(450, 800, delay=1.0)  # Tap reader text area
    screenshot('reader_center_tap')
    texts, bounds, raw = dump_ui()
    print('After center tap:', texts[:30])
    if 'D.S Chương' in raw or 'Tải lại' in raw:
        print('** Reader overlay visible! **')
        for t, b in bounds:
            print(f'  {repr(t)} @ {b}')
