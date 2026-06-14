import concurrent.futures as cf
import json
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, r'C:\Dev\MTC_Download\scripts')
sys.path.insert(0, r'C:\Dev\MTC_Download\scripts\download')

from download_unfinished_id_queue_to_repo import process_book, download_one_chapter, commit_folder

ROOT = Path(r'C:\Dev\MTC_Continune')
QUEUE = Path(r'C:\Dev\MTC_Download\logs\all_id_unfinished_missing_repo.json')
AUDIT_QUEUE = Path(r'C:\Dev\MTC_Download\logs\oldest_first_repair_queue.json')
LOG = Path(r'C:\Dev\MTC_Download\logs\oldest_first_repair_worker.log')
STATE = Path(r'C:\Dev\MTC_Download\logs\oldest_first_repair_worker_state.json')
CHAP_RE = re.compile(r'(?i)^Chương\s+(\d+)\b')
FOLDER_WORKERS = 4
CHAPTER_WORKERS = 8
BATCH_SIZE = 32
MAX_PER_RUN = 240


def log(msg: str):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with LOG.open('a', encoding='utf-8') as f:
        f.write(line + '\n')


def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text(encoding='utf-8'))
    return {'done': [], 'failed': []}


def save_state(state):
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')


def load_book_map():
    rows = json.loads(QUEUE.read_text(encoding='utf-8'))
    return {row.get('folder') or row.get('name'): row for row in rows}


def local_indices(folder: Path):
    out = set()
    for p in folder.glob('*.txt'):
        m = CHAP_RE.match(p.name)
        if m:
            out.add(int(m.group(1)))
    return out


def repair_issue(issue: dict, book_map: dict):
    folder_name = issue['folder']
    folder = ROOT / folder_name
    book = book_map.get(folder_name)
    if issue.get('status') in {'missing_info', 'bad_info'}:
        if not book:
            return {'folder': folder_name, 'status': 'skip_no_book_map'}
        result = process_book({'id': book['id'], 'name': book.get('name') or folder_name, 'chapter_count': book.get('chapter_count') or 1}, CHAPTER_WORKERS, BATCH_SIZE)
        return {'folder': folder_name, 'status': result.get('status'), 'missing_after': result.get('missing_after_count'), 'failed': result.get('failed_count')}

    info = folder / 'info.json'
    if not info.exists():
        return {'folder': folder_name, 'status': 'skip_missing_info'}
    meta = json.loads(info.read_text(encoding='utf-8'))
    chapters = meta.get('chapters') or []
    by_idx = {}
    for seq, ch in enumerate(chapters, 1):
        idx = int(ch.get('index') or ch.get('number') or seq)
        by_idx.setdefault(idx, (seq, ch))
    targets = sorted(set(issue.get('missing') or []) | set(issue.get('empty') or []))
    if not targets:
        targets = sorted(set(by_idx) - local_indices(folder))
    ok = 0
    failed = []
    for idx in targets:
        item = by_idx.get(idx)
        if not item:
            failed.append(f'missing_manifest_idx={idx}')
            continue
        seq, ch = item
        _, success, msg = download_one_chapter(folder, ch, seq)
        if success:
            ok += 1
        else:
            failed.append(msg)
        time.sleep(0.02)
    committed, commit_msg = commit_folder(folder)
    return {'folder': folder_name, 'status': 'ok' if committed and not failed else 'issue', 'redownloaded': ok, 'failed_count': len(failed), 'commit': committed, 'commit_msg': commit_msg[:200]}


def main():
    book_map = load_book_map()
    payload = json.loads(AUDIT_QUEUE.read_text(encoding='utf-8'))
    issues = payload.get('issues') or []
    state = load_state()
    done = set(state.get('done') or [])
    failed_seen = set(state.get('failed') or [])
    pending = [issue for issue in issues if issue['folder'] not in done]
    log(f'issues_total={len(issues)} pending={len(pending)} folder_workers={FOLDER_WORKERS}')
    processed = 0
    with cf.ThreadPoolExecutor(max_workers=FOLDER_WORKERS) as executor:
        for start in range(0, min(len(pending), MAX_PER_RUN), FOLDER_WORKERS):
            batch = pending[start:start + FOLDER_WORKERS]
            for issue in batch:
                log(f'start folder={issue["folder"]}')
            future_map = {executor.submit(repair_issue, issue, book_map): issue for issue in batch}
            for future in cf.as_completed(future_map):
                issue = future_map[future]
                folder = issue['folder']
                try:
                    result = future.result()
                except Exception as exc:
                    result = {'folder': folder, 'status': 'error', 'error': str(exc)}
                ok = result.get('status') == 'ok'
                if ok:
                    done.add(folder)
                else:
                    failed_seen.add(folder)
                state['done'] = sorted(done)
                state['failed'] = sorted(failed_seen)
                save_state(state)
                log(f'done folder={folder} result={json.dumps(result, ensure_ascii=False)}')
                processed += 1
    log(f'processed={processed}')


if __name__ == '__main__':
    main()
