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

def type_text(text):
    # Use ADB input text with proper encoding
    import urllib.parse
    escaped = text.replace(' ', '%s').replace("'", "\\'")
    adb('shell', 'input', 'text', escaped)
    time.sleep(1.0)

# ============================================================
# STEP 1: Navigate to Khám Phá (search screen)
# ============================================================
print('=== Step 1: Navigate to Kham Pha search screen ===')
# Tap Khám Phá in bottom nav: [225,1519][450,1597] center=(338, 1558)
back(); back()  # Go back to get out of book detail
time.sleep(0.5)

# Navigate to Kham Pha
tap(338, 1558)
screenshot('kham_pha_screen')
texts, bounds, raw = dump_ui()
print('Texts on Kham Pha:', texts[:20])

# ============================================================
# STEP 2: Find and tap the search box
# ============================================================
print('\n=== Step 2: Tap search box ===')
# Look for search icon/box
for t, b in bounds:
    if any(kw in t.lower() for kw in ['tìm', 'search', 'truyện']):
        print(f'  Potential search: {repr(t)} @ {b}')

# The search icon should be visible - tap it
# From prior sessions, search box is at top area
tap(450, 80, delay=2.0)
screenshot('after_search_tap')
texts, _, raw = dump_ui()
print('Texts after search tap:', texts[:15])

# ============================================================
# STEP 3: Type book name
# ============================================================
print('\n=== Step 3: Type book name ===')
# Clear and type
adb('shell', 'input', 'keyevent', 'KEYCODE_CTRL_A')
time.sleep(0.3)
type_text('De')  # Start with simpler text 
screenshot('after_type')
texts, _, _ = dump_ui()
print('Texts after typing:', texts[:10])
