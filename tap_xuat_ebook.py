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
def ss(n):
    a('shell', 'screencap', '-p', f'/sdcard/{n}.png')
    a('pull', f'/sdcard/{n}.png', f'{n}.png')

# Before state
print('=== Before XUẤT EBOOK ===')
files_before = atext('shell', 'ls', '-la', '/sdcard/Download/NovelFever/')
print(files_before)

# Tap XUẤT EBOOK at (450, 889)
print('\nTapping XUẤT EBOOK at (450, 889)...')
tap(450, 889, 3.0)

ss('after_xuat_ebook_1')
print('\n=== After tap (3s) ===')
files1 = atext('shell', 'ls', '-la', '/sdcard/Download/NovelFever/')
print(files1)

# Get UIAutomator to see what's on screen
xml = atext('shell', 'uiautomator', 'dump', '/sdcard/ui.xml', t=10)
atext('shell', 'cat', '/sdcard/ui.xml')
ui = atext('shell', 'cat', '/sdcard/ui.xml')
# Extract text nodes
texts = re.findall(r'text="([^"]+)"', ui)
print('\nUI texts:', texts[:20])

# Wait 5 more seconds
print('\nWaiting 5s...')
time.sleep(5)
ss('after_xuat_ebook_2')
files2 = atext('shell', 'ls', '-la', '/sdcard/Download/NovelFever/')
print('\n=== After tap (8s total) ===')
print(files2)

# Wait again
print('\nWaiting 10 more seconds...')
time.sleep(10)
files3 = atext('shell', 'ls', '-la', '/sdcard/Download/NovelFever/')
print('\n=== After tap (18s total) ===')
print(files3)

# List full sdcard/Download too
print('\n=== /sdcard/Download/ ===')
print(atext('shell', 'ls', '-la', '/sdcard/Download/'))
