#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from mtc_downloader import MTCDownloader
from download_completed_to_mtc import clean_filename

ROOT = Path(r"C:\Dev\MTC")
LOG_DIR = Path(r"C:\Dev\MTC_Download\logs")
QUEUE_PATH = LOG_DIR / "free_completed_queue.json"
STATE_PATH = LOG_DIR / "free_completed_queue_state.json"
DOWNLOADER = Path(r"C:\Dev\MTC_Download\download_one_completed_live_decrypt.py")


def parse_dt(s):
    if not s:
        return datetime.min
    try: return datetime.fromisoformat(str(s).replace('Z','+00:00'))
    except Exception: return datetime.min


def folder_name(name):
    return clean_filename(name or 'Untitled')


def good_count(name):
    d = ROOT / folder_name(name)
    if not d.exists(): return 0
    return sum(1 for p in d.glob('*.txt') if p.is_file() and p.stat().st_size >= 5000)


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def sample_free(d, book):
    bid = int(book['id'])
    chapters = (d.get_chapters(bid, page=1, limit=2000) or {}).get('data') or []
    if not chapters: return False, []
    picks = [chapters[0], chapters[len(chapters)//2], chapters[-1]]
    uniq=[]; seen=set()
    for c in picks:
        cid=c.get('id')
        if cid in seen: continue
        seen.add(cid); uniq.append(c)
    rows=[]; ok=True
    for c in uniq:
        det=(d.get_chapter_content(c['id']) or {}).get('data') or {}
        content=det.get('content') or ''
        row={'index':det.get('index'),'id':det.get('id'),'is_locked':det.get('is_locked'),'word_count':det.get('word_count'),'content_len':len(content)}
        rows.append(row)
        if row['is_locked'] not in (0, None) or row['content_len'] < 2000:
            ok=False
    return ok, rows


def build_incremental(target_count=30, max_pages=30):
    d=MTCDownloader()
    queue=[]; rejected=[]
    for page in range(1, max_pages+1):
        data=d.get_books(limit=100, page=page) or {}
        rows=data.get('data') or []
        if not rows: break
        rows=[b for b in rows if b.get('status_name')=='Hoàn thành' or b.get('status')==2]
        rows.sort(key=lambda b:(parse_dt(b.get('updated_at')),parse_dt(b.get('new_chap_at')),parse_dt(b.get('published_at'))), reverse=True)
        for b in rows:
            expected=int(b.get('chapter_count') or b.get('latest_index') or 0)
            if expected<=0: continue
            have=good_count(b.get('name'))
            if have>=expected:
                rejected.append({'id':b.get('id'),'name':b.get('name'),'reason':'already_downloaded','have':have,'expected':expected})
                continue
            ok,samples=sample_free(d,b)
            item={'id':int(b['id']),'name':b.get('name'),'chapter_count':expected,'updated_at':b.get('updated_at'),'new_chap_at':b.get('new_chap_at'),'published_at':b.get('published_at'),'samples':samples}
            if ok:
                queue.append(item)
                save_json(QUEUE_PATH, {'queue':queue,'rejected_tail':rejected[-20:]})
                print(f"QUEUE {len(queue)} {item['id']} {item['name']} expected={expected}", flush=True)
                if len(queue)>=target_count:
                    return queue
            else:
                item['reason']='locked_or_short_sample'
                rejected.append(item)
        if len(rows)<100: break
    save_json(QUEUE_PATH, {'queue':queue,'rejected_tail':rejected[-50:]})
    return queue


def run_book(book):
    cmd=[sys.executable,str(DOWNLOADER),'--book-id',str(book['id']),'--delay','0.12']
    p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=1800)
    (LOG_DIR/f"queue_book_{book['id']}.log").write_text((p.stdout or '')+'\n[stderr]\n'+(p.stderr or ''),encoding='utf-8')
    return p.returncode


def main():
    queue=build_incremental(target_count=20,max_pages=30)
    state={'queue_size':len(queue),'current':None,'done':[],'failed':[]}
    save_json(STATE_PATH,state)
    print(f'queue_size={len(queue)}', flush=True)
    for book in queue:
        expected=int(book['chapter_count'])
        state['current']={'id':book['id'],'name':book['name'],'expected':expected,'have':good_count(book['name'])}
        save_json(STATE_PATH,state)
        attempts=0
        while good_count(book['name'])<expected and attempts<20:
            attempts+=1
            try: rc=run_book(book)
            except subprocess.TimeoutExpired: rc=124
            have=good_count(book['name'])
            print(f"BOOK {book['id']} attempt={attempts} rc={rc} have={have}/{expected}", flush=True)
            state['current']={'id':book['id'],'name':book['name'],'expected':expected,'have':have,'attempts':attempts,'last_rc':rc}
            save_json(STATE_PATH,state)
            if have>=expected: break
            time.sleep(2)
        have=good_count(book['name'])
        if have>=expected:
            state['done'].append({'id':book['id'],'name':book['name'],'have':have,'expected':expected})
        else:
            state['failed'].append({'id':book['id'],'name':book['name'],'have':have,'expected':expected})
        save_json(STATE_PATH,state)
    state['current']=None
    save_json(STATE_PATH,state)
    print('DONE_QUEUE', flush=True)

if __name__=='__main__': main()
