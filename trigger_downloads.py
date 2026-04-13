"""trigger_downloads.py – Quickly queue TẢI TẤT CẢ for every book in the library.

Phase-1 helper.  Does NOT wait for downloads to finish – just taps TẢI TẤT CẢ
for each book as fast as possible so the app queues them all.

Run overnight, then follow up with export_all.py --only-parse or the full
export pass once the app finishes downloading everything in the background.

Usage:
    python trigger_downloads.py [--start-id N] [--limit N]
"""
import sys, json, time, re, subprocess, argparse
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, str(Path(__file__).parent))
from mtc.adb import AdbController

# ── Config ────────────────────────────────────────────────────────────────────
ADB_PATH   = r'C:\Program Files\BlueStacks_nxt\HD-Adb.exe'
DEVICE     = '127.0.0.1:5555'
BOOKS_JSON = Path(r'C:\Dev\MTC_Download\all_books.json')

# Confirmed coordinates (900×1600 screen)
_CU_TAP  = (135, 168)   # Left side of first search result → Công cụ dialog
_TAI_TAP = (450, 797)   # TẢI TẤT CẢ in Công cụ dialog
_HUY_TAP = (450, 1001)  # HỦY in Công cụ dialog


def adb_raw(*args, timeout=30):
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    r = subprocess.run(
        [ADB_PATH, '-s', DEVICE] + [str(a) for a in args],
        capture_output=True, text=True, timeout=timeout,
        encoding='utf-8', errors='replace', creationflags=flags,
    )
    return r.stdout.strip(), r.stderr.strip()


def get_all_texts(xml_str: str) -> set:
    """Return all text/content-desc values from UIAutomator XML (lower-cased)."""
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(xml_str)
    except ET.ParseError:
        return set()
    result = set()
    for node in root.iter():
        for attr in ('text', 'content-desc'):
            v = (node.get(attr, '') or '').strip().lower()
            if v:
                result.add(v)
    return result


def trigger_one(ctrl: AdbController, book_name: str) -> str:
    """Trigger TẢI TẤT CẢ for one book.  Returns 'ok', 'already', or 'fail'."""
    # 1. Tủ Truyện tab
    ctrl.tap(113, 1558)
    time.sleep(1.2)

    # 2. Search icon
    ctrl.tap(720, 75)
    time.sleep(0.8)

    # 3. Clear + type
    ctrl.sh('shell', 'input', 'keyevent', 'KEYCODE_CTRL_A')
    ctrl.sh('shell', 'input', 'keyevent', 'KEYCODE_DEL')
    ctrl.type_text(book_name[:40])
    time.sleep(2.2)

    # 4. Tap Công cụ hotspot
    ctrl.tap(*_CU_TAP)
    time.sleep(1.3)

    # 5. Check dialog appeared
    xml = ctrl.dump_ui()
    texts = get_all_texts(xml)
    if not any('tải tất cả' in t or 'xuất ebook' in t for t in texts):
        # Dialog did not appear – might have gone to book detail, back out
        ctrl.sh('shell', 'input', 'keyevent', 'KEYCODE_BACK')
        time.sleep(0.5)
        return 'fail'

    # 6. Tap TẢI TẤT CẢ
    ctrl.tap(*_TAI_TAP)
    time.sleep(1.2)

    # 7. Check result
    xml2 = ctrl.dump_ui()
    texts2 = get_all_texts(xml2)
    if any('đã tải tất cả' in t or 'bạn đã tải' in t for t in texts2):
        return 'already'

    # Dismiss Công cụ dialog / go back to library
    ctrl.tap(113, 1558)
    time.sleep(0.5)
    return 'ok'


def main():
    p = argparse.ArgumentParser(description='Queue TẢI TẤT CẢ for all books (no wait)')
    p.add_argument('--start-id', type=int, default=0)
    p.add_argument('--limit',    type=int, default=9999)
    args = p.parse_args()

    with open(BOOKS_JSON, encoding='utf-8') as f:
        books = json.load(f)
    books.sort(key=lambda b: b['id'])

    ctrl = AdbController(ADB_PATH, DEVICE)
    ctrl.ensure_device()

    n_ok = n_already = n_fail = 0
    processed = 0

    for book in books:
        if processed >= args.limit:
            break
        if book['id'] < args.start_id:
            continue
        if book.get('chapter_count', 0) == 0:
            continue

        bname = book['name']
        print(f"[#{book['id']}] {bname[:60]}...", end=' ', flush=True)
        result = trigger_one(ctrl, bname)
        print(result)
        if result == 'ok':
            n_ok += 1
        elif result == 'already':
            n_already += 1
        else:
            n_fail += 1
        processed += 1
        # Brief pause so the app can process the download start
        time.sleep(1.0)

    print(f'\nDone. triggered={n_ok}  already_done={n_already}  fail={n_fail}')


if __name__ == '__main__':
    main()
