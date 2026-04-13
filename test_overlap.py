"""Test overlap optimizations: skip close-menu sleep, dump to faster location."""
import sys, time
sys.path.insert(0, ".")
from mtc.adb import AdbController, _normalize_xml_dump

ADB = r"C:\Program Files\BlueStacks_nxt\HD-Adb.exe"
DEV = "127.0.0.1:5555"
adb = AdbController(ADB, DEV)

w, h = adb.screen_size()
mx, my = w // 2, int(h * 0.75)
nx, ny = adb._reader_nav_point("next")
cx, cy = int(w * 0.933), int(h * 0.305)

# Verify we're in reader
xml = adb.dump_ui()
p = adb._extract_reader_payload(xml)
if not p:
    print("NOT IN READER!")
    sys.exit(1)
print(f"Start: ch{p.get('chapter_index')} - {p.get('title','?')[:60]}")

def test_config(name, shell_cmd, count=5):
    """Test a config string for `count` chapters."""
    results = []
    successes = 0
    for i in range(count):
        before_xml = adb._dump_ui_fast()
        before = adb._extract_reader_payload(before_xml)
        bt = before.get("title", "?") if before else "?"

        t0 = time.perf_counter()
        out, err = adb._cmd("shell", shell_cmd, timeout=15)
        merged = (out or "") + (err or "")
        xml = ""
        if "<hierarchy" in merged:
            xml = _normalize_xml_dump(merged)
        # If menu still visible, close and redump
        if xml and adb._reader_menu_visible(xml):
            adb.tap(cx, cy)
            time.sleep(0.1)
            xml = adb._dump_ui_fast()
        result = adb._extract_reader_payload(xml) if xml else None
        t1 = time.perf_counter()

        ms = (t1 - t0) * 1000
        results.append(ms)

        if result and result.get("title") != bt:
            successes += 1
            at = result.get("title", "?")[:60]
            tl = len(result.get("text", ""))
            print(f"  #{i+1}: {ms:.0f}ms OK | {at} | {tl}ch")
        else:
            at = result.get("title", "?")[:60] if result else "NONE"
            print(f"  #{i+1}: {ms:.0f}ms FAIL | still={at}")

    avg = sum(results) / len(results)
    print(f"  >> {name}: avg={avg:.0f}ms, success={successes}/{count}\n")
    return avg, successes

# === Test 1: Dump to /data/local/tmp vs /sdcard ===
print("\n=== Benchmark: dump location ===")
for loc in ["/sdcard/_ui.xml", "/data/local/tmp/_ui.xml"]:
    times = []
    for _ in range(3):
        t0 = time.perf_counter()
        out, err = adb._cmd("shell",
            f"uiautomator dump --compressed {loc} 2>/dev/null; cat {loc}",
            timeout=8)
        t1 = time.perf_counter()
        merged = (out or "") + (err or "")
        ok = "<hierarchy" in merged
        times.append((t1-t0)*1000)
    avg = sum(times)/len(times)
    print(f"  {loc}: avg={avg:.0f}ms ({', '.join(f'{t:.0f}' for t in times)})")

# === Test 2: Overlap close-menu with dump (no sleep after close) ===
print("\n=== Config A: 0.2/0.25/NO_CLOSE_SLEEP (5 ch) ===")
cmd_a = (
    f"input tap {mx} {my}; sleep 0.2; "
    f"input tap {nx} {ny}; sleep 0.25; "
    f"input tap {cx} {cy}; "  # NO sleep after close!
    "uiautomator dump --compressed /data/local/tmp/_ui.xml 2>/dev/null; "
    "cat /data/local/tmp/_ui.xml"
)
test_config("A: 0.2/0.25/no_close", cmd_a, 5)

# === Test 3: Aggressive overlap (0.2/0.15/no_close) ===
print("=== Config B: 0.2/0.15/NO_CLOSE_SLEEP (5 ch) ===")
cmd_b = (
    f"input tap {mx} {my}; sleep 0.2; "
    f"input tap {nx} {ny}; sleep 0.15; "
    f"input tap {cx} {cy}; "
    "uiautomator dump --compressed /data/local/tmp/_ui.xml 2>/dev/null; "
    "cat /data/local/tmp/_ui.xml"
)
test_config("B: 0.2/0.15/no_close", cmd_b, 5)

# === Test 4: Ultra aggressive (0.15/0.1/no_close) ===
print("=== Config C: 0.15/0.1/NO_CLOSE_SLEEP (5 ch) ===")
cmd_c = (
    f"input tap {mx} {my}; sleep 0.15; "
    f"input tap {nx} {ny}; sleep 0.1; "
    f"input tap {cx} {cy}; "
    "uiautomator dump --compressed /data/local/tmp/_ui.xml 2>/dev/null; "
    "cat /data/local/tmp/_ui.xml"
)
test_config("C: 0.15/0.1/no_close", cmd_c, 5)

# === Test 5: Use `input touchscreen tap` (might be faster) ===
print("=== Config D: 0.2/0.2/no_close + /data/local/tmp (5 ch) ===")
cmd_d = (
    f"input tap {mx} {my}; sleep 0.2; "
    f"input tap {nx} {ny}; sleep 0.2; "
    f"input tap {cx} {cy}; "
    "uiautomator dump --compressed /data/local/tmp/_ui.xml 2>/dev/null; "
    "cat /data/local/tmp/_ui.xml"
)
test_config("D: 0.2/0.2/no_close", cmd_d, 5)

print("Done!")
