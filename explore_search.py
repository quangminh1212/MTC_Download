"""explore_search.py – Navigate to search, type a query, dump search results XML.

This helps understand how search results are structured in the app,
since scan_visible_books() may not parse them correctly.
"""
import sys, time, re, xml.etree.ElementTree as ET
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, str(Path(__file__).parent))
from mtc.adb import AdbController

ADB_PATH = r'C:\Program Files\BlueStacks_nxt\HD-Adb.exe'
DEVICE   = '127.0.0.1:5555'

QUERY = sys.argv[1] if len(sys.argv) > 1 else 'batman'

def print_all_nodes(xml_str, label):
    print(f'\n{"="*60}')
    print(f' {label}')
    print('='*60)
    try:
        root = ET.fromstring(xml_str)
    except ET.ParseError as e:
        print(f'XML parse error: {e}')
        return

    print('\n── ALL UNIQUE TEXT/DESC ─────────────────────────────────')
    seen = set()
    for node in root.iter():
        for attr in ('text', 'content-desc'):
            v = (node.get(attr, '') or '').strip()
            if v and len(v) > 2 and v not in seen:
                seen.add(v)
                print(f'  [{attr}] {repr(v[:100])}')

    print('\n── CLICKABLE NODES ──────────────────────────────────────')
    for node in root.iter():
        if node.get('clickable') != 'true':
            continue
        t   = (node.get('text', '') or '').strip()
        cd  = (node.get('content-desc', '') or '').strip()
        cls = node.get('class', '').split('.')[-1]
        bnd = node.get('bounds', '')
        nl_count = (cd or t).count('\n')
        print(f'  [{cls}] nl={nl_count} text={repr(t[:40]):<45} desc={repr(cd[:50]):<55} {bnd}')


def main():
    adb = AdbController(ADB_PATH, DEVICE)
    adb.ensure_device()

    print('[0] Ensuring main tabs...')
    if not adb.ensure_main_tabs(log_fn=print):
        print('FAIL: cannot reach main tabs')
        return

    print('[1] Opening Khám Phá tab...')
    if not adb.open_explore_tab(log_fn=print):
        print('FAIL: cannot open Explore tab')
        return

    time.sleep(0.5)
    xml_explore = adb.dump_ui()
    print_all_nodes(xml_explore, 'EXPLORE TAB (before search)')

    print(f'\n[2] Opening search, typing: {QUERY}')
    if not adb.open_search_screen(log_fn=print):
        print('FAIL: cannot open search screen')
        xml_fail = adb.dump_ui()
        print_all_nodes(xml_fail, 'STATE AFTER SEARCH FAIL')
        return

    time.sleep(0.3)
    # Type search query
    adb.type_text(QUERY)
    time.sleep(2.0)  # Wait for search results

    xml_results = adb.dump_ui()
    print_all_nodes(xml_results, f'SEARCH RESULTS for "{QUERY}"')

    # How many books does scan_visible_books find?
    books = adb.scan_visible_books(xml_str=xml_results)
    print(f'\n── scan_visible_books found {len(books)} books ────────────')
    for b in books:
        print(f'  title={b["title"]!r}  center={b["center"]}')


if __name__ == '__main__':
    main()
