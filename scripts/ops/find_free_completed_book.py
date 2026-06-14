import json
from pathlib import Path
from mtc_downloader import MTCDownloader

d = MTCDownloader()
books_path = Path(r'C:\Dev\MTC_Download\completed_books.json')
if books_path.exists():
    books = json.loads(books_path.read_text(encoding='utf-8'))
else:
    books = []
    page = 1
    while page <= 20:
        rows = (d.get_books(limit=100, page=page) or {}).get('data') or []
        if not rows: break
        books.extend(rows)
        if len(rows) < 100: break
        page += 1

completed = [b for b in books if b.get('status_name') == 'Hoàn thành' or b.get('status') == 2]
# Prefer modest length for test.
completed.sort(key=lambda b: int(b.get('chapter_count') or b.get('latest_index') or 999999))
results = []
for b in completed[:300]:
    bid = int(b['id'])
    chapters = (d.get_chapters(bid, page=1, limit=20) or {}).get('data') or []
    if not chapters:
        continue
    # sample first, middle-ish if available, last-ish from returned list
    sample = []
    for ch in [chapters[0], chapters[min(len(chapters)-1, len(chapters)//2)], chapters[-1]]:
        if ch.get('id') not in [x.get('id') for x in sample]:
            sample.append(ch)
    details=[]
    ok=True
    for ch in sample:
        det=(d.get_chapter_content(ch['id']) or {}).get('data') or {}
        content=det.get('content') or ''
        details.append({
            'index': det.get('index'),
            'id': det.get('id'),
            'is_locked': det.get('is_locked'),
            'word_count': det.get('word_count'),
            'content_len': len(content),
        })
        if det.get('is_locked') not in (0, None) or len(content) < 2000:
            ok=False
    results.append({
        'id': bid,
        'name': b.get('name'),
        'chapter_count': b.get('chapter_count') or b.get('latest_index'),
        'status_name': b.get('status_name'),
        'sample_ok': ok,
        'samples': details,
    })
    if ok:
        break

out=Path(r'C:\Dev\MTC_Download\logs\free_completed_candidates.json')
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
print(str(out))
if results:
    print(json.dumps(results[-1], ensure_ascii=True))
