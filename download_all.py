#!/usr/bin/env python3
"""download_all.py – Batch download ALL novels from MTC library.

Usage:
    python download_all.py                  # Queue in-app downloads for all books
    python download_all.py --mode hybrid    # Export chapters via API + ADB fallback
    python download_all.py --list           # Just list books in library
    python download_all.py --book "Title"   # Download specific book
    python download_all.py --skip-existing  # Skip books that already have files
"""
import sys, os, time, argparse, json
from pathlib import Path

# Ensure proper UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mtc.adb import AdbController
from mtc.pipeline import download_via_adb, download_via_api, _HAS_API_DEPS
from mtc.config import OUTPUT_DIR


ROOT_DIR = Path(__file__).resolve().parent
CATALOG_PATH = ROOT_DIR / "data" / "all_books.json"


def log(msg: str):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def _lookup_key(text: str) -> str:
    return "".join(ch for ch in (text or "").casefold() if ch.isalnum())


def _publish_status_from_text(text: str) -> str:
    lowered = (text or "").casefold()
    if "hoàn thành" in lowered:
        return "completed"
    if "còn tiếp" in lowered:
        return "ongoing"
    return "unknown"


def _publish_status_label(status: str) -> str:
    labels = {
        "all": "Tất cả",
        "completed": "Hoàn thành",
        "ongoing": "Còn tiếp",
        "unknown": "Không rõ",
    }
    return labels.get(status, status)


def load_book_queries(book_file: Path) -> list[str]:
    if not book_file.exists():
        raise FileNotFoundError(f"Không thấy file danh sách truyện: {book_file}")

    if book_file.suffix.lower() == ".json":
        data = json.loads(book_file.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("File JSON danh sách truyện phải là mảng")

        queries = []
        for item in data:
            if isinstance(item, str):
                title = item.strip()
            elif isinstance(item, dict):
                title = str(item.get("title") or item.get("name") or "").strip()
            else:
                title = ""
            if title:
                queries.append(title)
        return queries

    lines = book_file.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]


def collect_book_queries(args) -> list[str]:
    queries = []
    if args.book:
        queries.append(args.book.strip())
    if args.book_file:
        queries.extend(load_book_queries(Path(args.book_file)))

    seen = set()
    result = []
    for query in queries:
        key = _lookup_key(query)
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(query)
    return result


def book_matches_query(title: str, query: str) -> bool:
    title_folded = (title or "").casefold()
    query_folded = (query or "").casefold()
    if query_folded and query_folded in title_folded:
        return True

    title_key = _lookup_key(title)
    query_key = _lookup_key(query)
    return bool(query_key and query_key in title_key)


def filter_books_by_queries(books: list[dict], queries: list[str]) -> tuple[list[dict], list[str]]:
    if not queries:
        return books, []

    selected = []
    selected_keys = set()
    unmatched = []
    for query in queries:
        matched_any = False
        for book in books:
            if not book_matches_query(book["title"], query):
                continue
            matched_any = True
            if book["key"] in selected_keys:
                continue
            selected_keys.add(book["key"])
            selected.append(book)
        if not matched_any:
            unmatched.append(query)
    return selected, unmatched


def load_catalog_status_index() -> dict[str, dict]:
    if not CATALOG_PATH.exists():
        return {}

    try:
        data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}

    if not isinstance(data, list):
        return {}

    result = {}
    for item in data:
        if not isinstance(item, dict):
            continue
        title = str(item.get("name") or item.get("title") or "").strip()
        key = _lookup_key(title)
        if not key:
            continue
        status_text = str(item.get("status_name") or item.get("state") or "").strip()
        status = _publish_status_from_text(status_text)
        if status == "unknown":
            continue
        result[key] = {
            "publish_status": status,
            "status_text": status_text,
            "status_source": "catalog",
        }
    return result


def resolve_book_publish_status(adb: AdbController, book: dict, catalog_statuses: dict[str, dict]) -> dict:
    cached = catalog_statuses.get(book["key"])
    if cached:
        resolved = dict(book)
        resolved.update(cached)
        return resolved

    log(f"  🔎 Kiểm tra trạng thái phát hành: {book['title']}")
    if not adb.open_library_book(book["title"], log_fn=lambda *_: None):
        resolved = dict(book)
        resolved.update({
            "publish_status": "unknown",
            "status_text": "Không mở được chi tiết",
            "status_source": "detail",
        })
        return resolved

    detail = adb.get_book_detail_meta()
    status_text = detail.get("status_text") or "Không rõ trạng thái"
    resolved = dict(book)
    resolved.update({
        "publish_status": _publish_status_from_text(status_text),
        "status_text": status_text,
        "status_source": "detail",
    })
    adb.return_to_library(log_fn=lambda *_: None)
    return resolved


def filter_books_by_publish_status(
    adb: AdbController,
    books: list[dict],
    status_filter: str,
) -> list[dict]:
    if status_filter == "all":
        return books

    catalog_statuses = load_catalog_status_index()
    filtered = []
    for book in books:
        resolved = resolve_book_publish_status(adb, book, catalog_statuses)
        if resolved.get("publish_status") == status_filter:
            filtered.append(resolved)

    log(
        f"🎯 Lọc trạng thái {_publish_status_label(status_filter)}: "
        f"{len(filtered)}/{len(books)} truyện"
    )
    return filtered


def count_existing_chapters(book_dir: Path) -> int:
    """Count downloaded chapter files in a book directory."""
    import re
    count = 0
    for f in book_dir.glob("*.txt"):
        if re.match(r"^\d{6}_", f.name) and f.stat().st_size > 100:
            count += 1
    return count


def queue_book_download_in_app(
    adb: AdbController,
    title: str,
    total_chapters: int,
) -> dict:
    """Use the app's own `Tải truyện` popup to queue one book for download."""
    log("  📱 Dùng popup Tải truyện trong app...")

    book_info = adb.open_library_book(title, log_fn=lambda msg: log(f"    {msg}"))
    if not book_info:
        return {
            "success": False,
            "queued_in_app": False,
            "reason": "Không mở được truyện từ Tủ Truyện",
        }

    target_total = total_chapters or book_info.get("read_total") or 0
    if target_total <= 0:
        adb.return_to_library(log_fn=lambda msg: log(f"    {msg}"))
        return {
            "success": False,
            "queued_in_app": False,
            "reason": "Không xác định được tổng chương để xếp tải",
        }

    if not adb.open_current_book_reader(log_fn=lambda msg: log(f"    {msg}")):
        adb.return_to_library(log_fn=lambda msg: log(f"    {msg}"))
        return {
            "success": False,
            "queued_in_app": False,
            "reason": "Không vào được reader để mở popup tải",
        }

    queued = adb.queue_current_book_full_download(
        ch_start=1,
        ch_end=target_total,
        log_fn=lambda msg: log(f"    {msg}"),
    )
    adb.return_to_library(log_fn=lambda msg: log(f"    {msg}"))

    if not queued:
        return {
            "success": False,
            "queued_in_app": False,
            "reason": f"Không xếp được lệnh tải ch1-{target_total}",
        }

    return {
        "success": True,
        "queued_in_app": True,
        "range_end": target_total,
        "reason": "",
    }


def download_one_book(
    adb: AdbController,
    title: str,
    total_chapters: int,
    skip_existing: bool = False,
    mode: str = "app",
) -> dict:
    """Process a single book using the selected strategy."""
    from mtc.utils import safe_name

    if mode == "app":
        return queue_book_download_in_app(adb=adb, title=title, total_chapters=total_chapters)

    book_dir = OUTPUT_DIR / safe_name(title)
    existing = count_existing_chapters(book_dir) if book_dir.exists() else 0

    if skip_existing and existing >= total_chapters and total_chapters > 0:
        log(f"  ⏭ Đã có đủ {existing}/{total_chapters} chương, bỏ qua")
        return {"success": True, "ok": existing, "fail": 0, "skipped": True}

    if existing > 0:
        log(f"  📂 Đã có {existing}/{total_chapters} chương, sẽ tải bổ sung")

    # Try API first (faster, more reliable)
    if mode == "hybrid" and _HAS_API_DEPS:
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

    # ADB export path: need to open book in library, then navigate + read
    log(f"  📱 Tải qua ADB...")

    # First, open the book from library
    if not adb.open_library_book(title, log_fn=lambda msg: log(f"    {msg}")):
        log(f"  ❌ Không tìm thấy truyện trong Tủ Truyện")
        return {"success": False, "ok": 0, "fail": 0, "reason": "Không mở được truyện từ Tủ Truyện"}

    # download_via_adb handles chapter list navigation from the book detail page
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
    parser = argparse.ArgumentParser(description="Download novels from MTC app")
    parser.add_argument("--list", action="store_true", help="Just list books in library")
    parser.add_argument("--book", type=str, help="Download specific book by title (partial match)")
    parser.add_argument("--book-file", type=str, help="Load titles to queue from .txt or .json list")
    parser.add_argument("--skip-existing", action="store_true", help="Skip books already fully downloaded")
    parser.add_argument("--max-books", type=int, default=200, help="Max books to process")
    parser.add_argument("--device", type=str, default="127.0.0.1:5555", help="ADB device")
    parser.add_argument(
        "--status-filter",
        choices=["all", "completed", "ongoing"],
        default="all",
        help="Lọc theo trạng thái phát hành của truyện trong app/catalog",
    )
    parser.add_argument(
        "--mode",
        choices=["app", "hybrid", "adb"],
        default="app",
        help="app = dùng popup Tải truyện trong app; hybrid = API + ADB export; adb = chỉ ADB export",
    )
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

    if args.mode == "app" and args.skip_existing:
        log("ℹ --skip-existing chỉ áp dụng cho mode export; mode app sẽ để app tự quyết định chương đã tải hay chưa")

    queries = collect_book_queries(args)
    if queries:
        log(f"📝 Đã nạp {len(queries)} truy vấn truyện")

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

    targets, unmatched_queries = filter_books_by_queries(books, queries)
    if unmatched_queries:
        log(f"⚠ Không khớp {len(unmatched_queries)} truy vấn: {', '.join(unmatched_queries[:10])}")
    if queries and not targets:
        log("❌ Không tìm thấy truyện nào khớp danh sách yêu cầu")
        return 1

    targets = filter_books_by_publish_status(adb, targets, args.status_filter)
    if not targets:
        log("❌ Không còn truyện nào sau khi áp dụng bộ lọc")
        return 1

    for i, b in enumerate(targets, 1):
        from mtc.utils import safe_name
        book_dir = OUTPUT_DIR / safe_name(b["title"])
        existing = count_existing_chapters(book_dir) if book_dir.exists() else 0
        download_status = "✅" if existing >= b["read_total"] and b["read_total"] > 0 else f"📥 {existing}"
        publish_status = b.get("publish_status")
        publish_label = f" | {_publish_status_label(publish_status)}" if publish_status else ""
        print(f"  {i:3d}. [{download_status}/{b['read_total']}] {b['title']}{publish_label}")

    if args.list:
        return 0

    log(f"\n{'='*70}")
    if args.mode == "app":
        log(f"🚀 BẮT ĐẦU XẾP TẢI TRONG APP: {len(targets)} truyện")
    else:
        log(f"🚀 BẮT ĐẦU TẢI EXPORT: {len(targets)} truyện")
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
            mode=args.mode,
        )

        ok = result.get("ok", 0)
        fail = result.get("fail", 0)
        skipped = result.get("skipped", False)
        queued_in_app = result.get("queued_in_app", False)

        results.append({
            "title": title,
            "total": total,
            "ok": ok,
            "fail": fail,
            "success": result.get("success", False),
            "skipped": skipped,
            "queued_in_app": queued_in_app,
            "range_end": result.get("range_end", total),
        })

        if skipped:
            log(f"  ⏭ Đã bỏ qua (đủ chương)")
        elif args.mode == "app" and result.get("success"):
            log(f"  ✅ Đã gửi lệnh tải trong app: ch1-{result.get('range_end', total)}")
        elif args.mode == "app":
            log(f"  ⚠ Không xếp tải được: {result.get('reason', '?')}")
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
        if args.mode == "app":
            print(f"  {status} {r['title']}: ch1-{r['range_end']}")
        else:
            print(f"  {status} {r['title']}: {r['ok']}/{r['total']} chương")

    if args.mode == "app":
        log(f"\nTổng: {total_success}/{len(results)} truyện đã xếp tải trong app, {len(results) - total_success} truyện lỗi")
        return 0 if total_success == len(results) else 1

    log(f"\nTổng: {total_success}/{len(results)} truyện OK, {total_ok} chương tải được, {total_fail} lỗi, {total_skipped} bỏ qua")

    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
