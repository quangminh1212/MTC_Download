#!/usr/bin/env python3
"""test_download.py – Quick test: download a few chapters from 2-3 books."""
import sys, os, time, io
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mtc.adb import AdbController
from mtc.pipeline import download_via_adb, _HAS_API_DEPS
from mtc.config import OUTPUT_DIR
from mtc.utils import safe_name


def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def test_download_book(adb, title, max_chapters=5):
    """Test downloading a few chapters from one book."""
    log(f"\n{'='*60}")
    log(f"TEST: {title}")
    log(f"Max chapters: {max_chapters}")
    log(f"{'='*60}")

    # Step 1: Find and open book from library
    log("Step 1: Mo truyen tu Thu Truyen...")
    book_info = adb.open_library_book(title, log_fn=lambda msg: log(f"  {msg}"))
    if not book_info:
        log("FAIL: Khong tim thay truyen trong Thu Truyen")
        return False

    log(f"  -> Mo thanh cong: {book_info.get('title', '?')}")
    time.sleep(0.5)

    # Step 2: Open reader
    log("Step 2: Mo reader...")
    if not adb.open_current_book_reader(log_fn=lambda msg: log(f"  {msg}")):
        log("FAIL: Khong vao duoc reader")
        adb.return_to_library(log_fn=lambda msg: log(f"  {msg}"))
        return False

    log("  -> Da vao reader")
    time.sleep(0.5)

    # Step 3: Download via ADB
    log(f"Step 3: Tai {max_chapters} chuong qua ADB...")
    result = download_via_adb(
        adb=adb,
        book_name=title,
        ch_start=1,
        ch_end=max_chapters,
        log_fn=lambda msg: log(f"  {msg}"),
    )

    ok = result.get("ok", 0)
    fail = result.get("fail", 0)
    success = result.get("success", False)

    log(f"\nResult: ok={ok}, fail={fail}, success={success}")
    if result.get("reason"):
        log(f"Reason: {result['reason']}")

    # Step 4: Verify output files
    book_dir = OUTPUT_DIR / safe_name(title)
    if book_dir.exists():
        files = sorted(book_dir.glob("*.txt"))
        log(f"\nOutput files in {book_dir.name}:")
        for f in files[:10]:
            size = f.stat().st_size
            # Read first line to verify encoding
            try:
                first_lines = f.read_text(encoding="utf-8").split("\n")[:5]
                preview = first_lines[1] if len(first_lines) > 1 else first_lines[0]
                log(f"  {f.name} ({size} bytes) - {preview[:60]}")
            except Exception as e:
                log(f"  {f.name} ({size} bytes) - ERROR: {e}")

    # Step 5: Return to library
    log("\nStep 5: Quay lai Thu Truyen...")
    adb.return_to_library(log_fn=lambda msg: log(f"  {msg}"))
    time.sleep(1.0)

    return success


def main():
    adb_path = AdbController.find_adb()
    if not adb_path:
        log("FAIL: Khong tim thay ADB")
        return 1

    adb = AdbController(adb_path, "127.0.0.1:5555")
    if not adb.ensure_device():
        log("FAIL: Khong ket noi duoc thiet bi")
        return 1

    pkg = adb.get_installed_package()
    log(f"ADB: {adb_path}")
    log(f"Package: {pkg}")

    # Enable accessibility first
    adb.enable_accessibility(log_fn=lambda msg: log(f"  {msg}"))

    # Test books - pick 2 short ones
    test_books = [
        # Book with 84 chapters (already completed, good for verifying skip logic)
        ("Ta Có Thể Diễn Hóa Tiên Thần Đạo Đồ", 5),
        # Short book, only 3 chapters read
        ("Theo Môn Phái Võ Lâm Đến Trường Sinh Tiên Môn", 5),
        # Another one with 20 chapters read
        ("Để Ngươi Người Quản Lý Phế Vật Lớp, Làm Sao Thành Võ Thần Điện", 5),
    ]

    results = []
    for title, max_ch in test_books:
        try:
            success = test_download_book(adb, title, max_chapters=max_ch)
            results.append((title, success))
        except Exception as e:
            log(f"EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            results.append((title, False))
            # Try to recover
            adb.return_to_library(log_fn=lambda msg: log(f"  {msg}"))
            time.sleep(1.0)

    log(f"\n{'='*60}")
    log("SUMMARY")
    log(f"{'='*60}")
    for title, success in results:
        status = "PASS" if success else "FAIL"
        log(f"  [{status}] {title}")

    passed = sum(1 for _, s in results if s)
    log(f"\n{passed}/{len(results)} tests passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
