"""pipeline.py – Download orchestrator via API or ADB/BlueStacks."""
import base64
import difflib
import re
import string
import time
from pathlib import Path
from typing import Optional, Dict, Callable, List

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

from .config import OUTPUT_DIR, API_BASE, USER_AGENT, log
from .adb import AdbController
from .utils import safe_name, merge_to_single_file


_API_HEADERS = {
    "content-type": "application/json",
    "Accept": "application/json",
    "User-Agent": USER_AGENT,
    "x-app": "app.android",
}
_BASE64_BYTES = set((string.ascii_letters + string.digits + "+/=").encode())


def _lookup_key(text: str) -> str:
    return "".join(ch for ch in (text or "").casefold() if ch.isalnum())


def _api_session():
    if not _HAS_API_DEPS:
        raise RuntimeError("Thiếu requests/pycryptodome/ftfy để tải trực tiếp qua API")

    sess = requests.Session()
    retry = Retry(total=2, backoff_factor=1,
                  status_forcelist=[429, 500, 502, 503, 504])
    sess.mount("https://", HTTPAdapter(max_retries=retry))
    sess.headers.update(_API_HEADERS)
    return sess


def _resolve_book(sess, book_name: str, book_id: Optional[int] = None) -> Optional[Dict]:
    if book_id:
        resp = sess.get(f"{API_BASE}/books/{book_id}", timeout=15)
        resp.raise_for_status()
        data = (resp.json() or {}).get("data") or {}
        if data:
            return data

    resp = sess.get(
        f"{API_BASE}/books",
        params={"per_page": 10, "page": 1, "search": book_name},
        timeout=15,
    )
    resp.raise_for_status()
    candidates = (resp.json() or {}).get("data") or []
    if not candidates:
        return None

    lookup_key = _lookup_key(book_name)
    best = None
    best_score = 0.0
    for candidate in candidates:
        candidate_key = _lookup_key(candidate.get("name", ""))
        score = difflib.SequenceMatcher(None, lookup_key, candidate_key).ratio()
        if lookup_key and lookup_key == candidate_key:
            score += 0.25
        if score > best_score:
            best = candidate
            best_score = score

    return best if best_score >= 0.65 else None


def _fetch_chapter_list(sess, book_id: int) -> List[Dict]:
    resp = sess.get(
        f"{API_BASE}/chapters",
        params={
            "filter[book_id]": book_id,
            "filter[type]": "published",
            "limit": 50000,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = (resp.json() or {}).get("data") or []
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


class LockedChapterPreviewError(PermissionError):
    pass


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

    text = plain.decode("latin1")
    return fix_text(text)


def _cleanup_api_text(text: str, chapter_name: str = "") -> str:
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.strip() for line in text.split("\n")]

    non_empty = [(idx, line) for idx, line in enumerate(lines) if line]
    for pos, (idx, line) in enumerate(non_empty[:4]):
        if re.fullmatch(r"\d+\s*/\s*\d+", line):
            drop = {item_idx for item_idx, _ in non_empty[:pos + 1]}
            lines = [item for item_idx, item in enumerate(lines) if item_idx not in drop]
            break

    non_empty = [line for line in lines if line]
    if non_empty:
        first_line = non_empty[0]
        similarity = difflib.SequenceMatcher(
            None,
            _lookup_key(first_line),
            _lookup_key(chapter_name),
        ).ratio() if chapter_name else 0.0
        looks_garbled = bool(re.search(r"[^\w\sÀ-ỹ.,:;!?()'\"“”‘’/\-]", first_line))
        looks_like_bad_title = chapter_name and len(first_line) < 120 and (
            similarity >= 0.25 or
            (looks_garbled and first_line.casefold().startswith("ch"))
        )
        if looks_like_bad_title:
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


def _fetch_api_chapter_text(sess, chapter: Dict, max_attempts: int = 3) -> tuple[str, str]:
    ch_idx = chapter.get("index") or 0
    ch_id = chapter.get("id")
    fallback_name = chapter.get("name") or f"Chương {ch_idx}"
    last_error: Optional[Exception] = None

    for attempt in range(1, max_attempts + 1):
        try:
            resp = sess.get(f"{API_BASE}/chapters/{ch_id}", timeout=30)
            resp.raise_for_status()
            detail = (resp.json() or {}).get("data") or {}
            if detail.get("is_locked"):
                raise LockedChapterPreviewError(
                    f"Chương bị khóa, API chỉ trả preview (giá {detail.get('unlock_price') or 0})"
                )
            chapter_name = detail.get("name") or fallback_name
            content = _decrypt_content_blob(detail.get("content") or "")
            content = _cleanup_api_text(content, chapter_name)
            if len(content) < 50:
                raise ValueError("Nội dung sau giải mã quá ngắn")
            return chapter_name, content
        except LockedChapterPreviewError:
            raise
        except Exception as exc:
            last_error = exc
            if attempt < max_attempts:
                time.sleep(0.4 * attempt)

    assert last_error is not None
    raise last_error


def download_via_api(
    book_name:   str,
    ch_start:    int = 1,
    ch_end:      Optional[int] = None,
    output_dir:  Path = OUTPUT_DIR,
    log_fn:      Callable[[str], None] = print,
    stop_flag:   Callable[[], bool] = lambda: False,
    progress_cb: Optional[Callable[[int, int], None]] = None,
    book_id:     Optional[int] = None,
) -> Dict:
    sess = _api_session()
    book = _resolve_book(sess, book_name, book_id)
    if not book:
        return {"success": False, "reason": "Không tìm thấy truyện qua API"}

    api_book_id = book.get("id")
    api_book_name = book.get("name") or book_name
    chapters = _fetch_chapter_list(sess, api_book_id)
    if not chapters:
        return {"success": False, "reason": "Không lấy được danh sách chương qua API"}

    if ch_end is None:
        ch_end = max((item.get("index") or 0) for item in chapters)

    targets = [item for item in chapters if ch_start <= (item.get("index") or 0) <= ch_end]
    if not targets:
        return {"success": False, "reason": "Khoảng chương không hợp lệ"}

    book_dir = output_dir / safe_name(api_book_name)
    book_dir.mkdir(parents=True, exist_ok=True)

    total = len(targets)
    completed_indices = set()
    locked_indices: List[int] = []
    failed_chapters: List[Dict] = []
    log_fn(f"Tải trực tiếp qua API: {api_book_name} ({total} chương)")

    for done, chapter in enumerate(targets):
        if stop_flag():
            log_fn("Đã dừng.")
            break

        if progress_cb:
            progress_cb(done, total)

        ch_idx = chapter.get("index") or 0
        ch_file = book_dir / f"{ch_idx:06d}_Chuong_{ch_idx}.txt"
        if _existing_chapter_looks_ok(ch_file):
            log_fn(f"  [ch{ch_idx}] Đã có, bỏ qua")
            completed_indices.add(ch_idx)
            continue

        try:
            chapter_name, content = _fetch_api_chapter_text(sess, chapter)

            ch_file.write_text(
                f"{'='*60}\n{chapter_name}\n{'='*60}\n\n{content}\n",
                encoding="utf-8",
            )
            log_fn(f"  [ch{ch_idx}] ✔ API ({len(content)} ký tự)")
            completed_indices.add(ch_idx)
        except LockedChapterPreviewError as exc:
            if ch_file.exists() and not _existing_chapter_looks_ok(ch_file):
                ch_file.unlink(missing_ok=True)
            log_fn(f"  [ch{ch_idx}] 🔒 {exc}")
            locked_indices.append(ch_idx)
        except Exception as exc:
            log_fn(f"  [ch{ch_idx}] ⚠ API lỗi: {exc}")
            failed_chapters.append(chapter)

    retry_round = 0
    while failed_chapters and retry_round < 2 and not stop_flag():
        retry_round += 1
        pending = failed_chapters
        failed_chapters = []
        log_fn(f"\nRetry API lượt {retry_round}: {len(pending)} chương")
        for chapter in pending:
            ch_idx = chapter.get("index") or 0
            ch_file = book_dir / f"{ch_idx:06d}_Chuong_{ch_idx}.txt"
            if _existing_chapter_looks_ok(ch_file):
                completed_indices.add(ch_idx)
                continue
            try:
                chapter_name, content = _fetch_api_chapter_text(sess, chapter, max_attempts=5)
                ch_file.write_text(
                    f"{'='*60}\n{chapter_name}\n{'='*60}\n\n{content}\n",
                    encoding="utf-8",
                )
                log_fn(f"  [ch{ch_idx}] ✔ API retry ({len(content)} ký tự)")
                completed_indices.add(ch_idx)
            except LockedChapterPreviewError as exc:
                if ch_file.exists() and not _existing_chapter_looks_ok(ch_file):
                    ch_file.unlink(missing_ok=True)
                log_fn(f"  [ch{ch_idx}] 🔒 {exc}")
                locked_indices.append(ch_idx)
            except Exception as exc:
                log_fn(f"  [ch{ch_idx}] ⚠ API vẫn lỗi: {exc}")
                failed_chapters.append(chapter)

    n_ok = len(completed_indices)
    failed_indices = sorted((chapter.get("index") or 0) for chapter in failed_chapters)
    n_fail = len(failed_indices) + len(locked_indices)
    if n_fail == 0:
        merge_to_single_file(book_dir, api_book_name)
    if progress_cb:
        progress_cb(total, total)
    log_fn(f"\nXong API! ✔{n_ok}  ✖{n_fail}  →  {book_dir}")
    return {
        "success": n_fail == 0 and n_ok > 0,
        "ok": n_ok,
        "fail": n_fail,
        "output": str(book_dir),
        "book_id": api_book_id,
        "book_name": api_book_name,
        "locked_chapters": sorted(set(locked_indices)),
        "failed_chapter_indices": failed_indices,
        "reason": (
            f"{len(locked_indices)} chương bị khóa, API chỉ có preview"
            if locked_indices else
            (f"Còn {len(failed_indices)} chương lỗi API" if failed_indices else "")
        ),
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
    book_id:     Optional[int] = None,
) -> Dict:
    try:
        result = download_via_api(
            book_name=book_name,
            ch_start=ch_start,
            ch_end=ch_end,
            output_dir=output_dir,
            log_fn=log_fn,
            stop_flag=stop_flag,
            progress_cb=progress_cb,
            book_id=book_id,
        )
        if result.get("success"):
            return result
        log_fn(f"API không dùng được: {result.get('reason', 'không rõ lỗi')}")
    except Exception as exc:
        log_fn(f"API lỗi, chuyển sang ADB: {exc}")

    if not adb or not adb.device:
        api_reason = result.get("reason") if 'result' in locals() and isinstance(result, dict) else None
        if api_reason:
            return {"success": False, "reason": f"{api_reason}. Không có ADB để fallback"}
        return {"success": False, "reason": "Không có ADB để fallback và API không tải được"}

    pending_indices = sorted(set(
        (result.get("locked_chapters") or []) +
        (result.get("failed_chapter_indices") or [])
    )) if 'result' in locals() and isinstance(result, dict) else []
    fallback_start = pending_indices[0] if pending_indices else ch_start
    if pending_indices:
        log_fn(f"Fallback sang ADB từ chương {fallback_start}...")
    else:
        log_fn("Fallback sang ADB...")
    return download_via_adb(
        adb=adb,
        book_name=book_name,
        ch_start=fallback_start,
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
        if _existing_chapter_looks_ok(ch_file):
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
