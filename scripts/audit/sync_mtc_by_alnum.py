#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

from mtc_downloader import MTCDownloader
from download_completed_to_mtc import clean_filename, chapter_filename
from download_one_completed_live_decrypt import (
    maybe_decrypt,
    normalize_chapter_title,
    sanitize_path_component,
    write_plain_chapter,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Dev\MTC")
LOG_DIR = Path(r"C:\Dev\MTC_download\logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
REPORT_PATH = LOG_DIR / "sync_mtc_by_alnum_report.json"

IGNORE_DIRS = {".git", ".githooks", ".vscode", "git", "__pycache__"}
CHAP_NUM_RE = re.compile(r"(?i)(?:chương|chuong)\s*(\d+)")


def alnum_norm(value: str) -> str:
    text = html.unescape(str(value or "")).strip().lower()
    return "".join(ch for ch in text if ch.isalnum())


def get_all_books(downloader: MTCDownloader) -> list[dict]:
    rows = []
    page = 1
    while True:
        data = downloader.get_books(limit=100, page=page)
        part = (data or {}).get("data") or []
        if not part:
            break
        rows.extend(part)
        print(f"[BOOKS] page={page} got={len(part)} total={len(rows)}", flush=True)
        if len(part) < 100:
            break
        page += 1
        time.sleep(0.1)
    return rows


def choose_book(candidates: list[dict], local_count: int) -> dict:
    if len(candidates) == 1:
        return candidates[0]

    def score(book: dict):
        expected = int(book.get("chapter_count") or book.get("latest_index") or 0)
        finished_bias = 0 if (book.get("status") == 2 or book.get("status_name") == "Hoàn thành") else 1
        return (abs(expected - local_count), finished_bias, expected)

    return sorted(candidates, key=score)[0]


def get_chapters_once_safe(downloader: MTCDownloader, book_id: int) -> list[dict]:
    data = downloader.get_chapters(book_id, page=1, limit=500)
    rows = (data or {}).get("data") or []
    seen = set()
    out = []
    for row in rows:
        chapter_id = row.get("id")
        if chapter_id in seen:
            continue
        seen.add(chapter_id)
        out.append(row)

    def key(chapter: dict):
        try:
            return int(chapter.get("index") or chapter.get("number") or 0)
        except Exception:
            return 0

    return sorted(out, key=key)


def build_local_index(folder: Path) -> dict[int, list[dict]]:
    grouped: dict[int, list[dict]] = defaultdict(list)
    for path in folder.glob("*.txt"):
        match = CHAP_NUM_RE.search(path.name)
        if not match:
            continue
        number = int(match.group(1))
        grouped[number].append(
            {
                "path": path,
                "name": path.name,
                "norm_name": alnum_norm(path.stem),
                "size": path.stat().st_size,
            }
        )
    return grouped


def pick_keeper(entries: list[dict], remote_norm_name: str) -> tuple[dict, list[dict]]:
    ranked = sorted(
        entries,
        key=lambda entry: (
            0 if entry["norm_name"] == remote_norm_name else 1,
            -int(entry["size"]),
            entry["name"].lower(),
        ),
    )
    return ranked[0], ranked[1:]


def fetch_and_write_chapter(
    downloader: MTCDownloader,
    folder: Path,
    chapter: dict,
    fallback_index: int,
) -> str:
    chapter_id = chapter.get("id")
    detail = downloader.get_chapter_content(chapter_id)
    data = (detail or {}).get("data") or {}
    content = data.get("content") or data.get("body") or ""
    if not content:
        raise ValueError(f"chapter {chapter_id} has no content")

    plain, _ = maybe_decrypt(content)
    index = int(chapter.get("index") or chapter.get("number") or fallback_index)
    title = normalize_chapter_title(data.get("name") or chapter.get("name") or f"Chương {index}", index)
    filename = sanitize_path_component(chapter_filename(data or chapter, fallback_index))
    path = folder / filename
    write_plain_chapter(path, sanitize_path_component(title), plain)
    return path.name


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--delay", type=float, default=0.2)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    downloader = MTCDownloader()
    books = get_all_books(downloader)

    books_by_name: dict[str, list[dict]] = defaultdict(list)
    for book in books:
        key = alnum_norm(book.get("name") or "")
        if key:
            books_by_name[key].append(book)

    folders = [path for path in ROOT.iterdir() if path.is_dir() and path.name not in IGNORE_DIRS]
    folders.sort(key=lambda item: item.name.lower())
    if args.limit:
        folders = folders[: args.limit]

    summary = {
        "scanned_folders": 0,
        "matched_folders": 0,
        "unmatched_folders": 0,
        "downloaded_missing": 0,
        "deleted_duplicates": 0,
        "deleted_extra": 0,
        "errors": 0,
        "folders": [],
    }

    for index, folder in enumerate(folders, 1):
        local_map = build_local_index(folder)
        if not local_map:
            continue

        summary["scanned_folders"] += 1
        key = alnum_norm(folder.name)
        candidates = books_by_name.get(key, [])
        item = {
            "folder": folder.name,
            "folder_key": key,
            "local_count": sum(len(values) for values in local_map.values()),
        }

        if not candidates:
            summary["unmatched_folders"] += 1
            item["status"] = "unmatched_remote"
            summary["folders"].append(item)
            print(f"[{index}] {folder.name}: unmatched_remote", flush=True)
            continue

        summary["matched_folders"] += 1
        book = choose_book(candidates, len(local_map))
        item["book_id"] = int(book["id"])
        item["book_name"] = book.get("name")

        remote_chapters = get_chapters_once_safe(downloader, int(book["id"]))
        remote_by_index = {}
        for chapter in remote_chapters:
            try:
                chapter_index = int(chapter.get("index") or chapter.get("number") or 0)
            except Exception:
                continue
            if chapter_index > 0:
                remote_by_index[chapter_index] = chapter

        missing = []
        duplicate_deleted = []
        extra_deleted = []
        folder_errors = []

        remote_indices = set(remote_by_index)
        local_indices = set(local_map)

        for chapter_index, entries in sorted(local_map.items()):
            if chapter_index not in remote_indices:
                for entry in entries:
                    try:
                        entry["path"].unlink()
                        extra_deleted.append(entry["name"])
                        summary["deleted_extra"] += 1
                    except Exception as exc:
                        folder_errors.append(f"delete extra {entry['name']}: {exc}")
                        summary["errors"] += 1
                continue

            remote_norm_name = alnum_norm(clean_filename(chapter_filename(remote_by_index[chapter_index], chapter_index)).removesuffix('.txt'))
            keeper, duplicates = pick_keeper(entries, remote_norm_name)
            for entry in duplicates:
                try:
                    entry["path"].unlink()
                    duplicate_deleted.append(entry["name"])
                    summary["deleted_duplicates"] += 1
                except Exception as exc:
                    folder_errors.append(f"delete duplicate {entry['name']}: {exc}")
                    summary["errors"] += 1

        for chapter_index in sorted(remote_indices - local_indices):
            try:
                written = fetch_and_write_chapter(downloader, folder, remote_by_index[chapter_index], chapter_index)
                missing.append({"index": chapter_index, "written": written})
                summary["downloaded_missing"] += 1
            except Exception as exc:
                folder_errors.append(f"download missing {chapter_index}: {exc}")
                summary["errors"] += 1
            time.sleep(args.delay)

        item.update(
            {
                "status": "ok" if not folder_errors else "partial_error",
                "remote_count": len(remote_indices),
                "missing_downloaded": missing,
                "duplicates_deleted": duplicate_deleted,
                "extra_deleted": extra_deleted,
                "errors": folder_errors,
            }
        )
        summary["folders"].append(item)
        print(
            f"[{index}] {folder.name}: remote={len(remote_indices)} +{len(missing)} dup_del={len(duplicate_deleted)} extra_del={len(extra_deleted)} err={len(folder_errors)}",
            flush=True,
        )

    REPORT_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"REPORT={REPORT_PATH}", flush=True)
    print(json.dumps({k: v for k, v in summary.items() if k != 'folders'}, ensure_ascii=False), flush=True)
    return 0 if summary["errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
