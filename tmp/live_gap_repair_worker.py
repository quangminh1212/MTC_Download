import json, sys, time
from pathlib import Path
sys.path.insert(0, r'C:\Dev\MTC_Download\scripts')
sys.path.insert(0, r'C:\Dev\MTC_Download\scripts\download')
from download_unfinished_id_queue_to_repo import process_book
QUEUE=Path(r'C:\Dev\MTC_Download\logs\all_id_unfinished_missing_repo.json')
GAPS=Path(r'C:\Dev\MTC_Download\logs\live_recent_gap_queue.json')
LOG=Path(r'C:\Dev\MTC_Download\logs\live_gap_repair_worker.log')
def log(msg):
    line=f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with LOG.open('a',encoding='utf-8') as f: f.write(line+'\n')
queue=json.loads(QUEUE.read_text(encoding='utf-8'))
by_folder={x.get('folder') or x.get('name'):x for x in queue}
issues=json.loads(GAPS.read_text(encoding='utf-8')).get('issues') or []
for issue in issues:
    folder=issue['folder']
    book=by_folder.get(folder)
    if not book:
        log(f'skip no_map folder={folder}')
        continue
    log(f'start folder={folder} id={book.get("id")}')
    result=process_book({'id':book['id'],'name':book.get('name') or folder,'chapter_count':book.get('chapter_count') or 1}, 10, 40)
    log(f'done folder={folder} status={result.get("status")} missing={result.get("missing_after_count")} failed={result.get("failed_count")}')
