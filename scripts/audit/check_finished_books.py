import json
from pathlib import Path
from download_completed_to_mtc import clean_filename

root = Path(r'C:\Dev\MTC')
books = json.loads(Path(r'C:\Dev\MTC_Download\completed_books.json').read_text(encoding='utf-8'))
by_name = {}
for b in books:
    name = clean_filename(b.get('name') or '')
    expected = int(b.get('chapter_count') or b.get('latest_index') or 0)
    by_name[name.lower()] = {
        'id': b.get('id'),
        'name': b.get('name'),
        'expected': expected,
        'status_name': b.get('status_name'),
    }

rows = []
for d in root.iterdir():
    if not d.is_dir():
        continue
    txts = list(d.glob('*.txt'))
    good = sum(1 for p in txts if p.stat().st_size >= 5000)
    key = d.name.lower()
    meta = by_name.get(key)
    rows.append({
        'folder': d.name,
        'matched': bool(meta),
        'book_id': meta.get('id') if meta else None,
        'book_name': meta.get('name') if meta else None,
        'expected': meta.get('expected') if meta else None,
        'chapter_files': len(txts),
        'good_files': good,
        'done': bool(meta and good >= (meta.get('expected') or 0) and (meta.get('expected') or 0) > 0),
    })

rows.sort(key=lambda x: (not x['done'], x['folder'].lower()))
out = Path(r'C:\Dev\MTC_Download\logs\mtc_finished_check.json')
out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
print(str(out))
