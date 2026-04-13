"""
Test XUẤT EBOOK via search -> Công cụ dialog path.
The 'Để Ngươi' book should have downloads from the 'Tải truyện' operation.
"""
import subprocess, time, re

ADB = r'C:\Program Files\BlueStacks_nxt\HD-Adb.exe'
DEV = '127.0.0.1:5555'

def a(*args, t=8):
    return subprocess.run([ADB, '-s', DEV] + list(args), capture_output=True, timeout=t)

def atext(*args, t=8):
    r = subprocess.run([ADB, '-s', DEV] + list(args), capture_output=True, timeout=t)
    return r.stdout.decode('utf-8', errors='replace')

def tap(x, y, d=1.5):
    a('shell', 'input', 'tap', str(x), str(y))
    time.sleep(d)

def swipe(x1, y1, x2, y2, dur=300, d=0.8):
    a('shell', 'input', 'swipe', str(x1), str(y1), str(x2), str(y2), str(dur))
    time.sleep(d)

def text_input(t, d=0.5):
    a('shell', 'input', 'text', t)
    time.sleep(d)

def ss(n):
    a('shell', 'screencap', '-p', f'/sdcard/{n}.png')
    a('pull', f'/sdcard/{n}.png', f'{n}.png')
    print(f'[ss] {n}.png')

def dump():
    a('shell', 'uiautomator', 'dump', '/sdcard/ui.xml')
    raw = atext('shell', 'cat', '/sdcard/ui.xml')
    texts = re.findall(r'text="([^"]+)"', raw)
    bounds = re.findall(r'text="([^"]+)"[^>]+bounds="(\[\d+,\d+\]\[\d+,\d+\])"', raw)
    return texts, bounds, raw

def key(code):
    a('shell', 'input', 'keyevent', str(code))
    time.sleep(0.6)

def center(b):
    nums = re.findall(r'\d+', b)
    if len(nums) == 4:
        return (int(nums[0]) + int(nums[2])) // 2, (int(nums[1]) + int(nums[3])) // 2
    return None

# ============================================================
# Step 1: Check current state - we should be on book detail page
# ============================================================
print('=== Current state ===')
ss('start')
texts, bounds, raw = dump()
print('Current texts:', texts[:10])

# ============================================================
# Step 2: Navigate to search
# ============================================================
print('\n=== Step 2: Go to Khám Phá tab then search ===')
# Tap "Khám Phá" bottom nav (center-bottom ~(338, 1558))
tap(338, 1558, 2.0)
ss('kham_pha')
texts, bounds, raw = dump()
print('Khám Phá:', texts[:10])

# Tap search icon (should be visible in header)
# From prior sessions, search icon was shown in Tủ Truyện header as gear+search
# The search icon in Khám Phá should be at top-right area
search_found = False
for t, b in bounds:
    if 'tìm kiếm' in t.lower() or 'search' in t.lower():
        c = center(b)
        if c:
            print(f'Found search: "{t}" at {c}')
            tap(c[0], c[1], 1.5)
            search_found = True
            break

if not search_found:
    # Try tapping where search input usually is in Khám Phá
    # Looking at Tủ Truyện header: search icon at top right
    print('No search found in Khám Phá, trying Tủ Truyện search icon...')
    # Go to Tủ Truyện
    tap(113, 1558, 2.0)
    texts, bounds, raw = dump()
    # Find search icon
    for t, b in bounds:
        if 'tìm kiếm' in t.lower() or 'search' in t.lower():
            c = center(b)
            if c:
                print(f'Found search in Tủ Truyện: "{t}" at {c}')
                tap(c[0], c[1], 1.5)
                search_found = True
                break
    if not search_found:
        # Tap the search icon position in Tủ Truyện header (magnifier icon at ~(720, 75))
        print('Fallback: tap (720, 75) for search icon')
        tap(720, 75, 1.5)

ss('search_screen')
texts, bounds, raw = dump()
print('Search screen:', texts[:10])
for t, b in bounds[:10]:
    print(f'  "{t}" @ {b}')

# ============================================================
# Step 3: Type search query
# ============================================================
print('\n=== Step 3: Type search query ===')
# Type the book name (partial - Vietnamese without diacritics might work)
# Search for "De Nguoi" or the full name
search_query = 'Để Ngươi Người Quản Lý'
text_input(search_query.replace(' ', '%s'), 2.0)  # %s = space in adb input

ss('after_type')
texts, bounds, raw = dump()
print('After typing:', texts[:10])

# ============================================================
# Step 4: Wait for search results and tap first result (Công cụ path)
# From prior sessions: tap at (135, 168) on first search result
# ============================================================
print('\n=== Step 4: Tap first search result ===')
# The first result center-left position from prior sessions: (135, 168)
# This triggers the Công cụ dialog with TẢI TẤT CẢ + XUẤT EBOOK
time.sleep(1.5)  # Wait for search
tap(135, 168, 2.0)
ss('cong_cu_dialog')
texts, bounds, raw = dump()
print('After tap first result:')
for t, b in bounds:
    print(f'  "{t}" @ {b}')

# Check for Công cụ dialog
if 'xuất' in raw.lower() or 'xuat' in raw.lower() or 'ebook' in raw.lower():
    print('\n** FOUND XUẤT EBOOK! **')
    for t, b in bounds:
        if 'xuất' in t.lower() or 'ebook' in t.lower():
            c = center(b)
            print(f'  XUẤT EBOOK at: "{t}" => {c}')
