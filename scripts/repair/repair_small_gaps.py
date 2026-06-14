#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
import sys
import time
import unicodedata
from pathlib import Path

sys.path.insert(0, r"C:\Dev\MTC_DOWNLOAD")

from mtc_downloader import MTCDownloader
from download_one_completed_live_decrypt import (
    get_chapters_once_safe,
    maybe_decrypt,
    normalize_chapter_title,
    sanitize_path_component,
    write_info_json,
    write_plain_chapter,
)
from download_all_missing_books import (
    ROOT,
    strict_book_name,
    strict_chapter_filename,
    strict_component,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

AUDIT_PATH = Path("C:/Dev/MTC_DOWNLOAD/logs/full_library_chapter_audit_v2.json")
OUT_PATH = Path("C:/Dev/MTC_DOWNLOAD/logs/repair_small_gaps_report.json")
CHAPTER_RE = re.compile(r"(?i)(?:chương|chuong)\s*(\d+)")


def norm(value: str) -> str:
    text = unicodedata.normalize("NFC", str(value or "")).casefold()
    return "".join(ch for ch in text if ch.isalnum())


def folder_map() -> dict[str, Path]:
    ignore = {".git", ".githooks", ".vscode", "__pycache__"}
    return {
        norm(path.name): path
        for path in ROOT.iterdir()
        if path.is_dir() and path.name not in ignore
    }


def index_from_filename(path: Path) -> int | None:
    match = CHAPTER_RE.search(path.stem)
    if not match:
        return None
    return int(match.group(1))


def write_one_chapter(folder: Path, chapter: dict, seq: int) -> str:
    downloader = MTCDownloader()
    chapter_id = chapter.get("id")
    detail = downloader.get_chapter_content(chapter_id)
    data = (detail or {}).get("data") or {}
    content = data.get("content") or data.get("body") or ""
    if not content:
        raise ValueError(f"chapter {chapter_id} empty content")
    plain, _ = maybe_decrypt(content)
    idx = int(chapter.get("index") or chapter.get("number") or seq)
    title = normalize_chapter_title(data.get("name") or chapter.get("name") or f"Chương {idx}", idx)
    filename = sanitize_path_component(strict_chapter_filename(data or chapter, seq))
    filepath = folder / filename
    write_plain_chapter(filepath, sanitize_path_component(strict_component(title, default=f"Chương {idx}")), plain)
    return filepath.name


def main() -> int:
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    audit_items = [
        item for item in audit["results"]
        if item.get("status") == "needs_repair" and item["id"] != 153588
    ]

    fmap = folder_map()
    downloader = MTCDownloader()
    report = []

    for item in audit_items:
        bid = int(item["id"])
        name = item["name"]
        folder = fmap.get(norm(name))
        if folder is None:
            folder = ROOT / strict_book_name(name)
            folder.mkdir(parents=True, exist_ok=True)

        print(f"repair book={bid} name={name}", flush=True)
        chapters = get_chapters_once_safe(downloader, bid)
        remote_by_index = {}
        for seq, chapter in enumerate(chapters, 1):
            idx = int(chapter.get("index") or chapter.get("number") or seq)
            remote_by_index[idx] = (seq, chapter)

        local_files = list(folder.glob("*.txt"))
        local_by_index: dict[int, list[Path]] = {}
        for path in local_files:
            idx = index_from_filename(path)
            if idx is not None:
                local_by_index.setdefault(idx, []).append(path)

        remote_set = set(remote_by_index)
        local_set = set(local_by_index)
        missing = sorted(remote_set - local_set)
        extra = sorted(local_set - remote_set)

        book_result = {
            "id": bid,
            "name": name,
            "folder": folder.name,
            "missing_before": missing,
            "extra_before": extra,
            "downloaded": [],
            "deleted": [],
            "errors": [],
        }

        for idx in extra:
            for path in local_by_index.get(idx, []):
                try:
                    path.unlink()
                    book_result["deleted"].append(path.name)
                except Exception as exc:
                    book_result["errors"].append(f"delete extra {path.name}: {exc}")

        for idx in missing:
            seq, chapter = remote_by_index[idx]
            ok = False
            for attempt in range(1, 5):
                try:
                    written = write_one_chapter(folder, chapter, seq)
                    book_result["downloaded"].append(written)
                    ok = True
                    break
                except Exception as exc:
                    if attempt == 4:
                        book_result["errors"].append(f"download idx {idx}: {exc}")
                    time.sleep(0.4 * attempt)
            if ok:
                time.sleep(0.05)

        detail = downloader.get_book_detail(bid)
        book_data = (detail or {}).get("data") or {"id": bid, "name": name}
        write_info_json(folder, book_data, chapters)

        # verify after repair
        local_after = {}
        for path in folder.glob("*.txt"):
            idx = index_from_filename(path)
            if idx is not None:
                local_after.setdefault(idx, []).append(path)
        missing_after = sorted(remote_set - set(local_after))
        extra_after = sorted(set(local_after) - remote_set)
        book_result["missing_after"] = missing_after
        book_result["extra_after"] = extra_after
        book_result["status"] = "ok" if not missing_after and not extra_after and not book_result["errors"] else "issue"
        report.append(book_result)
        print(
            f"  => downloaded={len(book_result['downloaded'])} deleted={len(book_result['deleted'])} "
            f"missing_after={len(missing_after)} extra_after={len(extra_after)} errors={len(book_result['errors'])}",
            flush=True,
        )

    OUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"report={OUT_PATH}")
    return 0 if all(item["status"] == "ok" for item in report) else 1


if __name__ == "__main__":
    raise SystemExit(main())
