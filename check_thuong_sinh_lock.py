import json
from pathlib import Path
from mtc_downloader import MTCDownloader

d = MTCDownloader()
chapters = (d.get_chapters(110512, page=1, limit=2000) or {}).get('data') or []
idxs = {135,136,137,207,220}
out=[]
for ch in chapters:
    if int(ch.get('index') or 0) in idxs:
        detail=(d.get_chapter_content(ch['id']) or {}).get('data') or {}
        content=detail.get('content') or ''
        out.append({
            'index': detail.get('index'),
            'id': detail.get('id'),
            'name': detail.get('name'),
            'is_locked': detail.get('is_locked'),
            'unlock_price': detail.get('unlock_price'),
            'unlock_key_price': detail.get('unlock_key_price'),
            'word_count': detail.get('word_count'),
            'content_b64_len': len(content),
            'content_raw_est_bytes': int(len(content)*3/4),
        })
Path(r'C:\Dev\MTC_Download\logs\thuong_sinh_lock_check.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(r'C:\Dev\MTC_Download\logs\thuong_sinh_lock_check.json')
