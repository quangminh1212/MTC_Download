#!/usr/bin/env python3
"""debug_library.py – Debug why books aren't found in library."""
import sys, time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mtc.adb import AdbController


def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def main():
    adb_path = AdbController.find_adb()
    adb = AdbController(adb_path, "127.0.0.1:5555")
    adb.ensure_device()

    # Step 1: Try opening library tab
    log("=== Opening library tab ===")
    result = adb.open_library_tab(log_fn=log)
    log(f"open_library_tab result: {result}")
    time.sleep(1.0)

    # Step 2: Dump UI and see what's visible
    log("\n=== Dumping UI ===")
    xml = adb.dump_ui()
    log(f"XML length: {len(xml)} chars")

    # Step 3: Get all text elements
    texts = adb.get_all_text(xml)
    log(f"\n=== All text elements ({len(texts)}) ===")
    for i, t in enumerate(texts[:30]):
        preview = t.replace("\n", " | ")[:120]
        log(f"  [{i}] {preview}")

    # Step 4: Try scanning visible books
    log("\n=== Scanning visible library books ===")
    books = adb.scan_visible_library_books(log_fn=log, xml_str=xml)
    log(f"Found {len(books)} visible books:")
    for b in books:
        log(f"  - {b['title']} ({b.get('read_at', '?')}/{b.get('read_total', '?')})")

    # Step 5: Try scrolling and scanning more
    log("\n=== Scrolling and scanning ===")
    all_books = []
    seen_keys = set()
    for scroll_round in range(5):
        log(f"\n--- Scroll round {scroll_round + 1} ---")
        adb.swipe_up()
        time.sleep(1.0)
        xml = adb.dump_ui()
        books = adb.scan_visible_library_books(log_fn=lambda *_: None, xml_str=xml)
        new_count = 0
        for b in books:
            key = b.get("key", "")
            if key not in seen_keys:
                seen_keys.add(key)
                all_books.append(b)
                new_count += 1
                log(f"  NEW: {b['title']}")
            else:
                log(f"  seen: {b['title'][:40]}...")
        if new_count == 0:
            log("  No new books found, stopping")
            break

    log(f"\n=== Total unique books found: {len(all_books)} ===")
    for i, b in enumerate(all_books, 1):
        log(f"  {i}. {b['title']}")


if __name__ == "__main__":
    main()
