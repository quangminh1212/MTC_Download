#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, sys, time, re
from pathlib import Path
import requests

EMAIL=sys.argv[1]
PASSWORD=sys.argv[2]
ROOT=Path(r'C:\Dev\MTC_Download')
MANIFEST=ROOT/'logs'/'bookmarked_books_manifest.json'
OUT=ROOT/'bookmarked_downloads'
LOG=ROOT/'logs'/'bookmarked_download_progress.json'
BASE='https://android.lonoapp.net/api'
DELAY=float(sys.argv[3]) if len(sys.argv)>3 else 0.35
MAX_BOOKS=int(sys.argv[4]) if len(sys.argv)>4 else 0

INVALID='<>:"/\\|?*'
def safe(name):
    if not name: return 'unknown'
    for c in INVALID: name=name.replace(c,'_')
    name=re.sub(r'\s+', ' ', name).strip().rstrip('.')
    return name[:170] or 'unknown'

def load_json(path, default):
    if path.exists():
        try: return json.loads(path.read_text(encoding='utf-8'))
        except Exception: return default
    return default

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

s=requests.Session()
s.headers.update({'User-Agent':'MTC/Android','Accept':'application/json','Content-Type':'application/json'})
r=s.post(BASE+'/auth/login', json={'email':EMAIL,'password':PASSWORD,'device_name':'OpenClaw Windows'}, timeout=30)
r.encoding='utf-8'
print('login', r.status_code, flush=True)
r.raise_for_status()
token=r.json()['data']['token']
s.headers.update({'Authorization':f'Bearer {token}'})

manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
books=manifest['books']
if MAX_BOOKS>0: books=books[:MAX_BOOKS]
progress=load_json(LOG, {'books':{}, 'started_at':time.strftime('%Y-%m-%d %H:%M:%S')})
OUT.mkdir(parents=True, exist_ok=True)

def get_json(url, params=None, retries=4):
    for attempt in range(retries):
        try:
            rr=s.get(url, params=params, timeout=35)
            rr.encoding='utf-8'
            if rr.status_code==429:
                time.sleep(3+attempt*2); continue
            rr.raise_for_status()
            return rr.json()
        except Exception as e:
            if attempt==retries-1: raise
            time.sleep(2+attempt*2)

for bi,b in enumerate(books,1):
    bid=int(b['id'])
    name=b.get('name') or f'book_{bid}'
    bkey=str(bid)
    bdir=OUT/f"{safe(name)}__{bid}"
    bdir.mkdir(parents=True, exist_ok=True)
    bp=progress['books'].setdefault(bkey, {'id':bid,'name':name,'status':'pending','downloaded':0,'failed':[]})
    if bp.get('status')=='complete':
        print(f"[{bi}/{len(books)}] skip complete {bid} {name}", flush=True)
        continue
    print(f"\n[{bi}/{len(books)}] BOOK {bid} {name}", flush=True)
    try:
        detail=get_json(BASE+f'/books/{bid}')
        (bdir/'info.json').write_text(json.dumps(detail.get('data',detail), ensure_ascii=False, indent=2), encoding='utf-8')
        chapters=[]; page=1
        while True:
            j=get_json(BASE+'/chapters', params={'filter[book_id]':bid,'page':page,'limit':100})
            items=j.get('data') or []
            if not items: break
            chapters.extend(items)
            pagination = j.get('pagination') or {}
            if not pagination:
                break
            current = pagination.get('current') or page
            last = pagination.get('last') or current
            if current >= last:
                break
            if len(items)<100:
                break
            page+=1; time.sleep(DELAY)
        (bdir/'chapters_manifest.json').write_text(json.dumps(chapters, ensure_ascii=False, indent=2), encoding='utf-8')
        bp['expected']=len(chapters)
        bp['latest_index']=b.get('latest_index')
        bp['status']='downloading'
        save_json(LOG, progress)
        ok=0; failed=[]
        for idx,ch in enumerate(chapters,1):
            cid=ch.get('id')
            f=bdir/f"chapter_{idx:04d}_{cid}.json"
            if f.exists() and f.stat().st_size>30:
                ok+=1; continue
            try:
                cj=get_json(BASE+f'/chapters/{cid}')
                f.write_text(json.dumps(cj.get('data',cj), ensure_ascii=False, indent=2), encoding='utf-8')
                ok+=1
            except Exception as e:
                failed.append({'index':idx,'id':cid,'name':ch.get('name'),'error':str(e)[:300]})
            if idx%25==0 or idx==len(chapters):
                bp['downloaded']=ok; bp['failed']=failed; bp['updated_at']=time.strftime('%Y-%m-%d %H:%M:%S')
                save_json(LOG, progress)
                print(f"  chapters {idx}/{len(chapters)} ok={ok} fail={len(failed)}", flush=True)
            time.sleep(DELAY)
        bp['downloaded']=ok; bp['failed']=failed; bp['status']='complete' if ok==len(chapters) and not failed else 'partial'
        bp['updated_at']=time.strftime('%Y-%m-%d %H:%M:%S')
        save_json(LOG, progress)
        print(f"DONE {bid}: {bp['status']} {ok}/{len(chapters)} fail={len(failed)}", flush=True)
    except Exception as e:
        bp['status']='error'; bp['error']=str(e)[:500]; bp['updated_at']=time.strftime('%Y-%m-%d %H:%M:%S')
        save_json(LOG, progress)
        print(f"ERROR {bid}: {e}", flush=True)
        time.sleep(3)
print('ALL DONE/STOPPED', flush=True)
