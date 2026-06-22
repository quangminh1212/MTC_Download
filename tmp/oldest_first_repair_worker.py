import json
import re
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
CHAP_RE = re.compile(r'(?i)^Chương\s+(\d+)\b')


def log(msg: str):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    with LOG.open('a', encoding='utf-8') as f:
        f.write(line + '\n')


def load_book_map():
    rows = json.loads(QUEUE.read_text(encoding='utf-8'))
    out = {}
    for row in rows:
        out[row.get('folder') or row.get('name')] = row
    return out


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
        result = process_book({'id': book['id'], 'name': book.get('name') or folder_name, 'chapter_count': book.get('chapter_count') or 1}, 12, 48)
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
        time.sleep(0.03)
    committed, commit_msg = commit_folder(folder)
    return {'folder': folder_name, 'status': 'ok' if committed and not failed else 'issue', 'redownloaded': ok, 'failed_count': len(failed), 'commit': committed, 'commit_msg': commit_msg[:200]}


def main():
    book_map = load_book_map()
    payload = json.loads(AUDIT_QUEUE.read_text(encoding='utf-8'))
    issues = payload.get('issues') or []
    log(f'issues_total={len(issues)}')
    processed = 0
    for issue in issues:
        folder_name = issue['folder']
        log(f'start folder={folder_name}')
        try:
            result = repair_issue(issue, book_map)
            log(f'done folder={folder_name} result={json.dumps(result, ensure_ascii=False)}')
        except Exception as exc:
            log(f'error folder={folder_name} err={exc}')
        processed += 1
        if processed >= 100:
            break
    log(f'processed={processed}')


if __name__ == '__main__':
    main()
