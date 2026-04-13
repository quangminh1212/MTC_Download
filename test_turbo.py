"""Test persistent ADB shell to eliminate subprocess overhead."""
import sys, time, subprocess, threading, queue
sys.path.insert(0, ".")
from mtc.adb import AdbController, _normalize_xml_dump

ADB = r"C:\Program Files\BlueStacks_nxt\HD-Adb.exe"
DEV = "127.0.0.1:5555"
MARKER = "___END_MARKER___"


class PersistentShell:
    """Keep a single adb shell subprocess alive, send commands via stdin."""

    def __init__(self, adb_path, device):
        cmd = [adb_path, "-s", device, "shell"]
        self.proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        self._q = queue.Queue()
        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()
        # Warm up
        self.run("echo READY")

    def _read_loop(self):
        buf = b""
        while True:
            try:
                chunk = self.proc.stdout.read(4096)
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    self._q.put(line.decode("utf-8", errors="replace").rstrip("\r"))
            except:
                break

    def run(self, command: str, timeout: float = 15.0) -> str:
        """Run command and collect output until marker line appears."""
        marker_cmd = f'{command}; echo {MARKER}\n'
        self.proc.stdin.write(marker_cmd.encode())
        self.proc.stdin.flush()

        lines = []
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                line = self._q.get(timeout=0.5)
                if MARKER in line:
                    break
                lines.append(line)
            except queue.Empty:
                continue
        return "\n".join(lines)

    def close(self):
        try:
            self.proc.stdin.write(b"exit\n")
            self.proc.stdin.flush()
            self.proc.wait(timeout=3)
        except:
            self.proc.kill()


# Navigate to reader first
adb = AdbController(ADB, DEV)
adb.go_back()
time.sleep(0.5)

xml = adb.dump_ui()
payload = adb._extract_reader_payload(xml)
if not payload:
    print("Not in reader, navigating...")
    adb._cmd("shell", "monkey -p com.novelfever.app.android -c android.intent.category.LAUNCHER 1")
    time.sleep(3)
    adb.scroll_to_top()
    adb.tap(450, 350)
    time.sleep(2)
    payload = adb._extract_reader_payload(adb.dump_ui())
    if not payload:
        print("FAIL: Cannot get to reader")
        sys.exit(1)

print(f"In reader: {payload.get('title', '?')}")

# Now open persistent shell
print("\nOpening persistent ADB shell...")
shell = PersistentShell(ADB, DEV)

w, h = adb.screen_size()
mx, my = w // 2, int(h * 0.75)
nx, ny = adb._reader_nav_point("next")
cx, cy = int(w * 0.933), int(h * 0.305)

# Benchmark: single tap via persistent shell vs subprocess
print("\n=== Benchmark: persistent shell vs subprocess ===")
for i in range(3):
    t0 = time.perf_counter()
    shell.run(f"input tap {mx} 800")
    t1 = time.perf_counter()

    t2 = time.perf_counter()
    adb.sh("input", "tap", str(mx), "800")
    t3 = time.perf_counter()

    print(f"  #{i+1}: persistent={1000*(t1-t0):.0f}ms  subprocess={1000*(t3-t2):.0f}ms")

# Test turbo via persistent shell
print("\n=== Turbo via persistent shell (5 chapters) ===")
results = []
for i in range(5):
    before_xml = adb._dump_ui_fast()
    before = adb._extract_reader_payload(before_xml)
    bt = before.get("title", "?") if before else "?"

    t0 = time.perf_counter()
    # All taps + sleeps via persistent shell (no subprocess overhead per command)
    shell.run(f"input tap {mx} {my}; sleep 0.2; input tap {nx} {ny}; sleep 0.25; input tap {cx} {cy}; sleep 0.1")
    # Still need subprocess for dump (needs stdout data)
    xml = adb._dump_ui_fast()
    result = adb._extract_reader_payload(xml)
    t1 = time.perf_counter()

    ms = (t1 - t0) * 1000
    results.append(ms)

    if result and result.get("title") != bt:
        at = result.get("title", "?")
        tl = len(result.get("text", ""))
        print(f"  #{i+1}: {bt} -> {at} | {ms:.0f}ms | {tl} chars")
    else:
        at = result.get("title", "?") if result else "NONE"
        print(f"  #{i+1}: {bt} -> {at} | {ms:.0f}ms | SAME/FAIL")

if results:
    print(f"\nAvg: {sum(results)/len(results):.0f}ms")
    print(f"Min: {min(results):.0f}ms  Max: {max(results):.0f}ms")

# Try full all-in-one via persistent shell (taps + dump)
print("\n=== Full all-in-one via persistent shell (5 chapters) ===")
results2 = []
for i in range(5):
    before_xml = adb._dump_ui_fast()
    before = adb._extract_reader_payload(before_xml)
    bt = before.get("title", "?") if before else "?"

    t0 = time.perf_counter()
    cmd = (
        f"input tap {mx} {my}; sleep 0.2; "
        f"input tap {nx} {ny}; sleep 0.25; "
        f"input tap {cx} {cy}; sleep 0.1; "
        "uiautomator dump --compressed /sdcard/_ui.xml 2>/dev/null; "
        "cat /sdcard/_ui.xml"
    )
    raw = shell.run(cmd, timeout=10)
    xml = _normalize_xml_dump(raw) if "<hierarchy" in raw else ""
    result = adb._extract_reader_payload(xml) if xml else None
    t1 = time.perf_counter()

    ms = (t1 - t0) * 1000
    results2.append(ms)

    if result and result.get("title") != bt:
        at = result.get("title", "?")
        tl = len(result.get("text", ""))
        print(f"  #{i+1}: {bt} -> {at} | {ms:.0f}ms | {tl} chars")
    else:
        at = result.get("title", "?") if result else "NONE"
        print(f"  #{i+1}: {bt} -> {at} | {ms:.0f}ms | SAME/FAIL")

if results2:
    print(f"\nAvg: {sum(results2)/len(results2):.0f}ms")
    print(f"Min: {min(results2):.0f}ms  Max: {max(results2):.0f}ms")

shell.close()
print("\nDone!")
"""Test reduced sleeps in turbo. Need to find minimum reliable sleeps."""
import sys, time, subprocess
sys.path.insert(0, ".")
from mtc.adb import AdbController

adb = AdbController(r"C:\Program Files\BlueStacks_nxt\HD-Adb.exe", "127.0.0.1:5555")

# First go back to close the menu that's open
adb.go_back()
time.sleep(0.5)

# Check we're in reader
xml = adb.dump_ui()
payload = adb._extract_reader_payload(xml)
if not payload:
    print("NOT in reader!")
    # Launch app and navigate
    adb._cmd("shell", "monkey -p com.novelfever.app.android -c android.intent.category.LAUNCHER 1")
    time.sleep(3)
    adb.scroll_to_top()
    # Tap first novel
    adb.tap(450, 350)
    time.sleep(2)
    payload = adb._extract_reader_payload(adb.dump_ui())
    if not payload:
        print("Still not in reader!")
        sys.exit(1)

print(f"Starting at: {payload.get('title','?')}")

# Test different sleep configs
configs = [
    ("0.2/0.25/0.1", "0.2", "0.25", "0.1"),
    ("0.15/0.2/0.1", "0.15", "0.2", "0.1"),
    ("0.25/0.3/0.1", "0.25", "0.3", "0.1"),
]

w, h = adb.screen_size()
mx, my = w // 2, int(h * 0.75)
nx, ny = adb._reader_nav_point("next")
cx, cy = int(w * 0.933), int(h * 0.305)

for label, s1, s2, s3 in configs:
    print(f"\n=== Config: {label} (3 chapters) ===")
    results = []
    ok = 0
    for i in range(3):
        before = adb._extract_reader_payload(adb._dump_ui_fast())
        bt = before.get("title", "?") if before else "?"

        t0 = time.perf_counter()
        cmd = (
            f"input tap {mx} {my}; sleep {s1}; "
            f"input tap {nx} {ny}; sleep {s2}; "
            f"input tap {cx} {cy}; sleep {s3}; "
            "uiautomator dump --compressed /sdcard/_ui.xml >/dev/null 2>&1; "
            "cat /sdcard/_ui.xml"
        )
        from mtc.adb import _normalize_xml_dump
        out, err = adb._cmd("shell", cmd, timeout=15)
        merged = (out or "") + (err or "")
        xml = _normalize_xml_dump(merged) if "<hierarchy" in merged else ""
        result = adb._extract_reader_payload(xml) if xml else None
        t1 = time.perf_counter()

        ms = (t1 - t0) * 1000
        results.append(ms)

        if result and result.get("title") != bt:
            at = result.get("title", "?")
            ok += 1
            print(f"  #{i+1}: {bt} -> {at} | {ms:.0f}ms | OK")
        else:
            at = result.get("title", "?") if result else "NONE"
            print(f"  #{i+1}: {bt} -> {at} | {ms:.0f}ms | SAME/FAIL")

    avg = sum(results) / len(results)
    print(f"  Avg: {avg:.0f}ms | Success: {ok}/3")
"""Test all-in-one turbo (taps + dump in single subprocess)."""
import sys, time
sys.path.insert(0, ".")
from mtc.adb import AdbController

adb = AdbController(r"C:\Program Files\BlueStacks_nxt\HD-Adb.exe", "127.0.0.1:5555")

# Verify we're in reader
xml = adb.dump_ui()
payload = adb._extract_reader_payload(xml)
if not payload:
    print("NOT in reader! Launch app first.")
    sys.exit(1)
print(f"Starting at: {payload.get('title','?')}")

print("\n=== All-in-one turbo test (10 chapters) ===")
results = []
for i in range(10):
    before = adb._extract_reader_payload(adb._dump_ui_fast())
    bt = before.get("title", "?") if before else "?"

    t0 = time.perf_counter()
    result = adb.turbo_advance_and_read()
    t1 = time.perf_counter()

    ms = (t1 - t0) * 1000
    results.append(ms)

    if result:
        at = result.get("title", "?")
        tl = len(result.get("text", ""))
        print(f"  #{i+1}: {bt} -> {at} | {ms:.0f}ms | {tl} chars")
    else:
        print(f"  #{i+1}: {bt} -> FAILED | {ms:.0f}ms")

print(f"\nAvg: {sum(results)/len(results):.0f}ms")
print(f"Min: {min(results):.0f}ms  Max: {max(results):.0f}ms")
"""Tap first novel to resume, then test turbo."""
import sys, time
sys.path.insert(0, ".")
from mtc.adb import AdbController

ADB = r"C:\Program Files\BlueStacks_nxt\HD-Adb.exe"
DEV = "127.0.0.1:5555"
adb = AdbController(ADB, DEV)

# Step 1: We're at library. Tap the first novel to resume reading.
print("Tapping first novel in library...")
adb.tap(450, 350)  # approximate center of first novel card
time.sleep(2.0)

xml = adb.dump_ui()
payload = adb._extract_reader_payload(xml)
if payload:
    title = payload.get("title", "?")
    tlen = len(payload.get("text", ""))
    ch = payload.get("chapter_index", "?")
    print(f"In reader: ch{ch} - {title} ({tlen} chars)")
else:
    # Maybe we landed on novel detail page, look for "Đọc tiếp" or similar
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(xml)
        texts = [(n.get("text", "") or n.get("content-desc", "")).strip()
                 for n in root.iter()
                 if (n.get("text", "") or n.get("content-desc", "")).strip()]
    except:
        texts = []
    print("Not in reader. Screen:")
    for t in texts[:15]:
        print(f"  {t[:100]}")
    # Try tapping "Đọc tiếp" if visible
    if adb.tap_text("Đọc tiếp", xml):
        print("\nTapped 'Đọc tiếp', waiting...")
        time.sleep(2.0)
        payload = adb._extract_reader_payload(adb.dump_ui())
        if payload:
            print(f"Now in reader: ch{payload.get('chapter_index','?')} - {payload.get('title','?')}")
        else:
            print("Still not in reader!")
            sys.exit(1)
    else:
        print("No 'Đọc tiếp' found")
        sys.exit(1)

print("\n=== Turbo batch test (8 chapters) ===")
results = []
for i in range(8):
    before = adb._extract_reader_payload(adb._dump_ui_fast())
    bt = before.get("title", "?") if before else "?"
    bch = before.get("chapter_index", "?") if before else "?"

    t0 = time.perf_counter()
    result = adb.turbo_advance_and_read()
    t1 = time.perf_counter()

    ms = (t1 - t0) * 1000
    results.append(ms)

    if result:
        at = result.get("title", "?")
        ach = result.get("chapter_index", "?")
        tl = len(result.get("text", ""))
        print(f"  #{i+1}: ch{bch} -> ch{ach} | {ms:.0f}ms | {tl} chars")
    else:
        print(f"  #{i+1}: ch{bch} -> FAILED | {ms:.0f}ms")

print(f"\nAverage: {sum(results)/len(results):.0f}ms")
print(f"Min: {min(results):.0f}ms, Max: {max(results):.0f}ms")
"""Nav to chapter 21 then run turbo test."""
import sys, time
sys.path.insert(0, ".")
from mtc.adb import AdbController

ADB = r"C:\Program Files\BlueStacks_nxt\HD-Adb.exe"
DEV = "127.0.0.1:5555"
adb = AdbController(ADB, DEV)

# Scroll to top
adb.scroll_to_top(max_swipes=5)

print("Navigating to chapter 21...")
adb.nav_to_chapter(chapter_index=21)
time.sleep(1.0)
xml = adb.dump_ui()
payload = adb._extract_reader_payload(xml)
if payload:
    title = payload.get("title", "?")
    tlen = len(payload.get("text", ""))
    print(f"In reader: {title} ({tlen} chars)")
else:
    print("NOT in reader!")
    sys.exit(1)

print("\n=== Turbo batch test (5 chapters) ===")
results = []
for i in range(5):
    before = adb._extract_reader_payload(adb._dump_ui_fast())
    bt = before.get("title", "?") if before else "?"

    t0 = time.perf_counter()
    result = adb.turbo_advance_and_read()
    t1 = time.perf_counter()

    ms = (t1 - t0) * 1000
    results.append(ms)

    if result:
        at = result.get("title", "?")
        tl = len(result.get("text", ""))
        print(f"  #{i+1}: {bt} -> {at} | {ms:.0f}ms | {tl} chars")
    else:
        print(f"  #{i+1}: {bt} -> FAILED | {ms:.0f}ms")

print(f"\nAverage: {sum(results)/len(results):.0f}ms")
print(f"Min: {min(results):.0f}ms, Max: {max(results):.0f}ms")
"""Test optimized turbo with batch taps."""
import sys, time, xml.etree.ElementTree as ET
sys.path.insert(0, ".")
from mtc.adb import AdbController

ADB = r"C:\Program Files\BlueStacks_nxt\HD-Adb.exe"
DEV = "127.0.0.1:5555"
adb = AdbController(ADB, DEV)

# Check where we are
xml = adb.dump_ui()
payload = adb._extract_reader_payload(xml)
if payload:
    print(f"In reader: {payload.get('title','?')}")
else:
    try:
        root = ET.fromstring(xml)
        texts = [(n.get("text","") or n.get("content-desc","")).strip()
                 for n in root.iter()
                 if (n.get("text","") or n.get("content-desc","")).strip()]
    except:
        texts = []
    print("Not in reader. Screen texts (first 10):")
    for t in texts[:10]:
        print(f"  {t[:80]}")
    print("\nNavigating to chapter 1...")
    # Scroll to top of library
    for _ in range(5):
        adb.swipe(450, 400, 450, 1200, duration_ms=100)
        time.sleep(0.2)
    adb.nav_to_chapter(chapter_index=1)
    time.sleep(1.0)
    payload = adb._extract_reader_payload(adb.dump_ui())
    if not payload:
        print("Failed to get to reader!")
        sys.exit(1)
    print(f"Now at: {payload.get('title','?')}")

print(f"\n=== Turbo batch test (5 chapters) ===")
results = []
for i in range(5):
    before = adb._extract_reader_payload(adb._dump_ui_fast())
    before_title = before.get('title', '?') if before else '?'

    t0 = time.perf_counter()
    result = adb.turbo_advance_and_read()
    t1 = time.perf_counter()

    ms = (t1 - t0) * 1000
    results.append(ms)

    if result:
        after_title = result.get('title', '?')
        text_len = len(result.get('text', ''))
        print(f"  #{i+1}: {before_title} -> {after_title} | {ms:.0f}ms | {text_len} chars")
    else:
        print(f"  #{i+1}: {before_title} -> FAILED | {ms:.0f}ms")

print(f"\nAverage: {sum(results)/len(results):.0f}ms")
print(f"Min: {min(results):.0f}ms, Max: {max(results):.0f}ms")
"""Test turbo advance+read speed - explore fastest approach."""
import time, sys
sys.path.insert(0, '.')
from mtc.adb import AdbController
adb = AdbController(r'C:\Program Files\BlueStacks_nxt\HD-Adb.exe', '127.0.0.1:5555')
adb.ensure_device()

w, h = adb.screen_size()
print(f'Screen: {w}x{h}')

# Should still be in reader from last test
xml = adb.dump_ui()
p = adb._extract_reader_payload(xml)
print(f'Starting at: {p.get("title") if p else "N/A"}')

if not p:
    print('Not in reader, need to navigate first')
    sys.exit(1)

# Test A: tap right side without menu (direct advance?)
print('\n=== Test A: Direct right-tap (no menu) ===')
for i in range(3):
    before = adb._extract_reader_payload(adb.dump_ui())
    before_title = before.get('title', '?') if before else '?'
    
    t0 = time.perf_counter()
    # Just tap right side of screen
    adb.tap(int(w * 0.85), h // 2)
    time.sleep(0.5)
    xml = adb.dump_ui()
    after = adb._extract_reader_payload(xml)
    t1 = time.perf_counter()
    
    after_title = after.get('title', '?') if after else '?'
    changed = before_title != after_title
    print(f'  #{i+1}: {(t1-t0)*1000:.0f}ms | {before_title} -> {after_title} | changed={changed}')

# Test B: open menu with longer sleep, tap "next", close
print('\n=== Test B: Menu with 0.3s sleep ===')
for i in range(3):
    before = adb._extract_reader_payload(adb.dump_ui())
    before_title = before.get('title', '?') if before else '?'
    
    t0 = time.perf_counter()
    adb.reader_open_menu()
    time.sleep(0.3)
    adb.tap(*adb._reader_nav_point("next"))
    time.sleep(0.35)
    adb.reader_close_menu()
    time.sleep(0.15)
    xml = adb.dump_ui()
    after = adb._extract_reader_payload(xml)
    t1 = time.perf_counter()
    
    after_title = after.get('title', '?') if after else '?'
    changed = before_title != after_title
    print(f'  #{i+1}: {(t1-t0)*1000:.0f}ms | {before_title} -> {after_title} | changed={changed}')
