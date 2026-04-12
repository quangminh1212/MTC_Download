"""pipeline.py – Download orchestrator via ADB/BlueStacks."""
import time
from pathlib import Path
from typing import Optional, Dict, Callable

from .config import APK_PATH, OUTPUT_DIR, PACKAGE, log
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
      1. Bật accessibility → Flutter semantics tree
      2. Mở app MTC
      3. Tìm truyện → mở
      4. Từng chương: điều hướng → đọc text → lưu file
    """
    # Ensure APK installed
    pkg = adb.get_installed_package()
    if not pkg:
        log_fn("App MTC chưa cài. Đang cài...")
        if not adb.install_apk(APK_PATH, log_fn):
            return {"success": False, "reason": "install_failed"}
        pkg = adb.get_installed_package() or PACKAGE

    log_fn(f"Package: {pkg}")
    model, ver = adb.get_device_model(), adb.get_android_version()
    if model or ver:
        log_fn(f"Device: {model} (Android {ver})")

    log_fn("Bật accessibility (Flutter semantics)...")
    adb.enable_accessibility(log_fn)

    log_fn("Mở app MTC...")
    adb.force_stop(pkg)
    time.sleep(0.5)
    adb.launch(pkg)

    if not adb.nav_to_book(book_name, log_fn):
        log_fn(f"⚠ Không tìm thấy «{book_name}» trong app.")
        log_fn("  → Hãy mở truyện thủ công trên BlueStacks, tool sẽ tiếp tục...")
        time.sleep(5)
        if stop_flag():
            return {"success": False, "reason": "stopped"}

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

        log_fn(f"  [ch{ch_idx}] Điều hướng...")
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

        adb.go_back(2)
        time.sleep(0.3)

    merge_to_single_file(book_dir, book_name)
    log_fn(f"\nXong! ✔{n_ok}  ✖{n_fail}  →  {book_dir}")
    adb.disable_accessibility()
    return {"success": True, "ok": n_ok, "fail": n_fail, "output": str(book_dir)}
