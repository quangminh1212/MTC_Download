import json, re, sys, unicodedata
from pathlib import Path
sys.path.insert(0, r"C:\Dev\MTC_DOWNLOAD")
from mtc_downloader import MTCDownloader
from download_completed_to_mtc import clean_filename, chapter_filename
from queue_free_completed_newest_to_oldest import parse_dt
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"C:\Dev\MTC")
OUT = Path(r"C:\Dev\MTC_DOWNLOAD\logs\free_completed_queue_exact.json")
D = MTCDownloader()
def norm(s):
    s = unicodedata.normalize('NFC', str(s)).casefold()
    return ''.join(ch for ch in s if ch.isalnum())
folder_map = {norm(p.name): p for p in ROOT.iterdir() if p.is_dir() and p.name != '.git'}
books = []
for page in range(1, 31):
    data = D.get_books(limit=100, page=page) or {}
    rows = data.get('data') or []
    if not rows:
        break
    books.extend(rows)
    if len(rows) < 100:
        break
completed = [b for b in books if b.get('status_name') == 'Hoàn thành' or b.get('status') == 2]
completed.sort(key=lambda b: (parse_dt(b.get('updated_at')), parse_dt(b.get('new_chap_at')), parse_dt(b.get('published_at'))), reverse=True)
queue = []
for b in completed:
    bid = int(b['id'])
    expected = int(b.get('chapter_count') or b.get('latest_index') or 0)
    if expected <= 0:
        continue
    folder_name = clean_filename(b.get('name') or f'book_{bid}')
    folder = folder_map.get(norm(folder_name))
    chapters = (D.get_chapters(bid, page=1, limit=2000) or {}).get('data') or []
    if not chapters:
        continue
    expected_names = {chapter_filename(ch, i) for i, ch in enumerate(chapters, 1)}
    expected_norms = {norm(name) for name in expected_names}
    # free check by samples
    sample = [chapters[0], chapters[len(chapters)//2], chapters[-1]]
    seen = set(); ok = True; samples=[]
    for ch in sample:
        cid = ch.get('id')
        if cid in seen: continue
        seen.add(cid)
        det = (D.get_chapter_content(cid) or {}).get('data') or {}
        content = det.get('content') or ''
        row = {'index': det.get('index'), 'id': det.get('id'), 'is_locked': det.get('is_locked'), 'content_len': len(content)}
        samples.append(row)
        if row['is_locked'] not in (0, None) or row['content_len'] < 2000:
            ok = False
    if not ok:
        continue
    if folder:
        local_names = {p.name for p in folder.glob('*.txt')}
        local_norms = {norm(name) for name in local_names}
        if local_norms == expected_norms and (folder/'info.json').exists():
            continue
    queue.append({'id': bid, 'name': b.get('name'), 'folder': folder_name, 'chapter_count': expected, 'updated_at': b.get('updated_at'), 'new_chap_at': b.get('new_chap_at'), 'published_at': b.get('published_at'), 'samples': samples})
OUT.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding='utf-8')
print(str(OUT))
print('queue_size', len(queue))
for b in queue[:30]:
    print(f"{b['id']}\t{b['chapter_count']}\t{b['folder']}\t{b['updated_at']}")
