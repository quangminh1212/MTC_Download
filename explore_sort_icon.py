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
    print(f'Screenshot saved: {name}.png')

def dump_ui():
    adb('shell', 'uiautomator', 'dump', '/sdcard/ui.xml')
    raw = adb_text('shell', 'cat', '/sdcard/ui.xml')
    texts = re.findall(r'text="([^"]+)"', raw)
    bounds = re.findall(r'text="([^"]+)"[^>]+bounds="(\[\d+,\d+\]\[\d+,\d+\])"', raw)
    return texts, bounds, raw

# Currently on D.S Chuong tab
# Screenshot to confirm state
screenshot('state_before')

# 1. Try tapping the sort/filter icon (≡) at top right of chapter list 
# Looking at image: "Số chương" text is around y=430, sort icon at x~755, y=430
print('=== Tapping sort icon (expected ~755, 430) ===')
tap(755, 430)
screenshot('after_sort_tap')
texts, bounds, raw = dump_ui()
print('Texts after sort tap:', texts[:30])
print()
for t, b in bounds[:20]:
    print(f'  {repr(t)} @ {b}')

# Check for Cong cu
if 'Công cụ' in raw or 'cong cu' in raw.lower():
    print('** CONG CU FOUND! **')

# Back/escape to dismiss any popup
time.sleep(0.5)
print('\n=== State after sort tap ===')
screenshot('after_sort_view')
