import json, re, sys, unicodedata
from pathlib import Path
sys.path.insert(0, r"C:\Dev\MTC_DOWNLOAD")
from download_completed_to_mtc import clean_filename, chapter_filename
from download_one_completed_live_decrypt import get_chapters_once_safe, MTCDownloader
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"C:\Dev\MTC")
BOOKS = json.loads(Path(r"C:\Dev\MTC_DOWNLOAD\completed_books.json").read_text(encoding="utf-8"))
D = MTCDownloader()
TARGET_IDS = [121843, 102223, 102461, 100738, 100677]
idx_re = re.compile(r'(?i)(?:chương|chuong)\s*(\d+)')
book_map = {int(b['id']): b for b in BOOKS}
def norm(s): return unicodedata.normalize('NFC', str(s)).casefold().strip()
folder_map = {norm(p.name): p for p in ROOT.iterdir() if p.is_dir() and p.name != '.git'}
for bid in TARGET_IDS:
    b = book_map[bid]
    folder = folder_map[norm(clean_filename(b['name']))]
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
        if not m:
            continue
        idx = int(m.group(1))
        by_idx.setdefault(idx, []).append(p)
    removed = []
    renamed = []
    # remove or rename per index
    for idx, paths in sorted(by_idx.items()):
        expected = expected_by_idx.get(idx)
        if expected is None:
            for p in paths:
                p.unlink(missing_ok=True)
                removed.append(p.name)
            continue
        expected_path = folder / expected
        if expected_path.exists():
            for p in paths:
                if p.name != expected:
                    p.unlink(missing_ok=True)
                    removed.append(p.name)
            continue
        # exact expected missing
        if len(paths) == 1:
            p = paths[0]
            if p.name != expected:
                p.rename(expected_path)
                renamed.append((p.name, expected))
        else:
            # keep first, rename to expected, delete rest
            keeper = paths[0]
            if keeper.name != expected:
                keeper.rename(expected_path)
                renamed.append((keeper.name, expected))
            for p in paths[1:]:
                p.unlink(missing_ok=True)
                removed.append(p.name)
    # remove leftovers not in expected set
    for p in sorted(folder.glob('*.txt')):
        if p.name not in expected_names:
            p.unlink(missing_ok=True)
            removed.append(p.name)
    print(f'--- {folder.name} ---')
    print('renamed', len(renamed))
    for old, new in renamed[:20]:
        print('  RENAME', old, '=>', new)
    print('removed', len(removed))
    for name in removed[:20]:
        print('  REMOVE', name)
