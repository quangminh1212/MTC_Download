import json, sys
from pathlib import Path
from mtc_downloader import MTCDownloader
if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8', errors='replace')
d=MTCDownloader()
targets={142470:(25,38),140878:(40,60),102973:(168,176),105459:(94,122)}
out={}
for bid,(a,b) in targets.items():
    detail=(d.get_book_detail(bid) or {}).get('data') or {}
    rows=(d.get_chapters(bid,page=1,limit=1000) or {}).get('data') or []
    arr=[]
    for ch in rows:
        try: idx=int(ch.get('index') or ch.get('number') or 0)
        except: idx=0
        if a<=idx<=b:
            arr.append({'id':ch.get('id'),'index':idx,'name':ch.get('name') or ch.get('title')})
    out[str(bid)]={'book_name': detail.get('name'), 'chapter_count': detail.get('chapter_count'), 'latest_index': detail.get('latest_index'), 'status': detail.get('status'), 'rows': sorted(arr,key=lambda x:x['index'])}
p=Path(r'C:\Dev\MTC_Download\logs\remote_missing_ranges.json')
p.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(str(p))
print(json.dumps(out,ensure_ascii=False,indent=2))
