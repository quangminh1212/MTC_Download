"""explore_reader.py – Dump reader overlay UI to locate the 'Công cụ' button.

Usage:
    python explore_reader.py [book_name]

Opens the named book (default: first in library), enters the reader,
opens the overlay, then prints every clickable element and all text.
"""
import sys, time, xml.etree.ElementTree as ET
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))
from mtc.adb import AdbController

ADB_PATH = r'C:\Program Files\BlueStacks_nxt\HD-Adb.exe'
DEVICE   = '127.0.0.1:5555'

BOOK = sys.argv[1] if len(sys.argv) > 1 else 'Ta Treo Máy Ngàn Vạn Năm'


def dump_elements(xml_str: str, label: str) -> None:
    print(f'\n{"="*60}')
    print(f' {label}')
    print('='*60)
    try:
        root = ET.fromstring(xml_str)
    except ET.ParseError as e:
        print(f'XML parse error: {e}')
        return

    print('\n── ALL TEXT ─────────────────────────────────────────────')
    for node in root.iter():
        t  = (node.get('text', '') or '').strip()
        cd = (node.get('content-desc', '') or '').strip()
        for val in (t, cd):
            if val and len(val) > 1 and val not in ('[', ']'):
                print(f'  {repr(val[:80])}')

    print('\n── CLICKABLE ELEMENTS ───────────────────────────────────')
    for node in root.iter():
        if node.get('clickable') != 'true':
            continue
        t      = (node.get('text', '') or '').strip()
        cd     = (node.get('content-desc', '') or '').strip()
        bounds = node.get('bounds', '')
        cls    = node.get('class', '').split('.')[-1]
        short_cd = cd[:60] if cd else ''
        print(f'  [{cls}] text={repr(t):<35} desc={repr(short_cd):<60} bounds={bounds}')


def main():
    adb = AdbController(ADB_PATH, DEVICE)
    adb.ensure_device()

    print(f'[1] Opening book (search): {BOOK}')
    # Use search (Khám Phá) instead of library scroll – works even with empty history
    ok = adb.nav_to_book(BOOK, log_fn=print)
    if not ok:
        print('FAIL: book not found via search')
        return

    xml_detail = adb.dump_ui()
    dump_elements(xml_detail, 'BOOK DETAIL PAGE')

    print('\n[2] Opening reader...')
    ok = adb.open_current_book_reader(log_fn=print)
    if not ok:
        print('FAIL: could not open reader')
        return

    time.sleep(0.8)
    xml_reader = adb.dump_ui()
    dump_elements(xml_reader, 'READER (before menu)')

    print('\n[3] Opening reader overlay menu...')
    adb.reader_open_menu()
    time.sleep(0.7)
    xml_overlay = adb.dump_ui()
    dump_elements(xml_overlay, 'READER OVERLAY MENU')

    # Try to find 'Công cụ' specifically
    print('\n── SEARCHING FOR Công cụ / cong cu ─────────────────────')
    try:
        root = ET.fromstring(xml_overlay)
        found = False
        for node in root.iter():
            t  = (node.get('text', '') or '').lower()
            cd = (node.get('content-desc', '') or '').lower()
            if 'cong' in t or 'cụ' in t or 'công' in t or 'tool' in t or 'cong' in cd or 'cụ' in cd or 'công' in cd:
                print(f'  FOUND: text={repr(node.get("text",""))} desc={repr(node.get("content-desc","")[:60])} bounds={node.get("bounds","")} clickable={node.get("clickable","false")}')
                found = True
        if not found:
            print('  NOT FOUND in overlay. Trying toggle...')
            adb.reader_toggle_menu()
            time.sleep(0.4)
            xml2 = adb.dump_ui()
            dump_elements(xml2, 'READER (after toggle)')
    except ET.ParseError:
        pass

    print('\n[4] Close overlay and check BOOK DETAIL for Công cụ...')
    adb.go_back()
    time.sleep(0.6)
    adb.go_back()
    time.sleep(0.6)
    xml_back = adb.dump_ui()
    dump_elements(xml_back, 'AFTER go_back x2')


if __name__ == '__main__':
    main()
