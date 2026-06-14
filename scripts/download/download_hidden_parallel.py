#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parallel-book wrapper for hidden discovered books.

Runs N books concurrently, each book using its own chapter-level worker pool
inside download_all_missing_books.py. Reuses the same discovered list and
state file as download_hidden_discovered_books.py so progress remains
resumable and compatible.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import subprocess
import sys
import threading
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

STATUS_NAMES = {
    "completed": "Ho\u00e0n th\u00e0nh",
    "ongoing": "C\u00f2n ti\u1ebfp",
    "paused": "T\u1ea1m d\u1eebng",
}

_state_lock = threading.Lock()
_folder_lock = threading.Lock()


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


def filter_books(books: list[dict], args: argparse.Namespace) -> list[dict]:
    out = [b for b in books if int(b.get("chapter_count") or 0) >= args.min_chapters]
    if args.status != "all":
        expected = STATUS_NAMES[args.status]
        out = [b for b in out if str(b.get("status_name") or "") == expected]
    if args.max_chapters is not None:
        out = [b for b in out if int(b.get("chapter_count") or 0) <= args.max_chapters]
    if args.order == "small":
        out.sort(key=lambda b: (int(b.get("chapter_count") or 0), int(b["id"])))
    elif args.order == "large":
        out.sort(key=lambda b: (-int(b.get("chapter_count") or 0), int(b["id"])))
    else:
        out.sort(key=lambda b: int(b["id"]))
    return out


def run_one_book(
    book: dict,
    args: argparse.Namespace,
    state: dict,
    done_ids: set[int],
    failed_ids: set[int],
    folder_norms: set[str],
    total: int,
    index: int,
) -> None:
    book_id = int(book["id"])
    name = book.get("name")
    folder_name = strict_book_name(name or f"book {book_id}")
    norm = alnum_norm(folder_name)

    with _folder_lock:
        already_done = book_id in done_ids
        already_local = norm in folder_norms

    if already_done or already_local:
        print(f"[{index}/{total}] SKIP {book_id} {name}", flush=True)
        with _state_lock:
            state.setdefault("skipped", []).append({"id": book_id, "name": name})
            save_state(state)
        return

    print(
        f"[{index}/{total}] START {book_id} {name} "
        f"chapters={book.get('chapter_count')} status={book.get('status_name')}",
        flush=True,
    )
    cmd = [
        sys.executable,
        str(DOWNLOADER),
        "--book-id", str(book_id),
        "--delay", str(args.delay),
        "--workers", str(args.chapter_workers),
        "--batch-size", str(args.batch_size),
    ]
    start = time.time()
    try:
        proc = subprocess.run(
            cmd,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=args.book_timeout,
            capture_output=True,
        )
        rc = proc.returncode
        stdout_tail = (proc.stdout or "").splitlines()[-3:]
        stderr_tail = (proc.stderr or "").splitlines()[-3:]
    except subprocess.TimeoutExpired:
        rc = 124
        stdout_tail = []
        stderr_tail = ["TIMEOUT"]
    elapsed = round(time.time() - start, 2)

    row = {
        "id": book_id,
        "name": name,
        "chapter_count": book.get("chapter_count"),
        "status_name": book.get("status_name"),
        "elapsed_seconds": elapsed,
        "returncode": rc,
    }
    with _state_lock:
        if rc == 0:
            state.setdefault("done", []).append(row)
            done_ids.add(book_id)
        else:
            row["stdout_tail"] = stdout_tail
            row["stderr_tail"] = stderr_tail
            state.setdefault("failed", []).append(row)
            failed_ids.add(book_id)
        save_state(state)
    with _folder_lock:
        folder_norms.add(norm)
    print(
        f"[{index}/{total}] DONE {book_id} rc={rc} elapsed={elapsed}s name={name}",
        flush=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--min-chapters", type=int, default=1)
    parser.add_argument("--max-chapters", type=int, default=None)
    parser.add_argument("--delay", type=float, default=0.05)
    parser.add_argument("--book-workers", type=int, default=4,
                        help="Number of books processed concurrently")
    parser.add_argument("--chapter-workers", type=int, default=4,
                        help="Chapter-level workers per book subprocess")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--order", choices=["small", "large", "id"], default="small")
    parser.add_argument("--status", choices=["all", "completed", "ongoing", "paused"], default="all")
    parser.add_argument("--book-timeout", type=int, default=14400,
                        help="Per-book subprocess timeout in seconds")
    args = parser.parse_args()

    books = json.loads(DISCOVERED.read_text(encoding="utf-8"))
    books = filter_books(books, args)

    state = load_state()
    done_ids = {int(row["id"]) for row in state.get("done", [])}
    failed_ids = {int(row["id"]) for row in state.get("failed", [])}
    folder_norms = local_folder_norms()
    if args.limit is not None:
        books = books[: args.limit]

    total = len(books)
    print(
        f"queue={total} book_workers={args.book_workers} "
        f"chapter_workers={args.chapter_workers} state_done={len(done_ids)} "
        f"state_failed={len(failed_ids)}",
        flush=True,
    )

    with cf.ThreadPoolExecutor(max_workers=max(1, args.book_workers)) as pool:
        futures = []
        for index, book in enumerate(books, 1):
            futures.append(pool.submit(
                run_one_book, book, args, state, done_ids, failed_ids,
                folder_norms, total, index,
            ))
        for future in cf.as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                print(f"WORKER_ERROR {exc!r}", flush=True)

    print(
        json.dumps(
            {
                "processed_this_run": len(state.get("done", [])),
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
