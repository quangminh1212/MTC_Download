#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Download completed MTC stories to C:\\Dev\\MTC.

Output format:
  C:\\Dev\\MTC\\<Tên truyện>\\Chương N Tên chương.txt

Uses the same public app API discovered by the existing MTC_Download tooling.
Does not use credentials, DRM bypasses, or locked-content workarounds.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

from mtc_downloader import MTCDownloader

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT_OUT = Path(r"C:\Dev\MTC")
LOG_DIR = Path(r"C:\Dev\MTC_Download\logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

INVALID = '<>:"/\\|?*!'
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"[ \t\r\f\v]+")
CHAPTER_PREFIX_RE = re.compile(r"^\s*(?:chương|chuong)\s*\d+\s*[:.\-–—]?\s*", re.I)
STRIP_PUNCT_RE = re.compile(r"[^\w\sÀ-ỹà-ỹĐđ]+", re.UNICODE)


def clean_filename(name: str, max_len: int = 170) -> str:
    name = html.unescape(str(name or ""))
    name = re.sub(r"[\x00-\x1f\x7f]", " ", name).strip()
    # Remove punctuation/separators that tend to create duplicate folder names or messy git paths.
    name = STRIP_PUNCT_RE.sub(" ", name)
    for ch in INVALID:
        name = name.replace(ch, " ")
    name = re.sub(r"\s+", " ", name).strip(" .")
    return (name or "Untitled")[:max_len].strip(" .")


def safe_book_dir_name(name: str) -> str:
    """Folder name used in C:\\Dev\\MTC. Must match cleanup logic."""
    return clean_filename(name)


def clean_text(value: Any) -> str:
    text = str(value or "")
    text = html.unescape(text)
    text = text.replace("<br />", "\n").replace("<br/>", "\n").replace("<br>", "\n")
    text = re.sub(r"</p\s*>", "\n\n", text, flags=re.I)
    text = TAG_RE.sub("", text)
    lines = []
    for line in text.splitlines():
        line = WS_RE.sub(" ", line).strip()
        lines.append(line)
    # collapse too many blank lines
    out = []
    blanks = 0
    for line in lines:
        if not line:
            blanks += 1
            if blanks <= 1:
                out.append("")
        else:
            blanks = 0
            out.append(line)
    return "\n".join(out).strip() + "\n"


def chapter_filename(chapter: dict, fallback_index: int) -> str:
    idx = chapter.get("index") or chapter.get("number") or fallback_index
    try:
        idx_int = int(idx)
    except Exception:
        idx_int = fallback_index
    raw_name = chapter.get("name") or chapter.get("title") or ""
    title = CHAPTER_PREFIX_RE.sub("", str(raw_name)).strip(" :.\u2013\u2014-")
    title = clean_filename(title, max_len=130)
    return f"Chương {idx_int} {title}.txt" if title else f"Chương {idx_int}.txt"


def write_chapter(path: Path, book_name: str, chapter_name: str, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    body = clean_text(content)
    header = f"{'='*60}\n{chapter_name}\n{'='*60}\n\n"
    path.write_text(header + body, encoding="utf-8")


def get_all_books(d: MTCDownloader, limit_pages: int | None = None) -> list[dict]:
    books = []
    page = 1
    while True:
        data = d.get_books(limit=100, page=page)
        rows = (data or {}).get("data") or []
        if not rows:
            break
        books.extend(rows)
        print(f"[BOOKS] page={page} got={len(rows)} total={len(books)}")
        if len(rows) < 100:
            break
        if limit_pages and page >= limit_pages:
            break
        page += 1
        time.sleep(0.2)
    return books


def get_all_chapters(d: MTCDownloader, book_id: int) -> list[dict]:
    chapters = []
    page = 1
    while True:
        data = d.get_chapters(book_id, page=page, limit=100)
        rows = (data or {}).get("data") or []
        if not rows:
            break
        chapters.extend(rows)
        if len(rows) < 100:
            break
        page += 1
        time.sleep(0.15)
    def key(c: dict):
        try:
            return int(c.get("index") or 0)
        except Exception:
            return 0
    return sorted(chapters, key=key)


def download_completed(
    max_books: int | None = None,
    delay: float = 0.35,
    min_chapters: int = 1,
    book_ids: list[int] | None = None,
):
    out_root = ROOT_OUT
    out_root.mkdir(parents=True, exist_ok=True)
    d = MTCDownloader()

    all_books = get_all_books(d)
    completed = [b for b in all_books if b.get("status_name") == "Hoàn thành" or b.get("status") == 2]

    if book_ids:
        idset = set(book_ids)
        completed = [b for b in completed if int(b.get("id", -1)) in idset]
    else:
        completed = [b for b in completed if int(b.get("chapter_count") or b.get("latest_index") or 0) >= min_chapters]

    completed.sort(key=lambda b: int(b.get("chapter_count") or b.get("latest_index") or 0))

    if max_books:
        completed = completed[:max_books]
    manifest_path = LOG_DIR / "completed_manifest.json"
    manifest_path.write_text(json.dumps(completed, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[MANIFEST] completed={len(completed)} saved={manifest_path}")

    summary = []
    for bi, book in enumerate(completed, 1):
        book_id = int(book["id"])
        book_name = clean_filename(book.get("name") or f"book_{book_id}")
        book_dir = out_root / book_name
        book_dir.mkdir(parents=True, exist_ok=True)
        (book_dir / "info.json").write_text(json.dumps(book, ensure_ascii=False, indent=2), encoding="utf-8")

        print(f"\n[BOOK {bi}/{len(completed)}] {book_name} id={book_id}")
        chapters = get_all_chapters(d, book_id)
        print(f"[BOOK] chapters={len(chapters)} expected={book.get('chapter_count') or book.get('latest_index')}")

        ok = 0
        fail = 0
        for ci, ch in enumerate(chapters, 1):
            fname = chapter_filename(ch, ci)
            fpath = book_dir / fname
            if fpath.exists() and fpath.stat().st_size > 200:
                ok += 1
                continue
            cid = ch.get("id")
            detail = d.get_chapter_content(cid)
            data = (detail or {}).get("data") or {}
            content = data.get("content") or data.get("body") or ""
            if not content:
                fail += 1
                print(f"  [MISS] {ci}/{len(chapters)} id={cid} {fname}")
                time.sleep(delay)
                continue
            display_name = data.get("name") or ch.get("name") or f"Chương {ci}"
            try:
                write_chapter(fpath, book_name, display_name, content)
                ok += 1
                if ok % 25 == 0 or ci == len(chapters):
                    print(f"  [OK] {ok}/{len(chapters)} last={fname}")
            except Exception as e:
                fail += 1
                print(f"  [ERR] {ci}/{len(chapters)} {fname}: {e}")
            time.sleep(delay)

        item = {"id": book_id, "name": book_name, "chapters": len(chapters), "ok": ok, "fail": fail}
        summary.append(item)
        (LOG_DIR / "completed_progress.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[DONE] {book_name}: ok={ok} fail={fail}")

    print("\nALL DONE")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-books", type=int, default=None, help="Limit number of completed books for smoke test")
    ap.add_argument("--delay", type=float, default=0.35, help="Delay between chapter requests")
    ap.add_argument("--min-chapters", type=int, default=1, help="Skip books below this chapter count (default 1)")
    ap.add_argument("--book-id", action="append", type=int, default=[], help="Only download specific completed book ID (repeatable)")
    args = ap.parse_args()
    download_completed(
        max_books=args.max_books,
        delay=args.delay,
        min_chapters=args.min_chapters,
        book_ids=args.book_id or None,
    )


if __name__ == "__main__":
    main()
