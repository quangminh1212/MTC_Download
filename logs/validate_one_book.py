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
folder = folder_map.get(norm(folder_name))
print(f"book={b.get('name')} id={bid}")
if not folder:
    print('status=NO_FOLDER')
    raise SystemExit(0)
chapters = get_chapters_once_safe(D, bid)
expected_by_idx = {}
expected_names = set()
for i, ch in enumerate(chapters, 1):
    idx = int(ch.get('index') or i)
    fname = chapter_filename(ch, i)
    expected_by_idx[idx] = fname
    expected_names.add(fname)
files = sorted(folder.glob('*.txt'))
by_idx = {}
for p in files:
    m = idx_re.search(p.name)
    if m:
        by_idx.setdefault(int(m.group(1)), []).append(p.name)
expected_norm_map = {norm(name): name for name in expected_names}
local_norm_map = {}
norm_dups = {}
for p in files:
    key = norm(p.name)
    norm_dups.setdefault(key, []).append(p.name)
    local_norm_map.setdefault(key, p.name)
missing = sorted(name for key, name in expected_norm_map.items() if key not in local_norm_map)
extra = sorted(name for key, name in local_norm_map.items() if key not in expected_norm_map)
dups = {idx:names for idx,names in by_idx.items() if len(names)>1}
norm_dups = {key:names for key,names in norm_dups.items() if len(names)>1}
print('folder=', folder.name)
print('remote=', len(chapters), 'local=', len(files), 'info_json=', (folder/'info.json').exists())
print('missing_count=', len(missing))
print('extra_count=', len(extra))
print('dup_count=', len(dups))
print('norm_dup_count=', len(norm_dups))
print('missing_first=', json.dumps(missing[:20], ensure_ascii=False))
print('extra_first=', json.dumps(extra[:20], ensure_ascii=False))
if dups:
    for idx,names in list(sorted(dups.items()))[:20]:
        print('dup', idx, json.dumps(names, ensure_ascii=False))
if norm_dups:
    for key,names in list(sorted(norm_dups.items()))[:20]:
        print('norm_dup', key, json.dumps(names, ensure_ascii=False))
