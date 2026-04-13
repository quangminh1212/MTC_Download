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

# "Văn bản (TXT/EPUB)" is at [39,780][861,852] -> center (450, 816)
print('Tapping "Văn bản (TXT/EPUB)" at (450, 816)...')
tap(450, 816, 5.0)
ss('after_van_ban_816')

print('\nDirectory listing (5s after):')
files = atext('shell', 'ls', '-la', '/sdcard/Download/NovelFever/')
print(files)

# Check UI state
a('shell', 'uiautomator', 'dump', '/sdcard/ui.xml')
ui = atext('shell', 'cat', '/sdcard/ui.xml')
texts = re.findall(r'text="([^"]+)"', ui)
print('UI texts:', texts[:20])

# Wait and check files appearing
print('\nWaiting 30 more seconds...')
for i in range(6):
    time.sleep(5)
    files = atext('shell', 'ls', '-la', '/sdcard/Download/NovelFever/')
    # Look for any new files
    lines = [l for l in files.split('\n') if l.strip() and 'total' not in l and '.' not in l.split()[-1:] or '.txt' in l]
    new_files = [l for l in files.split('\n') if l.strip() and '2026-04-13' in l]
    if new_files:
        print(f'\n** NEW FILES FOUND at {(i+1)*5}s:')
        for f in new_files:
            print(' ', f)
    else:
        print(f'{(i+1)*5}s: no new files yet')

print('\nFinal directory:')
print(atext('shell', 'ls', '-la', '/sdcard/Download/NovelFever/'))
