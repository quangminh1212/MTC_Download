#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Re-check all book IDs in range using /books/{id} endpoint to find missed books."""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import sys
import threading
import time
from pathlib import Path

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://android.lonoapp.net/api"
LOG_DIR = Path(r"C:\Dev\MTC_Download\logs")
OUT = LOG_DIR / "all_books_by_id_inventory.json"
STATE = LOG_DIR / "all_books_by_id_inventory_state.json"

_thread_local = threading.local()


def session() -> requests.Session:
    current = getattr(_thread_local, "session", None)
    if current is None:
        current = requests.Session()
        current.headers.update({"User-Agent": "MTC/Android", "Accept": "application/json"})
        _thread_local.session = current
    return current


def check_book(book_id: int) -> dict:
    try:
        response = session().get(BASE + f"/books/{book_id}", timeout=8)
        if response.status_code == 404:
            return {"id": book_id, "exists": False}
        if response.status_code != 200:
            return {"id": book_id, "exists": False, "http_status": response.status_code}
        payload = response.json()
        book = payload.get("data") or {}
        if not book:
            return {"id": book_id, "exists": False}
        status = int(book.get("status") or 0)
        chapter_count = int(book.get("latest_index") or book.get("chapter_count") or 0)
        return {
            "id": int(book.get("id") or book_id),
            "exists": True,
            "name": book.get("name") or f"book {book_id}",
            "status": status,
            "status_name": book.get("status_name", ""),
            "chapter_count": chapter_count,
        }
    except Exception as exc:
        return {"id": book_id, "exists": False, "error": str(exc)[:160]}


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"scanned_blocks": [], "books": [], "errors": []}


def save_outputs(state: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    books = [item for item in state.get("books", []) if item.get("exists")]
    books.sort(key=lambda x: x["id"])
    errors = [item for item in state.get("errors", [])]
    by_status: dict[str, int] = {}
    for book in books:
        key = book.get("status_name") or str(book.get("status") or "unknown")
        by_status[key] = by_status.get(key, 0) + 1
    stats = {
        "range_start": state.get("range_start"),
        "range_end": state.get("range_end"),
        "total_books": len(books),
        "empty": (state.get("range_end", 0) - state.get("range_start", 0) + 1) - len(books),
        "errors": len(errors),
        "by_status": by_status,
    }
    state["stats"] = stats
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT.write_text(
        json.dumps({"stats": stats, "books": books, "errors": errors}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=100009)
    parser.add_argument("--end", type=int, default=153616)
    parser.add_argument("--block-size", type=int, default=2000)
    parser.add_argument("--workers", type=int, default=64)
    args = parser.parse_args()

    state = load_state()
    state["range_start"] = args.start
    state["range_end"] = args.end
    done = {tuple(block) for block in state.get("scanned_blocks", [])}
    started = time.time()

    for block_start in range(args.start, args.end + 1, args.block_size):
        block_end = min(args.end, block_start + args.block_size - 1)
        block_key = (block_start, block_end)
        if block_key in done:
            print(f"skip block={block_start}-{block_end}", flush=True)
            continue
        ids = list(range(block_start, block_end + 1))
        books = []
        errors = []
        with cf.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            for row in pool.map(check_book, ids):
                if row.get("error"):
                    errors.append(row)
                elif row.get("exists"):
                    books.append(row)
        state.setdefault("books", []).extend(books)
        state.setdefault("errors", []).extend(errors)
        state.setdefault("scanned_blocks", []).append([block_start, block_end])
        save_outputs(state)
        elapsed = time.time() - started
        print(
            f"block={block_start}-{block_end} books={len(books)} errors={len(errors)} "
            f"total_books={len(state['books'])} elapsed={elapsed:.1f}s",
            flush=True,
        )

    save_outputs(state)
    stats = state.get("stats", {})
    print(f"DONE: total_books={stats.get('total_books')} empty={stats.get('empty')} errors={stats.get('errors')}")
    print(f"by_status={stats.get('by_status')}")
    print(f"OUT={OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
