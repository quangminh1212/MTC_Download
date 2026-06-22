#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from mtc_downloader import MTCDownloader
from download_one_completed_live_decrypt import (
    get_chapters_once_safe,
    maybe_decrypt,
    normalize_chapter_title,
    write_info_json,
    write_plain_chapter,
    sanitize_path_component,
)
from download_completed_to_mtc import chapter_filename

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(r'C:\Dev\MTC')
NUM_RE = re.compile(r'(\d+)')


def status_folders() -> list[str]:
    out = subprocess.check_output(['git','status','--porcelain','-z'], cwd=str(ROOT))
    items = [p.decode('utf-8','replace') for p in out.split(b'\x00') if p]
    tops = []
    seen = set()
    for item in items:
        path = item[3:] if len(item) > 3 else ''
        if ' -> ' in path:
            path = path.split(' -> ',1)[1]
        top = path.split('/',1)[0].split('\\',1)[0]
        if top and top not in seen:
            seen.add(top)
            tops.append(top)
    return tops


def chapter_indexes(folder: Path) -> set[int]:
    out = set()
    for path in folder.glob('*.txt'):
        match = NUM_RE.search(path.stem)
        if match:
            out.add(int(match.group(1)))
    return out


def main() -> int:
    downloader = MTCDownloader()
    targets = []
    for top in status_folders():
        folder = ROOT / top
        info_path = folder / 'info.json'
        if not folder.is_dir() or not info_path.exists():
            continue
        try:
            info = json.loads(info_path.read_text(encoding='utf-8'))
        except Exception:
            continue
        latest = int(info.get('latest_index') or info.get('chapter_count') or 0)
        have = chapter_indexes(folder)
        if latest > 0 and len(have) != latest:
            targets.append((folder, info, latest, have))
    print(f'targets={len(targets)}')
    failures = 0
    for idx, (folder, info, old_latest, have) in enumerate(targets, 1):
        book_id = int(info.get('id') or 0)
        print(f'[{idx}/{len(targets)}] {folder.name} id={book_id} local={len(have)} old_latest={old_latest}')
        if not book_id:
            failures += 1
            continue
        try:
            detail = downloader.get_book_detail(book_id)
            book = (detail or {}).get('data') or info
            chapters = get_chapters_once_safe(downloader, book_id)
        except Exception as exc:
            print(f'  FAIL refresh metadata: {exc}')
            failures += 1
            continue
        latest = int(book.get('latest_index') or book.get('chapter_count') or len(chapters) or 0)
        fresh_have = chapter_indexes(folder)
        missing = [ch for ch in chapters if int(ch.get('index') or 0) not in fresh_have]
        missing.sort(key=lambda ch: int(ch.get('index') or 0))
        print(f'  remote={len(chapters)} latest={latest} missing={len(missing)}')
        for ch in missing:
            cid = ch.get('id')
            cidx = int(ch.get('index') or 0)
            try:
                detail = downloader.get_chapter_content(cid)
                data = (detail or {}).get('data') or {}
                content = data.get('content') or data.get('body') or ''
                if not content:
                    raise ValueError('empty content')
                plain, decrypted = maybe_decrypt(content)
                title = normalize_chapter_title(data.get('name') or ch.get('name') or f'Ch??ng {cidx}', cidx)
                safe_name = sanitize_path_component(chapter_filename(ch, cidx))
                write_plain_chapter(folder / safe_name, title, plain)
                print(f'    OK index={cidx} id={cid} decrypted={decrypted}')
            except Exception as exc:
                print(f'    FAIL index={cidx} id={cid} error={exc}')
                failures += 1
            time.sleep(0.10)
        write_info_json(folder, book, chapters)
        final_have = chapter_indexes(folder)
        print(f'  final={len(final_have)}/{latest}')
        if len(final_have) != latest:
            failures += 1
    return 0 if failures == 0 else 1

if __name__ == '__main__':
    raise SystemExit(main())
