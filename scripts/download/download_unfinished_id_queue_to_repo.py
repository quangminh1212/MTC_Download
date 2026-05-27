#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from mtc_downloader import MTCDownloader
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

ROOT = Path(r"C:\Dev\MTC_Continune")
LOG_DIR = Path(r"C:\Dev\MTC_Download\logs")
QUEUE = LOG_DIR / "all_id_unfinished_missing_repo.json"
STATE = LOG_DIR / "download_unfinished_id_queue_state.json"
REPORT = LOG_DIR / "download_unfinished_id_queue_report.json"
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
    REPORT.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_index(path: Path) -> int | None:
    match = CHAPTER_RE.search(path.stem)
    return int(match.group(1)) if match else None


def local_indices(folder: Path) -> set[int]:
    out = set()
    for path in folder.glob("*.txt"):
        idx = parse_index(path)
        if idx is not None:
            out.add(idx)
    return out


def get_all_chapters(downloader: MTCDownloader, book_id: int) -> tuple[list[dict], dict]:
    chapters: list[dict] = []
    seen_ids = set()
    book_meta: dict = {}
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


def decrypt_resilient(content: str) -> str:
    plain, _ = maybe_decrypt(content)
    cleaned = clean_text(plain)
    if not MARKER_RE.search(cleaned):
        return plain
    match = INNER_PAYLOAD_RE.search(plain)
    if not match:
        return plain
    inner, _ = maybe_decrypt(match.group(0))
    return inner


def write_resilient(path: Path, title: str, body: str) -> None:
    try:
        write_plain_chapter(path, title, body)
        return
    except ValueError:
        cleaned = clean_text(body)
        lines = cleaned.splitlines()
        if lines:
            first = lines[0].strip()
            alpha = sum(ch.isalpha() for ch in first)
            if "�" in first or alpha < max(8, len(first) // 3) or "chương" in first.lower():
                lines.pop(0)
                while lines and not lines[0].strip():
                    lines.pop(0)
        cleaned = "\n".join(lines).replace("�", "").strip()
        if MARKER_RE.search(cleaned):
            raise
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{'=' * 60}\n{title}\n{'=' * 60}\n\n{cleaned}\n", encoding="utf-8")


def download_one_chapter(folder: Path, chapter: dict, seq: int) -> tuple[int, bool, str]:
    downloader = MTCDownloader()
    idx = int(chapter.get("index") or chapter.get("number") or seq)
    chapter_id = chapter.get("id")
    filename = sanitize_path_component(strict_chapter_filename(chapter, seq))
    path = folder / filename
    for attempt in range(1, 6):
        try:
            detail = downloader.get_chapter_content(chapter_id)
            data = (detail or {}).get("data") or {}
            content = data.get("content") or data.get("body") or ""
            if not content:
                raise ValueError("empty content")
            plain = decrypt_resilient(content)
            title = normalize_chapter_title(data.get("name") or chapter.get("name") or f"Chương {idx}", idx)
            safe_title = sanitize_path_component(strict_component(title, default=f"Chương {idx}"))
            safe_path = folder / sanitize_path_component(strict_chapter_filename(data or chapter, seq))
            write_resilient(safe_path, safe_title, plain)
            return idx, True, safe_path.name
        except Exception as exc:
            if attempt == 5:
                return idx, False, f"idx={idx} id={chapter_id}: {exc}"
            time.sleep(0.4 * attempt)
    return idx, False, f"idx={idx} id={chapter_id}: unknown"


def commit_folder(folder: Path) -> tuple[bool, str]:
    add = subprocess.run(
        ["git", "add", "--", folder.name],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if add.returncode != 0:
        return False, add.stderr.strip()
    commit = subprocess.run(
        ["git", "commit", "-m", folder.name],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = (commit.stdout + commit.stderr).strip()
    if commit.returncode == 0:
        return True, output
    if "nothing to commit" in output:
        return True, "nothing to commit"
    return False, output


def process_book(book: dict, chapter_workers: int, batch_size: int) -> dict:
    book_id = int(book["id"])
    folder_name = strict_book_name(book.get("name") or f"book {book_id}")
    folder = ROOT / folder_name
    folder.mkdir(parents=True, exist_ok=True)
    downloader = MTCDownloader()
    chapters, book_meta = get_all_chapters(downloader, book_id)
    if not chapters:
        return {"id": book_id, "name": book.get("name"), "folder": folder_name, "status": "no_chapters"}

    remote_indices = {int(ch.get("index") or ch.get("number") or seq) for seq, ch in enumerate(chapters, 1)}
    have = local_indices(folder)
    missing = [(seq, chapter) for seq, chapter in enumerate(chapters, 1) if int(chapter.get("index") or chapter.get("number") or seq) not in have]
    ok = 0
    failed = []
    with cf.ThreadPoolExecutor(max_workers=max(1, chapter_workers)) as executor:
        for start in range(0, len(missing), max(1, batch_size)):
            futures = [
                executor.submit(download_one_chapter, folder, chapter, seq)
                for seq, chapter in missing[start : start + max(1, batch_size)]
            ]
            for future in cf.as_completed(futures):
                idx, success, message = future.result()
                if success:
                    ok += 1
                else:
                    failed.append(message)
            time.sleep(0.03)

    book_payload = dict(book_meta or book)
    book_payload.setdefault("id", book_id)
    book_payload.setdefault("name", book.get("name") or folder_name)
    write_info_json(folder, book_payload, chapters)
    have_after = local_indices(folder)
    missing_after = sorted(remote_indices - have_after)
    extra_after = sorted(have_after - remote_indices)
    status = "ok" if not failed and not missing_after and not extra_after else "issue"
    result = {
        "id": book_id,
        "name": book.get("name"),
        "folder": folder_name,
        "remote_count": len(remote_indices),
        "downloaded": ok,
        "failed_count": len(failed),
        "failed": failed[:20],
        "missing_after_count": len(missing_after),
        "missing_after": missing_after[:20],
        "extra_after_count": len(extra_after),
        "status": status,
    }
    if status == "ok":
        committed, message = commit_folder(folder)
        result["committed"] = committed
        result["commit_message"] = message[:500]
        if not committed:
            result["status"] = "commit_failed"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapter-workers", type=int, default=24)
    parser.add_argument("--batch-size", type=int, default=96)
    parser.add_argument("--max-books", type=int, default=None)
    parser.add_argument("--max-seconds", type=int, default=None)
    parser.add_argument("--min-chapters", type=int, default=1)
    parser.add_argument("--max-chapters", type=int, default=None)
    args = parser.parse_args()

    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    queue = [item for item in queue if int(item.get("chapter_count") or 0) >= args.min_chapters]
    if args.max_chapters is not None:
        queue = [item for item in queue if int(item.get("chapter_count") or 0) <= args.max_chapters]
    queue.sort(key=lambda item: (int(item.get("chapter_count") or 0), int(item["id"])))
    state = load_state()
    done_ids = {int(item["id"]) for item in state.get("done", [])}
    started = time.time()
    processed = 0
    print(f"queue={len(queue)} done={len(done_ids)} chapter_workers={args.chapter_workers}", flush=True)
    for seq, book in enumerate(queue, 1):
        book_id = int(book["id"])
        if book_id in done_ids:
            continue
        if args.max_books is not None and processed >= args.max_books:
            break
        if args.max_seconds is not None and time.time() - started >= args.max_seconds:
            break
        print(
            f"[{seq}/{len(queue)}] start id={book_id} chapters={book.get('chapter_count')} name={book.get('name')}",
            flush=True,
        )
        result = process_book(book, args.chapter_workers, args.batch_size)
        target = "done" if result.get("status") == "ok" else "failed"
        state.setdefault(target, []).append(result)
        save_state(state)
        processed += 1
        print(
            f"[{seq}/{len(queue)}] {result.get('status')} id={book_id} "
            f"remote={result.get('remote_count')} downloaded={result.get('downloaded')} "
            f"missing_after={result.get('missing_after_count')} failed={result.get('failed_count')}",
            flush=True,
        )
    save_state(state)
    print(f"processed_this_run={processed}")
    print(f"done_total={len(state.get('done', []))}")
    print(f"failed_total={len(state.get('failed', []))}")
    print(f"report={REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
