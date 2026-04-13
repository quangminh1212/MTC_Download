"""Debug: dump UI on a specific book's detail page to find button text."""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from mtc.adb import AdbController

adb_path = AdbController.find_adb()
adb = AdbController(adb_path, "127.0.0.1:5555")
book_name = "Theo Môn Phái Võ Lâm Đến Trường Sinh Tiên Môn"

print(f"Opening book: {book_name}")
ok = adb.open_library_book(book_name)
if not ok:
    print("FAIL: Could not open book in library")
    sys.exit(1)

print("Book detail page opened. Dumping UI...")
import time
time.sleep(1)
xml = adb.dump_ui()

# Get all text elements
texts = adb.get_all_text(xml)
print(f"\n=== ALL TEXT ELEMENTS ({len(texts)}) ===")
for i, t in enumerate(texts):
    print(f"  [{i:3d}] {t}")

# Also check for clickable elements with specific button-like text
import xml.etree.ElementTree as ET
try:
    root = ET.fromstring(xml)
    print(f"\n=== CLICKABLE ELEMENTS ===")
    for node in root.iter():
        clickable = node.get("clickable", "false")
        desc = node.get("content-desc", "").strip()
        text = node.get("text", "").strip()
        cls = node.get("class", "")
        bounds = node.get("bounds", "")
        
        if clickable == "true" and (desc or text):
            label = desc or text
            print(f"  [{cls}] '{label}' bounds={bounds}")
    
    print(f"\n=== ALL CONTENT-DESC (including non-clickable) ===")
    for node in root.iter():
        desc = node.get("content-desc", "").strip()
        if desc:
            clickable = node.get("clickable", "false")
            cls = node.get("class", "")
            bounds = node.get("bounds", "")
            print(f"  [{cls}] click={clickable} '{desc}' bounds={bounds}")
except ET.ParseError as e:
    print(f"XML parse error: {e}")

# Try finding various button texts
for btn_text in ["Đọc truyện", "Đọc", "Đọc tiếp", "Tiếp tục đọc", "Đọc ngay", "Read", "Bắt đầu đọc"]:
    center = adb._find_clickable_text_center(btn_text, exact=True, xml_str=xml)
    found = "FOUND" if center else "not found"
    print(f"  Button '{btn_text}': {found} {center or ''}")

# Also try non-exact match
for btn_text in ["Đọc", "đọc", "Read"]:
    center = adb._find_clickable_text_center(btn_text, exact=False, xml_str=xml)
    found = "FOUND" if center else "not found"
    print(f"  Button contains '{btn_text}': {found} {center or ''}")

print("\nDone.")
