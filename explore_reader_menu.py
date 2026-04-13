"""
Navigate library -> book detail -> reader -> open reader menu overlay.
Capture what options are available in the reader menu.
"""
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
    print(f'  Screenshot: {name}.png')

def dump_ui():
    adb('shell', 'uiautomator', 'dump', '/sdcard/ui.xml')
    raw = adb_text('shell', 'cat', '/sdcard/ui.xml')
    texts = re.findall(r'text="([^"]+)"', raw)
    bounds = re.findall(r'text="([^"]+)"[^>]+bounds="(\[\d+,\d+\]\[\d+,\d+\])"', raw)
    return texts, bounds, raw

def center_of_bounds(b):
    nums = re.findall(r'\d+', b)
    if len(nums) == 4:
        return (int(nums[0]) + int(nums[2])) // 2, (int(nums[1]) + int(nums[3])) // 2
    return None

# ============================================================
# Step 1: Tap first book in library to open detail page
# ============================================================
print('\n=== Step 1: Open book detail ===')
# First book row center Y=283 based on prior sessions [12,216][888,351]
tap(400, 255, delay=2.5)
screenshot('step1_book_detail')
texts, bounds, raw = dump_ui()
print('Book detail texts:', texts[:15])
if not texts:
    print('No texts! Maybe Flutter-only rendering. Checking screenshot...')

# ============================================================
# Step 2: Find and tap "Đọc truyện" button
# ============================================================
print('\n=== Step 2: Looking for Doc truyen button ===')
doc_btn = None
for t, b in bounds:
    tl = t.lower()
    if 'đọc' in tl or 'doc' in tl:
        print(f'  Found: "{t}" @ {b}')
        c = center_of_bounds(b)
        if c:
            doc_btn = c

if not doc_btn:
    print('  Not found via text, using (308, 338) from prior research')
    doc_btn = (308, 338)

# Make sure we're on the right screen - check for "Đọc truyện" indicator
print(f'  Tapping Doc truyen at {doc_btn}')
tap(doc_btn[0], doc_btn[1], delay=3.5)  # Extra wait for reader to load
screenshot('step2_entered_reader')
texts, bounds, raw = dump_ui()
print('After entering reader:')
print('  Texts:', texts[:15])
print()

# ============================================================
# Step 3: Open reader menu overlay
# ============================================================
print('\n=== Step 3: Opening reader menu ===')
# The reader menu opens when tapping in the middle of the screen
# From mtc/adb.py: tap(w//2, h*0.75) = tap(450, 1200)
tap(450, 800, delay=1.5)
screenshot('step3_reader_menu_try1')
texts, bounds, raw = dump_ui()
print('Try 1 menu (center tap):')
for t, b in bounds:
    print(f'  "{t}" @ {b}')

if not texts:
    print('  Empty UIAutomator. Flutter canvas is showing reader text.')
    print('  Trying different positions...')
    
    # Try tapping very bottom of the screen
    tap(450, 1500, delay=1.0)
    screenshot('step3_try_bottom')
    texts, bounds, raw = dump_ui()
    print('  After bottom tap:', texts[:10])
    for t, b in bounds:
        print(f'    "{t}" @ {b}')

# ============================================================
# Step 4: Check for XUẤT EBOOK / Công cụ in reader overlay
# ============================================================
print('\n=== Step 4: Analyzing reader menu options ===')
all_texts = []
for t, b in bounds:
    all_texts.append(t)
    
print('All menu texts found:')
for t in all_texts:
    print(f'  - {repr(t)}')

# Key texts to look for:
look_for = ['xuất', 'xuat', 'ebook', 'công cụ', 'cong cu', 'tải', 'tai', 'D.S', 'chương']
found = [t for t in all_texts if any(k.lower() in t.lower() for k in look_for)]
print('\nRelevant texts:', found)
