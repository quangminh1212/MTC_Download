#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

from mtc_downloader import MTCDownloader
from download_one_completed_live_decrypt import (
    maybe_decrypt,
    normalize_chapter_title,
    sanitize_path_component,
    write_plain_chapter,
)
from download_completed_to_mtc import chapter_filename

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Dev\MTC")
LOG = Path(r"C:\Dev\MTC_Download\logs\fill_missing_from_manifest.json")
NUM_RE = re.compile(r"(\d+)")


def chapter_indexes(folder: Path) -> set[int]:
    out = set()
    for path in folder.glob("*.txt"):
        match = NUM_RE.search(path.name)
        if match:
            out.add(int(match.group(1)))
    return out


def iter_targets() -> list[dict]:
    targets = []
    for folder in sorted(
        [p for p in ROOT.iterdir() if p.is_dir() and not p.name.startswith(".")],
        key=lambda p: p.name.lower(),
    ):
        info_path = folder / "info.json"
        manifest_path = folder / "chapters_manifest.json"
        if not info_path.exists() or not manifest_path.exists():
            continue
        try:
            info = json.loads(info_path.read_text(encoding="utf-8"))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(manifest, list):
            continue
        have = chapter_indexes(folder)
        missing = []
        for chapter in manifest:
            try:
                index = int(chapter.get("index") or 0)
            except Exception:
                continue
            if index > 0 and index not in have:
                missing.append(chapter)
        if missing:
            targets.append(
                {
                    "id": int(info.get("id") or 0),
                    "folder": str(folder),
                    "name": info.get("name"),
                    "chapter_count": int(info.get("chapter_count") or 0),
                    "latest_index": int(info.get("latest_index") or 0),
                    "missing": missing,
                }
            )
    return targets


def write_one(folder: Path, chapter_stub: dict, detail_data: dict):
    index = int(chapter_stub.get("index") or detail_data.get("index") or 0)
    title = normalize_chapter_title(
        detail_data.get("name") or chapter_stub.get("name") or f"Chương {index}",
        index,
    )
    safe_name = sanitize_path_component(chapter_filename(chapter_stub, index))
    content = detail_data.get("content") or detail_data.get("body") or ""
    plain, _ = maybe_decrypt(content)
    write_plain_chapter(folder / safe_name, title, plain)


def main() -> int:
    downloader = MTCDownloader()
    targets = iter_targets()
    report = {"targets": [], "summary": {"books": len(targets), "downloaded": 0, "failed": 0}}

    print(f"targets={len(targets)}")
    for book_idx, book in enumerate(targets, 1):
        folder = Path(book["folder"])
        missing = sorted(book["missing"], key=lambda row: int(row.get("index") or 0))
        book_row = {
            "id": book["id"],
            "name": book["name"],
            "folder": book["folder"],
            "chapter_count": book["chapter_count"],
            "latest_index": book["latest_index"],
            "missing_indexes": [int(ch.get("index") or 0) for ch in missing],
            "downloaded": [],
            "failed": [],
        }
        print(f"[{book_idx}/{len(targets)}] book_id={book['id']} missing={len(missing)} folder={folder.name}")
        for chapter in missing:
            chapter_id = chapter.get("id")
            index = int(chapter.get("index") or 0)
            try:
                detail = downloader.get_chapter_content(chapter_id)
                data = (detail or {}).get("data") or {}
                content = data.get("content") or data.get("body") or ""
                if not content:
                    raise ValueError("empty content")
                write_one(folder, chapter, data)
                book_row["downloaded"].append({"index": index, "chapter_id": chapter_id})
                report["summary"]["downloaded"] += 1
                print(f"  OK index={index} chapter_id={chapter_id}")
            except Exception as exc:
                book_row["failed"].append({"index": index, "chapter_id": chapter_id, "error": str(exc)})
                report["summary"]["failed"] += 1
                print(f"  FAIL index={index} chapter_id={chapter_id} error={exc}")
            LOG.parent.mkdir(parents=True, exist_ok=True)
            LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            time.sleep(0.12)
        report["targets"].append(book_row)
        LOG.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print(LOG)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
