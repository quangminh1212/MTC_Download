#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import html
import json
import re
import sys
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
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Dev\MTC")
MANIFEST = Path(r"C:\Dev\MTC_DOWNLOAD\completed_books.json")
LOG_DIR = Path(r"C:\Dev\MTC_DOWNLOAD\logs")
REPORT = LOG_DIR / "sync_all_completed_strict_report.json"
LOG_DIR.mkdir(parents=True, exist_ok=True)

IGNORE_DIRS = {".git", ".githooks", ".vscode", "__pycache__"}
CHAPTER_RE = re.compile(r"(?i)(?:chương|chuong)\s*(\d+)")
SPACE_RE = re.compile(r"\s+")
ENCRYPTED_MARKERS = ("eyJpdiI6", '"iv":"', '"value":"')


def alnum_norm(value: str) -> str:
    text = unicodedata.normalize("NFC", html.unescape(str(value or ""))).casefold()
    return "".join(ch for ch in text if ch.isalnum())


def strict_component(value: str, default: str = "Untitled") -> str:
    text = unicodedata.normalize("NFC", html.unescape(str(value or "")))
    text = "".join(ch if (ch.isalnum() or ch.isspace()) else " " for ch in text)
    text = SPACE_RE.sub(" ", text).strip(" .")
    return text or default


def strict_book_name(raw_name: str) -> str:
    return strict_component(clean_filename(raw_name), default="Untitled")


def strict_chapter_filename(chapter: dict, fallback_index: int) -> str:
    base = chapter_filename(chapter, fallback_index)
    stem = Path(base).stem
    suffix = Path(base).suffix
    match = re.match(r"(?i)^(chương\s+\d+)(?:\s+(.*))?$", stem)
    if not match:
        return strict_component(stem, default=f"Chương {fallback_index}") + suffix
    prefix = strict_component(match.group(1), default=f"Chương {fallback_index}")
    title = strict_component(match.group(2) or "", default="")
    return f"{prefix} {title}{suffix}".strip()


def folder_map() -> dict[str, Path]:
    out: dict[str, Path] = {}
    for path in ROOT.iterdir():
        if path.is_dir() and path.name not in IGNORE_DIRS:
            out.setdefault(alnum_norm(path.name), path)
    return out


def parse_local(folder: Path) -> tuple[dict[int, list[Path]], list[Path]]:
    by_index: dict[int, list[Path]] = {}
    unknown: list[Path] = []
    for path in sorted(folder.glob("*.txt")):
        match = CHAPTER_RE.search(path.stem)
        if not match:
            unknown.append(path)
            continue
        index = int(match.group(1))
        by_index.setdefault(index, []).append(path)
    return by_index, unknown


def pick_keeper(paths: list[Path], expected_name: str) -> Path:
    expected_norm = alnum_norm(expected_name)
    ranked = sorted(
        paths,
        key=lambda path: (
            0 if alnum_norm(path.name) == expected_norm else 1,
            -path.stat().st_size,
            path.name.casefold(),
        ),
    )
    return ranked[0]


def rename_unique(src: Path, target: Path) -> Path:
    if src == target:
        return target
    if not target.exists():
        src.rename(target)
        return target
    if alnum_norm(src.name) == alnum_norm(target.name):
        target.unlink()
        src.rename(target)
        return target
    raise FileExistsError(f"target exists: {target}")


def fetch_and_write(downloader: MTCDownloader, folder: Path, chapter: dict, fallback_index: int) -> str:
    chapter_id = chapter.get("id")
    detail = downloader.get_chapter_content(chapter_id)
    data = (detail or {}).get("data") or {}
    content = data.get("content") or data.get("body") or ""
    if not content:
        raise ValueError(f"chapter {chapter_id} has no content")
    plain, _ = maybe_decrypt(content)
    index = int(chapter.get("index") or chapter.get("number") or fallback_index)
    title = normalize_chapter_title(data.get("name") or chapter.get("name") or f"Chương {index}", index)
    strict_name = strict_chapter_filename(data or chapter, fallback_index)
    path = folder / strict_name
    write_plain_chapter(path, strict_component(title, default=f"Chương {index}"), plain)
    return path.name


def has_markers(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="replace")
    return any(marker in text for marker in ENCRYPTED_MARKERS)


def main() -> int:
    books = json.loads(MANIFEST.read_text(encoding="utf-8"))
    completed = [
        book for book in books
        if (book.get("status_name") == "Hoàn thành" or book.get("status") == 2)
    ]
    downloader = MTCDownloader()
    summary = {
        "books_total": len(completed),
        "books_with_chapters": 0,
        "folders_created": 0,
        "folders_renamed": 0,
        "chapter_files_downloaded": 0,
        "chapter_files_renamed": 0,
        "chapter_duplicates_deleted": 0,
        "chapter_extras_deleted": 0,
        "chapter_unknown_deleted": 0,
        "errors": 0,
        "books": [],
    }

    for seq, book in enumerate(completed, 1):
        book_id = int(book["id"])
        expected_count = int(book.get("chapter_count") or book.get("latest_index") or 0)
        if expected_count <= 0:
            summary["books"].append({
                "id": book_id,
                "name": book.get("name"),
                "status": "no_chapters",
            })
            print(f"[{seq}/{len(completed)}] {book_id}: no chapters", flush=True)
            continue

        summary["books_with_chapters"] += 1
        strict_name = strict_book_name(book.get("name") or f"book {book_id}")
        current_folder = folder_map().get(alnum_norm(book.get("name") or strict_name))
        if current_folder is None:
            current_folder = ROOT / strict_name
            current_folder.mkdir(parents=True, exist_ok=True)
            summary["folders_created"] += 1
        elif current_folder.name != strict_name:
            target_folder = ROOT / strict_name
            if not target_folder.exists():
                current_folder.rename(target_folder)
                current_folder = target_folder
                summary["folders_renamed"] += 1

        book_result = {
            "id": book_id,
            "name": book.get("name"),
            "folder": current_folder.name,
            "expected_count": expected_count,
            "downloaded": [],
            "renamed": [],
            "duplicates_deleted": [],
            "extras_deleted": [],
            "unknown_deleted": [],
            "errors": [],
        }

        try:
            chapters = get_chapters_once_safe(downloader, book_id)
        except Exception as exc:
            summary["errors"] += 1
            book_result["status"] = "api_error"
            book_result["errors"].append(str(exc))
            summary["books"].append(book_result)
            print(f"[{seq}/{len(completed)}] {current_folder.name}: api_error {exc}", flush=True)
            continue

        remote_by_index: dict[int, dict] = {}
        expected_by_index: dict[int, str] = {}
        for idx, chapter in enumerate(chapters, 1):
            chapter_index = int(chapter.get("index") or chapter.get("number") or idx)
            remote_by_index[chapter_index] = chapter
            expected_by_index[chapter_index] = strict_chapter_filename(chapter, idx)

        local_by_index, unknown_files = parse_local(current_folder)
        for unknown in unknown_files:
            try:
                unknown.unlink()
                book_result["unknown_deleted"].append(unknown.name)
                summary["chapter_unknown_deleted"] += 1
            except Exception as exc:
                book_result["errors"].append(f"delete unknown {unknown.name}: {exc}")
                summary["errors"] += 1

        remote_indices = set(remote_by_index)

        for local_index, paths in sorted(local_by_index.items()):
            if local_index not in remote_indices:
                for path in paths:
                    try:
                        path.unlink()
                        book_result["extras_deleted"].append(path.name)
                        summary["chapter_extras_deleted"] += 1
                    except Exception as exc:
                        book_result["errors"].append(f"delete extra {path.name}: {exc}")
                        summary["errors"] += 1
                continue

            expected_name = expected_by_index[local_index]
            keeper = pick_keeper(paths, expected_name)
            consumed_names = {keeper.name}
            target = current_folder / expected_name
            if keeper.name != expected_name:
                try:
                    old_name = keeper.name
                    keeper = rename_unique(keeper, target)
                    consumed_names.add(old_name)
                    consumed_names.add(keeper.name)
                    book_result["renamed"].append({"from": old_name, "to": expected_name})
                    summary["chapter_files_renamed"] += 1
                except Exception as exc:
                    book_result["errors"].append(f"rename {keeper.name} -> {expected_name}: {exc}")
                    summary["errors"] += 1
            for path in paths:
                if path.name in consumed_names:
                    continue
                try:
                    path.unlink()
                    book_result["duplicates_deleted"].append(path.name)
                    summary["chapter_duplicates_deleted"] += 1
                except Exception as exc:
                    book_result["errors"].append(f"delete duplicate {path.name}: {exc}")
                    summary["errors"] += 1

        existing_norms = {alnum_norm(path.name) for path in current_folder.glob("*.txt")}
        for chapter_index in sorted(remote_indices):
            expected_name = expected_by_index[chapter_index]
            if alnum_norm(expected_name) in existing_norms:
                continue
            try:
                written = fetch_and_write(downloader, current_folder, remote_by_index[chapter_index], chapter_index)
                book_result["downloaded"].append(written)
                summary["chapter_files_downloaded"] += 1
                existing_norms.add(alnum_norm(written))
            except Exception as exc:
                book_result["errors"].append(f"download {chapter_index}: {exc}")
                summary["errors"] += 1
            time.sleep(0.08)

        final_files = sorted(current_folder.glob("*.txt"))
        final_norms = {alnum_norm(path.name) for path in final_files}
        expected_norms = {alnum_norm(name) for name in expected_by_index.values()}
        marker_hits = [path.name for path in final_files if has_markers(path)]
        missing_norms = sorted(expected_norms - final_norms)
        extra_norms = sorted(final_norms - expected_norms)
        write_info_json(current_folder, book, chapters)

        if marker_hits:
            for name in marker_hits:
                book_result["errors"].append(f"encrypted marker remains: {name}")
                summary["errors"] += 1

        book_result["final_count"] = len(final_files)
        book_result["missing_count"] = len(missing_norms)
        book_result["extra_count"] = len(extra_norms)
        book_result["status"] = "ok" if not book_result["errors"] and not missing_norms and not extra_norms else "issue"
        summary["books"].append(book_result)
        print(
            f"[{seq}/{len(completed)}] {current_folder.name}: remote={len(remote_indices)} "
            f"downloaded={len(book_result['downloaded'])} renamed={len(book_result['renamed'])} "
            f"dup_del={len(book_result['duplicates_deleted'])} extra_del={len(book_result['extras_deleted'])} "
            f"err={len(book_result['errors'])}",
            flush=True,
        )

    REPORT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"REPORT={REPORT}")
    print(json.dumps({k: v for k, v in summary.items() if k != 'books'}, ensure_ascii=False))
    return 0 if summary["errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
