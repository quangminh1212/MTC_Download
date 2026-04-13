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

# Get UIAutomator to find XUẤT TẤT CẢ button bounds
a('shell', 'uiautomator', 'dump', '/sdcard/ui.xml')
ui = atext('shell', 'cat', '/sdcard/ui.xml')

# Find all buttons with bounds
nodes = re.findall(r'text="([^"]*)"[^/]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', ui)
print('Buttons found:')
for name, x1, y1, x2, y2 in nodes:
    cx, cy = (int(x1)+int(x2))//2, (int(y1)+int(y2))//2
    print(f'  "{name}" @ [{x1},{y1}][{x2},{y2}] -> center ({cx},{cy})')

# Find XUẤT TẤT CẢ
xuat_tat_ca = None
for name, x1, y1, x2, y2 in nodes:
    if 'XUẤT TẤT CẢ' in name or 'XUAT TAT CA' in name.upper() or 'TẤT CẢ' in name:
        xuat_tat_ca = ((int(x1)+int(x2))//2, (int(y1)+int(y2))//2)
        print(f'\n** FOUND XUẤT TẤT CẢ at {xuat_tat_ca} **')

if xuat_tat_ca:
    print(f'\nTapping XUẤT TẤT CẢ at {xuat_tat_ca}...')
    tap(xuat_tat_ca[0], xuat_tat_ca[1], 5.0)
    ss('after_xuat_tat_ca')
    
    print('\nChecking export directory (5s)...')
    files = atext('shell', 'ls', '-la', '/sdcard/Download/NovelFever/')
    print(files)
    
    # Wait and check again
    print('Waiting 15 more seconds...')
    time.sleep(15)
    ss('after_xuat_tat_ca_2')
    files2 = atext('shell', 'ls', '-la', '/sdcard/Download/NovelFever/')
    print('After 20s total:')
    print(files2)
    
    # Get UI state
    a('shell', 'uiautomator', 'dump', '/sdcard/ui2.xml')
    ui2 = atext('shell', 'cat', '/sdcard/ui2.xml')
    texts2 = re.findall(r'text="([^"]+)"', ui2)
    print('UI texts after:', texts2[:15])
else:
    print('\nXUẤT TẤT CẢ NOT found - trying fallback tap at (693, 1337)')
    tap(693, 1337, 5.0)
    ss('after_xuat_fallback')
    files = atext('shell', 'ls', '-la', '/sdcard/Download/NovelFever/')
    print(files)
