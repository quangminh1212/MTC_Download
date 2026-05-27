#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Manual single-book downloader: fetch book -> fetch chapter list -> fetch each chapter one by one.
No batch, no multi-book logic. Always writes only under C:\\Dev\\MTC.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
from pathlib import Path

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = "https://android.lonoapp.net/api"
ONLY_OUTPUT_DIR = Path(r"C:\Dev\MTC")
HEADERS = {
    "User-Agent": "MTC/Android",
    "Accept": "application/json",
    "Content-Type": "application/json",
}
INVALID = '<>:"/\\|?*'
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"[ \t\r\f\v]+")
CHAPTER_PREFIX_RE = re.compile(r"^\s*(?:chương|chuong)\s*\d+\s*[:.\-–—]?\s*", re.I)


def clean_filename(name: str, max_len: int = 170) -> str:
    name = html.unescape(str(name or "")).strip()
    for ch in INVALID:
        name = name.replace(ch, " ")
    name = re.sub(r"\s+", " ", name).strip(" .")
    return (name or "Untitled")[:max_len].strip(" .")


def clean_text(value: str) -> str:
    text = html.unescape(str(value or ""))
    text = text.replace("<br />", "\n").replace("<br/>", "\n").replace("<br>", "\n")
    text = re.sub(r"</p\s*>", "\n\n", text, flags=re.I)
    text = TAG_RE.sub("", text)
    lines = []
    for line in text.splitlines():
        lines.append(WS_RE.sub(" ", line).strip())
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


def write_chapter(path: Path, chapter_name: str, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    header = f"{'='*60}\n{chapter_name}\n{'='*60}\n\n"
    path.write_text(header + clean_text(content), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--book-id", type=int, required=True)
    ap.add_argument("--delay", type=float, default=0.2)
    args = ap.parse_args()

    s = requests.Session()
    s.headers.update(HEADERS)

    print("[STEP 1] Lấy thông tin truyện")
    r = s.get(f"{BASE_URL}/books/{args.book_id}", timeout=20)
    r.raise_for_status()
    book = (r.json() or {}).get("data") or {}
    if not book:
        print("ERROR: book not found")
        return 2
    if not (book.get("status_name") == "Hoàn thành" or book.get("status") == 2):
        print(f"ERROR: book {args.book_id} chưa hoàn thành")
        return 3

    book_name = clean_filename(book.get("name") or f"book_{args.book_id}")
    out_dir = ONLY_OUTPUT_DIR / book_name
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "info.json").write_text(json.dumps(book, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"book={book_name}")
    print(f"status={book.get('status_name')}")

    print("[STEP 2] Lấy danh sách chapter")
    chapters = []
    page = 1
    while True:
        rr = s.get(f"{BASE_URL}/chapters", params={"filter[book_id]": args.book_id, "page": page, "limit": 100}, timeout=20)
        rr.raise_for_status()
        rows = (rr.json() or {}).get("data") or []
        if not rows:
            break
        chapters.extend(rows)
        print(f"  page={page} got={len(rows)} total={len(chapters)}")
        if len(rows) < 100:
            break
        page += 1
        time.sleep(args.delay)

    chapters = sorted(chapters, key=lambda c: int(c.get("index") or 0), reverse=True)
    print(f"chapters_total={len(chapters)}")

    print("[STEP 3] Tải từng chapter thủ công (mới -> cũ)")
    ok = 0
    fail = 0
    for i, ch in enumerate(chapters, 1):
        cid = ch.get("id")
        name = ch.get("name") or f"Chương {i}"
        print(f"  [{i}/{len(chapters)}] chapter_id={cid} name={name}")
        rd = s.get(f"{BASE_URL}/chapters/{cid}", timeout=20)
        rd.raise_for_status()
        data = (rd.json() or {}).get("data") or {}
        content = data.get("content") or data.get("body") or ""
        if not content:
            fail += 1
            print(f"    -> MISS")
            continue
        display_name = data.get("name") or name
        fname = chapter_filename(ch, i)
        write_chapter(out_dir / fname, display_name, content)
        ok += 1
        print(f"    -> OK saved={fname}")
        time.sleep(args.delay)

    print("[STEP 4] Tổng kết")
    print(f"final_ok={ok}")
    print(f"final_fail={fail}")
    print(f"out={out_dir}")
    return 0 if fail == 0 else 4


if __name__ == "__main__":
    raise SystemExit(main())
