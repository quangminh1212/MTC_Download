#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Count completed MTC books in a given ID range."""
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
OUT = LOG_DIR / "completed_books_count.json"
STATE = LOG_DIR / "completed_books_count_state.json"

_thread_local = threading.local()


def session() -> requests.Session:
    current = getattr(_thread_local, "session", None)
    if current is None:
        current = requests.Session()
        current.headers.update({"User-Agent": "MTC/Android", "Accept": "application/json"})
        _thread_local.session = current
    return current


def check_one(book_id: int) -> dict | None:
    try:
        response = session().get(
            BASE + "/chapters",
            params={"filter[book_id]": book_id, "limit": 1, "page": 1},
            timeout=8,
        )
        if response.status_code != 200:
            return {"id": book_id, "status": "empty"}
        payload = response.json()
        book = (payload.get("extra") or {}).get("book") or {}
        if not book:
            return {"id": book_id, "status": "empty"}
        status = int(book.get("status") or 0)
        latest = int(book.get("latest_index") or book.get("chapter_count") or 0)
        name = book.get("name") or f"book {book_id}"
        status_name = book.get("status_name", "")
        if status == 2:
            return {
                "id": int(book.get("id") or book_id),
                "name": name,
                "status": status,
                "status_name": status_name,
                "chapter_count": latest,
            }
        return {"id": book_id, "status": "not_completed"}
    except Exception as exc:
        return {"id": book_id, "status": "error", "error": str(exc)[:160]}


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"scanned_blocks": [], "completed": [], "errors": [], "stats": {}}


def save_outputs(state: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    completed = [item for item in state.get("completed", []) if item.get("status") == 2]
    completed.sort(key=lambda x: x["id"])
    errors = [item for item in state.get("errors", [])]
    stats = {
        "range_start": state.get("range_start"),
        "range_end": state.get("range_end"),
        "completed": len(completed),
        "errors": len(errors),
        "not_completed_or_empty": state.get("not_completed_or_empty", 0),
    }
    state["stats"] = stats
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT.write_text(
        json.dumps(
            {"stats": stats, "completed": completed, "errors": errors},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=100009)
    parser.add_argument("--end", type=int, default=153616)
    parser.add_argument("--block-size", type=int, default=2000)
    parser.add_argument("--workers", type=int, default=32)
    args = parser.parse_args()

    state = load_state()
    state["range_start"] = args.start
    state["range_end"] = args.end
    done = {tuple(block) for block in state.get("scanned_blocks", [])}
    completed_count = len(state.get("completed", []))
    not_completed_count = state.get("not_completed_or_empty", 0)
    error_count = len(state.get("errors", []))
    started = time.time()

    for block_start in range(args.start, args.end + 1, args.block_size):
        block_end = min(args.end, block_start + args.block_size - 1)
        block_key = (block_start, block_end)
        if block_key in done:
            print(f"skip block={block_start}-{block_end}", flush=True)
            continue
        ids = list(range(block_start, block_end + 1))
        found = []
        errors = []
        not_completed = 0
        with cf.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            for row in pool.map(check_one, ids):
                if row.get("status") == 2:
                    found.append(row)
                elif row.get("status") in {"error"}:
                    errors.append(row)
                else:
                    not_completed += 1
        state.setdefault("completed", []).extend(found)
        state.setdefault("errors", []).extend(errors)
        state["not_completed_or_empty"] = state.get("not_completed_or_empty", 0) + not_completed
        state.setdefault("scanned_blocks", []).append([block_start, block_end])
        completed_count += len(found)
        error_count += len(errors)
        not_completed_count += not_completed
        elapsed = time.time() - started
        print(
            f"block={block_start}-{block_end} completed={len(found)} "
            f"total_completed={completed_count} not_completed={not_completed_count} "
            f"errors={error_count} elapsed={elapsed:.1f}s",
            flush=True,
        )
        save_outputs(state)

    save_outputs(state)
    print(f"DONE: completed={completed_count} not_completed_or_empty={not_completed_count} errors={error_count}")
    print(f"OUT={OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
