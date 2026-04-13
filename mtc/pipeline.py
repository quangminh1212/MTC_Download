"""pipeline.py – Download orchestrator via ADB/BlueStacks only."""
import time
from pathlib import Path
from typing import Callable, Dict, Optional

from .config import OUTPUT_DIR
from .adb import AdbController
from .utils import merge_to_single_file, safe_name


def _existing_chapter_looks_ok(ch_file: Path) -> bool:
    if not ch_file.exists() or ch_file.stat().st_size <= 100:
        return False
    try:
        text = ch_file.read_text(encoding="utf-8")
    except Exception:
        return False

    parts = text.split("\n\n", 1)
    body = parts[1].strip() if len(parts) == 2 else text.strip()
    non_empty_lines = [line for line in body.splitlines() if line.strip()]
    if len(body) < 600:
        return False
    if len(non_empty_lines) <= 2:
        return False
    return True


def download_book(
    adb:         Optional[AdbController],
    book_name:   str,
    ch_start:    int = 1,
    ch_end:      Optional[int] = None,
    output_dir:  Path = OUTPUT_DIR,
    log_fn:      Callable[[str], None] = print,
    stop_flag:   Callable[[], bool] = lambda: False,
    progress_cb: Optional[Callable[[int, int], None]] = None,
) -> Dict:
    if not adb or not adb.device:
        return {"success": False, "reason": "Cần BlueStacks/ADB để tải ở chế độ ADB-only"}

    log_fn("ADB-only mode: tải truyện trực tiếp qua BlueStacks")
    return download_via_adb(
        adb=adb,
        book_name=book_name,
        ch_start=ch_start,
        ch_end=ch_end,
        output_dir=output_dir,
        log_fn=log_fn,
        stop_flag=stop_flag,
        progress_cb=progress_cb,
    )


def download_via_adb(
    adb:         AdbController,
    book_name:   str,
    ch_start:    int = 1,
    ch_end:      Optional[int] = None,
    output_dir:  Path = OUTPUT_DIR,
    log_fn:      Callable[[str], None] = print,
    stop_flag:   Callable[[], bool] = lambda: False,
    progress_cb: Optional[Callable[[int, int], None]] = None,
) -> Dict:
    """
    Pipeline tải truyện qua BlueStacks:
      User đã mở truyện trên MTC app sẵn.
      1. Bật accessibility
      2. Từng chương: điều hướng → đọc text → lưu file
    """
    log_fn("Bật accessibility...")
    adb.enable_accessibility(log_fn)

    try:
        if not adb.open_chapter_list(log_fn=lambda *_: None):
            log_fn("ADB chưa đứng ở màn truyện hiện tại, thử tự mở truyện...")
            if not adb.nav_to_book(book_name, log_fn):
                return {
                    "success": False,
                    "ok": 0,
                    "fail": 0,
                    "reason": "ADB không mở được đúng truyện để bắt đầu tải",
                }
            if not adb.open_chapter_list(log_fn):
                return {
                    "success": False,
                    "ok": 0,
                    "fail": 0,
                    "reason": "ADB đã vào app nhưng không mở được danh sách chương",
                }

        book_dir = output_dir / safe_name(book_name)
        book_dir.mkdir(parents=True, exist_ok=True)

        if ch_end is None:
            ch_end = ch_start + 9999

        total = ch_end - ch_start + 1
        n_ok = 0
        n_fail = 0

        for ch_idx in range(ch_start, ch_end + 1):
            if stop_flag():
                log_fn("Đã dừng.")
                break

            if progress_cb:
                progress_cb(ch_idx - ch_start, total)

            ch_file = book_dir / f"{ch_idx:06d}_Chuong_{ch_idx}.txt"
            if _existing_chapter_looks_ok(ch_file):
                log_fn(f"  [ch{ch_idx}] Đã có, bỏ qua")
                n_ok += 1
                continue

            if ch_idx == ch_start:
                log_fn(f"  [ch{ch_idx}] Điều hướng tới chương đầu...")
                if not adb.nav_to_chapter(ch_idx, log_fn):
                    log_fn(f"  [ch{ch_idx}] ⚠ Không tìm thấy chương")
                    n_fail += 1
                    if n_fail >= 5:
                        log_fn("Quá nhiều lỗi điều hướng. Dừng.")
                        break
                    continue
            else:
                log_fn(f"  [ch{ch_idx}] Chuyển chương nhanh...")
                if not adb.reader_next_chapter(log_fn):
                    log_fn(f"  [ch{ch_idx}] ⚠ Chuyển chương nhanh lỗi, thử fallback")
                    if not adb.nav_to_chapter(ch_idx, log_fn):
                        log_fn(f"  [ch{ch_idx}] ⚠ Không tìm thấy chương")
                        n_fail += 1
                        if n_fail >= 5:
                            log_fn("Quá nhiều lỗi điều hướng. Dừng.")
                            break
                        continue

            text = adb.read_current_chapter(log_fn)
            if not text or len(text) < 50:
                log_fn(f"  [ch{ch_idx}] ⚠ Nội dung trống")
                n_fail += 1
            else:
                ch_file.write_text(
                    f"{'='*60}\nChương {ch_idx}\n{'='*60}\n\n{text}\n",
                    encoding="utf-8",
                )
                log_fn(f"  [ch{ch_idx}] ✔ ({len(text)} ký tự)")
                n_ok += 1

            if ch_idx == ch_end:
                adb.go_back(2)
                time.sleep(0.2)

        if n_ok > 0:
            merge_to_single_file(book_dir, book_name)
        log_fn(f"\nXong! ✔{n_ok}  ✖{n_fail}  →  {book_dir}")

        success = n_ok > 0 and n_fail == 0
        reason = "" if success else (
            f"ADB tải được {n_ok} chương, lỗi {n_fail} chương" if n_ok > 0 else "ADB không đọc được chương nào"
        )
        return {
            "success": success,
            "ok": n_ok,
            "fail": n_fail,
            "output": str(book_dir),
            "reason": reason,
        }
    finally:
        adb.disable_accessibility()
