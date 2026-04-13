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

# Dump raw XML to understand structure
a('shell', 'uiautomator', 'dump', '/sdcard/ui.xml')
ui = atext('shell', 'cat', '/sdcard/ui.xml')

# Print all nodes with non-empty text
print('=== All nodes ===')
# Match any node with text and bounds
all_nodes = re.findall(r'<node[^>]*text="([^"]*)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', ui)
for name, x1, y1, x2, y2 in all_nodes:
    print(f'  TEXT="{name[:50]}" bounds=[{x1},{y1}][{x2},{y2}]')

# Also try reversed order (bounds before text)
all_nodes2 = re.findall(r'<node[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"[^>]*text="([^"]*)"', ui)
print('\n=== bounds before text ===')
for x1, y1, x2, y2, name in all_nodes2:
    print(f'  TEXT="{name[:50]}" bounds=[{x1},{y1}][{x2},{y2}]')

# Print raw XML snippet for the dialog container
idx = ui.find('Văn bản')
if idx > 0:
    snippet = ui[max(0, idx-300):idx+300]
    print(f'\n=== XML near "Văn bản" ===')
    print(snippet)
else:
    # Print last 1000 chars
    print('\n=== Last 1000 chars of XML ===')
    print(ui[-1000:])
