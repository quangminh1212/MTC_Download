#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sync MTC chapters using info.json (book_id) in each folder.

For every folder under C:\Dev\MTC that has an info.json with a book id,
fetch the remote chapter list and:
  1. Download any missing chapters.
  2. Delete duplicate files (same chapter number).
  3. Delete extra files whose chapter number is not in the remote list.

Comparison rule: only letters and digits (alnum) are compared.
"""
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
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Dev\mtc_done")
LOG_DIR = Path(r"C:\Dev\MTC_download\logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
REPORT_PATH = LOG_DIR / "sync_mtc_done_via_info_report.json"

IGNORE_DIRS = {".git", ".githooks", ".vscode", "git", "__pycache__"}
CHAP_NUM_RE = re.compile(r"(?i)(?:ch\u01b0\u01a1ng|chuong)\s*(\d+)")


def alnum_norm(value: str) -> str:
    text = html.unescape(str(value or "")).strip().lower()
    return "".join(ch for ch in text if ch.isalnum())


def get_chapters_once_safe(downloader: MTCDownloader, book_id: int) -> list[dict]:
    data = downloader.get_chapters(book_id, page=1, limit=100)
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
    title = normalize_chapter_title(
        data.get("name") or chapter.get("name") or f"Ch\u01b0\u01a1ng {index}", index
    )
    filename = sanitize_path_component(chapter_filename(data or chapter, fallback_index))
    path = folder / filename
    write_plain_chapter(path, sanitize_path_component(title), plain)
    return path.name


def read_book_id(folder: Path) -> int | None:
    info_path = folder / "info.json"
    if not info_path.exists():
        return None
    try:
        info = json.loads(info_path.read_text(encoding="utf-8"))
        book_id = info.get("id")
        return int(book_id) if book_id else None
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--delay", type=float, default=0.15)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    downloader = MTCDownloader()

    folders = [
        path
        for path in ROOT.iterdir()
        if path.is_dir() and path.name not in IGNORE_DIRS
    ]
    folders.sort(key=lambda item: item.name.lower())
    if args.limit:
        folders = folders[: args.limit]

    summary = {
        "scanned_folders": 0,
        "with_info_json": 0,
        "no_info_json": 0,
        "no_chapters_local": 0,
        "downloaded_missing": 0,
        "deleted_duplicates": 0,
        "deleted_extra": 0,
        "errors": 0,
        "folders": [],
    }

    for index, folder in enumerate(folders, 1):
        summary["scanned_folders"] += 1
        book_id = read_book_id(folder)
        if book_id is None:
            summary["no_info_json"] += 1
            continue

        try:
            local_info = json.loads((folder / "info.json").read_text(encoding="utf-8"))
        except Exception:
            local_info = {}
        status_name = str(local_info.get("status_name") or "").strip().lower()
        if local_info.get("status") == 2 or status_name in {"ho?n th?nh", "hoan thanh", "completed", "full", "finished"}:
            continue

        local_map = build_local_index(folder)
        if not local_map:
            summary["no_chapters_local"] += 1
            continue

        summary["with_info_json"] += 1
        item: dict = {
            "folder": folder.name,
            "book_id": book_id,
            "local_unique_chapters": len(local_map),
        }

        try:
            remote_chapters = get_chapters_once_safe(downloader, book_id)
        except Exception as exc:
            item["status"] = "api_error"
            item["error"] = str(exc)
            summary["errors"] += 1
            summary["folders"].append(item)
            print(f"[{index}] {folder.name}: API error {exc}", flush=True)
            continue

        remote_by_index: dict[int, dict] = {}
        for chapter in remote_chapters:
            try:
                chapter_index = int(
                    chapter.get("index") or chapter.get("number") or 0
                )
            except Exception:
                continue
            if chapter_index > 0:
                remote_by_index[chapter_index] = chapter

        remote_indices = set(remote_by_index)
        local_indices = set(local_map)

        missing = []
        duplicate_deleted = []
        extra_deleted = []
        folder_errors = []

        for chapter_index, entries in sorted(local_map.items()):
            if chapter_index not in remote_indices:
                for entry in entries:
                    if args.dry_run:
                        extra_deleted.append(entry["name"])
                        summary["deleted_extra"] += 1
                    else:
                        try:
                            entry["path"].unlink()
                            extra_deleted.append(entry["name"])
                            summary["deleted_extra"] += 1
                        except Exception as exc:
                            folder_errors.append(
                                f"delete extra {entry['name']}: {exc}"
                            )
                            summary["errors"] += 1
                continue

            if len(entries) > 1:
                remote_norm_name = alnum_norm(
                    clean_filename(
                        chapter_filename(
                            remote_by_index[chapter_index], chapter_index
                        )
                    ).removesuffix(".txt")
                )
                keeper, duplicates = pick_keeper(entries, remote_norm_name)
                for entry in duplicates:
                    if args.dry_run:
                        duplicate_deleted.append(entry["name"])
                        summary["deleted_duplicates"] += 1
                    else:
                        try:
                            entry["path"].unlink()
                            duplicate_deleted.append(entry["name"])
                            summary["deleted_duplicates"] += 1
                        except Exception as exc:
                            folder_errors.append(
                                f"delete duplicate {entry['name']}: {exc}"
                            )
                            summary["errors"] += 1

        for chapter_index in sorted(remote_indices - local_indices):
            if args.dry_run:
                missing.append({"index": chapter_index, "written": "(dry-run)"})
                summary["downloaded_missing"] += 1
            else:
                try:
                    written = fetch_and_write_chapter(
                        downloader,
                        folder,
                        remote_by_index[chapter_index],
                        chapter_index,
                    )
                    missing.append({"index": chapter_index, "written": written})
                    summary["downloaded_missing"] += 1
                except Exception as exc:
                    folder_errors.append(
                        f"download missing {chapter_index}: {exc}"
                    )
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

        tag = "DRY" if args.dry_run else "LIVE"
        print(
            f"[{index}] {folder.name}: [{tag}] remote={len(remote_indices)} "
            f"+{len(missing)} dup_del={len(duplicate_deleted)} "
            f"extra_del={len(extra_deleted)} err={len(folder_errors)}",
            flush=True,
        )

    REPORT_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    stats = {k: v for k, v in summary.items() if k != "folders"}
    print(f"REPORT={REPORT_PATH}", flush=True)
    print(json.dumps(stats, ensure_ascii=False), flush=True)
    return 0 if summary["errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
