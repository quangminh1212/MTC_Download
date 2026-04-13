"""Comprehensive speed optimization test for turbo chapter advancing.

Tests:
1. Dump location: /sdcard/ vs /data/local/tmp/
2. Overlap: skip close-menu sleep (overlap with uiautomator)
3. Skip close-menu tap entirely (extract from XML with menu visible)
4. Swipe-left to advance chapter (skip menu entirely!)
5. sendevent for faster taps
"""
import sys, time, subprocess
sys.path.insert(0, ".")
from mtc.adb import AdbController, _normalize_xml_dump

ADB = r"C:\Program Files\BlueStacks_nxt\HD-Adb.exe"
DEV = "127.0.0.1:5555"
adb = AdbController(ADB, DEV)

w, h = adb.screen_size()
mx, my = w // 2, int(h * 0.75)           # menu open
nx, ny = adb._reader_nav_point("next")   # next chapter
cx, cy = int(w * 0.933), int(h * 0.305)  # close menu

print(f"Screen: {w}×{h} | menu=({mx},{my}) next=({nx},{ny}) close=({cx},{cy})")

# Verify we're in reader with a numbered chapter
xml = adb.dump_ui()
p = adb._extract_reader_payload(xml)
if not p or p.get("chapter_index") is None:
    print(f"NOT IN A NUMBERED CHAPTER! Got: {p}")
    print("Navigate to a chapter first (not intro page).")
    sys.exit(1)
print(f"Start: ch{p['chapter_index']} - {p.get('title','?')[:60]}\n")


def run_test(name, shell_cmd, count=5, extract_with_menu=False):
    """Run a speed test config for `count` chapters."""
    results = []
    successes = 0
    for i in range(count):
        # Get current chapter before advancing
        before_xml = adb._dump_ui_fast()
        before = adb._extract_reader_payload(before_xml)
        bt = before.get("title", "?") if before else "?"

        t0 = time.perf_counter()
        out, err = adb._cmd("shell", shell_cmd, timeout=15)
        merged = (out or "") + (err or "")
        xml = ""
        if "<hierarchy" in merged:
            xml = _normalize_xml_dump(merged)

        result = None
        if xml:
            if extract_with_menu:
                # Try extracting even with menu visible
                result = adb._extract_reader_payload(xml)
            else:
                if adb._reader_menu_visible(xml):
                    adb.tap(cx, cy)
                    time.sleep(0.1)
                    xml = adb._dump_ui_fast()
                result = adb._extract_reader_payload(xml)
        t1 = time.perf_counter()

        ms = (t1 - t0) * 1000
        results.append(ms)

        if result and result.get("title") != bt and len(result.get("text", "")) >= 50:
            successes += 1
            ci = result.get("chapter_index", "?")
            tl = len(result.get("text", ""))
            print(f"  #{i+1}: {ms:.0f}ms OK | ch{ci} | {tl}ch")
        else:
            at = result.get("title", "?")[:60] if result else "NONE"
            tl = len(result.get("text", "")) if result else 0
            print(f"  #{i+1}: {ms:.0f}ms FAIL | {at} | {tl}ch")

    avg = sum(results) / len(results) if results else 0
    print(f"  >> {name}: avg={avg:.0f}ms, success={successes}/{count}\n")
    return avg, successes


# ============================================================
# TEST 1: Dump location benchmark (no navigation)
# ============================================================
print("=" * 60)
print("TEST 1: Dump location (/sdcard vs /data/local/tmp)")
print("=" * 60)
for loc in ["/sdcard/_ui.xml", "/data/local/tmp/_ui.xml"]:
    times = []
    for _ in range(5):
        t0 = time.perf_counter()
        out, err = adb._cmd("shell",
            f"uiautomator dump --compressed {loc} 2>/dev/null; cat {loc}",
            timeout=8)
        t1 = time.perf_counter()
        merged = (out or "") + (err or "")
        ok = "<hierarchy" in merged
        times.append((t1 - t0) * 1000)
    avg = sum(times) / len(times)
    print(f"  {loc}: avg={avg:.0f}ms ({', '.join(f'{t:.0f}' for t in times)}) ok={ok}")
print()


# ============================================================
# TEST 2: Current best (0.2/0.25/no_close_sleep)
# ============================================================
print("=" * 60)
print("TEST 2: 0.2/0.25/no_close_sleep + /data/local/tmp (5 ch)")
print("=" * 60)
cmd2 = (
    f"input tap {mx} {my}; sleep 0.2; "
    f"input tap {nx} {ny}; sleep 0.25; "
    f"input tap {cx} {cy}; "
    "uiautomator dump --compressed /data/local/tmp/_ui.xml 2>/dev/null; "
    "cat /data/local/tmp/_ui.xml"
)
run_test("T2: 0.2/0.25/no_close", cmd2)


# ============================================================
# TEST 3: Skip close-menu tap entirely (extract with menu visible)
# ============================================================
print("=" * 60)
print("TEST 3: 0.2/0.25/NO_CLOSE_TAP (extract from menu XML) (5 ch)")
print("=" * 60)
cmd3 = (
    f"input tap {mx} {my}; sleep 0.2; "
    f"input tap {nx} {ny}; sleep 0.25; "
    # NO close tap at all! Dump with menu overlay still showing
    "uiautomator dump --compressed /data/local/tmp/_ui.xml 2>/dev/null; "
    "cat /data/local/tmp/_ui.xml"
)
run_test("T3: no_close_tap", cmd3, extract_with_menu=True)


# ============================================================
# TEST 4: Swipe-left to advance chapter (skip menu entirely!)
# ============================================================
print("=" * 60)
print("TEST 4: Swipe-left to advance chapter (5 ch)")
print("=" * 60)
# Swipe from right-center to left-center
sx1, sy1 = int(w * 0.85), h // 2   # start: right side
sx2, sy2 = int(w * 0.15), h // 2   # end: left side
cmd4 = (
    f"input swipe {sx1} {sy1} {sx2} {sy2} 150; sleep 0.3; "
    "uiautomator dump --compressed /data/local/tmp/_ui.xml 2>/dev/null; "
    "cat /data/local/tmp/_ui.xml"
)
run_test("T4: swipe-left", cmd4, extract_with_menu=True)


# ============================================================
# TEST 5: find sendevent device for faster taps
# ============================================================
print("=" * 60)
print("TEST 5: sendevent device discovery")
print("=" * 60)
out, err = adb._cmd("shell", "ls /dev/input/", timeout=5)
print(f"  Input devices: {(out or '').strip()}")

out, err = adb._cmd("shell", "getevent -il 2>&1 | head -40", timeout=5)
print(f"  getevent info:\n{(out or '')[:500]}")

# Try to find touch device by checking which one handles ABS_MT_POSITION_X
out, err = adb._cmd("shell", "getevent -il 2>&1 | grep -B5 ABS_MT_POSITION | head -20", timeout=5)
print(f"\n  Touch device:\n{(out or '')[:500]}")


# ============================================================
# TEST 6: Aggressive timing (0.15/0.2/no_close)
# ============================================================
print("=" * 60)
print("TEST 6: Aggressive 0.15/0.2/no_close + /data/local/tmp (5 ch)")
print("=" * 60)
cmd6 = (
    f"input tap {mx} {my}; sleep 0.15; "
    f"input tap {nx} {ny}; sleep 0.2; "
    f"input tap {cx} {cy}; "
    "uiautomator dump --compressed /data/local/tmp/_ui.xml 2>/dev/null; "
    "cat /data/local/tmp/_ui.xml"
)
run_test("T6: 0.15/0.2/no_close", cmd6)


# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("DONE - review results above for best config")
print("=" * 60)
