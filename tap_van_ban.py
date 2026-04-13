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

# Show UIAutomator for current dialog
a('shell', 'uiautomator', 'dump', '/sdcard/ui.xml')
ui = atext('shell', 'cat', '/sdcard/ui.xml')
nodes = re.findall(r'text="([^"]*)"[^/]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', ui)
print('UI nodes:')
for name, x1, y1, x2, y2 in nodes:
    cx, cy = (int(x1)+int(x2))//2, (int(y1)+int(y2))//2
    print(f'  "{name}" @ [{x1},{y1}][{x2},{y2}] -> ({cx},{cy})')

# Dialog: "Chọn định dạng xuất" with:
#   "Văn bản (TXT/EPUB)"  ← we want this
#   "Dữ liệu (Database)"
# Based on screenshot: dialog center around (400, 742) for văn bản
# Try to find via UIAutomator first, fallback to screenshot coordinates

van_ban_pos = None
for name, x1, y1, x2, y2 in nodes:
    if 'Văn bản' in name or 'TXT' in name or 'EPUB' in name or 'van ban' in name.lower():
        van_ban_pos = ((int(x1)+int(x2))//2, (int(y1)+int(y2))//2)
        print(f'\n** FOUND "Văn bản" at {van_ban_pos} **')
        break

if not van_ban_pos:
    # Fallback: from screenshot the dialog appears between y=655 and y=850
    # "Văn bản (TXT/EPUB)" appears to be at roughly y=742
    van_ban_pos = (400, 742)
    print(f'\nUsing fallback position: {van_ban_pos}')

print(f'\nTapping "Văn bản (TXT/EPUB)" at {van_ban_pos}...')
tap(van_ban_pos[0], van_ban_pos[1], 3.0)
ss('after_van_ban_choice')

# Monitor files
for i in range(1, 7):
    files = atext('shell', 'ls', '-la', '/sdcard/Download/NovelFever/')
    print(f'\n=== {i*5}s after tap ===')
    print(files)
    if i < 6:
        time.sleep(5)

# Also check UI state
a('shell', 'uiautomator', 'dump', '/sdcard/ui2.xml')
ui2 = atext('shell', 'cat', '/sdcard/ui2.xml')
texts2 = re.findall(r'text="([^"]+)"', ui2)
print('\nUI texts after:', texts2[:15])
