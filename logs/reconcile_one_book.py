import json, re, sys, unicodedata
from pathlib import Path
sys.path.insert(0, r"C:\Dev\MTC_DOWNLOAD")
from download_completed_to_mtc import clean_filename, chapter_filename
from download_one_completed_live_decrypt import get_chapters_once_safe, MTCDownloader
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"C:\Dev\MTC")
BOOKS = json.loads(Path(r"C:\Dev\MTC_DOWNLOAD\completed_books.json").read_text(encoding="utf-8"))
D = MTCDownloader()
bid = int(sys.argv[1])
idx_re = re.compile(r'(?i)(?:chương|chuong)\s*(\d+)')
book_map = {int(b['id']): b for b in BOOKS}
def norm(s):
    s = unicodedata.normalize('NFC', str(s)).casefold()
    return ''.join(ch for ch in s if ch.isalnum())
folder_map = {norm(p.name): p for p in ROOT.iterdir() if p.is_dir() and p.name != '.git'}
b = book_map.get(bid) or ((D.get_book_detail(bid) or {}).get('data') or {})
folder_name = clean_filename(b.get('name') or f'book_{bid}')
folder = folder_map[norm(folder_name)]
chapters = get_chapters_once_safe(D, bid)
expected_by_idx = {}
for i, ch in enumerate(chapters, 1):
    idx = int(ch.get('index') or i)
    expected_by_idx[idx] = chapter_filename(ch, i)
files = sorted(folder.glob('*.txt'))
renamed = 0
for p in files:
    m = idx_re.search(p.name)
    if not m:
        continue
    idx = int(m.group(1))
    expected = expected_by_idx.get(idx)
    if expected and norm(p.name) != norm(expected):
        target = p.with_name(expected)
        if target.exists() and target != p:
            continue
        p.rename(target)
        print(f'RENAME: {p.name} -> {expected}')
        renamed += 1
print('renamed', renamed)
