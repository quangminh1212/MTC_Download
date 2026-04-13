"""Relaunch app, navigate library -> book -> reader, open reader menu."""
import subprocess, time, re

ADB = r'C:\Program Files\BlueStacks_nxt\HD-Adb.exe'
DEV = '127.0.0.1:5555'
PKG = 'com.novelfever.app.android'
ACTIVITY = 'com.novelfever.app.android/.MainActivity'

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

def get_focused_pkg():
    out = adb_text('shell', 'dumpsys', 'window', 'windows')
    m = re.search(r'mCurrentFocus.*?(\w+\.\w+\.\w+\S*)', out)
    return m.group(1) if m else ''

def launch_app():
    print('Launching app...')
    adb('shell', 'am', 'start', '-n', ACTIVITY)
    time.sleep(4.0)

def is_app_running():
    pkg = get_focused_pkg()
    return PKG in pkg

# ============================================================
# 1. Launch app if not running
# ============================================================
if not is_app_running():
    launch_app()
else:
    print('App already running')

screenshot('app_launched')
texts, bounds, raw = dump_ui()
print('After launch texts:', texts[:10])

# Look for library tab indicator
lib_keywords = ['tủ truyện', 'tu truyen', 'tủ', 'truyện', 'đọc', 'yêu thích']
if any(any(k in t.lower() for k in lib_keywords) for t in texts):
    print('App is on main screen')
else:
    print('App may not be on main screen, trying navigation...')
    # Tap bottom nav "Tủ Truyện" (library)
    tap(113, 1558, delay=2.0)
    screenshot('library_nav')
    texts, bounds, raw = dump_ui()
    print('After nav tap:', texts[:10])

# ============================================================
# 2. Navigate to library tab (Tủ Truyện at bottom-left)
# ============================================================
print('\n=== Tapping library tab ===')
tap(113, 1558, delay=2.0)
screenshot('library_screen')
texts, bounds, raw = dump_ui()
print('Library screen texts:', texts[:15])
print()
for t, b in bounds[:15]:
    print(f'  {repr(t)} @ {b}')

# ============================================================
# 3. Find first book row and tap it
# ============================================================
# Library rows have content-desc with newlines. Let's find book titles.
book_rows = [(t, b) for t, b in bounds if '\n' in t or len(t) > 15]
print('\nPotential book rows:')
for t, b in book_rows[:5]:
    nums = re.findall(r'\d+', b)
    if len(nums) == 4:
        x1, y1, x2, y2 = int(nums[0]), int(nums[1]), int(nums[2]), int(nums[3])
        cx, cy = (x1+x2)//2, (y1+y2)//2
        print(f'  {repr(t[:40])} @ ({cx},{cy})')

# Tap first visible book row center (y = 283 for first row historically)
print('\n=== Tapping first book row at (400, 283) ===')
tap(400, 283, delay=2.5)
screenshot('book_detail')
texts, bounds, raw = dump_ui()
print('Book detail texts:', texts[:20])
print()
for t, b in bounds[:15]:
    print(f'  {repr(t)} @ {b}')

# ============================================================
# 4. Enter reader via "Đọc truyện" button
# ============================================================
# Look for the "Đọc truyện" button in the accessible texts
doc_btn_center = None
for t, b in bounds:
    tl = t.lower()
    if 'đọc' in tl or 'doc' in tl:
        nums = re.findall(r'\d+', b)
        if len(nums) == 4:
            cx = (int(nums[0]) + int(nums[2])) // 2
            cy = (int(nums[1]) + int(nums[3])) // 2
            doc_btn_center = (cx, cy)
            print(f'\nFound read button: {repr(t)} @ ({cx},{cy})')
            break

if not doc_btn_center:
    print('\nFalling back to (308, 338) for Doc truyen...')
    doc_btn_center = (308, 338)

print(f'=== Tapping Doc truyen at {doc_btn_center} ===')
tap(doc_btn_center[0], doc_btn_center[1], delay=4.0)
screenshot('in_reader')

texts, bounds, raw = dump_ui()
print('Reader screen texts:', texts[:20])
print()
for t, b in bounds[:10]:
    print(f'  {repr(t)} @ {b}')

# ============================================================
# 5. Open reader menu overlay (tap center of screen)
# ============================================================
print('\n=== Opening reader menu (tap center-top area) ===')
tap(450, 800, delay=1.0)
screenshot('reader_menu_open')
texts, bounds, raw = dump_ui()

has_menu = 'D.S Chương' in raw or 'Tải lại nội dung' in raw
print(f'Reader menu visible: {has_menu}')
if has_menu:
    print('\nMenu items:')
    for t, b in bounds:
        print(f'  {repr(t)} @ {b}')
else:
    print('Menu not visible, trying bottom area...')
    tap(450, 1200, delay=1.0)  # Try h*0.75
    screenshot('reader_menu_bottom')
    texts, bounds, raw = dump_ui()
    print('After bottom tap:', texts[:20])
    for t, b in bounds[:10]:
        print(f'  {repr(t)} @ {b}')
