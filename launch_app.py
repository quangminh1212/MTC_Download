import sys, time, subprocess
sys.path.insert(0, '.')
from mtc.adb import AdbController

ADB = r'C:\Program Files\BlueStacks_nxt\HD-Adb.exe'
DEVICE = '127.0.0.1:5555'

adb = AdbController(ADB, DEVICE)
adb.ensure_device()

def adb_shell(cmd):
    r = subprocess.run([ADB, '-s', DEVICE, 'shell'] + cmd.split(), capture_output=True, text=True)
    return r.stdout + r.stderr

def screencap(name='sc.png'):
    adb_shell(f'screencap -p /sdcard/{name}')
    subprocess.run([ADB, '-s', DEVICE, 'pull', f'/sdcard/{name}', name])

# Launch app
print("Launching MTC app...")
adb_shell('am start -n com.novelfever.app.android/com.novelfever.app.android.MainActivity')
time.sleep(4)

screencap('app_launch.png')
xml = adb.dump_ui()
texts = adb.get_all_text(xml)
print("App launched. Texts:", texts[:15])

w, h = adb.screen_size()
print(f"Screen: {w}x{h}")
