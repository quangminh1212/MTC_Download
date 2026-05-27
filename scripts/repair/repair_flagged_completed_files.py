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
from download_all_missing_books import strict_chapter_filename, strict_component

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Dev\MTC")
SCAN_REPORT = Path(r"C:\Dev\MTC_DOWNLOAD\logs\deep_scan_completed.json")
OUT_REPORT = Path(r"C:\Dev\MTC_DOWNLOAD\logs\repair_flagged_completed_files.json")
CHAPTER_RE = re.compile(r"(?i)(?:chương|chuong)\s*(\d+)")
TARGET_KINDS = {"duplicate_title_fragment", "control_char"}


def alnum_norm(v: str) -> str:
    text = unicodedata.normalize("NFC", str(v or "")).casefold()
    return "".join(c for c in text if c.isalnum())


def parse_index(filename: str) -> int | None:
    m = CHAPTER_RE.search(Path(filename).stem)
    return int(m.group(1)) if m else None


def title_core_words(title: str) -> set[str]:
    t = re.sub(r"(?i)^chương\s*\d+\s*", "", title or "").strip()
    return {w for w in re.findall(r"\w+", t.casefold(), flags=re.UNICODE) if w}


def looks_like_title_fragment(line: str, title: str, index: int) -> bool:
    s = (line or "").strip()
    if not s:
        return False

    compact = alnum_norm(s)
    title_norm = alnum_norm(title)
    if len(s) <= 3:
        return True
    if re.match(rf"(?i)^chương\s*0*{index}(?:\b|\s*[:.\-])", s):
        return True
    if compact and title_norm and len(compact) >= 5 and compact in title_norm:
        return True

    words = {w for w in re.findall(r"\w+", s.casefold(), flags=re.UNICODE) if w}
    core = title_core_words(title)
    if words and core and words.issubset(core):
        return True

    alpha = sum(ch.isalpha() for ch in s)
    if len(s) < 80 and alpha < max(4, len(s) // 3):
        return True
    return False


def strip_leading_title_garbage(body: str, title: str, index: int) -> str:
    lines = body.splitlines()
    kept = []
    removed = 0
    i = 0
    # only inspect the first few body lines to avoid harming prose later
    while i < len(lines) and i < 8:
        line = lines[i]
        if not line.strip():
            if removed > 0:
                i += 1
                continue
            kept.append(line)
            i += 1
            continue
        if looks_like_title_fragment(line, title, index):
            removed += 1
            i += 1
            continue
        break
    result = lines[i:]
    while result and not result[0].strip():
        result.pop(0)
    return "\n".join(result).strip()


def fetch_and_write(downloader: MTCDownloader, folder: Path, chapter: dict, seq: int) -> str:
    chapter_id = chapter.get("id")
    detail = downloader.get_chapter_content(chapter_id)
    data = (detail or {}).get("data") or {}
    content = data.get("content") or data.get("body") or ""
    if not content:
        raise ValueError(f"chapter {chapter_id} has no content")
    plain, _ = maybe_decrypt(content)
    index = int(chapter.get("index") or chapter.get("number") or seq)
    title = normalize_chapter_title(data.get("name") or chapter.get("name") or f"Chương {index}", index)
    cleaned_plain = strip_leading_title_garbage(plain, title, index)
    filename = sanitize_path_component(strict_chapter_filename(data or chapter, seq))
    path = folder / filename
    write_plain_chapter(path, sanitize_path_component(strict_component(title, default=f"Chương {index}")), cleaned_plain)
    return path.name


def main() -> int:
    report = json.loads(SCAN_REPORT.read_text(encoding="utf-8"))
    todo = []
    for entry in report:
        files = set()
        for issue in entry.get("issues", []):
            if issue.get("kind") in TARGET_KINDS and issue.get("file"):
                files.add(issue["file"])
        if files:
            todo.append({
                "id": int(entry["id"]),
                "folder": entry["folder"],
                "book": entry["book"],
                "files": sorted(files),
            })

    downloader = MTCDownloader()
    results = []
    total_books = len(todo)

    for seq_book, item in enumerate(todo, 1):
        book_id = item["id"]
        folder = ROOT / item["folder"]
        print(f"[{seq_book}/{total_books}] book={book_id} {item['folder']} flagged_files={len(item['files'])}", flush=True)
        book_result = {
            "id": book_id,
            "folder": item["folder"],
            "book": item["book"],
            "flagged_files": len(item["files"]),
            "repaired": [],
            "errors": [],
        }
        try:
            detail = downloader.get_book_detail(book_id)
            book_data = (detail or {}).get("data") or {"id": book_id, "name": item["book"]}
            chapters = get_chapters_once_safe(downloader, book_id)
            remote_by_index = {}
            for seq, chapter in enumerate(chapters, 1):
                idx = int(chapter.get("index") or chapter.get("number") or seq)
                remote_by_index.setdefault(idx, (seq, chapter))

            for bad_file in item["files"]:
                idx = parse_index(bad_file)
                if idx is None:
                    book_result["errors"].append(f"cannot parse index from {bad_file}")
                    continue
                payload = remote_by_index.get(idx)
                if payload is None:
                    book_result["errors"].append(f"remote chapter missing for index {idx} ({bad_file})")
                    continue
                seq, chapter = payload
                try:
                    written = fetch_and_write(downloader, folder, chapter, seq)
                    book_result["repaired"].append({"from": bad_file, "to": written, "index": idx})
                except Exception as exc:
                    book_result["errors"].append(f"index {idx} {bad_file}: {exc}")
                time.sleep(0.02)

            write_info_json(folder, book_data, chapters)
        except Exception as exc:
            book_result["errors"].append(f"book_error: {exc}")

        print(f"  => repaired={len(book_result['repaired'])} errors={len(book_result['errors'])}", flush=True)
        results.append(book_result)

    OUT_REPORT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    total_repaired = sum(len(r["repaired"]) for r in results)
    total_errors = sum(len(r["errors"]) for r in results)
    print(f"report={OUT_REPORT}")
    print(f"repaired={total_repaired} errors={total_errors}")
    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
