#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import re
import requests
import subprocess
import sys
import time
from pathlib import Path

from mtc_downloader import MTCDownloader, set_global_token
from download_all_missing_books import strict_book_name, strict_chapter_filename, strict_component
from download_one_completed_live_decrypt import (
    clean_text,
    maybe_decrypt,
    normalize_chapter_title,
    sanitize_path_component,
    write_info_json,
    write_plain_chapter,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"D:\Dev\MTC_Continune")
COMMIT_LOCK = ROOT / ".codex_commit.lock"
LOG_DIR = Path(r"C:\Dev\MTC_Download\logs")
QUEUE = LOG_DIR / "non_completed_missing_queue.json"
STATE = LOG_DIR / "download_non_completed_missing_state.json"
REPORT = LOG_DIR / "download_non_completed_missing_report.json"
CHAPTER_RE = re.compile(r"(\d+)")
MARKER_RE = re.compile(r'eyJpdiI6|"iv":"|"value":"')
INNER_PAYLOAD_RE = re.compile(r"eyJpdiI6[A-Za-z0-9+/=]+")


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"done": [], "failed": [], "started_at": time.strftime("%Y-%m-%d %H:%M:%S")}


def save_state(state: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def save_report(report: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


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


def download_chapter(downloader: MTCDownloader, chapter: dict, book_dir: Path, seq: int, max_retries: int = 3) -> bool:
    """Download a single chapter with retries."""
    chapter_id = chapter.get("id")
    idx = int(chapter.get("index") or chapter.get("number") or seq)
    
    for attempt in range(max_retries):
        try:
            detail = downloader.get_chapter_content(chapter_id)
            data = (detail or {}).get("data") or {}
            content = data.get("content") or data.get("body") or ""
            if not content:
                raise ValueError("empty content")
            
            # Decrypt if needed
            plain, _ = maybe_decrypt(content)
            cleaned = clean_text(plain)
            
            # Get title
            title = normalize_chapter_title(data.get("name") or chapter.get("name") or f"Chương {idx}", idx)
            
            # Write chapter file
            filename = sanitize_path_component(strict_chapter_filename(chapter, seq))
            chapter_path = book_dir / "chapters" / filename
            chapter_path.parent.mkdir(parents=True, exist_ok=True)
            write_plain_chapter(chapter_path, title, cleaned)
            
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(0.4 * attempt)
            else:
                print(f"  ERROR downloading chapter {chapter_id}: {e}")
                return False
    return False


def fetch_chapters_with_meta(downloader: MTCDownloader, book_id: int) -> tuple[list[dict], dict]:
    """Fetch all chapters and book metadata using pagination."""
    chapters = []
    seen_ids = set()
    book_meta = {}
    page = 1
    while True:
        data = downloader.get_chapters(book_id, page=page, limit=500) or {}
        rows = data.get("data") or []
        extra = data.get("extra") or {}
        if extra.get("book"):
            book_meta = extra["book"]
        added = 0
        for chapter in rows:
            chapter_id = chapter.get("id")
            if chapter_id in seen_ids:
                continue
            seen_ids.add(chapter_id)
            chapters.append(chapter)
            added += 1
        pagination = data.get("pagination") or {}
        last = int(pagination.get("last") or 0)
        if not rows or added == 0:
            break
        if last and page >= last:
            break
        if len(rows) < 500:
            break
        page += 1
        time.sleep(0.03)

    def key(chapter: dict) -> int:
        try:
            return int(chapter.get("index") or chapter.get("number") or 0)
        except Exception:
            return 0

    return sorted(chapters, key=key), book_meta


def download_book(downloader: MTCDownloader, book_id: int, chapter_workers: int = 8) -> dict:
    """Download all chapters for a book."""
    try:
        # Get chapters and book metadata
        chapters, book_meta = fetch_chapters_with_meta(downloader, book_id)
        
        if not book_meta:
            return {"id": book_id, "status": "error", "error": "Book not found"}
        
        name = book_meta.get("name", f"Book {book_id}")
        safe_name = strict_book_name(name)
        book_dir = ROOT / safe_name
        
        # Create book directory
        book_dir.mkdir(parents=True, exist_ok=True)
        
        # Write info.json
        write_info_json(book_dir, book_meta, chapters)
        
        remote_count = len(chapters)
        
        if remote_count == 0:
            return {"id": book_id, "status": "ok", "remote": 0, "downloaded": 0, "missing_after": 0, "failed": 0}
        
        # Download chapters concurrently
        downloaded = 0
        failed = 0
        
        with cf.ThreadPoolExecutor(max_workers=chapter_workers) as executor:
            futures = {
                executor.submit(download_chapter, downloader, ch, book_dir, seq): ch.get("id")
                for seq, ch in enumerate(chapters, 1)
            }
            
            for future in cf.as_completed(futures):
                if future.result():
                    downloaded += 1
                else:
                    failed += 1
        
        return {
            "id": book_id,
            "status": "ok",
            "remote": remote_count,
            "downloaded": downloaded,
            "missing_after": remote_count - downloaded,
            "failed": failed
        }
        
    except Exception as e:
        return {"id": book_id, "status": "error", "error": str(e)}


def commit_changes() -> bool:
    """Commit changes to git."""
    try:
        subprocess.run(
            ["git", "-C", str(ROOT), "add", "."],
            check=True,
            capture_output=True,
            timeout=300
        )
        subprocess.run(
            ["git", "-C", str(ROOT), "commit", "-m", f"Download books {time.strftime('%Y-%m-%d %H:%M:%S')}"],
            check=True,
            capture_output=True,
            timeout=300
        )
        return True
    except Exception as e:
        print(f"Git commit failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", help="Login email")
    parser.add_argument("--password", help="Login password")
    parser.add_argument("--chapter-workers", type=int, default=8, help="Chapter download workers")
    parser.add_argument("--batch-size", type=int, default=10, help="Books per batch")
    parser.add_argument("--limit", type=int, help="Limit number of books to download")
    parser.add_argument("--shard", type=int, default=1, help="Shard number")
    parser.add_argument("--total-shards", type=int, default=1, help="Total shards")
    args = parser.parse_args()
    
    # Login if credentials provided
    if args.email and args.password:
        token = login(args.email, args.password)
        if token:
            set_global_token(token)
            print(f"authenticated as {args.email}")
        else:
            print("login failed")
            return
    
    downloader = MTCDownloader()
    
    # Load queue
    with open(QUEUE, 'r', encoding='utf-8') as f:
        queue = json.load(f)
    
    print(f"queue={len(queue)}")
    
    # Load state
    state = load_state()
    done_set = set(state.get("done", []))
    failed_set = set(state.get("failed", []))
    
    # Filter queue
    remaining = [bid for bid in queue if bid not in done_set and bid not in failed_set]
    
    # Apply shard
    if args.total_shards > 1:
        shard_size = len(remaining) // args.total_shards
        start = (args.shard - 1) * shard_size
        end = start + shard_size if args.shard < args.total_shards else len(remaining)
        remaining = remaining[start:end]
    
    # Apply limit
    if args.limit:
        remaining = remaining[:args.limit]
    
    print(f"done={len(done_set)} shard={args.shard}/{args.total_shards}")
    
    # Process books
    report = {
        "started_at": state.get("started_at", time.strftime("%Y-%m-%d %H:%M:%S")),
        "books": []
    }
    
    for i, book_id in enumerate(remaining, 1):
        print(f"[{i}/{len(remaining)}] start id={book_id}")
        
        result = download_book(downloader, book_id, args.chapter_workers)
        
        if result["status"] == "ok":
            done_set.add(book_id)
            print(f"[{i}/{len(remaining)}] ok id={book_id} remote={result['remote']} downloaded={result['downloaded']} missing_after={result['missing_after']} failed={result['failed']}")
        else:
            failed_set.add(book_id)
            print(f"[{i}/{len(remaining)}] FAIL id={book_id} error={result.get('error', 'unknown')}")
        
        report["books"].append(result)
        
        # Save state periodically
        if i % args.batch_size == 0:
            state["done"] = list(done_set)
            state["failed"] = list(failed_set)
            save_state(state)
            save_report(report)
            
            # Commit changes
            if COMMIT_LOCK.exists():
                COMMIT_LOCK.unlink()
            commit_changes()
    
    # Final save
    state["done"] = list(done_set)
    state["failed"] = list(failed_set)
    state["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    save_state(state)
    save_report(report)
    
    print(f"processed_this_run={len(remaining)}")
    print(f"done_total={len(done_set)}")
    print(f"failed_total={len(failed_set)}")
    print(f"report={REPORT}")


if __name__ == "__main__":
    main()
