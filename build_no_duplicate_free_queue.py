import json
from datetime import datetime
from pathlib import Path
from mtc_downloader import MTCDownloader
from download_completed_to_mtc import clean_filename

ROOT=Path(r'C:\Dev\MTC')
BOOKS_PATH=Path(r'C:\Dev\MTC_Download\completed_books.json')
OUT=Path(r'C:\Dev\MTC_Download\logs\free_completed_queue_no_existing_folders.json')

def parse_dt(s):
    if not s: return datetime.min
    try: return datetime.fromisoformat(str(s).replace('Z','+00:00'))
    except Exception: return datetime.min

def exists_by_name(name):
    target=clean_filename(name or 'Untitled').lower()
    for d in ROOT.iterdir():
        if d.is_dir() and d.name.lower()==target:
            return True
    return False

def sample_free(d,b):
    chapters=(d.get_chapters(int(b['id']),page=1,limit=2000) or {}).get('data') or []
    if not chapters: return False,[]
    picks=[chapters[0],chapters[len(chapters)//2],chapters[-1]]
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
        if row['is_locked'] not in (0,None) or row['content_len']<2000: ok=False
    return ok,rows

books=json.loads(BOOKS_PATH.read_text(encoding='utf-8'))
completed=[b for b in books if b.get('status_name')=='Hoàn thành' or b.get('status')==2]
completed.sort(key=lambda b:(parse_dt(b.get('updated_at')),parse_dt(b.get('new_chap_at')),parse_dt(b.get('published_at'))), reverse=True)
d=MTCDownloader(); queue=[]; skipped=[]
for b in completed:
    expected=int(b.get('chapter_count') or b.get('latest_index') or 0)
    if expected<=0: continue
    if exists_by_name(b.get('name')):
        skipped.append({'id':b.get('id'),'name':b.get('name'),'reason':'folder_exists'})
        continue
    ok,samples=sample_free(d,b)
    if ok:
        queue.append({'id':int(b['id']),'name':b.get('name'),'chapter_count':expected,'updated_at':b.get('updated_at'),'new_chap_at':b.get('new_chap_at'),'published_at':b.get('published_at'),'samples':samples})
        print(json.dumps(queue[-1],ensure_ascii=True), flush=True)
        if len(queue)>=10: break
    else:
        skipped.append({'id':b.get('id'),'name':b.get('name'),'reason':'locked_or_short_sample'})
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({'queue':queue,'skipped_tail':skipped[-50:]},ensure_ascii=False,indent=2),encoding='utf-8')
print(str(OUT))
