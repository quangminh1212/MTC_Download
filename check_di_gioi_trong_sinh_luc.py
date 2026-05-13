import json, re, sys
from pathlib import Path
from mtc_downloader import MTCDownloader
from download_completed_to_mtc import clean_filename
if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8', errors='replace')
folder = Path(r'C:\Dev\MTC\Dị Giới Trọng Sinh Lục')
books = json.loads(Path(r'C:\Dev\MTC_Download\completed_books.json').read_text(encoding='utf-8'))
match = None
for b in books:
    if clean_filename(b.get('name') or '') == folder.name:
        match = b
        break
pat=re.compile(r'(?i)(?:chương|chuong)\s*(\d+)')
files=[]
for p in sorted(folder.glob('*.txt')):
    m=pat.search(p.name)
    text=''
    try:
        text=p.read_text(encoding='utf-8', errors='replace')[:500]
    except Exception:
        pass
    files.append({'name':p.name,'idx':int(m.group(1)) if m else None,'size':p.stat().st_size,'head':text})
idxs=[f['idx'] for f in files if f['idx'] is not None]
seen=set(idxs)
d=MTCDownloader()
book_id=int(match['id']) if match else None
detail=(d.get_book_detail(book_id) or {}).get('data') or {} if book_id else {}
remote_rows=(d.get_chapters(book_id,page=1,limit=1000) or {}).get('data') or [] if book_id else []
remote_indexes=sorted({int(c.get('index') or c.get('number') or 0) for c in remote_rows if c.get('index') or c.get('number')})
remote_target=[]
for c in remote_rows:
    try: idx=int(c.get('index') or c.get('number') or 0)
    except: idx=0
    if idx==32:
        remote_target.append({'id':c.get('id'),'index':idx,'name':c.get('name') or c.get('title')})
remote_ch=None
if remote_target:
    rcid=remote_target[0]['id']
    data=(d.get_chapter_content(rcid) or {}).get('data') or {}
    content=(data.get('content') or data.get('body') or '')
    remote_ch={
        'id': rcid,
        'name': data.get('name') or remote_target[0]['name'],
        'content_len': len(content),
        'preview': str(content)[:300]
    }
out={
    'folder': str(folder),
    'matched_book_id': book_id,
    'matched_book_name': match.get('name') if match else None,
    'local_file_count': len(files),
    'local_unique_indexes': len(seen),
    'metadata_expected': int(match.get('chapter_count') or match.get('latest_index') or 0) if match else None,
    'missing_by_metadata': [i for i in range(1, (int(match.get('chapter_count') or match.get('latest_index') or 0) if match else 0)+1) if i not in seen],
    'duplicates': {str(i): [f['name'] for f in files if f['idx']==i] for i in sorted(seen) if idxs.count(i)>1},
    'small_files': [ {'idx':f['idx'],'name':f['name'],'size':f['size'],'head':f['head']} for f in files if f['size']<5000 ],
    'remote_detail': {k: detail.get(k) for k in ['id','name','chapter_count','latest_index','status','status_name']},
    'remote_index_count': len(remote_indexes),
    'remote_missing_local': [i for i in remote_indexes if i not in seen],
    'remote_ch32': remote_ch,
}
p=Path(r'C:\Dev\MTC_Download\logs\di_gioi_trong_sinh_luc_check.json')
p.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))
print(str(p))
