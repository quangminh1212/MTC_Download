#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

from mtc_downloader import MTCDownloader
from mtc_status_utils import cleanup_root_completed_dirs, is_ongoing_status, is_paused_status, is_unfinished_status
from download_one_completed_live_decrypt import (
    maybe_decrypt,
    normalize_chapter_title,
    sanitize_path_component,
    write_info_json,
    write_plain_chapter,
    get_chapters_once_safe,
)
from download_all_missing_books import strict_book_name, strict_chapter_filename, strict_component

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(r'D:\\Dev\\MTC_Continune')
LOG_DIR = Path(r'C:\Dev\MTC_Download\logs')
LOG = LOG_DIR / 'ongoing_download_to_repo_report.json'
STATE = LOG_DIR / 'ongoing_download_to_repo_state.json'
QUEUE = LOG_DIR / 'ongoing_download_to_repo_queue.json'
CHAPTER_INDEX_RE = re.compile(r'(?i)(?:chương|chuong)\s*(\d+)')
MIN_VALID_CHAPTER_SIZE = 2000


def chapter_path(folder: Path, chapter: dict, seq: int) -> Path:
    filename = sanitize_path_component(strict_chapter_filename(chapter, seq))
    return folder / filename


def local_index_set(folder: Path) -> set[int]:
    out = set()
    for path in folder.glob('*.txt'):
        match = CHAPTER_INDEX_RE.search(path.stem)
        if match and path.stat().st_size >= MIN_VALID_CHAPTER_SIZE:
            out.add(int(match.group(1)))
    return out


def load_state(reset: bool) -> dict:
    if not reset and STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {
        'started_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'root': str(ROOT),
        'done_books': 0,
        'ok_books': 0,
        'issue_books': 0,
        'skipped_books': 0,
        'books': [],
    }


def save_state(data: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    LOG.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def clear_stale_git_lock() -> bool:
    lock_path = ROOT / '.git' / 'index.lock'
    if not lock_path.exists():
        return False
    git_proc = subprocess.run(
        ['powershell.exe', '-Command', 'Get-Process git -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Id'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        encoding='utf-8',
        errors='replace',
    )
    if git_proc.stdout.strip():
        return False
    try:
        lock_path.unlink()
        return True
    except Exception:
        return False


def commit_folder(folder: Path, message: str) -> dict:
    for attempt in range(3):
        status = subprocess.run(
            ['git', 'status', '--porcelain=v1', '--', folder.name],
            cwd=str(ROOT), capture_output=True, text=True, encoding='utf-8', errors='replace'
        )
        status_error = (status.stderr or '').strip()
        if status.returncode != 0:
            if 'index.lock' in status_error and clear_stale_git_lock():
                time.sleep(1)
                continue
            return {'status': 'status_failed', 'error': status_error}
        changed = [line for line in status.stdout.splitlines() if line.strip()]
        if not changed:
            return {'status': 'nothing_to_commit'}

        add = subprocess.run(
            ['git', 'add', '-A', '--', folder.name],
            cwd=str(ROOT), capture_output=True, text=True, encoding='utf-8', errors='replace'
        )
        add_error = (add.stderr or '').strip()
        if add.returncode != 0:
            if 'index.lock' in add_error and clear_stale_git_lock():
                time.sleep(1)
                continue
            return {'status': 'add_failed', 'error': add_error}

        staged = subprocess.run(
            ['git', 'diff', '--cached', '--name-only', '--', folder.name],
            cwd=str(ROOT), capture_output=True, text=True, encoding='utf-8', errors='replace'
        )
        staged_files = [line.strip() for line in staged.stdout.splitlines() if line.strip()]
        if not staged_files:
            return {'status': 'nothing_staged'}

        commit = subprocess.run(
            ['git', '-c', 'commit.gpgsign=false', '-c', 'core.hooksPath=NUL', 'commit', '--no-verify', '-m', message, '--', folder.name],
            cwd=str(ROOT), capture_output=True, text=True, encoding='utf-8', errors='replace'
        )
        output = (commit.stdout + commit.stderr).strip()
        if commit.returncode == 0:
            return {'status': 'committed', 'staged_count': len(staged_files), 'output': output[:1000]}
        if 'nothing to commit' in output.lower():
            return {'status': 'nothing_to_commit'}
        if 'index.lock' in output and clear_stale_git_lock():
            time.sleep(1)
            continue
        return {'status': 'commit_failed', 'staged_count': len(staged_files), 'error': output[:2000]}
    return {'status': 'commit_failed', 'error': 'git index.lock persisted after retries'}


def fetch_books(downloader: MTCDownloader, include_paused: bool, limit_pages: int | None) -> list[dict]:
    books = []
    page = 1
    while True:
        if limit_pages is not None and page > limit_pages:
            break
        data = downloader.get_books(limit=100, page=page)
        rows = (data or {}).get('data') or []
        print(f'books_page={page} rows={len(rows)} total={len(books) + len(rows)}', flush=True)
        if not rows:
            break
        for book in rows:
            if not is_unfinished_status(book):
                continue
            if not include_paused and not is_ongoing_status(book):
                continue
            if include_paused and not (is_ongoing_status(book) or is_paused_status(book)):
                continue
            chapter_count = int(book.get('chapter_count') or book.get('latest_index') or 0)
            if chapter_count <= 0:
                continue
            books.append(book)
        if len(rows) < 100:
            break
        page += 1
        time.sleep(0.05)
    books.sort(key=lambda item: (int(item.get('chapter_count') or item.get('latest_index') or 0), int(item['id'])))
    QUEUE.write_text(json.dumps(books, ensure_ascii=False, indent=2), encoding='utf-8')
    return books


def download_book(downloader: MTCDownloader, book: dict, delay: float) -> dict:
    book_id = int(book['id'])
    name = book.get('name') or f'book_{book_id}'
    folder = ROOT / strict_book_name(name)
    folder.mkdir(parents=True, exist_ok=True)

    chapters = get_chapters_once_safe(downloader, book_id)
    remote_by_index: dict[int, tuple[int, dict]] = {}
    for seq, chapter in enumerate(chapters, 1):
        idx = int(chapter.get('index') or chapter.get('number') or seq)
        remote_by_index[idx] = (seq, chapter)

    downloaded = skipped = failed = 0
    errors = []
    local_before = local_index_set(folder)
    missing_before = sorted(set(remote_by_index) - local_before)

    for idx in sorted(remote_by_index):
        seq, chapter = remote_by_index[idx]
        path = chapter_path(folder, chapter, seq)
        if idx in local_before and path.exists() and path.stat().st_size >= MIN_VALID_CHAPTER_SIZE:
            skipped += 1
            continue

        chapter_id = chapter.get('id')
        last_error = None
        for attempt in range(1, 5):
            try:
                detail = downloader.get_chapter_content(chapter_id)
                data = (detail or {}).get('data') or {}
                content = data.get('content') or data.get('body') or ''
                if not content:
                    raise ValueError(f'empty content chapter_id={chapter_id}')
                plain, _ = maybe_decrypt(content)
                title = normalize_chapter_title(data.get('name') or chapter.get('name') or f'Chương {idx}', idx)
                safe_title = sanitize_path_component(strict_component(title, default=f'Chương {idx}'))
                safe_path = folder / sanitize_path_component(strict_chapter_filename(data or chapter, seq))
                write_plain_chapter(safe_path, safe_title, plain)
                downloaded += 1
                last_error = None
                break
            except Exception as exc:
                last_error = exc
                time.sleep(0.35 * attempt)
        if last_error is not None:
            failed += 1
            errors.append(f'idx={idx} chapter_id={chapter_id}: {last_error}')
            print(f'  FAIL idx={idx} chapter_id={chapter_id} err={last_error}', flush=True)
        elif downloaded % 25 == 0:
            print(f'  progress downloaded={downloaded} skipped={skipped} failed={failed}', flush=True)
        time.sleep(delay)

    detail = downloader.get_book_detail(book_id)
    book_data = (detail or {}).get('data') or dict(book)
    write_info_json(folder, book_data, chapters)

    local_after = local_index_set(folder)
    missing_after = sorted(set(remote_by_index) - local_after)
    extra_after = sorted(local_after - set(remote_by_index))
    status = 'ok' if not missing_after and not extra_after and failed == 0 else 'issue'
    commit = commit_folder(folder, folder.name)
    if status == 'ok' and commit.get('status') in {'add_failed', 'commit_failed', 'status_failed'}:
        status = 'commit_failed'

    return {
        'id': book_id,
        'name': name,
        'status_name': book_data.get('status_name') or book.get('status_name'),
        'folder': folder.name,
        'remote_count': len(remote_by_index),
        'missing_before': len(missing_before),
        'downloaded': downloaded,
        'skipped': skipped,
        'failed': failed,
        'missing_after': len(missing_after),
        'extra_after': len(extra_after),
        'errors': errors[:30],
        'status': status,
        'commit': commit,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Download unfinished MTC books to C:\\Dev\\MTC_Continune and commit each folder.')
    parser.add_argument('--delay', type=float, default=0.03)
    parser.add_argument('--limit', type=int, default=None, help='Process at most N books this run.')
    parser.add_argument('--limit-pages', type=int, default=None, help='Scan at most N API book pages.')
    parser.add_argument('--include-paused', action='store_true', help='Also download Tạm dừng books. Default only Còn tiếp.')
    parser.add_argument('--reset-state', action='store_true')
    parser.add_argument('--rebuild-queue', action='store_true')
    args = parser.parse_args()

    ROOT.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    cleanup_actions = cleanup_root_completed_dirs(ROOT)
    if cleanup_actions:
        print(f'moved/deleted completed root folders: {len(cleanup_actions)}', flush=True)

    downloader = MTCDownloader()
    if QUEUE.exists() and not args.rebuild_queue:
        targets = json.loads(QUEUE.read_text(encoding='utf-8'))
        print(f'loaded_queue={len(targets)} path={QUEUE}', flush=True)
    else:
        targets = fetch_books(downloader, include_paused=args.include_paused, limit_pages=args.limit_pages)
        print(f'built_queue={len(targets)} path={QUEUE}', flush=True)

    state = load_state(reset=args.reset_state)
    done_ids = {int(row['id']) for row in state.get('books', []) if row.get('status') in {'ok', 'issue', 'commit_failed'}}
    processed = 0

    for pos, book in enumerate(targets, 1):
        if args.limit is not None and processed >= args.limit:
            break
        book_id = int(book['id'])
        if book_id in done_ids:
            continue
        print(f'\n[{pos}/{len(targets)}] book_id={book_id} status={book.get("status_name")} name={book.get("name")}', flush=True)
        try:
            row = download_book(downloader, book, args.delay)
        except Exception as exc:
            row = {
                'id': book_id,
                'name': book.get('name'),
                'status_name': book.get('status_name'),
                'folder': strict_book_name(book.get('name') or f'book_{book_id}'),
                'status': 'api_error',
                'error': str(exc),
            }
        state.setdefault('books', []).append(row)
        state['done_books'] = len(state['books'])
        state['ok_books'] = sum(1 for item in state['books'] if item.get('status') == 'ok')
        state['issue_books'] = sum(1 for item in state['books'] if item.get('status') not in {'ok'})
        save_state(state)
        done_ids.add(book_id)
        processed += 1
        commit_status = (row.get('commit') or {}).get('status')
        print(
            f"  => remote={row.get('remote_count')} downloaded={row.get('downloaded')} skipped={row.get('skipped')} "
            f"failed={row.get('failed')} missing_after={row.get('missing_after')} extra_after={row.get('extra_after')} "
            f"status={row.get('status')} commit={commit_status}",
            flush=True,
        )

    save_state(state)
    print(f'\nprocessed_this_run={processed}')
    print(f'report={LOG}')
    return 0 if state.get('issue_books', 0) == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
