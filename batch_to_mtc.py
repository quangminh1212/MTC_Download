#!/usr/bin/env python3
"""batch_to_mtc.py – Download ALL books from catalog to c:/dev/MTC, git commit each."""
import json
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mtc.api import create_session, fetch_full_catalog, fetch_chapters, fetch_chapter_text, resolve_book, cache_book
from mtc.downloader import load_catalog, save_catalog
from mtc.utils import safe_name
from mtc.config import CATALOG

TARGET = Path(r"c:\dev\MTC")
TARGET.mkdir(parents=True, exist_ok=True)


def git_commit(msg: str):
    """Stage all and commit in TARGET repo."""
    try:
        subprocess.run(["git", "add", "-A"], cwd=TARGET, capture_output=True, timeout=30)
        result = subprocess.run(
            ["git", "commit", "-m", msg],
            cwd=TARGET, capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace"
        )
        if result.returncode == 0:
            print(f"  📦 Committed: {msg}")
        else:
            stderr = result.stderr.strip()
            if "nothing to commit" in stderr:
                print(f"  (nothing new to commit)")
            else:
                print(f"  ⚠ git commit: {stderr[:120]}")
    except Exception as e:
        print(f"  ⚠ git error: {e}")


def download_one_book(session, book: dict) -> dict:
    """Download all chapters of one book. Returns {ok, fail, skipped}."""
    bid = book.get("id")
    bname = book.get("name", "?")
    bslug = book.get("slug", "")
    ch_count = book.get("chapter_count", 0)

    book_dir = TARGET / safe_name(bname)
    book_dir.mkdir(parents=True, exist_ok=True)

    # Fetch chapter list
    chapters = fetch_chapters(session, bid)
    if not chapters:
        # Try resolving by name
        resolved = resolve_book(session, bname, bid)
        if resolved:
            bid = resolved["id"]
            chapters = fetch_chapters(session, bid)
    
    if not chapters:
        print(f"  ✖ Không lấy được danh sách chương")
        return {"ok": 0, "fail": 0, "skipped": 0}

    ok, fail, skipped = 0, 0, 0
    failed_chapters = []

    for ch in chapters:
        ch_idx = ch.get("index") or 0
        ch_id = ch.get("id")

        # Check existing
        prefix = f"{ch_idx:06d}_"
        existing = list(book_dir.glob(f"{prefix}*.txt"))
        if existing:
            f = existing[0]
            if f.stat().st_size > 100:
                skipped += 1
                continue

        try:
            title, content = fetch_chapter_text(session, ch)
            if not content or len(content.strip()) < 50:
                raise ValueError(f"Nội dung quá ngắn ({len(content)} chars)")

            ch_file = book_dir / f"{ch_idx:06d}_{safe_name(title)}.txt"
            ch_file.write_text(
                f"{'=' * 60}\n{title}\n{'=' * 60}\n\n{content}\n",
                encoding="utf-8",
            )
            # Remove old file if name changed
            for old in existing:
                if old != ch_file and old.exists():
                    old.unlink()
            ok += 1
        except Exception as exc:
            fail += 1
            failed_chapters.append(ch)
            print(f"  [ch{ch_idx}] ⚠ {exc}")

    # Retry pass
    if failed_chapters:
        print(f"  Retry {len(failed_chapters)} chương lỗi...")
        time.sleep(1)
        for ch in failed_chapters:
            ch_idx = ch.get("index") or 0
            try:
                title, content = fetch_chapter_text(session, ch)
                if not content or len(content.strip()) < 50:
                    raise ValueError(f"Nội dung quá ngắn")
                ch_file = book_dir / f"{ch_idx:06d}_{safe_name(title)}.txt"
                ch_file.write_text(
                    f"{'=' * 60}\n{title}\n{'=' * 60}\n\n{content}\n",
                    encoding="utf-8",
                )
                ok += 1
                fail -= 1
            except Exception as exc:
                print(f"  [ch{ch_idx}] ✖ retry: {exc}")

    return {"ok": ok, "fail": fail, "skipped": skipped, "total_chapters": len(chapters)}


def main():
    session = create_session()

    # Refresh catalog
    print("Đang cập nhật catalog từ API...")
    books = fetch_full_catalog(session)
    if books:
        save_catalog(books)
        print(f"Catalog: {len(books)} truyện")
    else:
        books = load_catalog()
        print(f"Dùng catalog local: {len(books)} truyện")

    if not books:
        print("Không có truyện nào!")
        return

    # Sort by id for consistent order
    books.sort(key=lambda b: b.get("id", 0))

    total = len(books)
    total_ok = 0
    total_fail = 0
    total_skip_books = 0

    for i, book in enumerate(books):
        bname = book.get("name", "?")
        bid = book.get("id", 0)
        ch_count = book.get("chapter_count", 0)
        status = book.get("status_name", "?")

        # Quick check if already fully downloaded
        book_dir = TARGET / safe_name(bname)
        if book_dir.is_dir():
            existing_count = sum(
                1 for f in book_dir.glob("*.txt")
                if re.match(r"^\d{6}_", f.name) and f.stat().st_size > 100
            )
            if ch_count > 0 and existing_count >= ch_count:
                print(f"[{i+1}/{total}] ⊘ {bname} — đã có {existing_count}/{ch_count} ch")
                total_skip_books += 1
                continue

        print(f"\n[{i+1}/{total}] ⚡ {bname} (#{bid}, {ch_count} ch, {status})")

        result = download_one_book(session, book)
        ok = result["ok"]
        fail = result["fail"]
        skipped = result["skipped"]
        total_ch = result.get("total_chapters", ch_count)

        print(f"  ✔{ok}  ✖{fail}  ⊘{skipped}  (tổng {total_ch} chương)")

        if ok > 0:
            total_ok += 1
            git_commit(f"📚 {bname} ({ok + skipped}/{total_ch} chương)")
        elif skipped > 0 and fail == 0:
            total_ok += 1
        else:
            total_fail += 1

    print(f"\n{'=' * 60}")
    print(f"HOÀN TẤT: {total} truyện")
    print(f"  ✔ Thành công: {total_ok}")
    print(f"  ✖ Lỗi: {total_fail}")
    print(f"  ⊘ Đã có sẵn: {total_skip_books}")


if __name__ == "__main__":
    main()
