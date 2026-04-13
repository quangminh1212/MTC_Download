"""Test turbo advance from current reader position."""
import sys, time
sys.path.insert(0, ".")
from mtc.adb import AdbController

adb = AdbController(r"C:\Program Files\BlueStacks_nxt\HD-Adb.exe", "127.0.0.1:5555")

for i in range(5):
    t0 = time.perf_counter()
    r = adb.turbo_advance_and_read()
    t1 = time.perf_counter()
    ms = (t1 - t0) * 1000
    if r:
        ci = r.get("chapter_index", "?")
        tt = r.get("title", "?")[:50]
        tl = len(r.get("text", ""))
        print(f"#{i+1}: {ms:.0f}ms | ch{ci} | {tt} | {tl}ch")
    else:
        print(f"#{i+1}: {ms:.0f}ms | FAIL")
