#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

from mtc_downloader import MTCDownloader
from download_completed_to_mtc import chapter_filename
from download_one_completed_live_decrypt import (
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

ROOT = Path(r"C:\Dev\MTC")
LOG_DIR = Path(r"C:\Dev\MTC_DOWNLOAD\logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
REPORT_PATH = LOG_DIR / "audit_and_fill_full_library_report.json"
IGNORE_DIRS = {".git", ".githooks", ".vscode", "__pycache__", "git"}
CHAPTER_RE = re.compile(r"(?i)(?:chương|chuong)\s*(\d+)")


def parse_local_indexes(folder: Path) -> tuple[dict[int, list[Path]], list[str]]:
    grouped: dict[int, list[Path]] = {}
    unparsable: list[str] = []
    for path in folder.glob("*.txt"):
        match = CHAPTER_RE.search(path.name)
        if not match:
            unparsable.append(path.name)
            continue
        try:
            index = int(match.group(1))
            grouped.setdefault(index, []).append(path)
        except Exception:
            unparsable.append(path.name)
    return grouped, sorted(unparsable)


def get_all_chapters_safe(downloader: MTCDownloader, book_id: int, delay: float) -> list[dict]:
    chapters: list[dict] = []
    seen_ids: set[int] = set()
    seen_signatures: set[tuple[int, ...]] = set()
    page = 1

    while True:
        data = downloader.get_chapters(book_id, page=page, limit=100)
        rows = (data or {}).get("data") or []
        if not rows:
            break

        signature = tuple(int(row.get("id") or 0) for row in rows[:10])
        if signature in seen_signatures:
            break
        seen_signatures.add(signature)

        added_this_page = 0
        for row in rows:
            chapter_id = int(row.get("id") or 0)
            if chapter_id and chapter_id not in seen_ids:
                seen_ids.add(chapter_id)
                chapters.append(row)
                added_this_page += 1

        if len(rows) < 100 or added_this_page == 0:
            break

        page += 1
        time.sleep(delay)

    def sort_key(chapter: dict) -> tuple[int, int]:
        try:
            index = int(chapter.get("index") or chapter.get("number") or 0)
        except Exception:
            index = 0
        try:
            chapter_id = int(chapter.get("id") or 0)
        except Exception:
            chapter_id = 0
        return index, chapter_id

    return sorted(chapters, key=sort_key)


def fetch_and_write_missing(
    downloader: MTCDownloader,
    folder: Path,
    chapter: dict,
) -> str:
    chapter_id = int(chapter.get("id") or 0)
    chapter_index = int(chapter.get("index") or chapter.get("number") or 0)
    detail = downloader.get_chapter_content(chapter_id)
    data = (detail or {}).get("data") or {}
    content = data.get("content") or data.get("body") or ""
    if not content:
        raise ValueError("empty content")

    plain, _ = maybe_decrypt(content)
    title = normalize_chapter_title(
        data.get("name") or chapter.get("name") or f"Chương {chapter_index}",
        chapter_index,
    )
    filename = sanitize_path_component(chapter_filename(data or chapter, chapter_index))
    path = folder / filename
    write_plain_chapter(path, sanitize_path_component(title), plain)
    return path.name


def load_folders() -> list[Path]:
    folders = []
    for path in ROOT.iterdir():
        if not path.is_dir() or path.name in IGNORE_DIRS:
            continue
        if (path / "info.json").exists():
            folders.append(path)
    folders.sort(key=lambda item: item.name.lower())
    return folders


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--delay", type=float, default=0.12)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    downloader = MTCDownloader()
    folders = load_folders()
    if args.limit:
        folders = folders[: args.limit]

    summary: dict = {
        "scanned_folders": 0,
        "downloaded_missing": 0,
        "books_with_missing": 0,
        "books_with_extra": 0,
        "books_with_duplicates": 0,
        "books_with_unparsable": 0,
        "errors": 0,
        "folders": [],
    }

    for idx, folder in enumerate(folders, 1):
        summary["scanned_folders"] += 1
        info_path = folder / "info.json"
        try:
            info = json.loads(info_path.read_text(encoding="utf-8"))
            book_id = int(info.get("id") or 0)
        except Exception as exc:
            summary["errors"] += 1
            summary["folders"].append(
                {"folder": folder.name, "status": "bad_info_json", "errors": [str(exc)]}
            )
            print(f"[{idx}] {folder.name}: bad_info_json", flush=True)
            continue

        try:
            chapters = get_all_chapters_safe(downloader, book_id, args.delay)
        except Exception as exc:
            summary["errors"] += 1
            summary["folders"].append(
                {"folder": folder.name, "book_id": book_id, "status": "api_error", "errors": [str(exc)]}
            )
            print(f"[{idx}] {folder.name}: api_error {exc}", flush=True)
            continue

        remote_by_index: dict[int, dict] = {}
        for chapter in chapters:
            try:
                chapter_index = int(chapter.get("index") or chapter.get("number") or 0)
            except Exception:
                continue
            if chapter_index > 0 and chapter_index not in remote_by_index:
                remote_by_index[chapter_index] = chapter

        local_map, unparsable = parse_local_indexes(folder)
        local_indexes = set(local_map)
        remote_indexes = set(remote_by_index)
        missing_indexes = sorted(remote_indexes - local_indexes)
        extra_indexes = sorted(local_indexes - remote_indexes)
        duplicate_indexes = sorted(index for index, paths in local_map.items() if len(paths) > 1)
        missing_written = []
        extra_deleted = []
        duplicate_deleted = []
        errors = []

        if missing_indexes:
            summary["books_with_missing"] += 1
        if extra_indexes:
            summary["books_with_extra"] += 1
        if duplicate_indexes:
            summary["books_with_duplicates"] += 1
        if unparsable:
            summary["books_with_unparsable"] += 1

        for chapter_index in missing_indexes:
            if args.dry_run:
                missing_written.append({"index": chapter_index, "file": "(dry-run)"})
                summary["downloaded_missing"] += 1
                continue
            try:
                written = fetch_and_write_missing(downloader, folder, remote_by_index[chapter_index])
                missing_written.append({"index": chapter_index, "file": written})
                summary["downloaded_missing"] += 1
            except Exception as exc:
                errors.append(f"index {chapter_index}: {exc}")
                summary["errors"] += 1
            time.sleep(args.delay)

        for chapter_index in extra_indexes:
            for path in local_map.get(chapter_index, []):
                if args.dry_run:
                    extra_deleted.append(path.name)
                    continue
                try:
                    path.unlink()
                    extra_deleted.append(path.name)
                except Exception as exc:
                    errors.append(f"delete extra {path.name}: {exc}")
                    summary["errors"] += 1

        for chapter_index in duplicate_indexes:
            paths = sorted(local_map.get(chapter_index, []), key=lambda item: (item.stat().st_size, item.name.lower()), reverse=True)
            for path in paths[1:]:
                if args.dry_run:
                    duplicate_deleted.append(path.name)
                    continue
                try:
                    path.unlink()
                    duplicate_deleted.append(path.name)
                except Exception as exc:
                    errors.append(f"delete duplicate {path.name}: {exc}")
                    summary["errors"] += 1

        if not args.dry_run:
            try:
                write_info_json(folder, info, chapters)
            except Exception as exc:
                errors.append(f"write_info_json: {exc}")
                summary["errors"] += 1

        status = "ok"
        if errors:
            status = "partial_error"
        elif missing_indexes or extra_indexes or duplicate_indexes or unparsable:
            status = "repaired" if not args.dry_run else "needs_repair"

        item = {
            "folder": folder.name,
            "book_id": book_id,
            "status": status,
            "remote_count": len(remote_indexes),
            "local_count": len(local_indexes),
            "missing_count": len(missing_indexes),
            "missing_written": missing_written,
            "extra_count": len(extra_indexes),
            "extra_deleted": extra_deleted,
            "duplicate_count": len(duplicate_indexes),
            "duplicate_deleted": duplicate_deleted,
            "unparsable_files": unparsable,
            "errors": errors,
        }
        summary["folders"].append(item)
        tag = "DRY" if args.dry_run else "LIVE"
        print(
            f"[{idx}] {folder.name}: [{tag}] remote={len(remote_indexes)} local={len(local_indexes)} "
            f"missing={len(missing_indexes)} extra={len(extra_indexes)} dup={len(duplicate_indexes)} "
            f"unparsable={len(unparsable)} err={len(errors)}",
            flush=True,
        )

    REPORT_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"REPORT={REPORT_PATH}", flush=True)
    print(
        json.dumps(
            {key: value for key, value in summary.items() if key != "folders"},
            ensure_ascii=False,
        ),
        flush=True,
    )
    return 0 if summary["errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
