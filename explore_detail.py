import subprocess, time, re

ADB = r'C:\Program Files\BlueStacks_nxt\HD-Adb.exe'
DEV = '127.0.0.1:5555'

def adb(*args):
    return subprocess.run([ADB, '-s', DEV] + list(args), capture_output=True)

def adb_text(*args):
    r = subprocess.run([ADB, '-s', DEV] + list(args), capture_output=True)
    return r.stdout.decode('utf-8', errors='replace')

def tap(x, y):
    adb('shell', 'input', 'tap', str(x), str(y))
    time.sleep(1.5)

def screenshot(name):
    adb('shell', 'screencap', '-p', f'/sdcard/{name}.png')
    adb('pull', f'/sdcard/{name}.png', f'{name}.png')

def dump_ui():
    adb('shell', 'uiautomator', 'dump', '/sdcard/ui.xml')
    raw = adb_text('shell', 'cat', '/sdcard/ui.xml')
    texts = re.findall(r'text="([^"]+)"', raw)
    bounds = re.findall(r'text="([^"]+)"[^>]+bounds="(\[\d+,\d+\]\[\d+,\d+\])"', raw)
    return texts, bounds, raw

# ---- Tap D.S Chuong tab (4th tab, from [675,384][900,456]) ----
print('=== Tapping D.S Chuong tab ===')
tap(787, 420)
screenshot('chapter_list_tab')
texts, bounds, raw = dump_ui()
print('Texts:', texts[:50])
print()
print('Bounds with text:')
for t, b in bounds[:30]:
    print(f'  {repr(t)} @ {b}')

# Look for Cong cu / export / tool buttons
print()
print('=== Looking for Cong cu / export ===')
keywords = ['cong', 'xu', 'ebook', 'tai', 'tro', 'chuyen', 'cai', 'tool', 'setting']
for t, b in bounds:
    for kw in keywords:
        if kw in t.lower():
            print(f'  FOUND: {repr(t)} @ {b}')
            break

print()
print('=== All clickable items ===')
clickable = re.findall(r'clickable="true"[^>]+text="([^"]+)"[^>]+bounds="(\[\d+,\d+\]\[\d+,\d+\])"', raw)
clickable2 = re.findall(r'text="([^"]+)"[^>]+clickable="true"[^>]+bounds="(\[\d+,\d+\]\[\d+,\d+\])"', raw)
all_click = clickable + clickable2
for t, b in all_click[:30]:
    print(f'  {repr(t)} @ {b}')
