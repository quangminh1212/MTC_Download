"""pipeline.py – Download orchestrator via ADB/BlueStacks."""
import time
from pathlib import Path
from typing import Optional, Dict, Callable

from .config import OUTPUT_DIR, log
from .adb import AdbController
from .utils import safe_name, merge_to_single_file


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

    book_dir = output_dir / safe_name(book_name)
    book_dir.mkdir(parents=True, exist_ok=True)

    if ch_end is None:
        ch_end = ch_start + 9999

    total  = ch_end - ch_start + 1
    n_ok   = 0
    n_fail = 0

    for ch_idx in range(ch_start, ch_end + 1):
        if stop_flag():
            log_fn("Đã dừng."); break

        if progress_cb:
            progress_cb(ch_idx - ch_start, total)

        ch_file = book_dir / f"{ch_idx:06d}_Chuong_{ch_idx}.txt"
        if ch_file.exists() and ch_file.stat().st_size > 100:
            log_fn(f"  [ch{ch_idx}] Đã có, bỏ qua"); n_ok += 1; continue

        if ch_idx == ch_start:
            log_fn(f"  [ch{ch_idx}] Điều hướng tới chương đầu...")
            if not adb.nav_to_chapter(ch_idx, log_fn):
                log_fn(f"  [ch{ch_idx}] ⚠ Không tìm thấy chương"); n_fail += 1
                if n_fail >= 5:
                    log_fn("Quá nhiều lỗi điều hướng. Dừng."); break
                continue
        else:
            log_fn(f"  [ch{ch_idx}] Chuyển chương nhanh...")
            if not adb.reader_next_chapter(log_fn):
                log_fn(f"  [ch{ch_idx}] ⚠ Chuyển chương nhanh lỗi, thử fallback")
                if not adb.nav_to_chapter(ch_idx, log_fn):
                    log_fn(f"  [ch{ch_idx}] ⚠ Không tìm thấy chương"); n_fail += 1
                    if n_fail >= 5:
                        log_fn("Quá nhiều lỗi điều hướng. Dừng."); break
                    continue

        text = adb.read_current_chapter(log_fn)
        if not text or len(text) < 50:
            log_fn(f"  [ch{ch_idx}] ⚠ Nội dung trống"); n_fail += 1
        else:
            ch_file.write_text(
                f"{'='*60}\nChương {ch_idx}\n{'='*60}\n\n{text}\n",
                encoding="utf-8",
            )
            log_fn(f"  [ch{ch_idx}] ✔ ({len(text)} ký tự)"); n_ok += 1

        if ch_idx == ch_end:
            adb.go_back(2)
            time.sleep(0.2)

    merge_to_single_file(book_dir, book_name)
    log_fn(f"\nXong! ✔{n_ok}  ✖{n_fail}  →  {book_dir}")
    adb.disable_accessibility()
    return {"success": True, "ok": n_ok, "fail": n_fail, "output": str(book_dir)}
