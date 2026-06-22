import json, os, re, sys, unicodedata
from pathlib import Path
sys.path.insert(0, r"C:\Dev\MTC_DOWNLOAD")
from download_completed_to_mtc import clean_filename
from download_one_completed_live_decrypt import get_chapters_once_safe, MTCDownloader, chapter_filename
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"C:\Dev\MTC")
BOOKS = json.loads(Path(r"C:\Dev\MTC_DOWNLOAD\completed_books.json").read_text(encoding="utf-8"))
D = MTCDownloader()
ids = [121843,102223,102461,100738,100677,112190,142470,105037,106124,106815,106431,109958,114701]
book_map = {int(b["id"]): b for b in BOOKS}
markers = ["eyJpdiI6", '"iv":"', '"value":"']
mojis = ['ChÃ†Â°Ã†Â¡ng', 'Ã¡Âº', 'Ã¡Â»', 'Ãƒ', 'Ã‚']
idx_re = re.compile(r'(?i)(?:chương|chuong)\s*(\d+)')

def norm(s): return unicodedata.normalize('NFC', str(s)).casefold().strip()
folder_map = {norm(p.name): p for p in ROOT.iterdir() if p.is_dir() and p.name != '.git'}
def has_ctrl(s): return any(ord(ch) < 32 and ch not in "\n\r\t" for ch in s)
for bid in ids:
    b = book_map.get(bid) or ((D.get_book_detail(bid) or {}).get('data') or {})
    folder_name = clean_filename(b.get('name') or f'book_{bid}')
    folder = folder_map.get(norm(folder_name))
    print(f"--- {bid} {folder_name} ---")
    if not folder:
        print('status=NO_FOLDER')
        continue
    chapters = get_chapters_once_safe(D, bid)
    remote_indexes = []
    expected_files = set()
    for i, ch in enumerate(chapters, 1):
        try: remote_indexes.append(int(ch.get('index') or i))
        except Exception: remote_indexes.append(i)
        expected_files.add(chapter_filename(ch, i))
    txts = sorted(folder.glob('*.txt'))
    jsons = sorted(folder.glob('*.json'))
    local_indexes = []
    for p in txts:
        m = idx_re.search(p.name)
        if m: local_indexes.append(int(m.group(1)))
    missing_files = sorted(expected_files - {p.name for p in txts})[:20]
    extra_files = sorted({p.name for p in txts} - expected_files)[:20]
    bad_marker = bad_fffd = bad_moji = bad_ctrl = 0
    bad_line = 0
    for p in txts:
        t = p.read_text(encoding='utf-8', errors='replace')
        if any(m in t for m in markers): bad_marker += 1
        if '\ufffd' in t: bad_fffd += 1
        if any(m in t for m in mojis): bad_moji += 1
        if has_ctrl(t): bad_ctrl += 1
        lines = t.splitlines()
        if len(lines) < 4 or lines[0] != '='*60 or not lines[1].startswith('Chương ') or lines[2] != '='*60:
            bad_line += 1
    dup_indexes = sorted([i for i in set(local_indexes) if local_indexes.count(i) > 1])[:20]
    print(f"folder={folder.name}")
    print(f"remote_chapters={len(chapters)} local_txt={len(txts)} json_count={len(jsons)} info_json={(folder/'info.json').exists()}")
    print(f"missing_files={len(expected_files - {p.name for p in txts})} extra_files={len({p.name for p in txts} - expected_files)} dup_indexes={len(dup_indexes)}")
    if missing_files: print('missing_first=', json.dumps(missing_files, ensure_ascii=False))
    if extra_files: print('extra_first=', json.dumps(extra_files, ensure_ascii=False))
    print(f"bad_marker={bad_marker} bad_fffd={bad_fffd} bad_moji={bad_moji} bad_ctrl={bad_ctrl} bad_header={bad_line}")
