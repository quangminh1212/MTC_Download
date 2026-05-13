import json
from datetime import datetime
from pathlib import Path
from mtc_downloader import MTCDownloader


def parse_dt(s):
    if not s:
        return datetime.min
    try:
        return datetime.fromisoformat(str(s).replace('Z', '+00:00'))
    except Exception:
        return datetime.min


d = MTCDownloader()
books = []
for page in range(1, 31):
    data = d.get_books(limit=100, page=page) or {}
    rows = data.get('data') or []
    if not rows:
        break
    books.extend(rows)
    if len(rows) < 100:
        break

completed = [b for b in books if b.get('status_name') == 'Hoàn thành' or b.get('status') == 2]
completed.sort(key=lambda b: (parse_dt(b.get('updated_at')), parse_dt(b.get('new_chap_at')), parse_dt(b.get('published_at'))), reverse=True)

checked = []
chosen = None
for b in completed[:500]:
    bid = int(b['id'])
    chapters = (d.get_chapters(bid, page=1, limit=2000) or {}).get('data') or []
    if not chapters:
        continue
    sample = [chapters[0], chapters[len(chapters)//2], chapters[-1]]
    uniq = []
    seen = set()
    for x in sample:
        cid = x.get('id')
        if cid in seen:
            continue
        seen.add(cid)
        uniq.append(x)

    sample_rows = []
    ok = True
    for ch in uniq:
        det = (d.get_chapter_content(ch['id']) or {}).get('data') or {}
        content = det.get('content') or ''
        row = {
            'index': det.get('index'),
            'id': det.get('id'),
            'is_locked': det.get('is_locked'),
            'word_count': det.get('word_count'),
            'content_len': len(content),
        }
        sample_rows.append(row)
        if row['is_locked'] not in (0, None) or row['content_len'] < 2000:
            ok = False

    item = {
        'id': bid,
        'name': b.get('name'),
        'chapter_count': b.get('chapter_count') or b.get('latest_index'),
        'updated_at': b.get('updated_at'),
        'new_chap_at': b.get('new_chap_at'),
        'published_at': b.get('published_at'),
        'sample_ok': ok,
        'samples': sample_rows,
    }
    checked.append(item)
    if ok:
        chosen = item
        break

out = Path(r'C:\Dev\MTC_Download\logs\latest_free_completed_pick.json')
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({'chosen': chosen, 'checked': checked[:50]}, ensure_ascii=False, indent=2), encoding='utf-8')
print(str(out))
print(json.dumps(chosen, ensure_ascii=True) if chosen else 'null')
