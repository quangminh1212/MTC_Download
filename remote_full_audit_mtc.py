import json, re, sys, time
from pathlib import Path
from mtc_downloader import MTCDownloader
from download_completed_to_mtc import clean_filename

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(r'C:\Dev\MTC')
BOOKS = json.loads(Path(r'C:\Dev\MTC_Download\completed_books.json').read_text(encoding='utf-8'))
LOG = Path(r'C:\Dev\MTC_Download\logs\mtc_remote_full_audit.json')
PAT = re.compile(r'(?i)(?:chương|chuong)\s*(\d+)')
by_name = {}
for b in BOOKS:
    by_name[clean_filename(b.get('name') or '').lower()] = b

d = MTCDownloader()
report = []

folders = [p for p in ROOT.iterdir() if p.is_dir() and p.name != '.git']
folders.sort(key=lambda p: p.name.lower())

for i, folder in enumerate(folders, 1):
    meta = by_name.get(folder.name.lower())
    txts = sorted(folder.glob('*.txt'))
    seen = {}
    small = []
    for p in txts:
        m = PAT.search(p.name)
        if not m:
            continue
        idx = int(m.group(1))
        seen.setdefault(idx, []).append(p.name)
        size = p.stat().st_size
        if size < 5000:
            small.append({'chapter': idx, 'name': p.name, 'size': size})
    row = {
        'folder': folder.name,
        'matched': bool(meta),
        'book_id': meta.get('id') if meta else None,
        'book_name': meta.get('name') if meta else None,
        'local_file_count': len(txts),
        'local_unique_indexes': len(seen),
        'duplicate_indexes': sorted([idx for idx, arr in seen.items() if len(arr) > 1]),
        'small_files': small[:20],
    }
    if not meta:
        row['status'] = 'unmatched_local_folder'
        report.append(row)
        continue
    try:
        detail = (d.get_book_detail(int(meta['id'])) or {}).get('data') or {}
        chapters = (d.get_chapters(int(meta['id']), page=1, limit=5000) or {}).get('data') or []
        remote_indexes = sorted({int(c.get('index') or c.get('number') or 0) for c in chapters if (c.get('index') or c.get('number'))})
        remote_index_set = set(remote_indexes)
        local_index_set = set(seen)
        missing_remote = sorted([idx for idx in remote_indexes if idx not in local_index_set])
        extra_local = sorted([idx for idx in local_index_set if idx not in remote_index_set])
        row.update({
            'remote_expected': int(detail.get('chapter_count') or detail.get('latest_index') or 0),
            'remote_latest_index': int(detail.get('latest_index') or detail.get('chapter_count') or 0),
            'remote_index_count': len(remote_indexes),
            'missing_vs_remote': missing_remote[:100],
            'missing_vs_remote_count': len(missing_remote),
            'extra_local_vs_remote': extra_local[:100],
            'extra_local_vs_remote_count': len(extra_local),
        })
        if not missing_remote and not extra_local and not row['duplicate_indexes']:
            row['status'] = 'remote_index_complete'
        elif not missing_remote and not extra_local and row['duplicate_indexes']:
            row['status'] = 'remote_index_complete_but_duplicates'
        else:
            row['status'] = 'remote_index_mismatch'
    except Exception as e:
        row['status'] = 'remote_check_failed'
        row['error'] = str(e)
    report.append(row)
    LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'[{i}/{len(folders)}] {folder.name} :: {row["status"]}')
    time.sleep(0.12)

summary = {
    'total_folders': len(report),
    'status_counts': {},
    'report': report,
}
for r in report:
    summary['status_counts'][r['status']] = summary['status_counts'].get(r['status'], 0) + 1
LOG.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(str(LOG))
print(json.dumps(summary['status_counts'], ensure_ascii=False, indent=2))
