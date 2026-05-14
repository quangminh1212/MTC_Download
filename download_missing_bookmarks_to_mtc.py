#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from download_completed_to_mtc import safe_book_dir_name

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

args = sys.argv[1:]
EMAIL = None
PASSWORD = None
MAX_BOOKS = 0
if len(args) >= 2 and not str(args[0]).isdigit():
    EMAIL = args[0]
    PASSWORD = args[1]
    if len(args) > 2:
        MAX_BOOKS = int(args[2])
elif len(args) >= 1:
    MAX_BOOKS = int(args[0])
ROOT = Path(r'C:\Dev\MTC')
LOG_DIR = Path(r'C:\Dev\MTC_Download\logs')
MISSING_PATH = LOG_DIR / 'bookmarked_missing_in_mtc.json'
STATE_PATH = LOG_DIR / 'download_missing_bookmarks_to_mtc_state.json'
RUNNER = Path(r'C:\Dev\MTC_Download\download_one_book_decrypted_to_mtc.py')

LOG_DIR.mkdir(parents=True, exist_ok=True)
books = json.loads(MISSING_PATH.read_text(encoding='utf-8'))
if MAX_BOOKS > 0:
    books = books[:MAX_BOOKS]
state = {'books': []}
if STATE_PATH.exists():
    try:
        state = json.loads(STATE_PATH.read_text(encoding='utf-8'))
    except Exception:
        pass
seen_done = {str(row.get('id')) for row in state.get('books', []) if row.get('status') == 'complete'}

def safe(name: str) -> str:
    if not name:
        return 'unknown'
    return safe_book_dir_name(name)

def txt_count(folder: Path) -> int:
    if not folder.exists():
        return 0
    return sum(1 for p in folder.glob('*.txt') if p.is_file() and p.stat().st_size > 200)

for index, book in enumerate(books, 1):
    book_id = str(book['id'])
    folder = ROOT / safe(book.get('name') or book.get('folder') or '')
    expected = int(book.get('latest_index') or 0)
    if book_id in seen_done and txt_count(folder) >= expected:
        print(f"=== [{index}/{len(books)}] SKIP complete {book_id} {book['folder']}", flush=True)
        continue
    print(f"=== [{index}/{len(books)}] START {book_id} expected={expected} {book['folder']}", flush=True)
    cmd = [sys.executable, str(RUNNER)]
    if EMAIL and PASSWORD:
        cmd.extend([EMAIL, PASSWORD])
    cmd.extend([book_id, book['name'] or book['folder']])
    rc = 1
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=7200)
        rc = proc.returncode
        (LOG_DIR / f"download_missing_bookmark_{book_id}.log").write_text(
            (proc.stdout or '') + '\n[stderr]\n' + (proc.stderr or ''),
            encoding='utf-8',
        )
        if proc.stdout:
            print(proc.stdout[-2000:], flush=True)
        if proc.stderr:
            print(proc.stderr[-1000:], flush=True)
    except subprocess.TimeoutExpired as exc:
        rc = 124
        (LOG_DIR / f"download_missing_bookmark_{book_id}.log").write_text(str(exc), encoding='utf-8')
    have = txt_count(folder)
    status = 'complete' if expected == 0 or have >= expected else 'partial'
    if rc != 0 and status != 'complete':
        status = 'error'
    row = {
        'id': int(book_id),
        'name': book.get('name'),
        'folder': str(folder),
        'expected': expected,
        'have': have,
        'returncode': rc,
        'status': status,
        'updated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    state.setdefault('books', [])
    state['books'] = [x for x in state['books'] if str(x.get('id')) != book_id]
    state['books'].append(row)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(row, ensure_ascii=False), flush=True)
    if status == 'complete':
        seen_done.add(book_id)
    time.sleep(1)
print('ALL_DONE', flush=True)
