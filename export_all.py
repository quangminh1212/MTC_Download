"""export_all.py – Batch export all novels via TẢI TẤT CẢ → XUẤT EBOOK.

Strategy per book:
  1. Skip if downloads/<name>/ already has enough chapters
  2. Open book from Tủ Truyện → enter reader
  3. Open reader overlay → tap "Công cụ" → tap "TẢI TẤT CẢ"
  4. Wait for download to finish (poll UI)
  5. Open overlay again → tap "Công cụ" → tap "XUẤT EBOOK"
  6. Pull exported .txt from /sdcard/Download/NovelFever/
  7. Parse and save chapters to downloads/<name>/

Run:
    python export_all.py [--start-id N] [--limit N] [--force]
    
Options:
    --start-id N  Resume from book_id >= N
    --limit N     Process at most N books
    --force       Re-export even if chapters exist
"""
import sys, json, time, re, subprocess, argparse, os
from pathlib import Path
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, str(Path(__file__).parent))
from mtc.adb import AdbController

# ── Config ────────────────────────────────────────────────────────────────────
ADB_PATH          = r'C:\Program Files\BlueStacks_nxt\HD-Adb.exe'
DEVICE            = '127.0.0.1:5555'
BOOKS_JSON        = Path(r'C:\Dev\MTC_Download\all_books.json')
DOWNLOADS         = Path(r'C:\Dev\MTC_Download\downloads')
EXPORT_LOCAL_DIR  = Path(r'C:\Dev\MTC_Download\exports')   # temp dir for pulled txt
DEVICE_EXPORT_DIR = '/sdcard/Download/NovelFever'
STATE_FILE        = Path(r'C:\Dev\MTC_Download\export_state.json')

SEPARATOR         = '─' * 20  # chapter separator in export files

# Minimum content size to consider an export file "complete" (bytes).
# Header-only stubs are ~100-160 bytes.
MIN_CONTENT_BYTES = 500

# ── ADB helpers ───────────────────────────────────────────────────────────────
def _run(cmd, timeout=60):
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                       encoding='utf-8', errors='replace', creationflags=flags)
    return r.stdout.strip(), r.stderr.strip()

def adb(*args, timeout=30):
    out, err = _run([ADB_PATH, '-s', DEVICE] + [str(a) for a in args], timeout=timeout)
    return out

def adb_shell(cmd, timeout=30):
    return adb('shell', cmd, timeout=timeout)

def device_file_size(path: str) -> int:
    """Return file size in bytes, or 0 if not found."""
    out = adb_shell(f'stat -c %s {path!r} 2>/dev/null || echo 0')
    try:
        return int(out.strip())
    except (ValueError, AttributeError):
        return 0

def list_device_exports() -> dict:
    """Return {filename: size_bytes} for all .txt files in the export dir."""
    out = adb_shell(f'ls -la {DEVICE_EXPORT_DIR}/')
    result = {}
    for line in out.splitlines():
        if not line.strip() or line.startswith('total'):
            continue
        parts = line.split(None, 7)
        if len(parts) < 8:
            continue
        size_str = parts[4]
        name     = parts[7].strip()
        if not name.endswith('.txt'):
            continue
        try:
            result[name] = int(size_str)
        except ValueError:
            result[name] = 0
    return result

def pull_export_file(book_name: str) -> Path | None:
    """Pull the export .txt for book_name to EXPORT_LOCAL_DIR."""
    EXPORT_LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    remote = f'{DEVICE_EXPORT_DIR}/{book_name}.txt'
    local  = EXPORT_LOCAL_DIR / f'{book_name}.txt'
    out, err = _run([ADB_PATH, '-s', DEVICE, 'pull', remote, str(local)], timeout=120)
    combined = (out + err).lower()
    if 'pulled' in combined or '1 file' in combined:
        if local.exists() and local.stat().st_size > MIN_CONTENT_BYTES:
            return local
    return None

# ── Export file parsing ───────────────────────────────────────────────────────
def parse_export_file(txt_path: Path) -> list:
    """Parse NovelFever export TXT → list of dicts with 'title', 'body'."""
    content = txt_path.read_text(encoding='utf-8', errors='replace')
    sections = content.split(SEPARATOR + '\n')
    # sections[0] = book header
    # sections[1,3,5,...] = chapter title ("Chương XX: Title")
    # sections[2,4,6,...] = chapter body  (first lines are corrupted title repeat)
    chapters = []
    for i in range(1, len(sections) - 1, 2):
        title_sec = sections[i].strip()
        if not title_sec:
            continue
        # Normalize: accept both "Chương" and plain text titles
        body_sec  = sections[i + 1] if (i + 1) < len(sections) else ''
        body      = _clean_body(body_sec, title_sec)
        chapters.append({'title': title_sec, 'body': body})
    return chapters

def _clean_body(raw: str, title: str) -> str:
    """Strip the corrupted title-repeat lines from the start of a chapter body."""
    lines = raw.splitlines()
    # Skip blank lines and the first non-blank line (corrupted title)
    started = False
    kept    = []
    for line in lines:
        if not started:
            stripped = line.strip()
            if not stripped:
                continue  # skip leading blanks
            # First non-blank line is the corrupted title repeat — skip it
            started = True
            continue
        kept.append(line)
    return '\n'.join(kept).strip()

# ── Chapter saving ────────────────────────────────────────────────────────────
def save_chapters(book_name: str, chapters: list) -> int:
    """Save chapters to downloads/<book_name>/*.txt; return count saved."""
    out_dir = DOWNLOADS / book_name
    out_dir.mkdir(parents=True, exist_ok=True)
    saved = 0
    for ch in chapters:
        m      = re.search(r'Chương\s+(\d+)', ch['title'], re.IGNORECASE)
        ch_num = int(m.group(1)) if m else (saved + 1)
        safe   = re.sub(r'[<>:"/\\|?*]', '_', ch['title'])[:80]
        fname  = f'{ch_num:06d}_{safe}.txt'
        fpath  = out_dir / fname
        if not fpath.exists():
            fpath.write_text(ch['body'], encoding='utf-8')
            saved += 1
    return saved

def count_saved_chapters(book_name: str) -> int:
    d = DOWNLOADS / book_name
    if not d.is_dir():
        return 0
    return len(list(d.glob('*.txt')))

# ── UI automation helpers ─────────────────────────────────────────────────────
def get_all_text_lower(xml_str: str) -> set:
    try:
        root = ET.fromstring(xml_str)
    except ET.ParseError:
        return set()
    result = set()
    for node in root.iter():
        for attr in ('text', 'content-desc'):
            val = (node.get(attr, '') or '').strip().lower()
            if val:
                result.add(val)
    return result

def find_clickable_center(xml_str: str, keyword: str) -> tuple | None:
    """Find center of first clickable element whose text/desc contains keyword."""
    try:
        root = ET.fromstring(xml_str)
    except ET.ParseError:
        return None
    kw = keyword.lower()
    for node in root.iter():
        if node.get('clickable') != 'true':
            continue
        t  = (node.get('text', '') or '').lower()
        cd = (node.get('content-desc', '') or '').lower()
        if kw in t or kw in cd:
            bounds = node.get('bounds', '')
            nums   = re.findall(r'\d+', bounds)
            if len(nums) == 4:
                x1, y1, x2, y2 = (int(n) for n in nums)
                return (x1 + x2) // 2, (y1 + y2) // 2
    return None

def open_cong_cu_dialog(adb: AdbController, *, retries=2) -> bool:
    """Open reader overlay and tap 'Công cụ'. Returns True if dialog appeared."""
    for attempt in range(retries):
        adb.reader_open_menu()
        time.sleep(0.6)
        xml = adb.dump_ui()
        if not adb._reader_menu_visible(xml):
            adb.reader_toggle_menu()
            time.sleep(0.4)
            xml = adb.dump_ui()

        # Try exact 'Công cụ' or partial 'cụ'
        for kw in ('Công cụ', 'cụ', 'Cong cu', 'công cụ'):
            center = find_clickable_center(xml, kw)
            if center:
                adb.tap(*center)
                time.sleep(0.5)
                # Check dialog appeared (look for TẢI TẤT CẢ or XUẤT EBOOK)
                xml2 = adb.dump_ui()
                texts = get_all_text_lower(xml2)
                if any('tải tất cả' in t or 'xuất ebook' in t or 'xuat ebook' in t for t in texts):
                    return True
    return False

def tap_in_dialog(adb: AdbController, keyword: str) -> bool:
    """Tap a button within the currently-shown dialog."""
    xml = adb.dump_ui()
    center = find_clickable_center(xml, keyword)
    if center:
        adb.tap(*center)
        return True
    return False

def wait_for_download(adb: AdbController, book_name: str,
                      chapter_count: int, log_fn=print) -> bool:
    """Poll until download progress disappears or timeout."""
    # Estimate wait: ~1 sec/chapter, minimum 20s, max 10 minutes
    timeout = max(20, min(chapter_count * 1.2, 600))
    log_fn(f'  Waiting up to {timeout:.0f}s for download ({chapter_count} chapters)...')

    start = time.time()
    last_progress_seen = start
    consecutive_idle = 0

    while time.time() - start < timeout:
        time.sleep(8)
        xml = adb.dump_ui()
        texts = get_all_text_lower(xml)
        # Progress indicators
        has_progress = any(
            any(kw in t for kw in ('%', 'đang tải', 'downloading', 'loading'))
            for t in texts
        )
        # Also check for "already downloaded" message
        already_done = any(
            'đã tải tất cả' in t or 'tải tất cả' in t
            for t in texts
        )
        elapsed = time.time() - start
        if already_done:
            log_fn(f'  Download complete (already downloaded message) after {elapsed:.0f}s')
            return True
        if has_progress:
            last_progress_seen = time.time()
            consecutive_idle = 0
            log_fn(f'  Download in progress... ({elapsed:.0f}s)')
        else:
            consecutive_idle += 1
            log_fn(f'  No progress indicator ({elapsed:.0f}s, idle={consecutive_idle})')
            if consecutive_idle >= 2 and elapsed > 15:
                log_fn(f'  Download appears complete after {elapsed:.0f}s')
                return True

    log_fn(f'  Download timed out after {timeout:.0f}s')
    return False

# ── State (persist which books are done) ─────────────────────────────────────
def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {}

def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2),
                          encoding='utf-8')

# ── Main ──────────────────────────────────────────────────────────────────────
def process_book(adb: AdbController, book: dict, state: dict, force=False) -> str:
    """Process one book. Returns 'ok', 'skip', or 'fail'."""
    bid   = book['id']
    bname = book['name']
    btotal = book.get('chapter_count', 0)

    log = lambda msg: print(f'  [{bid}] {msg}', flush=True)

    # ── 1. Check already done ────────────────────────────────────────────────
    saved = count_saved_chapters(bname)
    if not force and saved > 0 and (btotal == 0 or saved >= int(btotal * 0.80)):
        log(f'SKIP – {saved}/{btotal} chapters already saved')
        return 'skip'

    if str(bid) in state and state[str(bid)] == 'ok' and not force:
        log(f'SKIP – marked done in state file')
        return 'skip'

    print(f'\n[{bid}] Processing: {bname} ({btotal} chapters, {saved} saved)')

    # ── 2. Open book from library ────────────────────────────────────────────
    book_info = adb.open_library_book(bname, log_fn=log)
    if not book_info:
        log('FAIL – not found in library')
        return 'fail'
    time.sleep(0.4)

    # ── 3. Enter reader ──────────────────────────────────────────────────────
    ok = adb.open_current_book_reader(log_fn=log)
    if not ok:
        log('FAIL – could not open reader')
        adb.go_back(2)
        return 'fail'
    time.sleep(0.6)

    # ── 4. Trigger TẢI TẤT CẢ ───────────────────────────────────────────────
    log('Opening Công cụ dialog...')
    if not open_cong_cu_dialog(adb):
        log('FAIL – Công cụ dialog not found; check explore_reader.py output')
        adb.go_back(3)
        return 'fail'

    log('Tapping TẢI TẤT CẢ...')
    if not tap_in_dialog(adb, 'tất cả'):
        # Try alternate text
        if not tap_in_dialog(adb, 'tai tat ca'):
            log('FAIL – TẢI TẤT CẢ button not found')
            adb.go_back(3)
            return 'fail'

    time.sleep(1.0)
    # Might show "already downloaded" toast — that's fine too
    xml_after = adb.dump_ui()
    texts_after = get_all_text_lower(xml_after)
    already = any('đã tải tất cả' in t or 'bạn đã tải' in t for t in texts_after)
    if not already:
        # Wait for download to complete
        wait_for_download(adb, bname, btotal, log_fn=log)

    # ── 5. Trigger XUẤT EBOOK ────────────────────────────────────────────────
    # Re-open overlay and Công cụ dialog
    log('Opening Công cụ dialog for XUẤT EBOOK...')
    time.sleep(1.0)
    if not open_cong_cu_dialog(adb):
        log('FAIL – could not re-open Công cụ dialog for export')
        adb.go_back(3)
        return 'fail'

    log('Tapping XUẤT EBOOK...')
    if not tap_in_dialog(adb, 'xuất ebook') and not tap_in_dialog(adb, 'ebook'):
        log('FAIL – XUẤT EBOOK button not found')
        adb.go_back(3)
        return 'fail'

    time.sleep(3.0)  # Give app time to write file

    # ── 6. Pull export file ──────────────────────────────────────────────────
    log('Pulling export file...')
    # Check if file exists and has content
    exports = list_device_exports()
    exp_name = f'{bname}.txt'
    if exp_name not in exports or exports[exp_name] < MIN_CONTENT_BYTES:
        # Wait a bit more and retry
        time.sleep(5)
        exports = list_device_exports()
    if exp_name not in exports:
        log(f'FAIL – export file not found: {exp_name}')
        log(f'  Available: {list(exports.keys())[:5]}')
        adb.go_back(3)
        return 'fail'
    if exports[exp_name] < MIN_CONTENT_BYTES:
        log(f'FAIL – export file too small ({exports[exp_name]} bytes)')
        adb.go_back(3)
        return 'fail'

    local_file = pull_export_file(bname)
    if not local_file:
        log('FAIL – could not pull file')
        adb.go_back(3)
        return 'fail'

    # ── 7. Parse and save chapters ───────────────────────────────────────────
    log('Parsing and saving chapters...')
    chapters = parse_export_file(local_file)
    if not chapters:
        log('FAIL – no chapters parsed from export file')
        adb.go_back(3)
        return 'fail'

    saved_new = save_chapters(bname, chapters)
    log(f'OK – saved {saved_new} new chapters ({len(chapters)} total in export)')

    # ── 8. Go back to library ────────────────────────────────────────────────
    adb.go_back(3)
    time.sleep(0.5)

    return 'ok'


def main():
    p = argparse.ArgumentParser(description='Export all novels via TẢI TẤT CẢ → XUẤT EBOOK')
    p.add_argument('--start-id', type=int, default=0,
                   help='Skip books with id < start-id')
    p.add_argument('--limit', type=int, default=9999,
                   help='Process at most this many books')
    p.add_argument('--force', action='store_true',
                   help='Re-process even if chapters exist')
    p.add_argument('--only-parse', action='store_true',
                   help='Only parse already-pulled export files (no ADB)')
    args = p.parse_args()

    with open(BOOKS_JSON, encoding='utf-8') as f:
        books = json.load(f)

    # Sort by id for reproducible order
    books.sort(key=lambda b: b['id'])

    state = load_state()

    if args.only_parse:
        print('=== PARSE-ONLY MODE ===')
        for txt in sorted(EXPORT_LOCAL_DIR.glob('*.txt')):
            bname = txt.stem
            print(f'Parsing: {bname}')
            chapters = parse_export_file(txt)
            if chapters:
                n = save_chapters(bname, chapters)
                print(f'  → {n} new chapters saved ({len(chapters)} total)')
            else:
                print(f'  → no chapters found')
        return

    ctrl = AdbController(ADB_PATH, DEVICE)
    ctrl.ensure_device()

    total_ok   = 0
    total_skip = 0
    total_fail = 0
    processed  = 0

    for book in books:
        if processed >= args.limit:
            break
        if book['id'] < args.start_id:
            continue
        if book.get('chapter_count', 0) == 0:
            # books with 0 chapters listed – skip
            continue

        result = process_book(ctrl, book, state, force=args.force)
        processed += 1

        if result == 'ok':
            total_ok += 1
            state[str(book['id'])] = 'ok'
            save_state(state)
        elif result == 'skip':
            total_skip += 1
        else:
            total_fail += 1
            state[str(book['id'])] = 'fail'
            save_state(state)
            # Brief pause after failure to let app settle
            time.sleep(2)
            ctrl.ensure_device()

        print(f'Progress: ok={total_ok} skip={total_skip} fail={total_fail}')

    print(f'\nDone. ok={total_ok} skip={total_skip} fail={total_fail}')


if __name__ == '__main__':
    main()
