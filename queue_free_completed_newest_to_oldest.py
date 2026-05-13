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
STATE_PATH = LOG_DIR / "free_completed_queue_state.json"
QUEUE_PATH = LOG_DIR / "free_completed_queue.json"
DOWNLOADER = Path(r"C:\Dev\MTC_Download\download_one_completed_live_decrypt.py")


def parse_dt(s):
    if not s:
        return datetime.min
    try:
        return datetime.fromisoformat(str(s).replace('Z', '+00:00'))
    except Exception:
        return datetime.min


def folder_for(book: dict) -> Path:
    return ROOT / clean_filename(book.get('name') or f"book_{book.get('id')}")


def count_good_txt(folder: Path) -> int:
    if not folder.exists():
        return 0
    return sum(1 for p in folder.glob('*.txt') if p.is_file() and p.stat().st_size >= 5000)


def is_downloaded(book: dict) -> bool:
    expected = int(book.get('chapter_count') or book.get('latest_index') or 0)
    if expected <= 0:
        return False
    return count_good_txt(folder_for(book)) >= expected


def build_queue(limit_pages: int = 30, check_top: int = 500) -> list[dict]:
    d = MTCDownloader()
    books = []
    for page in range(1, limit_pages + 1):
        data = d.get_books(limit=100, page=page) or {}
        rows = data.get('data') or []
        if not rows:
            break
        books.extend(rows)
        if len(rows) < 100:
            break

    completed = [b for b in books if b.get('status_name') == 'Hoàn thành' or b.get('status') == 2]
    completed.sort(key=lambda b: (parse_dt(b.get('updated_at')), parse_dt(b.get('new_chap_at')), parse_dt(b.get('published_at'))), reverse=True)

    queue = []
    checked = 0
    for b in completed:
        if checked >= check_top:
            break
        checked += 1
        bid = int(b['id'])
        expected = int(b.get('chapter_count') or b.get('latest_index') or 0)
        if expected <= 0:
            continue
        if is_downloaded(b):
            continue
        chapters = (d.get_chapters(bid, page=1, limit=2000) or {}).get('data') or []
        if not chapters:
            continue
        sample = [chapters[0], chapters[len(chapters)//2], chapters[-1]]
        uniq = []
        seen = set()
        for x in sample:
            cid = x.get('id')
            if cid in seen:
                continue
            seen.add(cid)
            uniq.append(x)
        ok = True
        samples = []
        for ch in uniq:
            det = (d.get_chapter_content(ch['id']) or {}).get('data') or {}
            content = det.get('content') or ''
            row = {
                'index': det.get('index'),
                'id': det.get('id'),
                'is_locked': det.get('is_locked'),
                'word_count': det.get('word_count'),
                'content_len': len(content),
            }
            samples.append(row)
            if row['is_locked'] not in (0, None) or row['content_len'] < 2000:
                ok = False
        if not ok:
            continue
        queue.append({
            'id': bid,
            'name': b.get('name'),
            'chapter_count': expected,
            'updated_at': b.get('updated_at'),
            'new_chap_at': b.get('new_chap_at'),
            'published_at': b.get('published_at'),
            'samples': samples,
        })
    return queue


def run_book(book: dict, delay: float, per_run_timeout: int = 1800) -> int:
    cmd = [sys.executable, str(DOWNLOADER), '--book-id', str(book['id']), '--delay', str(delay)]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=per_run_timeout)
    runlog = LOG_DIR / f"queue_book_{book['id']}.log"
    runlog.write_text((p.stdout or '') + "\n[stderr]\n" + (p.stderr or ''), encoding='utf-8')
    return p.returncode


def save_state(state: dict):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')


def main() -> int:
    delay = 0.12
    queue = build_queue()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    QUEUE_PATH.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding='utf-8')
    state = {
        'generated_at': datetime.now().isoformat(),
        'queue_size': len(queue),
        'current': None,
        'done': [],
        'skipped': [],
        'failed': [],
    }
    save_state(state)
    print(f'queue_size={len(queue)}')

    for book in queue:
        expected = int(book['chapter_count'])
        folder = folder_for(book)
        state['current'] = {
            'id': book['id'],
            'name': book['name'],
            'chapter_count': expected,
            'folder': str(folder),
        }
        save_state(state)
        print(f"START {book['id']} | {book['name']} | expected={expected}")

        attempts = 0
        while count_good_txt(folder) < expected and attempts < 20:
            attempts += 1
            try:
                rc = run_book(book, delay)
            except subprocess.TimeoutExpired:
                rc = 124
            have = count_good_txt(folder)
            print(f"attempt={attempts} rc={rc} have={have}/{expected}")
            if have >= expected:
                break
            time.sleep(2)

        have = count_good_txt(folder)
        if have >= expected:
            state['done'].append({'id': book['id'], 'name': book['name'], 'have': have, 'expected': expected})
            print(f"DONE {book['id']} {book['name']} {have}/{expected}")
        else:
            state['failed'].append({'id': book['id'], 'name': book['name'], 'have': have, 'expected': expected})
            print(f"FAIL {book['id']} {book['name']} {have}/{expected}")
        save_state(state)

    state['current'] = None
    save_state(state)
    print('ALL_QUEUE_DONE')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
