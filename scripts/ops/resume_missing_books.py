#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from download_completed_to_mtc import clean_filename

ROOT = Path(r"C:\Dev\MTC")
LOG_DIR = Path(r"C:\Dev\MTC_Download\logs")
DOWNLOADER = Path(r"C:\Dev\MTC_Download\download_one_completed_live_decrypt.py")

BOOKS = [
    {"id": 142470, "name": "Devil'S Path: Quỷ Giới Và Nhẫn Giới", "expected": 322},
    {"id": 140878, "name": "Marvel: Ta Là Tiểu Chiến Sỹ Họ Stark", "expected": 122},
    {"id": 102973, "name": "Nhị Thứ Nguyên Thần Tượng Âm Nhạc", "expected": 376},
    {"id": 105459, "name": "Siêu Dự Bị", "expected": 121},
]


def file_count(name: str) -> int:
    folder = ROOT / clean_filename(name)
    if not folder.exists():
        return 0
    return sum(1 for p in folder.glob('*.txt') if p.is_file())


def run_once(book: dict, timeout_seconds: int = 1800) -> int:
    cmd = [sys.executable, str(DOWNLOADER), '--book-id', str(book['id']), '--delay', '0.10']
    p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout_seconds)
    log = LOG_DIR / f"resume_missing_{book['id']}.log"
    log.write_text((p.stdout or '') + '\n[stderr]\n' + (p.stderr or ''), encoding='utf-8')
    return p.returncode


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    state = {'books': []}
    for book in BOOKS:
        attempts = 0
        have = file_count(book['name'])
        while have < book['expected'] and attempts < 8:
            attempts += 1
            try:
                rc = run_once(book)
            except subprocess.TimeoutExpired:
                rc = 124
            have = file_count(book['name'])
            row = {
                'id': book['id'],
                'name': book['name'],
                'expected': book['expected'],
                'have': have,
                'attempts': attempts,
                'last_rc': rc,
            }
            print(json.dumps(row, ensure_ascii=False), flush=True)
            time.sleep(2)
        state['books'].append({
            'id': book['id'],
            'name': book['name'],
            'expected': book['expected'],
            'have': have,
            'done': have >= book['expected'],
            'attempts': attempts,
        })
        (LOG_DIR / 'resume_missing_books_state.json').write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
