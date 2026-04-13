"""
Quick script: dismiss reader tutorial, then explore reader menu.
"""
import subprocess, time

ADB = r'C:\Program Files\BlueStacks_nxt\HD-Adb.exe'
DEV = '127.0.0.1:5555'

def a(*args, t=5):
    return subprocess.run([ADB, '-s', DEV] + list(args), capture_output=True, timeout=t)

def atext(*args, t=5):
    r = subprocess.run([ADB, '-s', DEV] + list(args), capture_output=True, timeout=t)
    return r.stdout.decode('utf-8', errors='replace')

def tap(x, y, d=1.2):
    a('shell', 'input', 'tap', str(x), str(y))
    time.sleep(d)

def ss(n):
    a('shell', 'screencap', '-p', f'/sdcard/{n}.png')
    a('pull', f'/sdcard/{n}.png', f'{n}.png')
    print(f'[ss] {n}.png')

# Tap "DA HIEU" button 
print('Tapping DA HIEU button at (413, 1495)...')
tap(413, 1495, 1.5)
ss('after_da_hieu')

# Now tap center of screen to show reader overlay
print('Tapping center (450, 800) to open reader menu...')
tap(450, 800, 1.5)
ss('reader_menu_overlay')

# Tap bottom-right area (settings gear icon at ~(795, 50))
print('Also checking gear icon at (795, 50)...')
import re
a('shell', 'uiautomator', 'dump', '/sdcard/ui.xml')
raw = atext('shell', 'cat', '/sdcard/ui.xml')
texts = re.findall(r'text="([^"]+)"', raw)
bounds = re.findall(r'text="([^"]+)"[^>]+bounds="(\[\d+,\d+\]\[\d+,\d+\])"', raw)
print(f'UI texts: {texts[:20]}')
for t, b in bounds:
    print(f'  "{t}" @ {b}')
