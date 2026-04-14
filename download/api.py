"""api.py – MTC/NovelFever API client (pure HTTP, no ADB)."""
import base64
import difflib
import json
import re
import string
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from Crypto.Cipher import AES
from ftfy import fix_text

from .config import API_BASE, USER_AGENT, TOKEN_FILE, OUTPUT_DIR

# ── Headers & Auth ──────────────────────────────────────────────────────────
_HEADERS = {
    "content-type": "application/json",
    "Accept": "application/json",
    "User-Agent": USER_AGENT,
    "x-app": "app.android",
}

if TOKEN_FILE.exists():
    _token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    if _token:
        _HEADERS["Authorization"] = f"Bearer {_token}"
        _HEADERS["Token"] = _token

# ── Internals ───────────────────────────────────────────────────────────────
_BASE64_CHARS = set((string.ascii_letters + string.digits + "+/=").encode())
_BOOK_CACHE_FILE = OUTPUT_DIR / ".book_id_cache.json"


def _key(text: str) -> str:
    """Normalize text to alphanumeric lowercase for matching."""
    return "".join(ch for ch in (text or "").casefold() if ch.isalnum())


# ── Session ─────────────────────────────────────────────────────────────────
def create_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=2, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update(_HEADERS)
    return session


# ── Book cache ──────────────────────────────────────────────────────────────
def _load_cache() -> Dict[str, Dict]:
    if not _BOOK_CACHE_FILE.exists():
        return {}
    try:
        data = json.loads(_BOOK_CACHE_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_cache(cache: Dict[str, Dict]) -> None:
    _BOOK_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _BOOK_CACHE_FILE.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def cache_book(book_name: str, book: Dict) -> None:
    book_id = book.get("id")
    if not book_id:
        return
    cache = _load_cache()
    payload = {"id": book_id, "name": book.get("name") or book_name}
    changed = False
    for name in (book_name, book.get("name") or ""):
        k = _key(name)
        if not k:
            continue
        if cache.get(k) == payload:
            continue
        cache[k] = payload
        changed = True
    if changed:
        _save_cache(cache)


# ── Book resolution ─────────────────────────────────────────────────────────
def get_book(session: requests.Session, book_id: int) -> Optional[Dict]:
    resp = session.get(f"{API_BASE}/books/{book_id}", timeout=15)
    resp.raise_for_status()
    return (resp.json() or {}).get("data") or None


def search_books(session: requests.Session, keyword: str) -> List[Dict]:
    keyword = re.sub(r"\s+", " ", keyword or "").strip()
    if not keyword:
        return []
    resp = session.get(f"{API_BASE}/books/search", params={"keyword": keyword}, timeout=20)
    resp.raise_for_status()
    return (resp.json() or {}).get("data") or []


def _score_candidate(book_name: str, candidate: Dict) -> float:
    q = _key(book_name)
    t = _key(candidate.get("name", ""))
    if not q or not t:
        return 0.0
    score = difflib.SequenceMatcher(None, q, t).ratio()
    if q == t:
        score += 0.4
    elif q in t or t in q:
        score += 0.25
    return score


def _search_keywords(book_name: str) -> List[str]:
    normalized = re.sub(r"\s+", " ", book_name or "").strip()
    if not normalized:
        return []
    keywords = [normalized]
    for sep in ("(", "[", ":", " - ", " – ", " — "):
        if sep in normalized:
            head = normalized.split(sep, 1)[0].strip()
            if head:
                keywords.append(head)
    seen = set()
    ordered = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            ordered.append(kw)
    return ordered


def resolve_book(
    session: requests.Session, book_name: str, book_id: Optional[int] = None
) -> Optional[Dict]:
    """Find a book by ID, cache, search, or catalog scan."""
    if book_id:
        data = get_book(session, book_id)
        if data:
            cache_book(book_name, data)
            return data

    # Check cache
    cached = _load_cache().get(_key(book_name))
    if cached and cached.get("id"):
        try:
            data = get_book(session, int(cached["id"]))
            if data:
                cache_book(book_name, data)
                return data
        except Exception:
            pass

    # Search by keyword
    best, best_score = None, 0.0
    seen_ids = set()
    for kw in _search_keywords(book_name):
        try:
            for c in search_books(session, kw):
                cid = c.get("id")
                if cid in seen_ids:
                    continue
                seen_ids.add(cid)
                s = _score_candidate(book_name, c)
                if s > best_score:
                    best, best_score = c, s
        except Exception:
            continue
        if best_score >= 1.0:
            break

    if best and best_score >= 0.7:
        cache_book(book_name, best)
        return best

    # Fallback: paginate catalog
    fb, fb_score = None, 0.0
    for page in range(1, 8):
        resp = session.get(f"{API_BASE}/books", params={"page": page, "limit": 100}, timeout=20)
        resp.raise_for_status()
        candidates = (resp.json() or {}).get("data") or []
        if not candidates:
            break
        for c in candidates:
            s = _score_candidate(book_name, c)
            if s > fb_score:
                fb, fb_score = c, s
        if fb_score >= 1.10 or len(candidates) < 100:
            break

    if fb and fb_score >= 0.65:
        cache_book(book_name, fb)
        return fb
    return None


# ── Chapter list ────────────────────────────────────────────────────────────
def fetch_chapters(session: requests.Session, book_id: int) -> List[Dict]:
    resp = session.get(
        f"{API_BASE}/chapters",
        params={"filter[book_id]": book_id, "filter[type]": "published", "limit": 50000},
        timeout=30,
    )
    resp.raise_for_status()
    data = (resp.json() or {}).get("data") or []
    return sorted(data, key=lambda c: c.get("index") or 0)


# ── Decrypt ─────────────────────────────────────────────────────────────────
def _b64_between(data: bytes, start: bytes, end: bytes) -> Optional[bytes]:
    s = data.find(start)
    if s < 0:
        return None
    s += len(start)
    e = data.find(end, s)
    if e < 0 or s >= e:
        return None
    return data[s:e]


def _b64_decode(data: bytes) -> bytes:
    cleaned = bytes(ch for ch in data if ch in _BASE64_CHARS and ch != ord("="))
    if not cleaned:
        raise ValueError("base64 rỗng sau khi lọc")
    pad = (-len(cleaned)) % 4
    if pad:
        cleaned += b"=" * pad
    return base64.b64decode(cleaned)


def decrypt_content(blob: str) -> str:
    """Decrypt AES/CBC/PKCS5 encrypted chapter content."""
    if not blob:
        raise ValueError("content blob rỗng")
    raw = blob.encode("ascii")
    outer = _b64_decode(raw)
    iv_bytes = _b64_between(outer, b'"iv":"', b'","value":"')
    value_bytes = _b64_between(outer, b'"value":"', b'","mac"')
    if not iv_bytes or not value_bytes:
        raise ValueError("Không tách được iv/value từ content blob")
    key = raw[17:33]
    if len(key) != 16:
        raise ValueError("Khóa AES không hợp lệ")
    iv = _b64_decode(iv_bytes)[:16]
    payload = _b64_decode(value_bytes)
    plain = AES.new(key, AES.MODE_CBC, iv).decrypt(payload)
    pad = plain[-1]
    if 1 <= pad <= 16 and plain.endswith(bytes([pad]) * pad):
        plain = plain[:-pad]
    return fix_text(plain.decode("latin1"))


# ── Chapter text fetch ──────────────────────────────────────────────────────
def _clean_text(text: str, chapter_name: str = "") -> str:
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.strip() for line in text.split("\n")]

    # Remove leading page-number lines (e.g. "1 / 5")
    non_empty = [(i, l) for i, l in enumerate(lines) if l]
    for pos, (idx, line) in enumerate(non_empty[:4]):
        if re.fullmatch(r"\d+\s*/\s*\d+", line):
            drop = {j for j, _ in non_empty[: pos + 1]}
            lines = [l for i, l in enumerate(lines) if i not in drop]
            break

    # Remove duplicate chapter title from body
    non_empty_lines = [l for l in lines if l]
    if non_empty_lines and chapter_name:
        first = non_empty_lines[0]
        sim = difflib.SequenceMatcher(None, _key(first), _key(chapter_name)).ratio()
        garbled = bool(re.search(r"[^\w\sÀ-ỹ.,:;!?()'\"""/\\-]", first))
        if len(first) < 120 and (sim >= 0.25 or (garbled and first.casefold().startswith("ch"))):
            removed = False
            new_lines = []
            for l in lines:
                if l and not removed:
                    removed = True
                    continue
                new_lines.append(l)
            lines = new_lines

    # Collapse multiple blank lines
    cleaned = []
    blank = False
    for l in lines:
        if not l:
            if cleaned and not blank:
                cleaned.append("")
            blank = True
        else:
            cleaned.append(l)
            blank = False
    return "\n".join(cleaned).strip()


def fetch_chapter_text(
    session: requests.Session, chapter: Dict, max_attempts: int = 3
) -> Tuple[str, str]:
    """Fetch and decrypt a single chapter. Returns (title, content)."""
    ch_idx = chapter.get("index") or 0
    ch_id = chapter.get("id")
    fallback = chapter.get("name") or f"Chương {ch_idx}"
    last_err: Optional[Exception] = None

    for attempt in range(1, max_attempts + 1):
        try:
            resp = session.get(f"{API_BASE}/chapters/{ch_id}", timeout=30)
            resp.raise_for_status()
            detail = (resp.json() or {}).get("data") or {}
            title = detail.get("name") or fallback
            content = _clean_text(decrypt_content(detail.get("content") or ""), title)
            if len(content) < 50:
                raise ValueError("Nội dung sau giải mã quá ngắn")
            return title, content
        except Exception as exc:
            last_err = exc
            if "401" in str(exc) or "403" in str(exc):
                raise ValueError(
                    "Bị giới hạn bản quyền/VIP. Cung cấp token vào file token.txt"
                ) from exc
            if attempt < max_attempts:
                time.sleep(0.3 * attempt)

    assert last_err is not None
    raise last_err


# ── Catalog ─────────────────────────────────────────────────────────────────
def fetch_full_catalog(session: requests.Session) -> List[Dict]:
    """Fetch all books from the API (paginated)."""
    all_books = []
    for page in range(1, 200):
        resp = session.get(
            f"{API_BASE}/books", params={"page": page, "limit": 100}, timeout=20
        )
        resp.raise_for_status()
        books = (resp.json() or {}).get("data") or []
        if not books:
            break
        all_books.extend(books)
        if len(books) < 100:
            break
    return all_books
