"""downloader.py – Download orchestrator (pure API, no ADB)."""
import json
import re
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional

from .config import OUTPUT_DIR, CATALOG, log
from .api import (
    create_session,
    resolve_book,
    fetch_chapters,
    fetch_chapter_text,
    fetch_full_catalog,
    cache_book,
)
from .utils import safe_name


# ── Helpers ─────────────────────────────────────────────────────────────────
def _find_chapter_file(book_dir: Path, ch_index: int) -> Optional[Path]:
    prefix = f"{ch_index:06d}_"
    for p in sorted(book_dir.glob(f"{prefix}*.txt")):
        return p
    return None


def _chapter_ok(ch_file: Path) -> bool:
    if not ch_file.exists() or ch_file.stat().st_size <= 100:
        return False
    try:
        text = ch_file.read_text(encoding="utf-8")
    except Exception:
        return False
    parts = text.split("\n\n", 1)
    body = parts[1].strip() if len(parts) == 2 else text.strip()
    non_empty = [l for l in body.splitlines() if l.strip()]
    return len(body) >= 600 and len(non_empty) > 2


def _delete_full_files(book_dir: Path) -> int:
    removed = 0
    for f in book_dir.glob("*_FULL.txt"):
        try:
            f.unlink()
            removed += 1
        except OSError:
            pass
    return removed


# ── Single book download ───────────────────────────────────────────────────
def download_book(
    book_name: str,
    ch_start: int = 1,
    ch_end: Optional[int] = None,
    output_dir: Path = OUTPUT_DIR,
    log_fn: Callable[[str], None] = print,
    stop_flag: Callable[[], bool] = lambda: False,
    progress_cb: Optional[Callable[[int, int], None]] = None,
    book_id: Optional[int] = None,
) -> Dict:
    """Download a single book via API. Returns result dict."""
    session = create_session()

    book = resolve_book(session, book_name, book_id)
    if not book:
        return {"success": False, "ok": 0, "fail": 0, "reason": "Không tìm thấy truyện"}

    bid = book.get("id")
    bname = book.get("name") or book_name

    chapters = fetch_chapters(session, bid)
    if not chapters:
        return {"success": False, "ok": 0, "fail": 0, "reason": "Không lấy được danh sách chương"}

    if ch_end is None:
        ch_end = max((c.get("index") or 0) for c in chapters)

    targets = [c for c in chapters if ch_start <= (c.get("index") or 0) <= ch_end]
    if not targets:
        return {"success": False, "ok": 0, "fail": 0, "reason": "Khoảng chương không hợp lệ"}

    book_dir = output_dir / safe_name(bname)
    book_dir.mkdir(parents=True, exist_ok=True)
    _delete_full_files(book_dir)

    total = len(targets)
    ok, fail = 0, 0
    failed_targets: List[Dict] = []
    log_fn(f"⚡ API: {bname} ({total} chương, #{bid})")

    for done, ch in enumerate(targets):
        if stop_flag():
            log_fn("Đã dừng.")
            break
        if progress_cb:
            progress_cb(done, total)

        ch_idx = ch.get("index") or 0
        existing = _find_chapter_file(book_dir, ch_idx)
        if existing and _chapter_ok(existing):
            ok += 1
            continue

        try:
            title, content = fetch_chapter_text(session, ch)
            ch_file = book_dir / f"{ch_idx:06d}_{safe_name(title)}.txt"
            ch_file.write_text(
                f"{'=' * 60}\n{title}\n{'=' * 60}\n\n{content}\n",
                encoding="utf-8",
            )
            # Remove old file if different name
            if existing and existing != ch_file and existing.exists():
                existing.unlink()
            log_fn(f"  [ch{ch_idx}] ⚡ {ch_file.name} ({len(content)} ký tự)")
            ok += 1
        except Exception as exc:
            log_fn(f"  [ch{ch_idx}] ⚠ {exc}")
            fail += 1
            failed_targets.append(ch)

    # Retry pass
    if failed_targets and not stop_flag():
        log_fn(f"Retry {len(failed_targets)} chương lỗi...")
        retry_list = failed_targets
        failed_targets = []
        fail = 0
        for ch in retry_list:
            ch_idx = ch.get("index") or 0
            try:
                title, content = fetch_chapter_text(session, ch)
                ch_file = book_dir / f"{ch_idx:06d}_{safe_name(title)}.txt"
                ch_file.write_text(
                    f"{'=' * 60}\n{title}\n{'=' * 60}\n\n{content}\n",
                    encoding="utf-8",
                )
                log_fn(f"  [ch{ch_idx}] ✔ retry ({len(content)} ký tự)")
                ok += 1
            except Exception as exc:
                log_fn(f"  [ch{ch_idx}] ✖ retry: {exc}")
                fail += 1

    if progress_cb:
        progress_cb(total, total)

    success = ok > 0 and fail == 0
    reason = "" if success else (
        f"Tải được {ok}, lỗi {fail}" if ok else "Không tải được chương nào"
    )
    log_fn(f"Xong! ✔{ok}  ✖{fail}  →  {book_dir}")
    return {
        "success": success,
        "ok": ok,
        "fail": fail,
        "output": str(book_dir),
        "book_id": bid,
        "book_name": bname,
        "reason": reason,
    }


# ── Batch download ──────────────────────────────────────────────────────────
def load_catalog() -> List[Dict]:
    """Load books from local all_books.json."""
    if not CATALOG.exists():
        return []
    try:
        return json.loads(CATALOG.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_catalog(books: List[Dict]) -> None:
    CATALOG.parent.mkdir(parents=True, exist_ok=True)
    CATALOG.write_text(
        json.dumps(books, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def refresh_catalog(log_fn: Callable[[str], None] = print) -> List[Dict]:
    """Fetch full catalog from API and save locally."""
    session = create_session()
    log_fn("Đang tải catalog từ API...")
    books = fetch_full_catalog(session)
    if books:
        save_catalog(books)
        log_fn(f"Đã lưu {len(books)} truyện vào {CATALOG}")
    else:
        log_fn("Không lấy được catalog từ API")
    return books


def download_batch(
    books: List[Dict],
    output_dir: Path = OUTPUT_DIR,
    log_fn: Callable[[str], None] = print,
    stop_flag: Callable[[], bool] = lambda: False,
    skip_existing: bool = True,
    status_filter: Optional[str] = None,
) -> Dict:
    """Download multiple books. Returns summary."""
    if status_filter:
        filtered = [
            b for b in books
            if status_filter.lower() in (b.get("status_name") or "").lower()
        ]
    else:
        filtered = list(books)

    total = len(filtered)
    done_ok = 0
    done_fail = 0
    skipped = 0

    for i, book in enumerate(filtered):
        if stop_flag():
            break

        name = book.get("name", "?")
        bid = book.get("id")

        if skip_existing:
            bdir = output_dir / safe_name(name)
            ch_count = book.get("chapter_count") or 0
            if bdir.is_dir():
                existing = sum(
                    1 for f in bdir.glob("*.txt")
                    if re.match(r"^\d{6}_", f.name) and f.stat().st_size > 100
                )
                if ch_count > 0 and existing >= ch_count * 0.9:
                    log_fn(f"[{i+1}/{total}] {name}: đã có {existing}/{ch_count} chương, bỏ qua")
                    skipped += 1
                    continue

        log_fn(f"\n[{i+1}/{total}] {name} (#{bid}, {book.get('chapter_count', '?')} ch)")
        result = download_book(
            book_name=name,
            book_id=bid,
            output_dir=output_dir,
            log_fn=log_fn,
            stop_flag=stop_flag,
        )
        if result.get("success"):
            done_ok += 1
        else:
            done_fail += 1
            log_fn(f"  → Lỗi: {result.get('reason', '?')}")

    return {
        "total": total,
        "ok": done_ok,
        "fail": done_fail,
        "skipped": skipped,
    }
