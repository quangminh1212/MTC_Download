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

# --- Check app storage for downloaded chapters ---
print('=== Checking NovelFever app data directory ===')
dirs_to_check = [
    '/sdcard/Android/data/com.novelfever.app.android/',
    '/sdcard/Download/NovelFever/',
    '/data/data/com.novelfever.app.android/',
    '/storage/emulated/0/Android/data/com.novelfever.app.android/',
]
for d in dirs_to_check:
    result = adb_text('shell', f'ls -la {d} 2>&1 | head -20')
    print(f'\n--- {d} ---')
    print(result[:500])

print('\n=== Files in NovelFever download dir ===')
result = adb_text('shell', 'ls -la /sdcard/Download/NovelFever/ 2>&1')
print(result[:1000])

print('\n=== Checking download progress via UI dump ===')
texts, bounds, raw = dump_ui()
print('Current screen texts:', texts[:20])
