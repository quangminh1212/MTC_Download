#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from download_all_missing_books import ROOT, alnum_norm, strict_book_name

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(r"C:\Dev\MTC_Download")
LOG_DIR = BASE / "logs"
DISCOVERED = LOG_DIR / "hidden_books_discovered.json"
STATE = LOG_DIR / "download_hidden_discovered_state.json"
DOWNLOADER = BASE / "download_all_missing_books.py"


def local_folder_norms() -> set[str]:
    return {
        alnum_norm(path.name)
        for path in ROOT.iterdir()
        if path.is_dir() and not path.name.startswith(".")
    }


def load_state() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"done": [], "failed": [], "skipped": []}


def save_state(state: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--min-chapters", type=int, default=1)
    parser.add_argument("--max-chapters", type=int, default=None)
    parser.add_argument("--delay", type=float, default=0.10)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--order", choices=["small", "large", "id"], default="small")
    parser.add_argument("--status", choices=["all", "completed", "ongoing", "paused"], default="all")
    args = parser.parse_args()

    books = json.loads(DISCOVERED.read_text(encoding="utf-8"))
    books = [book for book in books if int(book.get("chapter_count") or 0) >= args.min_chapters]
    if args.status != "all":
        status_names = {
            "completed": "\u0048\u006f\u00e0\u006e\u0020\u0074\u0068\u00e0\u006e\u0068",
            "ongoing": "\u0043\u00f2\u006e\u0020\u0074\u0069\u1ebf\u0070",
            "paused": "\u0054\u1ea1\u006d\u0020\u0064\u1eeb\u006e\u0067",
        }
        expected_status = status_names[args.status]
        books = [book for book in books if str(book.get("status_name") or "") == expected_status]
    if args.max_chapters is not None:
        books = [book for book in books if int(book.get("chapter_count") or 0) <= args.max_chapters]
    if args.order == "small":
        books.sort(key=lambda book: (int(book.get("chapter_count") or 0), int(book["id"])))
    elif args.order == "large":
        books.sort(key=lambda book: (-int(book.get("chapter_count") or 0), int(book["id"])))
    else:
        books.sort(key=lambda book: int(book["id"]))

    state = load_state()
    done_ids = {int(row["id"]) for row in state.get("done", [])}
    failed_ids = {int(row["id"]) for row in state.get("failed", [])}
    folder_norms = local_folder_norms()
    if args.limit is not None:
        books = books[: args.limit]

    print(f"queue={len(books)} state_done={len(done_ids)} state_failed={len(failed_ids)}")
    processed = 0
    for index, book in enumerate(books, 1):
        book_id = int(book["id"])
        folder_name = strict_book_name(book.get("name") or f"book {book_id}")
        if book_id in done_ids or alnum_norm(folder_name) in folder_norms:
            print(f"[{index}/{len(books)}] SKIP {book_id} {book.get('name')}", flush=True)
            state.setdefault("skipped", []).append({"id": book_id, "name": book.get("name")})
            save_state(state)
            continue
        print(
            f"[{index}/{len(books)}] DOWNLOAD {book_id} {book.get('name')} "
            f"chapters={book.get('chapter_count')} status={book.get('status_name')}",
            flush=True,
        )
        cmd = [
            sys.executable,
            str(DOWNLOADER),
            "--book-id",
            str(book_id),
            "--delay",
            str(args.delay),
            "--workers",
            str(args.workers),
            "--batch-size",
            str(args.batch_size),
        ]
        start = time.time()
        try:
            proc = subprocess.run(cmd, text=True, encoding="utf-8", errors="replace", timeout=14400)
            rc = proc.returncode
        except subprocess.TimeoutExpired:
            rc = 124
        elapsed = round(time.time() - start, 2)
        folder_norms = local_folder_norms()
        row = {
            "id": book_id,
            "name": book.get("name"),
            "chapter_count": book.get("chapter_count"),
            "status_name": book.get("status_name"),
            "elapsed_seconds": elapsed,
            "returncode": rc,
        }
        if rc == 0:
            state.setdefault("done", []).append(row)
            done_ids.add(book_id)
            processed += 1
        else:
            state.setdefault("failed", []).append(row)
            failed_ids.add(book_id)
        save_state(state)
        print(f"  RESULT id={book_id} rc={rc} elapsed={elapsed}s", flush=True)
        time.sleep(0.5)

    print(
        json.dumps(
            {
                "processed_this_run": processed,
                "done_total": len(state.get("done", [])),
                "failed_total": len(state.get("failed", [])),
                "state": str(STATE),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
