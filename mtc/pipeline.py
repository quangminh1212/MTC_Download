"""pipeline.py – Download orchestrator via ADB/BlueStacks only."""
import re
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from .config import OUTPUT_DIR
from .adb import AdbController
from .utils import safe_name


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


def _is_legacy_chapter_file(ch_file: Path, chapter_index: int) -> bool:
    return ch_file.name.casefold() == f"{chapter_index:06d}_Chuong_{chapter_index}.txt".casefold()


def _find_existing_chapter_file(book_dir: Path, chapter_index: int) -> Optional[Path]:
    prefix = f"{chapter_index:06d}_"
    candidates = sorted(book_dir.glob(f"{prefix}*.txt"))
    if not candidates:
        return None
    candidates.sort(key=lambda path: (_is_legacy_chapter_file(path, chapter_index), path.name.casefold()))
    for path in candidates:
        return path
    return None


def _collect_legacy_chapter_indexes(book_dir: Path) -> List[int]:
    chapter_indexes: List[int] = []
    for path in sorted(book_dir.glob("*.txt")):
        match = re.fullmatch(r"(\d{6})_Chuong_(\d+)\.txt", path.name, re.IGNORECASE)
        if not match:
            continue
        chapter_indexes.append(int(match.group(2)))
    return sorted(set(chapter_indexes))


def _compact_chapter_ranges(chapter_indexes: List[int]) -> List[Tuple[int, int]]:
    if not chapter_indexes:
        return []

    ranges: List[Tuple[int, int]] = []
    start = chapter_indexes[0]
    prev = chapter_indexes[0]
    for chapter_index in chapter_indexes[1:]:
        if chapter_index == prev + 1:
            prev = chapter_index
            continue
        ranges.append((start, prev))
        start = prev = chapter_index
    ranges.append((start, prev))
    return ranges


def _delete_book_full_files(book_dir: Path, log_fn: Callable[[str], None] = print) -> int:
    removed = 0
    for full_file in sorted(book_dir.glob("*_FULL.txt")):
        try:
            full_file.unlink()
            removed += 1
            log_fn(f"Xóa file cũ: {full_file.name}")
        except OSError as exc:
            log_fn(f"⚠ Không xóa được {full_file.name}: {exc}")
    return removed


def upgrade_existing_downloads(
    adb: AdbController,
    output_dir: Path = OUTPUT_DIR,
    log_fn: Callable[[str], None] = print,
    stop_flag: Callable[[], bool] = lambda: False,
    progress_cb: Optional[Callable[[int, int], None]] = None,
) -> Dict:
    if not adb or not adb.device:
        return {"success": False, "reason": "Cần BlueStacks/ADB để nâng cấp file chapter cũ"}

    if not output_dir.exists():
        return {"success": False, "reason": f"Không thấy thư mục output: {output_dir}"}

    book_dirs = sorted(path for path in output_dir.iterdir() if path.is_dir())
    migration_plan = []
    deleted_full = 0

    for book_dir in book_dirs:
        deleted_full += _delete_book_full_files(book_dir, log_fn)
        legacy_indexes = _collect_legacy_chapter_indexes(book_dir)
        if legacy_indexes:
            migration_plan.append(
                {
                    "book_dir": book_dir,
                    "book_name": book_dir.name,
                    "legacy_indexes": legacy_indexes,
                    "ranges": _compact_chapter_ranges(legacy_indexes),
                }
            )

    if not migration_plan:
        reason = "Không còn file chapter kiểu cũ; chỉ dọn file _FULL xong"
        log_fn(reason)
        return {
            "success": True,
            "books_total": 0,
            "books_upgraded": 0,
            "books_failed": 0,
            "chapters_upgraded": 0,
            "chapters_failed": 0,
            "full_deleted": deleted_full,
            "failed_books": [],
            "reason": reason,
        }

    total_books = len(migration_plan)
    books_upgraded = 0
    books_failed = 0
    chapters_upgraded = 0
    chapters_failed = 0
    failed_books: List[str] = []

    log_fn(
        f"Chuẩn bị nâng cấp {sum(len(item['legacy_indexes']) for item in migration_plan)} chapter cũ "
        f"của {total_books} truyện"
    )

    for book_pos, item in enumerate(migration_plan, start=1):
        if stop_flag():
            break

        book_name = item["book_name"]
        ranges = item["ranges"]
        remaining_chapters = sum(end - start + 1 for start, end in ranges)
        book_failed = False

        if progress_cb:
            progress_cb(book_pos - 1, total_books)

        log_fn(
            f"[{book_pos}/{total_books}] {book_name}: "
            f"{len(item['legacy_indexes'])} chapter cũ, {len(ranges)} lượt đọc lại"
        )

        for range_pos, (ch_start, ch_end) in enumerate(ranges, start=1):
            if stop_flag():
                break

            if not adb.open_library_book(book_name, log_fn=log_fn):
                failed_books.append(book_name)
                books_failed += 1
                chapters_failed += remaining_chapters
                book_failed = True
                break

            log_fn(f"  [{range_pos}/{len(ranges)}] Nâng cấp ch{ch_start}-{ch_end}")
            range_total = ch_end - ch_start + 1
            result = download_via_adb(
                adb=adb,
                book_name=book_name,
                ch_start=ch_start,
                ch_end=ch_end,
                output_dir=output_dir,
                log_fn=log_fn,
                stop_flag=stop_flag,
            )
            ok_count = result.get("ok", 0)
            fail_count = result.get("fail", 0)
            accounted = ok_count + fail_count
            missing_count = max(range_total - accounted, 0) if not result.get("success") else 0

            chapters_upgraded += ok_count
            chapters_failed += fail_count + missing_count
            remaining_chapters -= range_total

            adb.return_to_library(log_fn)

            if not result.get("success"):
                failed_books.append(book_name)
                books_failed += 1
                book_failed = True
                break

        if not book_failed:
            books_upgraded += 1

    if progress_cb:
        progress_cb(total_books, total_books)

    success = books_failed == 0 and chapters_failed == 0
    if success:
        reason = (
            f"Đã nâng cấp {chapters_upgraded} chapter cũ của {books_upgraded} truyện "
            f"và xóa {deleted_full} file _FULL"
        )
    else:
        reason = (
            f"Đã nâng cấp {chapters_upgraded} chapter, lỗi {chapters_failed} chapter, "
            f"xóa {deleted_full} file _FULL"
        )

    log_fn(reason)
    return {
        "success": success,
        "books_total": total_books,
        "books_upgraded": books_upgraded,
        "books_failed": books_failed,
        "chapters_upgraded": chapters_upgraded,
        "chapters_failed": chapters_failed,
        "full_deleted": deleted_full,
        "failed_books": failed_books,
        "reason": reason,
    }


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


def queue_completed_books_in_app(
    adb: AdbController,
    max_items: int = 200,
    max_scrolls: int = 40,
    log_fn: Callable[[str], None] = print,
    stop_flag: Callable[[], bool] = lambda: False,
    progress_cb: Optional[Callable[[int, int], None]] = None,
) -> Dict:
    """Queue in-app downloads for completed books from the library via the app's own download dialog."""
    if not adb or not adb.device:
        return {"success": False, "reason": "Cần BlueStacks/ADB để tải hàng loạt trong app"}

    log_fn("ADB mode: quét Tủ Truyện và dùng popup 'Tải truyện' trong app")
    if not adb.open_library_tab(log_fn):
        return {"success": False, "reason": "Không mở được Tủ Truyện"}

    seen = set()
    inspected = 0
    queued = 0
    skipped = 0
    failed = 0
    stagnant_rounds = 0

    for page_idx in range(max_scrolls):
        if stop_flag():
            break

        visible_books = adb.scan_visible_library_books(log_fn=lambda *_: None)
        pending_books = [book for book in visible_books if book["key"] not in seen]
        if not pending_books:
            stagnant_rounds += 1
            if stagnant_rounds >= 2:
                break
            adb.swipe_up()
            continue

        stagnant_rounds = 0
        log_fn(f"Lượt Tủ Truyện {page_idx + 1}: {len(pending_books)} truyện mới")

        for book in pending_books:
            if stop_flag():
                break
            if inspected >= max_items:
                break

            seen.add(book["key"])
            inspected += 1
            if progress_cb:
                progress_cb(inspected, max_items)

            log_fn(
                f"[{inspected}] {book['title']} "
                f"({book['read_current']}/{book['read_total']})"
            )

            adb.tap(*book["center"])
            time.sleep(1.1)

            detail = adb.get_book_detail_meta()
            status_text = detail.get("status_text") or "Không rõ trạng thái"
            if not detail.get("can_read"):
                log_fn("  ⚠ Không nhận ra màn chi tiết truyện")
                failed += 1
                adb.return_to_library(log_fn)
                continue

            if not adb.detail_status_is_completed(status_text):
                log_fn(f"  Bỏ qua: {status_text}")
                skipped += 1
                adb.return_to_library(log_fn)
                continue

            total_chapters = book.get("read_total") or 0
            if total_chapters <= 0:
                log_fn("  ⚠ Không xác định được tổng chương để tải")
                failed += 1
                adb.return_to_library(log_fn)
                continue

            log_fn(f"  Hoàn thành: {status_text} -> tải ch1-{total_chapters}")
            ok = adb.open_current_book_reader(log_fn) and adb.queue_current_book_full_download(
                ch_start=1,
                ch_end=total_chapters,
                log_fn=log_fn,
            )
            if ok:
                queued += 1
            else:
                failed += 1

            adb.return_to_library(log_fn)

        if stop_flag():
            break
        if inspected >= max_items:
            break
        adb.swipe_up()

    success = failed == 0
    if queued == 0 and failed == 0:
        reason = "Không thấy truyện nào ở trạng thái hoàn thành trong Tủ Truyện"
    elif failed > 0:
        reason = f"Đã xếp {queued} truyện, lỗi {failed} truyện"
    else:
        reason = ""

    log_fn(
        f"\nXong tải trong app! inspected={inspected} queued={queued} skipped={skipped} failed={failed}"
    )
    return {
        "success": success,
        "inspected": inspected,
        "queued": queued,
        "skipped": skipped,
        "failed": failed,
        "reason": reason,
    }


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
        removed_full = _delete_book_full_files(book_dir, log_fn=lambda *_: None)
        if removed_full:
            log_fn(f"Đã xóa {removed_full} file _FULL cũ trong {book_dir.name}")

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

            existing_file = _find_existing_chapter_file(book_dir, ch_idx)
            legacy_existing = bool(existing_file and _is_legacy_chapter_file(existing_file, ch_idx))
            if existing_file and _existing_chapter_looks_ok(existing_file) and not legacy_existing:
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

            payload = adb.read_current_chapter_payload(log_fn)
            text = (payload.get("text") or "").strip()
            chapter_title = (payload.get("title") or f"Chương {ch_idx}").strip()
            ch_file = book_dir / f"{ch_idx:06d}_{safe_name(chapter_title)}.txt"
            if not text or len(text) < 50:
                log_fn(f"  [ch{ch_idx}] ⚠ Nội dung trống")
                n_fail += 1
            else:
                ch_file.write_text(
                    f"{'='*60}\n{chapter_title}\n{'='*60}\n\n{text}\n",
                    encoding="utf-8",
                )
                if legacy_existing and existing_file and existing_file != ch_file and existing_file.exists():
                    existing_file.unlink()
                log_fn(f"  [ch{ch_idx}] ✔ {ch_file.name} ({len(text)} ký tự)")
                n_ok += 1

            if ch_idx == ch_end:
                adb.go_back(2)
                time.sleep(0.2)
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
