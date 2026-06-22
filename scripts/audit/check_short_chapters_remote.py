import json
from pathlib import Path
from mtc_downloader import MTCDownloader

candidates = json.loads(Path(r'C:\Dev\MTC_Download\logs\short_chapter_repair_candidates.json').read_text(encoding='utf-8'))
out=[]
d=MTCDownloader()
for book in candidates:
    bid=book['book_id']
    chapters=(d.get_chapters(bid,page=1,limit=2000) or {}).get('data') or []
    by_idx={int(c.get('index') or 0):c for c in chapters if c.get('index')}
    checks=[]
    targets=(book.get('small_suspicious_first20') or []) + (book.get('small_notice_first20') or [])
    for t in targets:
        idx=int(t['chapter'])
        ch=by_idx.get(idx)
        if not ch:
            checks.append({**t,'remote_found':False})
            continue
        det=(d.get_chapter_content(ch['id']) or {}).get('data') or {}
        content=det.get('content') or ''
        checks.append({
            **t,
            'remote_found': True,
            'chapter_id': ch.get('id'),
            'remote_name': det.get('name'),
            'is_locked': det.get('is_locked'),
            'word_count': det.get('word_count'),
            'content_len': len(content),
            'local_vs_remote_hint': 'local_short_likely_ok' if len(content) < 6000 else 'remote_full_available_repair',
        })
    out.append({
        'folder':book['folder'],
        'book_id':bid,
        'book_name':book['book_name'],
        'checks':checks,
    })
res=Path(r'C:\Dev\MTC_Download\logs\short_chapter_remote_check.json')
res.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(str(res))
