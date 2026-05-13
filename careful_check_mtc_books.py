import json
import re
from pathlib import Path
from download_completed_to_mtc import clean_filename

ROOT = Path(r'C:\Dev\MTC')
BOOKS = json.loads(Path(r'C:\Dev\MTC_Download\completed_books.json').read_text(encoding='utf-8'))
by_name = {}
for b in BOOKS:
    key = clean_filename(b.get('name') or '').lower()
    by_name[key] = {
        'id': b.get('id'),
        'name': b.get('name'),
        'expected': int(b.get('chapter_count') or b.get('latest_index') or 0),
    }

pat = re.compile(r'(?i)(?:chương|chuong)\s*(\d+)')
report = []
for d in ROOT.iterdir():
    if not d.is_dir() or d.name == '.git':
        continue
    meta = by_name.get(d.name.lower())
    txts = list(d.glob('*.txt'))
    rows = []
    seen = {}
    for p in txts:
        m = pat.search(p.name)
        if not m:
            continue
        idx = int(m.group(1))
        size = p.stat().st_size
        try:
            head = p.read_text(encoding='utf-8', errors='replace')[:400]
        except Exception:
            head = ''
        rows.append({'chapter': idx, 'name': p.name, 'size': size, 'head': head})
        seen.setdefault(idx, []).append({'name': p.name, 'size': size})
    rows.sort(key=lambda x: x['chapter'])
    expected = meta['expected'] if meta else None
    missing = []
    duplicate_indexes = []
    if expected:
        for i in range(1, expected + 1):
            if i not in seen:
                missing.append(i)
        duplicate_indexes = [i for i, arr in seen.items() if len(arr) > 1]
    small = [r for r in rows if r['size'] < 5000]
    small_real = []
    small_maybe_ok = []
    for r in small:
        name_l = r['name'].lower()
        text_l = r['head'].lower()
        is_last = bool(expected and r['chapter'] == expected)
        maybe_notice = any(k in name_l for k in ['thông báo', 'doi loi', 'đôi lời', 'đóng sách', 'lời tác giả', 'tác giả']) or any(k in text_l for k in ['thông báo', 'đôi lời', 'đóng sách', 'lời tác giả'])
        if is_last and maybe_notice:
            small_maybe_ok.append({'chapter': r['chapter'], 'name': r['name'], 'size': r['size']})
        else:
            small_real.append({'chapter': r['chapter'], 'name': r['name'], 'size': r['size']})
    if expected and not missing and not duplicate_indexes and not small_real:
        status = 'complete'
    elif expected and not missing and not duplicate_indexes and small_real == [] and small_maybe_ok:
        status = 'complete_with_short_notice'
    elif expected and not missing and duplicate_indexes:
        status = 'has_duplicates_needs_review'
    elif expected and missing:
        status = 'missing_chapters'
    elif small_real:
        status = 'has_short_suspicious_files'
    else:
        status = 'unknown'
    report.append({
        'folder': d.name,
        'matched': bool(meta),
        'book_id': meta['id'] if meta else None,
        'book_name': meta['name'] if meta else None,
        'expected': expected,
        'chapter_files': len(rows),
        'unique_indexes': len(seen),
        'missing_count': len(missing),
        'missing_first20': missing[:20],
        'duplicate_index_count': len(duplicate_indexes),
        'duplicate_indexes_first20': duplicate_indexes[:20],
        'small_suspicious_count': len(small_real),
        'small_suspicious_first20': small_real[:20],
        'small_notice_count': len(small_maybe_ok),
        'small_notice_first20': small_maybe_ok[:20],
        'status': status,
    })

order = {
    'complete': 0,
    'complete_with_short_notice': 1,
    'has_duplicates_needs_review': 2,
    'missing_chapters': 3,
    'has_short_suspicious_files': 4,
    'unknown': 5,
}
report.sort(key=lambda x: (order.get(x['status'], 99), x['folder'].lower()))
out = Path(r'C:\Dev\MTC_Download\logs\mtc_careful_check.json')
out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(str(out))
