#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Download every missing completed MTC book into D:\\Dev\\MTC_Done.

Uses helpers from download_all_missing_books, only swapping the target ROOT.
Reads the pre-built missing list from
``logs/mtc_done_missing_books.json`` (built once from the live API scan).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_ROOT))

import download_all_missing_books as dam
from mtc_downloader import MTCDownloader

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

TARGET_ROOT = Path(r"D:\Dev\MTC_Done")
LOG_DIR = Path(r"C:\Dev\MTC_Download\logs")
MISSING_PATH = LOG_DIR / "mtc_done_missing_books.json"
STATE_PATH = LOG_DIR / "download_missing_to_done_state.json"
STATE_BACKUP = LOG_DIR / "download_missing_to_done_state.json.bak"
STATE_LOCK = LOG_DIR / "download_missing_to_done_state.lock"

# Re-target every helper inside download_all_missing_books to MTC_Done.
dam.ROOT = TARGET_ROOT


def load_state() -> dict:
    for path in (STATE_PATH, STATE_BACKUP):
        if not path.exists():
            continue
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
    return {"done": [], "errors": []}


def save_state(state: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(state, ensure_ascii=False, indent=2)
    tmp_path = STATE_PATH.with_suffix(STATE_PATH.suffix + f".{os.getpid()}.tmp")
    tmp_path.write_text(payload, encoding="utf-8")
    if STATE_PATH.exists():
        try:
            os.replace(STATE_PATH, STATE_BACKUP)
        except OSError:
            pass
    os.replace(tmp_path, STATE_PATH)


def _acquire_lock(timeout: float = 30.0) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + timeout
    while True:
        try:
            fd = os.open(str(STATE_LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return
        except FileExistsError:
            if time.time() > deadline:
                try:
                    STATE_LOCK.unlink()
                except FileNotFoundError:
                    pass
                continue
            time.sleep(0.05)


def _release_lock() -> None:
    try:
        STATE_LOCK.unlink()
    except FileNotFoundError:
        pass


def merge_state_record(record: dict, *, kind: str) -> None:
    """Append a record under a coarse file lock so multiple shards don't clobber each other."""
    _acquire_lock()
    try:
        state = load_state()
        bucket = state.setdefault(kind, [])
        rid = int(record.get("id") or 0)
        if rid:
            existing = {int(r.get("id") or 0) for r in bucket}
            if rid in existing:
                return
        bucket.append(record)
        save_state(state)
    finally:
        _release_lock()


def build_queue() -> list[dict]:
    payload = json.loads(MISSING_PATH.read_text(encoding="utf-8"))
    rows = payload.get("missing") or []
    queue = []
    for row in rows:
        book_id = int(row.get("id") or 0)
        if not book_id:
            continue
        chapter_count = int(row.get("chapter_count") or 0)
        if chapter_count <= 0:
            continue
        queue.append({
            "id": book_id,
            "name": row.get("name"),
            "chapter_count": chapter_count,
            "status_name": row.get("status_name"),
            "clean_name": dam.strict_book_name(row.get("name") or f"book {book_id}"),
            "updated_at": row.get("updated_at"),
        })
    queue.sort(key=lambda b: (b["chapter_count"], b["id"]))
    return queue


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--max-chapters", type=int, default=None)
    parser.add_argument("--min-chapters", type=int, default=None)
    parser.add_argument("--delay", type=float, default=0.10)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=24)
    parser.add_argument("--book-id", type=int, default=None)
    parser.add_argument("--shard", type=int, default=0,
                        help="this shard index (0-based)")
    parser.add_argument("--shard-count", type=int, default=1,
                        help="number of parallel shards")
    args = parser.parse_args()

    TARGET_ROOT.mkdir(parents=True, exist_ok=True)
    downloader = MTCDownloader()

    if args.book_id:
        detail = downloader.get_book_detail(args.book_id)
        data = (detail or {}).get("data") or {}
        if not data:
            print(f"ERROR: book {args.book_id} not found")
            return 2
        queue = [{
            "id": args.book_id,
            "name": data.get("name"),
            "chapter_count": int(data.get("chapter_count") or data.get("latest_index") or 0),
            "status_name": data.get("status_name"),
            "clean_name": dam.strict_book_name(data.get("name") or f"book {args.book_id}"),
            "updated_at": data.get("updated_at"),
        }]
    else:
        queue = build_queue()

    if args.shard_count and args.shard_count > 1:
        queue = [b for b in queue if (int(b["id"]) % args.shard_count) == args.shard]

    if args.min_chapters is not None:
        queue = [b for b in queue if b["chapter_count"] >= args.min_chapters]
    if args.max_chapters is not None:
        queue = [b for b in queue if b["chapter_count"] <= args.max_chapters]
    if args.limit is not None:
        queue = queue[: args.limit]

    state = load_state()
    done_ids = {int(row["id"]) for row in state.get("done", [])}
    folder_norms = {dam.alnum_norm(p.name)
                    for p in TARGET_ROOT.iterdir()
                    if p.is_dir() and not p.name.startswith(".")}

    total = len(queue)
    print(f"queue={total} root={TARGET_ROOT} done_state={len(done_ids)}", flush=True)
    for seq, book in enumerate(queue, 1):
        book_id = int(book["id"])
        if book_id in done_ids:
            print(f"[{seq}/{total}] SKIP done state {book_id} {book['name']}", flush=True)
            continue
        if dam.alnum_norm(book["clean_name"]) in folder_norms:
            print(f"[{seq}/{total}] SKIP local exists {book_id} {book['name']}", flush=True)
            merge_state_record({"id": book_id, "name": book["name"], "status": "exists"}, kind="done")
            done_ids.add(book_id)
            continue

        print(
            f"[{seq}/{total}] {book_id} {book['name']} "
            f"chapters={book['chapter_count']} status={book['status_name']}",
            flush=True,
        )
        try:
            result = dam.download_book(downloader, book, args.delay, args.workers, args.batch_size)
        except Exception as exc:
            result = {"id": book_id, "folder": book["clean_name"], "status": "exception", "error": str(exc)}
        result.setdefault("name", book["name"])
        print(
            f"  => status={result.get('status')} ok={result.get('ok',0)} "
            f"skip={result.get('skip',0)} fail={result.get('fail',0)}",
            flush=True,
        )
        if result.get("status") in ("ok", "no_chapters", "exists"):
            merge_state_record(result, kind="done")
            done_ids.add(book_id)
            folder_norms.add(dam.alnum_norm(book["clean_name"]))
        else:
            merge_state_record(result, kind="errors")
        time.sleep(0.2)

    errors = len(state.get("errors", []))
    print(f"\nDONE: processed={total} errors={errors}")
    print(f"STATE={STATE_PATH}")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
