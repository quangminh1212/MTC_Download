import json, re, subprocess, sys, time, unicodedata
from pathlib import Path
sys.path.insert(0, r"C:\Dev\MTC_DOWNLOAD")
from mtc_downloader import MTCDownloader
from download_completed_to_mtc import clean_filename, chapter_filename
from download_one_completed_live_decrypt import get_chapters_once_safe, write_info_json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"C:\Dev\MTC")
DOWNLOADER = Path(r"C:\Dev\MTC_DOWNLOAD\download_one_completed_live_decrypt.py")
LOG_DIR = Path(r"C:\Dev\MTC_DOWNLOAD\logs")
idx_re = re.compile(r"(?i)(?:ch\u01b0\u01a1ng|chuong)\\s*(\\d+)")
markers = ["eyJpdiI6", '"iv":"', '"value":"']
D = MTCDownloader()
def norm(s):
    s = unicodedata.normalize('NFC', str(s)).casefold()
    return ''.join(ch for ch in s if ch.isalnum())
def validate_folder(folder, chapters):
    expected_names = {chapter_filename(ch, i) for i, ch in enumerate(chapters, 1)}
    local_names = {p.name for p in folder.glob('*.txt')}
    expected_norm_map = {norm(name): name for name in expected_names}
    local_norm_map = {norm(name): name for name in local_names}
    missing = sorted(name for key, name in expected_norm_map.items() if key not in local_norm_map)
    extra = sorted(name for key, name in local_norm_map.items() if key not in expected_norm_map)
    has_marker = any(any(m in p.read_text(encoding='utf-8', errors='replace') for m in markers) for p in folder.glob('*.txt'))
    info_ok = (folder / 'info.json').exists()
    return missing, extra, has_marker, info_ok, expected_names
def reconcile(folder, chapters):
    expected_by_idx = {}
    for i, ch in enumerate(chapters, 1):
        idx = int(ch.get('index') or i)
        fname = chapter_filename(ch, i)
        expected_by_idx[idx] = fname
    expected_names = set(expected_by_idx.values())
    files = sorted(folder.glob('*.txt'))
    by_idx = {}
    for p in files:
        m = idx_re.search(p.name)
        if m: by_idx.setdefault(int(m.group(1)), []).append(p)
    renamed = removed = 0
    for idx, paths in sorted(by_idx.items()):
        expected = expected_by_idx.get(idx)
        if expected is None:
            for p in paths: p.unlink(missing_ok=True); removed += 1
            continue
        target = folder / expected
        if target.exists():
            for p in paths:
                if norm(p.name) != norm(expected):
                    p.unlink(missing_ok=True); removed += 1
            continue
        if paths:
            keeper = paths[0]
            if norm(keeper.name) != norm(expected):
                keeper.rename(target); renamed += 1
            for p in paths[1:]: p.unlink(missing_ok=True); removed += 1
    expected_norms = {norm(name) for name in expected_names}
    for p in sorted(folder.glob('*.txt')):
        if norm(p.name) not in expected_norms: p.unlink(missing_ok=True); removed += 1
    return renamed, removed
def download_missing(bid, folder_name, missing_names):
    print(f"  download_missing: {len(missing_names)} chapters", flush=True)
    cmd = [sys.executable, str(DOWNLOADER), '--book-id', str(bid), '--delay', '0.08']
    log = LOG_DIR / f'auto_commit_{bid}.log'
    p = subprocess.run(cmd, cwd=str(Path(r'C:\Dev\MTC_DOWNLOAD')), capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=1800)
    log.write_text((p.stdout or '') + '\n[stderr]\n' + (p.stderr or ''), encoding='utf-8')
    return p.returncode
queue = json.loads((LOG_DIR / 'free_completed_queue_exact.json').read_text(encoding='utf-8'))
results = []
for book in queue:
    bid = book['id']
    name = book['folder']
    folder_map = {norm(p.name): p for p in ROOT.iterdir() if p.is_dir() and p.name != '.git'}
    folder = folder_map.get(norm(name)) or ROOT / name
    print(f'\n=== {bid} {name} ===' , flush=True)
    for attempt in range(1, 4):
        chapters = get_chapters_once_safe(D, bid)
        if not chapters:
            print('  no chapters, skip', flush=True)
            break
        folder.mkdir(parents=True, exist_ok=True)
        renamed, removed = reconcile(folder, chapters)
        print(f'  reconcile: renamed={renamed} removed={removed}', flush=True)
        write_info_json(folder, book, chapters)
        missing, extra, has_marker, info_ok, expected_names = validate_folder(folder, chapters)
        if not missing and not extra and not has_marker and info_ok:
            print(f'  VALID on attempt {attempt}', flush=True)
            break
        if missing:
            rc = download_missing(bid, name, missing)
            print(f'  downloader rc={rc}', flush=True)
        time.sleep(1)
    missing, extra, has_marker, info_ok, expected_names = validate_folder(folder, chapters)
    if missing or extra or has_marker or not info_ok:
        status = f'SKIP missing={len(missing)} extra={len(extra)} marker={has_marker} info={info_ok}'
    else:
        status = 'COMMIT'
    print(f'  status={status}', flush=True)
    if status == 'COMMIT':
        subprocess.run(['git', '-C', str(ROOT), 'add', '-A', '--', str(folder.name)], capture_output=True)
        cr = subprocess.run(['git', '-C', str(ROOT), 'commit', '-m', folder.name], capture_output=True, text=True, encoding='utf-8', errors='replace')
        print(f'  git commit: {cr.stdout.strip()[:200]}', flush=True)
    results.append({'id': bid, 'name': name, 'status': status, 'missing': len(missing), 'extra': len(extra)})
    (LOG_DIR / 'auto_commit_state.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
print('\nDONE ALL')
for r in results:
    print(f"{r['status']}\t{r['id']}\t{r['name'][:60]}")
