import ctypes
import sys
import os

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

if not is_admin():
    script = os.path.abspath(__file__)
    params = f'"{script}"'
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    sys.exit(0)

import threading
from PIL import ImageGrab
from datetime import datetime
from pathlib import Path
from pynput import keyboard as pk

OUT = Path('screenshots')
OUT.mkdir(exist_ok=True)

def shot(reason: str):
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    fn = OUT / f'screenshot_{ts}_{reason}.png'
    ImageGrab.grab().save(fn)
    print(f'[OK] {fn}', flush=True)

WIN = {pk.Key.cmd, pk.Key.cmd_l, pk.Key.cmd_r}
SHIFT = {pk.Key.shift, pk.Key.shift_l, pk.Key.shift_r}
held = set()

def on_press(key):
    held.add(key)
    if (key == pk.KeyCode.from_char('s') or key == pk.KeyCode.from_char('S')) \
            and (held & WIN) and (held & SHIFT):
        shot('win_shift_s')
        return False  # stop listener to suppress Windows default
    if key == pk.Key.print_screen:
        shot('printscreen')
        return False

def on_release(key):
    if key in held:
        held.discard(key)

print('READY. Hotkeys: Win+Shift+S | PrintScreen | ESC=quit', flush=True)

# run pynput listener in a thread, restart after each trigger
import keyboard  # for ESC-wait only
while True:
    with pk.Listener(on_press=on_press, on_release=on_release, suppress=True) as listener:
        listener.join()
    if keyboard.is_pressed('esc'):
        break
print('Bye.', flush=True)
