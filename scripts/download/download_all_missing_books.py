#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Download every book from the live API that has no local folder in C:\\Dev\\MTC.

  - Folder / file names: only letters + digits + spaces (strict-clean)
  - Chapter matching: alnum-norm (strip non-alnum before comparing)
  - Resumes automatically: skips chapters already on disk (size >= 2000 bytes)
  - Saves queue/state so it can be killed and rerun safely
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import html
import json
import re
import sys
import threading
import time
import unicodedata
from pathlib import Path

from mtc_downloader import MTCDownloader
from download_completed_to_mtc import clean_filename, chapter_filename
from download_one_completed_live_decrypt import (
    get_chapters_once_safe,
    maybe_decrypt,
    normalize_chapter_title,
    write_info_json,
    write_plain_chapter,
    sanitize_path_component,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Dev\MTC")
LOG_DIR = Path(r"C:\Dev\MTC_DOWNLOAD\logs")
QUEUE_PATH = LOG_DIR / "missing_books_queue.json"
STATE_PATH = LOG_DIR / "download_all_missing_state.json"
LOG_DIR.mkdir(parents=True, exist_ok=True)

IGNORE_DIRS = {".git", ".githooks", ".vscode", "__pycache__"}
CHAPTER_RE = re.compile(r"(?i)(?:ch\u01b0\u01a1ng|chuong)\s*(\d+)")
_THREAD_LOCAL = threading.local()


def thread_downloader() -> MTCDownloader:
    downloader = getattr(_THREAD_LOCAL, "downloader", None)
    if downloader is None:
        downloader = MTCDownloader()
        _THREAD_LOCAL.downloader = downloader
    return downloader


# ---------------------------------------------------------------------------
# Naming helpers (identical rule to sync_all_completed_strict.py)
# ---------------------------------------------------------------------------

def alnum_norm(value: str) -> str:
    text = unicodedata.normalize("NFC", html.unescape(str(value or ""))).casefold()
    return "".join(ch for ch in text if ch.isalnum())


def strict_component(value: str, default: str = "Untitled") -> str:
    text = unicodedata.normalize("NFC", html.unescape(str(value or "")))
    text = "".join(ch if (ch.isalnum() or ch.isspace()) else " " for ch in text)
    text = re.sub(r"\s+", " ", text).strip(" .")
    return text or default


def strict_book_name(raw_name: str) -> str:
    return strict_component(clean_filename(raw_name), default="Untitled")


def strict_chapter_filename(chapter: dict, fallback_index: int) -> str:
    base = chapter_filename(chapter, fallback_index)
    stem = Path(base).stem
    suffix = Path(base).suffix
    match = re.match(r"(?i)^(ch\u01b0\u01a1ng\s+\d+)(?:\s+(.*))?$", stem)
    if not match:
        return strict_component(stem, default=f"Ch\u01b0\u01a1ng {fallback_index}") + suffix
    prefix = strict_component(match.group(1), default=f"Ch\u01b0\u01a1ng {fallback_index}")
    title = strict_component(match.group(2) or "", default="")
    clean = f"{prefix} {title}{suffix}".strip() if title else f"{prefix}{suffix}"
    return clean


# ---------------------------------------------------------------------------
# Folder helpers
# ---------------------------------------------------------------------------

def local_folder_norm_map() -> dict[str, Path]:
    return {
        alnum_norm(path.name): path
        for path in ROOT.iterdir()
        if path.is_dir() and path.name not in IGNORE_DIRS
    }


# ---------------------------------------------------------------------------
# Build queue
# ---------------------------------------------------------------------------

def build_queue(downloader: MTCDownloader) -> list[dict]:
    folder_norms = local_folder_norm_map()
    all_books: list[dict] = []
    page = 1
    while True:
        data = downloader.get_books(limit=100, page=page)
        rows = (data or {}).get("data") or []
        if not rows:
            break
        all_books.extend(rows)
        print(f"  [scan] page={page} rows={len(rows)} total={len(all_books)}", flush=True)
        if len(rows) < 100:
            break
        page += 1
        time.sleep(0.15)

    queue = []
    for book in all_books:
        book_id = int(book.get("id") or 0)
        if not book_id:
            continue
        chapter_count = int(book.get("chapter_count") or book.get("latest_index") or 0)
        if chapter_count <= 0:
            continue
        name_norm = alnum_norm(book.get("name") or "")
        if name_norm in folder_norms:
            continue  # already exists locally
        queue.append({
            "id": book_id,
            "name": book.get("name"),
            "chapter_count": chapter_count,
            "status_name": book.get("status_name"),
            "clean_name": strict_book_name(book.get("name") or f"book {book_id}"),
            "updated_at": book.get("updated_at"),
        })

    queue.sort(key=lambda b: b["chapter_count"])  # small books first (faster feedback)
    QUEUE_PATH.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")
    return queue


# ---------------------------------------------------------------------------
# Download one book
# ---------------------------------------------------------------------------

def download_one_chapter(book_id: int, folder_name: str, chapter: dict, seq: int) -> tuple[int, bool, str]:
    folder = ROOT / folder_name
    chapter_id = chapter.get("id")
    idx = int(chapter.get("index") or chapter.get("number") or seq)
    for attempt in range(1, 4):
        try:
            downloader = thread_downloader()
            detail = downloader.get_chapter_content(chapter_id)
            data = (detail or {}).get("data") or {}
            content = data.get("content") or data.get("body") or ""
            if not content:
                raise ValueError("empty content")
            plain, _ = maybe_decrypt(content)
            title = normalize_chapter_title(
                data.get("name") or chapter.get("name") or f"Ch\u01b0\u01a1ng {idx}", idx
            )
            safe_fname = sanitize_path_component(strict_chapter_filename(data or chapter, seq))
            safe_title = sanitize_path_component(strict_component(title, default=f"Ch\u01b0\u01a1ng {idx}"))
            write_plain_chapter(folder / safe_fname, safe_title, plain)
            return seq, True, safe_fname
        except Exception as exc:
            if attempt == 3:
                return seq, False, f"ch={idx} id={chapter_id}: {exc}"
            time.sleep(0.4 * attempt)
    return seq, False, f"ch={idx} id={chapter_id}: unknown error"


def download_book(downloader: MTCDownloader, book: dict, delay: float, workers: int, batch_size: int) -> dict:
    book_id = book["id"]
    folder_name = book["clean_name"]
    folder = ROOT / folder_name
    folder.mkdir(parents=True, exist_ok=True)

    try:
        chapters = get_chapters_once_safe(downloader, book_id)
    except Exception as exc:
        return {"id": book_id, "folder": folder_name, "status": "api_error", "error": str(exc)}

    if not chapters:
        return {"id": book_id, "folder": folder_name, "status": "no_chapters"}

    existing_norms = {alnum_norm(path.name) for path in folder.glob("*.txt")}
    existing_indices = set()
    for path in folder.glob("*.txt"):
        match = CHAPTER_RE.search(path.stem)
        if match and path.stat().st_size >= 2000:
            existing_indices.add(int(match.group(1)))

    missing_jobs = []
    for seq, chapter in enumerate(chapters, 1):
        idx = int(chapter.get("index") or chapter.get("number") or seq)
        expected_name = strict_chapter_filename(chapter, seq)
        if alnum_norm(expected_name) in existing_norms or idx in existing_indices:
            continue
        missing_jobs.append((seq, chapter))

    skip = len(chapters) - len(missing_jobs)
    ok = fail = 0
    failed = []

    with cf.ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        for start in range(0, len(missing_jobs), max(1, batch_size)):
            batch = missing_jobs[start:start + max(1, batch_size)]
            futures = [
                executor.submit(download_one_chapter, book_id, folder_name, chapter, seq)
                for seq, chapter in batch
            ]
            for future in cf.as_completed(futures):
                seq, success, message = future.result()
                if success:
                    ok += 1
                else:
                    fail += 1
                    failed.append(message)
                    print(f"    FAIL {message}", flush=True)
            time.sleep(delay)

    detail_book = downloader.get_book_detail(book_id)
    book_data = (detail_book or {}).get("data") or book
    write_info_json(folder, book_data, chapters)

    status = "ok" if fail == 0 else "partial"
    return {
        "id": book_id,
        "folder": folder_name,
        "status": status,
        "total": len(chapters),
        "ok": ok,
        "skip": skip,
        "fail": fail,
        "failed": failed[:50],
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--delay", type=float, default=0.12)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--batch-size", type=int, default=24)
    ap.add_argument("--limit", type=int, default=None, help="process at most N books")
    ap.add_argument("--rebuild-queue", action="store_true", help="re-scan API even if queue file exists")
    ap.add_argument("--book-id", type=int, default=None, help="download single book id")
    args = ap.parse_args()

    downloader = MTCDownloader()

    # --- single book mode ---
    if args.book_id:
        detail = downloader.get_book_detail(args.book_id)
        book_data = (detail or {}).get("data") or {}
        if not book_data:
            print(f"ERROR: book {args.book_id} not found")
            return 2
        queue = [{
            "id": args.book_id,
            "name": book_data.get("name"),
            "chapter_count": int(book_data.get("chapter_count") or 0),
            "status_name": book_data.get("status_name"),
            "clean_name": strict_book_name(book_data.get("name") or f"book {args.book_id}"),
            "updated_at": book_data.get("updated_at"),
        }]
    # --- load/build queue ---
    elif QUEUE_PATH.exists() and not args.rebuild_queue:
        queue = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
        print(f"Loaded queue from {QUEUE_PATH}: {len(queue)} books", flush=True)
    else:
        print("Scanning live API for missing books...", flush=True)
        queue = build_queue(downloader)
        print(f"Queue built: {len(queue)} books missing locally", flush=True)

    if args.limit:
        queue = queue[:args.limit]

    state: dict = {"done": [], "errors": []}
    if STATE_PATH.exists():
        try:
            state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    done_ids = {int(r["id"]) for r in state.get("done", [])}

    total = len(queue)
    for seq, book in enumerate(queue, 1):
        book_id = int(book["id"])
        if book_id in done_ids:
            print(f"[{seq}/{total}] SKIP (already done) {book['name']}", flush=True)
            continue

        print(
            f"[{seq}/{total}] {book_id} {book['name']} "
            f"chapters={book['chapter_count']} status={book['status_name']}",
            flush=True,
        )
        result = download_book(downloader, book, args.delay, args.workers, args.batch_size)
        print(
            f"  => status={result['status']} ok={result.get('ok',0)} "
            f"skip={result.get('skip',0)} fail={result.get('fail',0)}",
            flush=True,
        )
        if result["status"] in ("ok", "partial", "no_chapters"):
            state["done"].append(result)
            done_ids.add(book_id)
        else:
            state["errors"].append(result)
        STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    errors = len(state.get("errors", []))
    print(f"\nDONE: processed={len(queue)} errors={errors}")
    print(f"STATE={STATE_PATH}")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
