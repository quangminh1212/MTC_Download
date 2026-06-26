#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Download every non-completed MTC book from mtc_extract into D:\\Dev\\MTC_Continune.

Uses helpers from download_all_missing_books, only swapping the target ROOT.
Reads the pre-built list from
``logs/mtc_extract_discovered_books.json`` (built once from the APK extract scan).
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
sys.path.insert(0, str(SCRIPT_ROOT / "download"))

import requests

import download_all_missing_books as dam
from mtc_downloader import MTCDownloader, set_global_token
from mtc_status_utils import is_completed_status

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

TARGET_ROOT = Path(r"D:\Dev\MTC_Continune")
LOG_DIR = Path(r"C:\Dev\MTC_Download\logs")
SOURCE_PATH = LOG_DIR / "mtc_extract_discovered_books.json"
STATE_PATH = LOG_DIR / "download_extract_non_completed_to_continune_state.json"
STATE_BACKUP = LOG_DIR / "download_extract_non_completed_to_continune_state.json.bak"
STATE_LOCK = LOG_DIR / "download_extract_non_completed_to_continune_state.lock"

# Re-target every helper inside download_all_missing_books to MTC_Continune.
dam.ROOT = TARGET_ROOT


def login(email: str, password: str, retries: int = 3) -> str:
    """Login to MTC and return a Bearer token."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "MTC/Android",
        "Accept": "application/json",
        "Content-Type": "application/json",
    })
    for attempt in range(1, retries + 1):
        try:
            response = session.post(
                "https://android.lonoapp.net/api/auth/login",
                json={"email": email, "password": password, "device_name": "OpenClaw Windows"},
                timeout=30,
            )
            response.encoding = "utf-8"
            print(f"login status={response.status_code}", flush=True)
            response.raise_for_status()
            data = response.json()
            if not data.get("success"):
                raise SystemExit(f"login failed: {data}")
            return data["data"]["token"]
        except Exception as exc:
            if attempt == retries:
                raise SystemExit(f"login failed after {retries} attempts: {exc}")
            time.sleep(2 + attempt)
    raise SystemExit("login unreachable")


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
    payload = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    rows = payload.get("books") or []
    queue = []
    for row in rows:
        if is_completed_status(row):
            continue
        book_id = int(row.get("id") or 0)
        if not book_id:
            continue
        chapter_count = int(row.get("chapter_count") or row.get("latest_index") or 0)
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
    parser.add_argument("--dry-run", action="store_true",
                        help="only list what would be downloaded")
    parser.add_argument("--email", type=str, default=None,
                        help="MTC account email (for locked chapters)")
    parser.add_argument("--password", type=str, default=None,
                        help="MTC account password")
    parser.add_argument("--accessibility-check", type=str, default=None,
                        help="JSON file from check_mtc_extract_accessibility.py to skip not_found books")
    args = parser.parse_args()

    TARGET_ROOT.mkdir(parents=True, exist_ok=True)
    if args.email and args.password:
        token = login(args.email, args.password)
        set_global_token(token)
        print(f"authenticated as {args.email}", flush=True)
    downloader = MTCDownloader()

    if args.book_id:
        data: dict | None = None
        if SOURCE_PATH.exists():
            try:
                payload = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
                for row in payload.get("books") or []:
                    if int(row.get("id") or 0) == args.book_id:
                        data = row
                        break
            except Exception:
                data = None
        if not data:
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

    if args.accessibility_check:
        check_path = Path(args.accessibility_check)
        if check_path.exists():
            check_data = json.loads(check_path.read_text(encoding="utf-8"))
            reachable = {
                int(b["id"]) for b in check_data.get("books", [])
                if b.get("status") in ("ok", "chapters_only")
            }
            before = len(queue)
            queue = [b for b in queue if int(b["id"]) in reachable]
            print(f"accessibility filtered: {before} -> {len(queue)} reachable", flush=True)

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
    print(f"queue={total} root={TARGET_ROOT} done_state={len(done_ids)} local_folders={len(folder_norms)}", flush=True)

    if args.dry_run:
        for seq, book in enumerate(queue, 1):
            book_id = int(book["id"])
            exists = dam.alnum_norm(book["clean_name"]) in folder_norms
            done = book_id in done_ids
            print(
                f"[{seq}/{total}] {book_id} {book['name']} "
                f"chapters={book['chapter_count']} status={book['status_name']} "
                f"local_exists={exists} done_state={done}",
                flush=True,
            )
        return 0

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
