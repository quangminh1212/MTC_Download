#!/usr/bin/env python3
"""download_all.py – Batch download ALL novels from MTC library via ADB.

Usage:
    python download_all.py                  # Download all books
    python download_all.py --list           # Just list books in library
    python download_all.py --book "Title"   # Download specific book
    python download_all.py --skip-existing  # Skip books that already have files
"""
import sys, os, time, argparse, json
from pathlib import Path

# Ensure proper UTF-8 output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mtc.adb import AdbController
from mtc.pipeline import download_via_adb, download_via_api, _HAS_API_DEPS
from mtc.config import OUTPUT_DIR


def log(msg: str):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def count_existing_chapters(book_dir: Path) -> int:
    """Count downloaded chapter files in a book directory."""
    import re
    count = 0
    for f in book_dir.glob("*.txt"):
        if re.match(r"^\d{6}_", f.name) and f.stat().st_size > 100:
            count += 1
    return count


def download_one_book(
    adb: AdbController,
    title: str,
    total_chapters: int,
    skip_existing: bool = False,
) -> dict:
    """Download a single book, trying API first then ADB fallback."""
    from mtc.utils import safe_name

    book_dir = OUTPUT_DIR / safe_name(title)
    existing = count_existing_chapters(book_dir) if book_dir.exists() else 0

    if skip_existing and existing >= total_chapters and total_chapters > 0:
        log(f"  ⏭ Đã có đủ {existing}/{total_chapters} chương, bỏ qua")
        return {"success": True, "ok": existing, "fail": 0, "skipped": True}

    if existing > 0:
        log(f"  📂 Đã có {existing}/{total_chapters} chương, sẽ tải bổ sung")

    # Try API first (faster, more reliable)
    if _HAS_API_DEPS:
        try:
            log(f"  ⚡ Thử tải qua API...")
            api_result = download_via_api(
                book_name=title,
                ch_start=1,
                ch_end=total_chapters if total_chapters > 0 else None,
                log_fn=lambda msg: log(f"    {msg}"),
            )
            if api_result.get("success"):
                log(f"  ✅ API thành công: {api_result.get('ok', 0)} chương")
                return api_result
            log(f"  ⚠ API không hoàn tất: {api_result.get('reason', '?')}")
        except Exception as e:
            log(f"  ⚠ API lỗi: {e}")

    # ADB fallback: need to open book in library, then navigate + read
    log(f"  📱 Tải qua ADB...")

    # First, open the book from library
    if not adb.open_library_book(title, log_fn=lambda msg: log(f"    {msg}")):
        log(f"  ❌ Không tìm thấy truyện trong Tủ Truyện")
        return {"success": False, "ok": 0, "fail": 0, "reason": "Không mở được truyện từ Tủ Truyện"}

    # Open reader
    if not adb.open_current_book_reader(log_fn=lambda msg: log(f"    {msg}")):
        log(f"  ❌ Không vào được reader")
        adb.return_to_library(log_fn=lambda msg: log(f"    {msg}"))
        return {"success": False, "ok": 0, "fail": 0, "reason": "Không mở được reader"}

    # Now use download_via_adb (it expects to be in the book already)
    result = download_via_adb(
        adb=adb,
        book_name=title,
        ch_start=1,
        ch_end=total_chapters if total_chapters > 0 else None,
        log_fn=lambda msg: log(f"    {msg}"),
    )

    # Return to library for next book
    adb.return_to_library(log_fn=lambda msg: log(f"    {msg}"))

    return result


def main():
    parser = argparse.ArgumentParser(description="Download novels from MTC app via ADB")
    parser.add_argument("--list", action="store_true", help="Just list books in library")
    parser.add_argument("--book", type=str, help="Download specific book by title (partial match)")
    parser.add_argument("--skip-existing", action="store_true", help="Skip books already fully downloaded")
    parser.add_argument("--max-books", type=int, default=200, help="Max books to process")
    parser.add_argument("--device", type=str, default="127.0.0.1:5555", help="ADB device")
    args = parser.parse_args()

    adb_path = AdbController.find_adb()
    if not adb_path:
        log("❌ Không tìm thấy ADB. Hãy cài BlueStacks hoặc ADB.")
        return 1

    adb = AdbController(adb_path, args.device)
    if not adb.ensure_device():
        log("❌ Không kết nối được thiết bị ADB")
        return 1

    pkg = adb.get_installed_package()
    if not pkg:
        log("❌ App MTC chưa được cài trên thiết bị")
        return 1

    log(f"✅ ADB: {adb_path}")
    log(f"✅ Package: {pkg}")

    # Enable accessibility for Flutter
    adb.enable_accessibility(log_fn=lambda msg: log(f"  {msg}"))

    # Scan library
    log("📚 Quét Tủ Truyện...")
    books = adb.scan_library_books(max_items=args.max_books, max_scrolls=40, log_fn=lambda msg: log(f"  {msg}"))

    if not books:
        log("❌ Không thấy truyện nào trong Tủ Truyện")
        return 1

    log(f"\n{'='*70}")
    log(f"📚 TỦ TRUYỆN: {len(books)} truyện")
    log(f"{'='*70}")

    for i, b in enumerate(books, 1):
        from mtc.utils import safe_name
        book_dir = OUTPUT_DIR / safe_name(b["title"])
        existing = count_existing_chapters(book_dir) if book_dir.exists() else 0
        status = "✅" if existing >= b["read_total"] and b["read_total"] > 0 else f"📥 {existing}"
        print(f"  {i:3d}. [{status}/{b['read_total']}] {b['title']}")

    if args.list:
        return 0

    # Filter books to download
    targets = books
    if args.book:
        query = args.book.lower()
        targets = [b for b in books if query in b["title"].lower()]
        if not targets:
            log(f"❌ Không tìm thấy truyện khớp: {args.book}")
            return 1

    log(f"\n{'='*70}")
    log(f"🚀 BẮT ĐẦU TẢI: {len(targets)} truyện")
    log(f"{'='*70}\n")

    results = []
    for idx, book in enumerate(targets, 1):
        title = book["title"]
        total = book["read_total"]

        log(f"\n[{idx}/{len(targets)}] 📖 {title} ({total} chương)")

        result = download_one_book(
            adb=adb,
            title=title,
            total_chapters=total,
            skip_existing=args.skip_existing,
        )

        ok = result.get("ok", 0)
        fail = result.get("fail", 0)
        skipped = result.get("skipped", False)

        results.append({
            "title": title,
            "total": total,
            "ok": ok,
            "fail": fail,
            "success": result.get("success", False),
            "skipped": skipped,
        })

        if skipped:
            log(f"  ⏭ Đã bỏ qua (đủ chương)")
        elif result.get("success"):
            log(f"  ✅ Thành công: {ok}/{total} chương")
        else:
            log(f"  ⚠ Kết quả: ✔{ok} ✖{fail} - {result.get('reason', '?')}")

    # Summary
    log(f"\n{'='*70}")
    log(f"📊 KẾT QUẢ TỔNG HỢP")
    log(f"{'='*70}")
    total_ok = sum(r["ok"] for r in results)
    total_fail = sum(r["fail"] for r in results)
    total_skipped = sum(1 for r in results if r["skipped"])
    total_success = sum(1 for r in results if r["success"])

    for r in results:
        status = "⏭" if r["skipped"] else ("✅" if r["success"] else "❌")
        print(f"  {status} {r['title']}: {r['ok']}/{r['total']} chương")

    log(f"\nTổng: {total_success}/{len(results)} truyện OK, {total_ok} chương tải được, {total_fail} lỗi, {total_skipped} bỏ qua")

    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
