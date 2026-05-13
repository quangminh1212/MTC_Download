import json, re, sys
from pathlib import Path
from mtc_downloader import MTCDownloader
from download_completed_to_mtc import clean_filename

if hasattr(sys.stdout,'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(r'C:\Dev\MTC')
BOOKS = json.loads(Path(r'C:\Dev\MTC_Download\completed_books.json').read_text(encoding='utf-8'))
by_name = {clean_filename(b.get('name') or '').lower(): b for b in BOOKS}

target_folders = [
    "Devil'S Path Quỷ Giới Và Nhẫn Giới",
    "Marvel Ta Là Tiểu Chiến Sỹ Họ Stark",
    "Nhị Thứ Nguyên Thần Tượng Âm Nhạc",
]

pat_local_idx = re.compile(r'(?i)(?:chương|chuong)\s*(\d+)')
pat_remote_display = re.compile(r'(?i)^\s*chương\s*(\d+)\s*[:\-]')

d = MTCDownloader()
report = []

for folder in target_folders:
    dirp = ROOT / folder
    meta = by_name.get(folder.lower())
    row = {'folder': folder, 'matched': bool(meta), 'book_id': meta.get('id') if meta else None, 'book_name': meta.get('name') if meta else None}
    if not meta or not dirp.exists():
        row['status'] = 'missing_meta_or_folder'
        report.append(row)
        continue

    # local indexes + filename map
    local_files = sorted(dirp.glob('*.txt'))
    local_idx_set = set()
    local_idx_to_names = {}
    for p in local_files:
        m = pat_local_idx.search(p.name)
        if not m:
            continue
        idx = int(m.group(1))
        local_idx_set.add(idx)
        local_idx_to_names.setdefault(idx, []).append(p.name)

    # remote chapters
    chapters = (d.get_chapters(int(meta['id']), page=1, limit=5000) or {}).get('data') or []
    remote_rows = []
    remote_index_set = set()
    display_set = set()

    for ch in chapters:
        ridx = int(ch.get('index') or ch.get('number') or 0)
        rname = str(ch.get('name') or ch.get('title') or '')
        remote_index_set.add(ridx)
        md = pat_remote_display.search(rname)
        d_idx = int(md.group(1)) if md else None
        if d_idx is not None:
            display_set.add(d_idx)
        remote_rows.append({'id': ch.get('id'), 'index': ridx, 'name': rname, 'display_idx': d_idx})

    # compare by raw index
    missing_raw = sorted([i for i in remote_index_set if i not in local_idx_set])
    extra_raw = sorted([i for i in local_idx_set if i not in remote_index_set])

    # compare by display chapter number inside remote title (author-visible numbering)
    missing_display = sorted([i for i in display_set if i not in local_idx_set])
    extra_vs_display = sorted([i for i in local_idx_set if display_set and i not in display_set])

    # find suspicious rows where remote index != display idx
    mismatch_rows = [r for r in remote_rows if r['display_idx'] is not None and r['index'] != r['display_idx']]

    # decision
    if not missing_display and not extra_vs_display and not missing_raw and not extra_raw:
        decision = 'PASS_exact'
    elif not missing_display and not extra_vs_display and (missing_raw or extra_raw):
        decision = 'PASS_display_index_ok_api_index_skew'
    else:
        decision = 'FAIL_missing_or_extra'

    row.update({
        'local_file_count': len(local_files),
        'local_unique_idx_count': len(local_idx_set),
        'remote_chapter_rows': len(remote_rows),
        'remote_unique_index_count': len(remote_index_set),
        'remote_unique_display_count': len(display_set),
        'missing_raw_index_first50': missing_raw[:50],
        'extra_raw_index_first50': extra_raw[:50],
        'missing_display_first50': missing_display[:50],
        'extra_vs_display_first50': extra_vs_display[:50],
        'remote_index_display_mismatch_count': len(mismatch_rows),
        'remote_index_display_mismatch_first30': mismatch_rows[:30],
        'decision': decision,
    })
    report.append(row)

out = Path(r'C:\Dev\MTC_Download\logs\deep_verify_3_mismatch.json')
out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(str(out))
print(json.dumps(report, ensure_ascii=False, indent=2))
