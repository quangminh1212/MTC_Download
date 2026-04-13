"""pipeline.py – Download orchestrator with fast API path and ADB fallback."""
import base64
import difflib
import json
import re
import string
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    from Crypto.Cipher import AES
    from ftfy import fix_text
    _HAS_API_DEPS = True
except Exception:
    requests = None
    HTTPAdapter = None
    Retry = None
    AES = None
    fix_text = None
    _HAS_API_DEPS = False

from .config import OUTPUT_DIR, API_BASE, USER_AGENT
from .adb import AdbController
from .utils import safe_name


_API_HEADERS = {
    "content-type": "application/json",
    "Accept": "application/json",
    "User-Agent": USER_AGENT,
    "x-app": "app.android",
}
_BASE64_BYTES = set((string.ascii_letters + string.digits + "+/=").encode())
_BOOK_ID_CACHE_FILE = OUTPUT_DIR / ".book_id_cache.json"


def _lookup_key(text: str) -> str:
    return "".join(ch for ch in (text or "").casefold() if ch.isalnum())


def _load_book_id_cache() -> Dict[str, Dict]:
    if not _BOOK_ID_CACHE_FILE.exists():
        return {}

    try:
        data = json.loads(_BOOK_ID_CACHE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

    return data if isinstance(data, dict) else {}


def _save_book_id_cache(cache: Dict[str, Dict]) -> None:
    _BOOK_ID_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _BOOK_ID_CACHE_FILE.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _cache_book_mapping(book_name: str, book: Dict) -> None:
    book_id = book.get("id")
    if not book_id:
        return

    cache = _load_book_id_cache()
    payload = {"id": book_id, "name": book.get("name") or book_name}
    changed = False

    for candidate_name in (book_name, book.get("name") or ""):
        key = _lookup_key(candidate_name)
        if not key:
            continue
        if cache.get(key) == payload:
            continue
        cache[key] = payload
        changed = True

    if changed:
        _save_book_id_cache(cache)


def _book_from_id(session, book_id: int) -> Optional[Dict]:
    response = session.get(f"{API_BASE}/books/{book_id}", timeout=15)
    response.raise_for_status()
    data = (response.json() or {}).get("data") or {}
    return data or None


def _search_books(session, keyword: str) -> List[Dict]:
    keyword = re.sub(r"\s+", " ", keyword or "").strip()
    if not keyword:
        return []

    response = session.get(
        f"{API_BASE}/books/search",
        params={"keyword": keyword},
        timeout=20,
    )
    response.raise_for_status()
    return (response.json() or {}).get("data") or []


def _score_book_candidate(book_name: str, candidate: Dict) -> float:
    query_key = _lookup_key(book_name)
    title_key = _lookup_key(candidate.get("name", ""))
    if not query_key or not title_key:
        return 0.0

    score = difflib.SequenceMatcher(None, query_key, title_key).ratio()
    if query_key == title_key:
        score += 0.4
    elif query_key in title_key or title_key in query_key:
        score += 0.25

    return score


def _search_keywords(book_name: str) -> List[str]:
    normalized = re.sub(r"\s+", " ", book_name or "").strip()
    if not normalized:
        return []

    keywords = [normalized]
    for separator in ("(", "[", ":", " - ", " – ", " — "):
        if separator in normalized:
            head = normalized.split(separator, 1)[0].strip()
            if head:
                keywords.append(head)

    seen = set()
    ordered = []
    for keyword in keywords:
        folded = keyword.strip()
        if not folded or folded in seen:
            continue
        seen.add(folded)
        ordered.append(folded)
    return ordered


def _api_session():
    if not _HAS_API_DEPS:
        raise RuntimeError("Thiếu requests/pycryptodome/ftfy để tải nhanh qua API")

    session = requests.Session()
    retry = Retry(total=2, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update(_API_HEADERS)
    return session


def _resolve_book(session, book_name: str, book_id: Optional[int] = None) -> Optional[Dict]:
    if book_id:
        data = _book_from_id(session, book_id)
        if data:
            _cache_book_mapping(book_name, data)
            return data

    query_key = _lookup_key(book_name)

    cached = _load_book_id_cache().get(query_key)
    if cached and cached.get("id"):
        try:
            data = _book_from_id(session, int(cached["id"]))
            if data:
                _cache_book_mapping(book_name, data)
                return data
        except Exception:
            pass

    search_best = None
    search_best_score = 0.0
    seen_ids = set()
    for keyword in _search_keywords(book_name):
        try:
            candidates = _search_books(session, keyword)
        except Exception:
            continue

        for candidate in candidates:
            candidate_id = candidate.get("id")
            if candidate_id in seen_ids:
                continue
            seen_ids.add(candidate_id)

            score = _score_book_candidate(book_name, candidate)
            if score > search_best_score:
                search_best = candidate
                search_best_score = score

        if search_best_score >= 1.0:
            break

    if search_best and search_best_score >= 0.7:
        _cache_book_mapping(book_name, search_best)
        return search_best

    best = None
    best_score = 0.0

    for page in range(1, 8):
        response = session.get(
            f"{API_BASE}/books",
            params={"page": page, "limit": 100},
            timeout=20,
        )
        response.raise_for_status()
        candidates = (response.json() or {}).get("data") or []
        if not candidates:
            break

        for candidate in candidates:
            score = _score_book_candidate(book_name, candidate)
            if score > best_score:
                best = candidate
                best_score = score

        if best_score >= 1.10 or len(candidates) < 100:
            break

    if best and best_score >= 0.65:
        _cache_book_mapping(book_name, best)
        return best
    return None


def _fetch_chapter_list(session, book_id: int) -> List[Dict]:
    response = session.get(
        f"{API_BASE}/chapters",
        params={
            "filter[book_id]": book_id,
            "filter[type]": "published",
            "limit": 50000,
        },
        timeout=30,
    )
    response.raise_for_status()
    data = (response.json() or {}).get("data") or []
    return sorted(data, key=lambda item: item.get("index") or 0)


def _extract_between(data: bytes, start_marker: bytes, end_marker: bytes) -> Optional[bytes]:
    start = data.find(start_marker)
    if start < 0:
        return None
    start += len(start_marker)
    end = data.find(end_marker, start)
    if end < 0 or start >= end:
        return None
    return data[start:end]


def _decode_base64_loose(data: bytes) -> bytes:
    cleaned = bytes(ch for ch in data if ch in _BASE64_BYTES and ch != ord("="))
    if not cleaned:
        raise ValueError("base64 rỗng sau khi lọc")
    missing_padding = (-len(cleaned)) % 4
    if missing_padding:
        cleaned += b"=" * missing_padding
    return base64.b64decode(cleaned)


def _decrypt_content_blob(blob: str) -> str:
    if not blob:
        raise ValueError("content blob rỗng")

    raw = blob.encode("ascii")
    outer = _decode_base64_loose(raw)
    iv_bytes = _extract_between(outer, b'"iv":"', b'","value":"')
    value_bytes = _extract_between(outer, b'"value":"', b'","mac"')
    if not iv_bytes or not value_bytes:
        raise ValueError("Không tách được iv/value từ content blob")

    key = raw[17:33]
    if len(key) != 16:
        raise ValueError("Khóa AES không hợp lệ")

    iv = _decode_base64_loose(iv_bytes)[:16]
    payload = _decode_base64_loose(value_bytes)
    plain = AES.new(key, AES.MODE_CBC, iv).decrypt(payload)

    pad = plain[-1]
    if 1 <= pad <= 16 and plain.endswith(bytes([pad]) * pad):
        plain = plain[:-pad]

    return fix_text(plain.decode("latin1"))


def _cleanup_api_text(text: str, chapter_name: str = "") -> str:
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.strip() for line in text.split("\n")]

    non_empty = [(idx, line) for idx, line in enumerate(lines) if line]
    for pos, (idx, line) in enumerate(non_empty[:4]):
        if re.fullmatch(r"\d+\s*/\s*\d+", line):
            drop = {item_idx for item_idx, _ in non_empty[:pos + 1]}
            lines = [item for item_idx, item in enumerate(lines) if item_idx not in drop]
            break

    non_empty_lines = [line for line in lines if line]
    if non_empty_lines and chapter_name:
        first_line = non_empty_lines[0]
        similarity = difflib.SequenceMatcher(None, _lookup_key(first_line), _lookup_key(chapter_name)).ratio()
        looks_garbled = bool(re.search(r"[^\w\sÀ-ỹ.,:;!?()'\"“”/\-]", first_line))
        if len(first_line) < 120 and (similarity >= 0.25 or (looks_garbled and first_line.casefold().startswith("ch"))):
            removed = False
            new_lines: List[str] = []
            for line in lines:
                if line and not removed:
                    removed = True
                    continue
                new_lines.append(line)
            lines = new_lines

    cleaned: List[str] = []
    blank = False
    for line in lines:
        if not line:
            if cleaned and not blank:
                cleaned.append("")
            blank = True
            continue
        cleaned.append(line)
        blank = False

    return "\n".join(cleaned).strip()


def _fetch_api_chapter_text(session, chapter: Dict, max_attempts: int = 3) -> Tuple[str, str]:
    chapter_index = chapter.get("index") or 0
    chapter_id = chapter.get("id")
    fallback_name = chapter.get("name") or f"Chương {chapter_index}"
    last_error: Optional[Exception] = None

    for attempt in range(1, max_attempts + 1):
        try:
            response = session.get(f"{API_BASE}/chapters/{chapter_id}", timeout=30)
            response.raise_for_status()
            detail = (response.json() or {}).get("data") or {}
            chapter_name = detail.get("name") or fallback_name
            content = _cleanup_api_text(_decrypt_content_blob(detail.get("content") or ""), chapter_name)
            if len(content) < 50:
                raise ValueError("Nội dung sau giải mã quá ngắn")
            return chapter_name, content
        except Exception as exc:
            last_error = exc
            if attempt < max_attempts:
                time.sleep(0.3 * attempt)

    assert last_error is not None
    raise last_error


def download_via_api(
    book_name: str,
    ch_start: int = 1,
    ch_end: Optional[int] = None,
    output_dir: Path = OUTPUT_DIR,
    log_fn: Callable[[str], None] = print,
    stop_flag: Callable[[], bool] = lambda: False,
    progress_cb: Optional[Callable[[int, int], None]] = None,
    book_id: Optional[int] = None,
) -> Dict:
    session = _api_session()
    book = _resolve_book(session, book_name, book_id)
    if not book:
        return {"success": False, "ok": 0, "fail": 0, "reason": "Không tìm thấy truyện qua API"}

    api_book_id = book.get("id")
    api_book_name = book.get("name") or book_name
    chapters = _fetch_chapter_list(session, api_book_id)
    if not chapters:
        return {"success": False, "ok": 0, "fail": 0, "reason": "Không lấy được danh sách chương qua API"}

    if ch_end is None:
        ch_end = max((item.get("index") or 0) for item in chapters)

    targets = [item for item in chapters if ch_start <= (item.get("index") or 0) <= ch_end]
    if not targets:
        return {"success": False, "ok": 0, "fail": 0, "reason": "Khoảng chương không hợp lệ"}

    book_dir = output_dir / safe_name(api_book_name)
    book_dir.mkdir(parents=True, exist_ok=True)
    removed_full = _delete_book_full_files(book_dir, log_fn=lambda *_: None)
    if removed_full:
        log_fn(f"Đã xóa {removed_full} file _FULL cũ trong {book_dir.name}")

    total = len(targets)
    ok_count = 0
    fail_count = 0
    failed_targets: List[Dict] = []
    log_fn(f"Fast API: {api_book_name} ({total} chương)")

    for done, chapter in enumerate(targets):
        if stop_flag():
            log_fn("Đã dừng.")
            break

        if progress_cb:
            progress_cb(done, total)

        chapter_index = chapter.get("index") or 0
        existing_file = _find_existing_chapter_file(book_dir, chapter_index)
        legacy_existing = bool(existing_file and _is_legacy_chapter_file(existing_file, chapter_index))
        if existing_file and _existing_chapter_looks_ok(existing_file) and not legacy_existing:
            log_fn(f"  [ch{chapter_index}] Đã có, bỏ qua")
            ok_count += 1
            continue

        try:
            chapter_title, content = _fetch_api_chapter_text(session, chapter)
            chapter_file = book_dir / f"{chapter_index:06d}_{safe_name(chapter_title)}.txt"
            chapter_file.write_text(
                f"{'='*60}\n{chapter_title}\n{'='*60}\n\n{content}\n",
                encoding="utf-8",
            )
            if legacy_existing and existing_file and existing_file != chapter_file and existing_file.exists():
                existing_file.unlink()
            log_fn(f"  [ch{chapter_index}] ⚡ API {chapter_file.name} ({len(content)} ký tự)")
            ok_count += 1
        except Exception as exc:
            log_fn(f"  [ch{chapter_index}] ⚠ API lỗi: {exc}")
            fail_count += 1
            failed_targets.append(chapter)

    if failed_targets and not stop_flag():
        log_fn(f"Retry-pass API cho {len(failed_targets)} chương lỗi tạm thời...")
        retry_targets = failed_targets
        failed_targets = []
        fail_count = 0
        for chapter in retry_targets:
            chapter_index = chapter.get("index") or 0
            try:
                chapter_title, content = _fetch_api_chapter_text(session, chapter)
                chapter_file = book_dir / f"{chapter_index:06d}_{safe_name(chapter_title)}.txt"
                chapter_file.write_text(
                    f"{'='*60}\n{chapter_title}\n{'='*60}\n\n{content}\n",
                    encoding="utf-8",
                )
                log_fn(f"  [ch{chapter_index}] ✔ API retry ({len(content)} ký tự)")
                ok_count += 1
            except Exception as exc:
                log_fn(f"  [ch{chapter_index}] ✖ API retry lỗi: {exc}")
                fail_count += 1
                failed_targets.append(chapter)

    if progress_cb:
        progress_cb(total, total)

    success = ok_count > 0 and fail_count == 0
    reason = "" if success else (
        f"API tải được {ok_count} chương, lỗi {fail_count} chương" if ok_count > 0 else "API không tải được chương nào"
    )
    log_fn(f"\nXong API! ✔{ok_count}  ✖{fail_count}  →  {book_dir}")
    return {
        "success": success,
        "ok": ok_count,
        "fail": fail_count,
        "output": str(book_dir),
        "book_id": api_book_id,
        "book_name": api_book_name,
        "reason": reason,
    }


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
    api_result = None
    try:
        api_result = download_via_api(
            book_name=book_name,
            ch_start=ch_start,
            ch_end=ch_end,
            output_dir=output_dir,
            log_fn=log_fn,
            stop_flag=stop_flag,
            progress_cb=progress_cb,
        )
        if api_result.get("success"):
            return api_result
        log_fn(f"API chưa hoàn tất: {api_result.get('reason', 'không rõ lỗi')}")
    except Exception as exc:
        log_fn(f"API lỗi, sẽ fallback ADB: {exc}")

    if not adb or not adb.device:
        return api_result or {"success": False, "reason": "Không có ADB để fallback và API không tải được"}

    log_fn("Fallback sang ADB để vá các chương còn thiếu...")
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
        in_reader = False
        last_read_ch = None  # Track last chapter read for turbo gap detection

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

            payload = None

            # Turbo path: consecutive chapter while already in reader
            if in_reader and last_read_ch is not None and ch_idx == last_read_ch + 1:
                log_fn(f"  [ch{ch_idx}] Turbo...")
                payload = adb.turbo_advance_and_read(log_fn)
                if payload:
                    log_fn(f"  Turbo ✔ {payload.get('title', '')}")
                else:
                    log_fn(f"  [ch{ch_idx}] Turbo fail, fallback nav...")
                    if not adb.nav_to_chapter(ch_idx, log_fn):
                        log_fn(f"  [ch{ch_idx}] ⚠ Không tìm thấy chương")
                        n_fail += 1
                        in_reader = False
                        if n_fail >= 5:
                            log_fn("Quá nhiều lỗi điều hướng. Dừng.")
                            break
                        continue
                    payload = adb.read_current_chapter_payload(log_fn)
            else:
                # First chapter or gap – use full navigation
                log_fn(f"  [ch{ch_idx}] Điều hướng tới chương {ch_idx}...")
                if not adb.nav_to_chapter(ch_idx, log_fn):
                    log_fn(f"  [ch{ch_idx}] ⚠ Không tìm thấy chương")
                    n_fail += 1
                    if n_fail >= 5:
                        log_fn("Quá nhiều lỗi điều hướng. Dừng.")
                        break
                    continue
                in_reader = True
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
                last_read_ch = ch_idx

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
