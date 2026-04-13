import subprocess, time

ADB = r'C:\Program Files\BlueStacks_nxt\HD-Adb.exe'
DEV = '127.0.0.1:5555'

def a(*args, t=8):
    return subprocess.run([ADB, '-s', DEV] + list(args), capture_output=True, timeout=t)
def atext(*args, t=8):
    r = subprocess.run([ADB, '-s', DEV] + list(args), capture_output=True, timeout=t)
    return r.stdout.decode('utf-8', errors='replace')
def ss(n):
    a('shell', 'screencap', '-p', f'/sdcard/{n}.png')
    a('pull', f'/sdcard/{n}.png', f'{n}.png')

# Pull all txt files
files_list = atext('shell', 'ls', '/sdcard/Download/NovelFever/')
for fname in files_list.strip().split('\n'):
    fname = fname.strip()
    if fname.endswith('.txt'):
        local = fname.replace('/', '_').replace(':', '_')
        a('pull', f'/sdcard/Download/NovelFever/{fname}', f'pulled_{local}')

# Show content of each pulled file
import os
for f in os.listdir('.'):
    if f.startswith('pulled_') and f.endswith('.txt'):
        size = os.path.getsize(f)
        with open(f, 'rb') as fh:
            content = fh.read()
        try:
            text = content.decode('utf-8')
        except:
            text = content.decode('utf-8', errors='replace')
        print(f'\n=== {f} ({size} bytes) ===')
        print(text[:400])
        print('...' if len(text) > 400 else '')
