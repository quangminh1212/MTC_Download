#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Download exactly ONE completed MTC story from first to last chapter.

Usage:
  python download_one_completed_book.py --book-id 127805

Rules:
- Only handles one book per run
- Refuses non-completed books
- Downloads all chapters sequentially
- Writes only under C:\\Dev\\MTC
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ONLY_OUTPUT_DIR = Path(r"C:\Dev\MTC")

from download_completed_to_mtc import (
    MTCDownloader,
    clean_filename,
    chapter_filename,
    get_all_chapters,
    write_chapter,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def is_completed(book: dict) -> bool:
    return book.get("status_name") == "Hoàn thành" or book.get("status") == 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--book-id", type=int, required=True)
    args = ap.parse_args()

    d = MTCDownloader()
    detail = d.get_book_detail(args.book_id)
    book = (detail or {}).get("data") or {}
    if not book:
        print(f"ERROR: book {args.book_id} not found")
        return 2
    if not is_completed(book):
        print(f"ERROR: book {args.book_id} is not completed")
        return 3

    book_name = clean_filename(book.get("name") or f"book_{args.book_id}")
    out_root = ONLY_OUTPUT_DIR
    book_dir = out_root / book_name
    book_dir.mkdir(parents=True, exist_ok=True)
    (book_dir / "info.json").write_text(json.dumps(book, ensure_ascii=False, indent=2), encoding="utf-8")

    chapters = get_all_chapters(d, args.book_id)
    print(f"book={book_name}")
    print(f"book_id={args.book_id}")
    print(f"chapters_total={len(chapters)}")

    ok = 0
    fail = 0
    for i, ch in enumerate(chapters, 1):
        cid = ch.get("id")
        detail = d.get_chapter_content(cid)
        data = (detail or {}).get("data") or {}
        content = data.get("content") or data.get("body") or ""
        if not content:
            fail += 1
            print(f"miss={i} chapter_id={cid}")
            continue
        fname = chapter_filename(ch, i)
        display_name = data.get("name") or ch.get("name") or f"Chương {i}"
        write_chapter(book_dir / fname, book_name, display_name, content)
        ok += 1
        if ok % 10 == 0 or ok == len(chapters):
            print(f"ok={ok}/{len(chapters)} last={fname}")

    print(f"final_ok={ok}")
    print(f"final_fail={fail}")
    print(f"out={book_dir}")
    return 0 if fail == 0 else 4


if __name__ == "__main__":
    raise SystemExit(main())
