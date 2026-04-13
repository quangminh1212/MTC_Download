"""Try various methods to dismiss the reader tutorial popup."""
import subprocess, time

ADB = r'C:\Program Files\BlueStacks_nxt\HD-Adb.exe'
DEV = '127.0.0.1:5555'

def a(*args):
    return subprocess.run([ADB, '-s', DEV] + list(args), capture_output=True, timeout=8)

def atext(*args):
    r = subprocess.run([ADB, '-s', DEV] + list(args), capture_output=True, timeout=8)
    return r.stdout.decode('utf-8', errors='replace')

def tap(x, y, d=1.2):
    r = a('shell', 'input', 'tap', str(x), str(y))
    time.sleep(d)
    return r

def ss(name):
    a('shell', 'screencap', '-p', f'/sdcard/{name}.png')
    a('pull', f'/sdcard/{name}.png', f'{name}.png')
    print(f'[ss] {name}.png saved')

def key(code):
    a('shell', 'input', 'keyevent', str(code))
    time.sleep(0.8)

# Try 1: Tap at different y positions for the button
print('Method 1: Tapping at different y positions...')
for y in [1480, 1495, 1505, 1515, 1525]:
    r = tap(413, y, 0.3)
    print(f'  tap(413, {y}) exit={r.returncode}')

ss('method1')

# Method 2: ENTER key  
print('\nMethod 2: ENTER key...')
key(66)  # ENTER
ss('method2_enter')

# Method 3: Try the tap with debug (check if touch registered)
print('\nMethod 3: Check UIAutomator with pointer overlay...')
import re
a('shell', 'uiautomator', 'dump', '/sdcard/ui.xml')
raw = atext('shell', 'cat', '/sdcard/ui.xml')
texts_all = re.findall(r'text="([^"]+)"', raw)
bounds_all = re.findall(r'text="([^"]+)"[^>]+bounds="(\[\d+,\d+\]\[\d+,\d+\])"', raw)
print(f'UIAutomator texts count: {len(texts_all)}')
print('All:', texts_all[:20])
for t, b in bounds_all:
    print(f'  "{t}" => {b}')

# Method 4: Back key to exit tutorial
print('\nMethod 4: Back key...')
key(4)  # BACK
ss('method4_back')

import re
a('shell', 'uiautomator', 'dump', '/sdcard/ui.xml')
raw = atext('shell', 'cat', '/sdcard/ui.xml')
texts_all = re.findall(r'text="([^"]+)"', raw)
print('After back:', texts_all[:10])
