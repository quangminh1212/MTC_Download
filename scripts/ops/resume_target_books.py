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
    {"id": 112190, "name": "Biển Vô Tận: Toàn Chức Vua Câu Cá", "expected": 181},
    {"id": 121843, "name": "Bắt Đầu Từ Kiếm Ma", "expected": 344},
    {"id": 100677, "name": "Công Cuộc Bị 999 Em Gái Chinh Phục", "expected": 1106},
    {"id": 127805, "name": "Tiền Hạo Kiếp Tây Du", "expected": 51},
]


def good_count(name: str) -> int:
    folder = ROOT / clean_filename(name)
    if not folder.exists():
        return 0
    return sum(1 for p in folder.glob('*.txt') if p.is_file() and p.stat().st_size >= 5000)


def run_once(book: dict, timeout_seconds: int = 1800) -> int:
    cmd = [sys.executable, str(DOWNLOADER), '--book-id', str(book['id']), '--delay', '0.10']
    p = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout_seconds)
    log = LOG_DIR / f"resume_{book['id']}.log"
    log.write_text((p.stdout or '') + '\n[stderr]\n' + (p.stderr or ''), encoding='utf-8')
    return p.returncode


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    state = {'books': []}
    for book in BOOKS:
        attempts = 0
        have = good_count(book['name'])
        while have < book['expected'] and attempts < 20:
            attempts += 1
            try:
                rc = run_once(book)
            except subprocess.TimeoutExpired:
                rc = 124
            have = good_count(book['name'])
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
        (LOG_DIR / 'resume_target_books_state.json').write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
