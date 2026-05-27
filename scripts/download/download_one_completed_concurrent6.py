#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import concurrent.futures as cf
import re
import sys
import time
from pathlib import Path

from download_completed_to_mtc import MTCDownloader, clean_filename, chapter_filename
from download_one_completed_live_decrypt import (
    ROOT,
    clean_text,
    get_chapters_once_safe,
    get_latest_completed,
    is_completed,
    maybe_decrypt,
    normalize_chapter_title,
    write_info_json,
    write_plain_chapter,
)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

INVALID = '<>:"/\\|?*!'

def clean_safe_name(name: str) -> str:
    for ch in INVALID:
        name = name.replace(ch, ' ')
    name = re.sub(r'\s+', ' ', name).strip(' .')
    return name or 'Untitled'


def safe_chapter_filename(ch: dict, fallback_index: int) -> str:
    fn = chapter_filename(ch, fallback_index)
    stem = Path(fn).stem
    return clean_safe_name(stem) + '.txt'


def download_decrypt_write(book_dir: Path, book_name: str, idx: int, total: int, ch: dict):
    cid = ch.get('id')
    fname = safe_chapter_filename(ch, idx)
    fpath = book_dir / fname
    if fpath.exists() and fpath.stat().st_size >= 5000:
        return idx, True, f'SKIP {idx}/{total} existing file={fname}'
    last_error = None
    for attempt in range(1, 4):
        try:
            d = MTCDownloader()  # session per attempt/worker for thread safety
            detail = d.get_chapter_content(cid)
            data = (detail or {}).get('data') or {}
            content = data.get('content') or data.get('body') or ''
            if not content:
                raise ValueError(f'MISS content chapter_id={cid}')
            plain, decrypted = maybe_decrypt(content)
            title = normalize_chapter_title(data.get('name') or ch.get('name') or f'Chương {idx}', idx)
            write_plain_chapter(fpath, title, plain)
            retry_note = f' retry={attempt}' if attempt > 1 else ''
            return idx, True, f'OK {idx}/{total} decrypted={decrypted}{retry_note} file={fname}'
        except Exception as e:
            last_error = e
            time.sleep(0.5 * attempt)
    return idx, False, f'FAIL {idx}/{total} chapter_id={cid} exception={last_error}'


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--book-id', type=int, default=None)
    ap.add_argument('--workers', type=int, default=6)
    ap.add_argument('--batch-size', type=int, default=6)
    args = ap.parse_args()

    ROOT.mkdir(parents=True, exist_ok=True)
    d = MTCDownloader()
    if args.book_id:
        detail = d.get_book_detail(args.book_id)
        book = (detail or {}).get('data') or {}
    else:
        book = get_latest_completed(d)
    if not book:
        print('ERROR no completed book found')
        return 2
    if not is_completed(book):
        print(f"ERROR book {book.get('id')} not completed")
        return 3

    book_id = int(book['id'])
    book_name = clean_filename(book.get('name') or f'book_{book_id}')
    book_dir = ROOT / book_name
    book_dir.mkdir(parents=True, exist_ok=True)

    chapters = get_chapters_once_safe(d, book_id)
    total = len(chapters)
    print(f'book={book_name}')
    print(f'book_id={book_id}')
    print(f'out={book_dir}')
    print(f'chapters_total={total} expected={book.get("chapter_count") or book.get("latest_index")}')
    print(f'workers={args.workers} batch_size={args.batch_size}')

    ok = fail = 0
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        for start in range(0, total, args.batch_size):
            batch = chapters[start:start + args.batch_size]
            print(f'BATCH {start+1}-{start+len(batch)} / {total}', flush=True)
            fut_map = {
                ex.submit(download_decrypt_write, book_dir, book_name, start + bi + 1, total, ch): (start + bi + 1, ch)
                for bi, ch in enumerate(batch)
            }
            results = []
            for fut in cf.as_completed(fut_map):
                idx0, ch0 = fut_map[fut]
                try:
                    results.append(fut.result())
                except Exception as e:
                    cid0 = (ch0 or {}).get('id')
                    results.append((idx0, False, f'FAIL {idx0}/{total} chapter_id={cid0} exception={e}'))
            for idx, success, msg in sorted(results, key=lambda x: x[0]):
                print(' ', msg, flush=True)
                if success:
                    ok += 1
                else:
                    fail += 1
            if fail:
                print(f'STOP fail={fail} ok={ok}')
                break

    write_info_json(book_dir, book, chapters)
    for junk in ['_decrypt_report.txt']:
        p = book_dir / junk
        if p.exists():
            p.unlink()
    print(f'final_ok={ok}')
    print(f'final_fail={fail}')
    print(f'out={book_dir}')
    return 0 if fail == 0 and ok == total else 4

if __name__ == '__main__':
    raise SystemExit(main())
