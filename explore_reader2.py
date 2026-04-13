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

# --- Currently on D.S Chuong tab ---
# Try 1: Tap "+" blue button at bottom right corner of sticky footer
# From UIAutomator: 'Doc' @ [695,1495][806,1537] center=(750,1516)
# "+" button should be to its right, ~ x=855 y=1516
print('=== Test 1: Tap + button at bottom-right (855, 1516) ===')
tap(855, 1516)
screenshot('plus_button_result')
texts, bounds, raw = dump_ui()
print('Texts:', texts[:30])
for t, b in bounds[:20]:
    print(f'  {repr(t)} @ {b}')
print()

# If Cong cu appeared
if 'cu' in raw.lower() or 'EBOOK' in raw.upper():
    print('** FOUND EXPORT OPTION! **')

# Go back (in case a modal appeared)
back()
time.sleep(0.5)

# --- Enter Reader via "Doc truyen" header button ---
# From UIAutomator: 'Doc truyen' @ [245,320][371,356] center=(308, 338)
print('=== Test 2: Enter reader via Doc truyen (308, 338) ===')
tap(308, 338, delay=3.0)
screenshot('reader_initial')
texts, bounds, raw = dump_ui()
print('Texts after entering reader:', texts[:30])
print()
for t, b in bounds[:20]:
    print(f'  {repr(t)} @ {b}')
print()

if 'cu' in raw.lower() or 'EBOOK' in raw.upper():
    print('** FOUND EXPORT IN READER! **')
