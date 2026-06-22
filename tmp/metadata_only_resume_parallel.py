import concurrent.futures as cf
import json, os, re, sys, time, traceback
from pathlib import Path

sys.path.insert(0, r'C:\Dev\MTC_Download\scripts')
sys.path.insert(0, r'C:\Dev\MTC_Download\scripts\download')
from mtc_downloader import MTCDownloader
from download_completed_to_mtc import chapter_filename
from download_one_completed_live_decrypt import maybe_decrypt, normalize_chapter_title, sanitize_path_component, write_plain_chapter

ROOT = Path(r'C:\Dev\MTC_Continune')
LOG = Path(r'C:\Dev\MTC_Download\logs\metadata_only_resume_parallel.json')
HEARTBEAT = Path(r'C:\Dev\MTC_Download\logs\metadata_only_resume_parallel.heartbeat.txt')
ID_RE = re.compile(r'"id"\s*:\s*(\d+)')
IGNORE={'.git','.githooks','.vscode','git','.claude','__pycache__'}
MAX_CHAPTER_WORKERS = 8
DELAY_BETWEEN_BOOKS = 0.2

def load_state():
    if LOG.exists():
        try:
            return json.loads(LOG.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {'started_at': time.strftime('%Y-%m-%d %H:%M:%S'), 'results': []}

def save_state(state):
    state['updated_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
    done = state.get('results', [])
    state['summary'] = {
        'processed_folders': len(done),
        'ok': sum(1 for r in done if r.get('status') == 'ok'),
        'partial': sum(1 for r in done if r.get('status') == 'partial'),
        'remote_empty': sum(1 for r in done if r.get('status') == 'remote_empty'),
        'error': sum(1 for r in done if r.get('status') == 'error'),
        'downloaded_chapters': sum(int(r.get('downloaded', 0)) for r in done),
    }
    LOG.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
    HEARTBEAT.write_text(json.dumps(state['summary'], ensure_ascii=False), encoding='utf-8')

def read_book_id(folder):
    p = folder / 'info.json'
    if not p.exists(): return None
    txt = p.read_text(encoding='utf-8', errors='replace')
    m = ID_RE.search(txt)
    return int(m.group(1)) if m else None

def folders_to_process(done_names):
    out=[]
    for folder in sorted([p for p in ROOT.iterdir() if p.is_dir() and p.name not in IGNORE], key=lambda p:p.name.lower()):
        if folder.name in done_names:
            continue
        if (folder/'info.json').exists() and not list(folder.glob('*.txt')):
            bid = read_book_id(folder)
            if bid:
                out.append((folder,bid))
    return out

def get_remote(book_id):
    d = MTCDownloader()
    rows=(d.get_chapters(book_id,page=1,limit=100) or {}).get('data') or []
    out=[]
    for seq,row in enumerate(rows,1):
        idx=int(row.get('index') or row.get('number') or seq)
        out.append((idx,seq,row))
    return sorted(out)

def download_one(args):
    folder_s, idx, seq, chapter = args
    folder = Path(folder_s)
    d = MTCDownloader()
    chapter_id=chapter.get('id')
    detail=d.get_chapter_content(chapter_id)
    data=(detail or {}).get('data') or {}
    content=data.get('content') or data.get('body') or ''
    if not content:
        raise ValueError(f'chapter {chapter_id} has no content')
    plain,_=maybe_decrypt(content)
    title=normalize_chapter_title(data.get('name') or chapter.get('name') or f'Chương {idx}', idx)
    path=folder / sanitize_path_component(chapter_filename(data or chapter, seq))
    write_plain_chapter(path, sanitize_path_component(title), plain)
    return idx, path.name, len(plain)

def main():
    state = load_state()
    done_names = {r.get('folder') for r in state.get('results', [])}
    queue = folders_to_process(done_names)
    state['remaining_at_start'] = len(queue)
    save_state(state)
    for folder, bid in queue:
        row = {'folder': folder.name, 'book_id': bid, 'started_at': time.strftime('%Y-%m-%d %H:%M:%S')}
        try:
            remote = get_remote(bid)
            row['remote_total'] = len(remote)
            if not remote:
                row['status'] = 'remote_empty'
                row['downloaded'] = 0
                row['errors'] = []
            else:
                ok=0; errors=[]
                jobs=[(str(folder), idx, seq, ch) for idx,seq,ch in remote]
                with cf.ThreadPoolExecutor(max_workers=MAX_CHAPTER_WORKERS) as ex:
                    futs={ex.submit(download_one, job): job[1] for job in jobs}
                    for fut in cf.as_completed(futs):
                        idx=futs[fut]
                        try:
                            fut.result(); ok += 1
                        except Exception as exc:
                            errors.append(f'{idx}: {exc}')
                row['status'] = 'ok' if not errors else 'partial'
                row['downloaded'] = ok
                row['errors'] = errors[:50]
        except Exception as exc:
            row['status'] = 'error'
            row['error'] = str(exc)
            row['traceback'] = traceback.format_exc()[-2000:]
        row['finished_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        state.setdefault('results', []).append(row)
        save_state(state)
        time.sleep(DELAY_BETWEEN_BOOKS)
    state['finished_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
    save_state(state)

if __name__ == '__main__':
    main()
