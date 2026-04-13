import subprocess, time, re, shlex

ADB = r'C:\Program Files\BlueStacks_nxt\HD-Adb.exe'
DEV = '127.0.0.1:5555'

def run_adb(args, timeout=8):
    cmd = [ADB, '-s', DEV] + list(args)
    print(f'\n=== RUNNING ADB: {shlex.join(cmd)} (timeout={timeout}s) ===')
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        print(f'ERROR: ADB command timed out after {timeout}s')
        print('COMMAND:', shlex.join(cmd))
        print('stdout:', e.stdout)
        print('stderr:', e.stderr)
        return None
    print('RETURN CODE:', r.returncode)
    if r.returncode != 0:
        print('WARNING: adb command exited with non-zero return code')
    if r.stdout:
        print('STDOUT:')
        print(r.stdout)
    if r.stderr:
        print('STDERR:')
        print(r.stderr)
    return r

def a(*args, t=8):
    return run_adb(list(args), timeout=t)

def atext(*args, t=8):
    r = run_adb(list(args), timeout=t)
    if r is None:
        return ''
    return r.stdout

def tap(x, y, d=1.5):
    print(f'>>> tap({x}, {y}) and sleep {d}s')
    a('shell', 'input', 'tap', str(x), str(y))
    time.sleep(d)

def ss(n):
    print(f'>>> screenshot {n}.png from device')
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
