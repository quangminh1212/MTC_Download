import json, re, sys
from pathlib import Path
from mtc_downloader import MTCDownloader
from download_completed_to_mtc import clean_filename
if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8', errors='replace')
folder = Path(r'C:\Dev\MTC\Tận Thế Xuyên Việt Giả')
books = json.loads(Path(r'C:\Dev\MTC_Download\completed_books.json').read_text(encoding='utf-8'))
# find by folder/name
matches=[]
for b in books:
    if clean_filename(b.get('name') or '') == folder.name or 'Tận Thế' in (b.get('name') or ''):
        matches.append(b)
pat=re.compile(r'(?i)(?:chương|chuong)\s*(\d+)')
files=[]
if folder.exists():
    for p in sorted(folder.glob('*.txt')):
        m=pat.search(p.name)
        files.append({'name':p.name,'idx':int(m.group(1)) if m else None,'size':p.stat().st_size})
idxs=[f['idx'] for f in files if f['idx'] is not None]
seen=set(idxs)
expected = None
book_id = None
book_name = None
for b in matches:
    if clean_filename(b.get('name') or '') == folder.name:
        expected=int(b.get('chapter_count') or b.get('latest_index') or 0)
        book_id=int(b['id'])
        book_name=b.get('name')
        break
if book_id:
    d=MTCDownloader()
    detail=(d.get_book_detail(book_id) or {}).get('data') or {}
    remote_rows=(d.get_chapters(book_id,page=1,limit=1000) or {}).get('data') or []
    remote_indexes=sorted({int(c.get('index') or c.get('number') or 0) for c in remote_rows if c.get('index') or c.get('number')})
else:
    detail={}
    remote_indexes=[]
out={
    'folder_exists': folder.exists(),
    'folder': str(folder),
    'matched_book_id': book_id,
    'matched_book_name': book_name,
    'local_file_count': len(files),
    'local_unique_indexes': len(seen),
    'local_minmax': [min(idxs) if idxs else None, max(idxs) if idxs else None],
    'metadata_expected': expected,
    'local_missing_by_metadata': [i for i in range(1,(expected or 0)+1) if i not in seen][:50] if expected else None,
    'local_missing_count_by_metadata': len([i for i in range(1,(expected or 0)+1) if i not in seen]) if expected else None,
    'duplicates': {str(i): [f for f in files if f['idx']==i] for i in sorted(seen) if idxs.count(i)>1},
    'remote_detail': {k: detail.get(k) for k in ['id','name','chapter_count','latest_index','status','status_name']},
    'remote_index_count': len(remote_indexes),
    'remote_minmax': [min(remote_indexes) if remote_indexes else None, max(remote_indexes) if remote_indexes else None],
    'local_missing_by_remote_indexes': [i for i in remote_indexes if i not in seen][:100],
    'extra_local_not_remote': [i for i in sorted(seen) if remote_indexes and i not in set(remote_indexes)][:100],
    'last20_files': files[-20:],
}
p=Path(r'C:\Dev\MTC_Download\logs\tan_the_xuyen_viet_gia_check.json')
p.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))
print(str(p))
