#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTC Novel Downloader v2.0
Tool tai truyen tu android.lonoapp.net (Love Novel / MTC app)

Tinh nang:
- Tim kiem truyen theo ten, ID, slug
- Tai chuong co Resume support  
- Decrypt noi dung khi co APP_KEY
- Luu file TXT (tung chuong va file gop)
- Khong tai trung chuong
- Xu ly ky tu dung
"""
import sys
import io

# Fix Windows console encoding  
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import os
import re
import json
import time
import base64
import unicodedata
import argparse
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ─── Constants ───────────────────────────────────────────────────────────────
VERSION = "2.0.0"
BASE_URL   = "https://android.lonoapp.net"
API_URL    = f"{BASE_URL}/api"
USER_AGENT = "Dart/3.0 (dart:io)"
OUTPUT_DIR = Path("downloads")
DELAY      = 0.5
MAX_RETRY  = 3
TIMEOUT    = 30

# Vietnamese chars for plain-text detection
VIET_CHARS = set(
    "àáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ"
    "ÀÁẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬĐÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴ"
)

# ─── Logging ─────────────────────────────────────────────────────────────────
def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    fmt   = "%(asctime)s [%(levelname)s] %(message)s"
    logging.basicConfig(level=level, format=fmt, datefmt="%H:%M:%S",
                        handlers=[logging.StreamHandler(sys.stdout)])

log = logging.getLogger("mtc")

# ─── Decryption ──────────────────────────────────────────────────────────────
_decrypt_available = False
try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    _decrypt_available = True
except ImportError:
    pass

def decrypt_content(content_b64: str, app_key: str) -> Optional[str]:
    """
    Decrypt Laravel-encrypted chapter content.
    Format: base64(json({"iv": base64_iv, "value": base64_cipher}))
    Uses AES-256-CBC with the provided APP_KEY (base64-encoded 32-byte key).
    """
    if not _decrypt_available:
        log.warning("pycryptodome not installed. Run: pip install pycryptodome")
        return None
    
    if not app_key:
        return None
    
    try:
        # Decode the APP_KEY (Laravel format: "base64:xxxxx" or raw base64)
        key_b64 = app_key.replace("base64:", "")
        key_bytes = base64.b64decode(key_b64 + "==")
        if len(key_bytes) not in (16, 24, 32):
            log.error(f"Invalid key length: {len(key_bytes)} bytes (expected 16/24/32)")
            return None
    except Exception as e:
        log.error(f"Invalid APP_KEY format: {e}")
        return None
    
    try:
        # Decode outer base64
        outer_bytes = base64.b64decode(content_b64 + "==")
        
        # Extract iv and value from JSON
        m = re.search(rb'"iv"\s*:\s*"([^"]+)"', outer_bytes)
        v = re.search(rb'"value"\s*:\s*"([^"]+)"', outer_bytes)
        
        if not m or not v:
            log.debug("Cannot find iv/value in content JSON")
            return None
        
        iv_raw  = m.group(1)
        val_raw = v.group(2) if len(v.groups()) > 1 else v.group(1)
        
        # Decode IV (may have binary contamination - extract clean base64 portion)
        # Strategy: find continuous base64 chars at end
        iv_clean = re.sub(rb'[^A-Za-z0-9+/=]', b'A', iv_raw)  # replace binary with 'A'
        try:
            iv = base64.b64decode(iv_clean + b"==")
            if len(iv) != 16:
                # Try raw bytes as IV
                iv = bytes(b & 0xFF for b in iv_raw[:16])
        except Exception:
            iv = bytes(b & 0xFF for b in iv_raw[:16])
        
        # Decode ciphertext
        ciphertext = base64.b64decode(val_raw + b"==")
        
        # Decrypt AES-256-CBC
        cipher = AES.new(key_bytes[:32], AES.MODE_CBC, iv[:16])
        decrypted = unpad(cipher.decrypt(ciphertext), 16)
        
        # Decode as UTF-8
        text = decrypted.decode("utf-8")
        return text
        
    except Exception as e:
        log.debug(f"Decryption failed: {e}")
        return None

# ─── Content Processing ───────────────────────────────────────────────────────
def is_encrypted(content: str) -> bool:
    """Check if content looks encrypted (base64) vs plain text."""
    if not content or len(content) < 20:
        return False
    # Plain text has many Vietnamese chars
    viet_count = sum(1 for c in content[:300] if c in VIET_CHARS)
    if viet_count > 5:
        return False
    # Encrypted looks like base64: mostly alphanumeric + /+=
    b64_chars = sum(1 for c in content[:200] if c in 
                    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/= \n")
    return len(content) > 100 and (b64_chars / min(200, len(content))) > 0.85

def extract_text_from_html(html: str) -> str:
    """Strip HTML tags and return clean text."""
    # Replace block tags with newlines
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"</?(p|div|section|article|h[1-6])[^>]*>", "\n", text, flags=re.IGNORECASE)
    # Remove all remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    # Decode HTML entities
    entities = {"&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"',
                 "&#39;": "'", "&nbsp;": " ", "&apos;": "'"}
    for ent, char in entities.items():
        text = text.replace(ent, char)
    # Clean up whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]*", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def process_content(raw_content: str, app_key: Optional[str] = None) -> Optional[str]:
    """
    Process raw chapter content from API.
    Returns: plain text string or None if encrypted and no key.
    """
    if not raw_content:
        return None
    
    # Check if already plain text
    if not is_encrypted(raw_content):
        # Could be HTML or plain text
        if "<" in raw_content and ">" in raw_content:
            return extract_text_from_html(raw_content)
        return raw_content
    
    # Content is encrypted - try to decrypt
    if app_key:
        text = decrypt_content(raw_content, app_key)
        if text:
            # Decrypted text may be HTML
            if "<" in text and ">" in text:
                return extract_text_from_html(text)
            return text
    
    return None  # Cannot decrypt without key

# ─── HTTP Session ─────────────────────────────────────────────────────────────
def make_session(token: Optional[str] = None) -> requests.Session:
    s = requests.Session()
    retry = Retry(total=MAX_RETRY, backoff_factor=1.5,
                  status_forcelist=[429, 500, 502, 503, 504])
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Content-Type": "application/json",
    })
    if token:
        s.headers["Authorization"] = f"Bearer {token}"
    return s

# ─── Auth ─────────────────────────────────────────────────────────────────────
def login(email: str, password: str) -> Optional[Dict]:
    """
    Login to MTC API (android.lonoapp.net) with MTC app credentials.
    Returns dict with: token, key (if found), raw_data (full response for key scanning).
    """
    s = make_session()
    try:
        resp = s.post(f"{API_URL}/auth/login", json={
            "email":       email,
            "password":    password,
            "device_name": "Android_Phone",  # mimic app
        }, timeout=TIMEOUT)
        data = resp.json()
        if data.get("success") and data.get("data"):
            d = data["data"]
            result: Dict = {
                "token":    None,
                "key":      None,
                "raw_data": d,  # full payload for key scanning in GUI
            }
            # Token
            result["token"] = (d.get("token") or d.get("access_token")
                                or d.get("api_token"))
            # Explicit key fields
            result["key"] = (d.get("key") or d.get("app_key")
                             or d.get("decrypt_key") or d.get("cipher_key"))
            # Auto-scan ALL string fields for base64 AES key (16/24/32 bytes)
            if not result["key"]:
                for k, v in d.items():
                    if isinstance(v, str) and len(v) > 20:
                        try:
                            raw = base64.b64decode(
                                v.replace("base64:", "") + "==")
                            if len(raw) in (16, 24, 32):
                                result["key"] = v
                                log.info(f"Auto-detected key in field '{k}'")
                                break
                        except Exception:
                            pass
            log.info(f"Login OK  |  token={'yes' if result['token'] else 'no'}"
                     f"  key={'yes' if result['key'] else 'no'}"
                     f"  raw_fields={list(d.keys())}")
            return result
        else:
            log.warning(f"Login failed: {data.get('message', 'Unknown error')}")
            log.debug(f"Full response: {data}")
    except Exception as e:
        log.error(f"Login error: {e}")
    return None


def probe_chapter_content(session: requests.Session, chapter_id: int) -> Dict:
    """
    Probe a single chapter to detect content type after login.
    Returns: {'encrypted': bool, 'plain': bool, 'length': int, 'sample': str}
    """
    try:
        data = api_get(session, f"chapters/{chapter_id}")
        ch   = data.get("data", {})
        raw  = ch.get("content", "")
        enc  = is_encrypted(raw)
        return {
            "encrypted": enc,
            "plain":     not enc and len(raw) > 50,
            "length":    len(raw),
            "sample":    raw[:120],
        }
    except Exception as e:
        return {"error": str(e)}


def fetch_user_profile(session: requests.Session) -> Dict:
    """Try to fetch user profile + any server-side key."""
    for ep in ["auth/me", "auth/user", "user", "users/me",
               "profile", "auth/profile"]:
        try:
            r = session.get(f"{API_URL}/{ep}", timeout=TIMEOUT)
            if r.status_code == 200:
                d = r.json().get("data", r.json())
                if isinstance(d, dict):
                    return d
        except Exception:
            pass
    return {}

# ─── API ─────────────────────────────────────────────────────────────────────
def api_get(session: requests.Session, path: str, params: dict = None) -> Dict:
    """Make GET request to API."""
    resp = session.get(f"{API_URL}/{path}", params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def search_books(session: requests.Session, query: str, page: int = 1) -> Dict:
    return api_get(session, "books", {"search": query, "per_page": 20, "page": page})

def list_books(session: requests.Session, page: int = 1, per_page: int = 20) -> Dict:
    return api_get(session, "books", {"per_page": per_page, "page": page})

def get_book_by_slug(session: requests.Session, slug: str) -> Optional[Dict]:
    data = api_get(session, "books", {"slug": slug})
    books = data.get("data", [])
    return books[0] if books else None

def get_book_by_id(session: requests.Session, book_id: int) -> Optional[Dict]:
    """Find book by ID across all API pages."""
    page = 1
    while True:
        data = api_get(session, "books", {"per_page": 50, "page": page})
        books = data.get("data", [])
        if not books:
            break
        for book in books:
            if book["id"] == book_id:
                return book
        pagination = data.get("pagination", {})
        total_pages = pagination.get("last", 1) if pagination else 1
        if page >= total_pages or len(books) < 50:
            break
        page += 1
    # Also try direct search
    data2 = api_get(session, "books", {"filter[id]": book_id})
    books2 = data2.get("data", [])
    if books2 and books2[0].get("id") == book_id:
        return books2[0]
    return None

def get_all_chapters(session: requests.Session, book_id: int) -> List[Dict]:
    """Get all chapters for a book (sorted by index)."""
    data = api_get(session, "chapters", {
        "filter[book_id]": book_id,
        "sort_by": "index",
        "sort_dir": "asc",
    })
    chapters = data.get("data", [])
    chapters.sort(key=lambda c: c.get("index", 0))
    return chapters

def get_chapter(session: requests.Session, chapter_id: int, delay: float = DELAY) -> Optional[Dict]:
    """Fetch chapter with content, with delay and retry on rate limit."""
    time.sleep(delay)
    try:
        data = api_get(session, f"chapters/{chapter_id}")
        return data.get("data")
    except requests.HTTPError as e:
        if e.response.status_code == 429:
            wait = int(e.response.headers.get("Retry-After", 15))
            log.warning(f"Rate limited! Waiting {wait}s...")
            time.sleep(wait)
            return get_chapter(session, chapter_id, delay)
        log.error(f"HTTP {e.response.status_code} for chapter {chapter_id}")
        return None
    except Exception as e:
        log.error(f"Error fetching chapter {chapter_id}: {e}")
        return None

# ─── File Utils ───────────────────────────────────────────────────────────────
def safe_name(name: str) -> str:
    """Create safe filesystem name."""
    name = unicodedata.normalize("NFC", name)
    # Remove invalid Windows chars
    for c in r'\/:*?"<>|':
        name = name.replace(c, "_")
    # Replace consecutive whitespace
    name = re.sub(r"\s+", " ", name).strip()
    return name[:200]

def write_chapter_file(path: Path, chapter: Dict, text: Optional[str]) -> bool:
    """Write chapter content to TXT file."""
    lines = []
    ch_name = chapter.get("name", f"Chuong {chapter.get('index', '?')}")
    
    lines.append("=" * 70)
    lines.append(ch_name)
    lines.append("=" * 70)
    lines.append("")
    
    if text:
        # Normalize whitespace
        content = text.replace("\r\n", "\n").replace("\r", "\n")
        content = re.sub(r"\n{3,}", "\n\n", content).strip()
        lines.append(content)
    else:
        lines.append("[Noi dung bi ma hoa - can APP_KEY de giai ma]")
        lines.append("")
        lines.append(f"Chapter ID: {chapter.get('id')}")
        lines.append(f"Word count: {chapter.get('word_count', '?')}")
    
    lines.append("")
    
    try:
        path.write_text("\n".join(lines), encoding="utf-8")
        return True
    except Exception as e:
        log.error(f"Write error: {e}")
        return False

def merge_to_single_file(book_dir: Path, book_name: str) -> Path:
    """Merge all chapter TXT files into one."""
    chapter_files = sorted(
        [f for f in book_dir.glob("[0-9]*.txt")],
        key=lambda f: f.name
    )
    
    merged = book_dir / f"_{safe_name(book_name)}_FULL.txt"
    
    with merged.open("w", encoding="utf-8") as out:
        out.write(f"{'=' * 70}\n")
        out.write(f"TRUYEN: {book_name}\n")
        out.write(f"Tao luc: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        out.write(f"So chuong: {len(chapter_files)}\n")
        out.write(f"{'=' * 70}\n\n")
        
        for fpath in chapter_files:
            content = fpath.read_text(encoding="utf-8")
            out.write(content)
            out.write("\n")
    
    return merged

# ─── Download Orchestrator ────────────────────────────────────────────────────
def download_book(
    session: requests.Session,
    book: Dict,
    output_dir: Path = OUTPUT_DIR,
    start_ch: int   = 1,
    end_ch:   Optional[int] = None,
    delay:    float = DELAY,
    app_key:  Optional[str] = None,
) -> Dict:
    """Download chapters of a book. Returns summary dict."""
    
    book_id   = book["id"]
    book_name = book["name"]
    
    log.info(f"Book: {book_name}")
    log.info(f"  ID={book_id} | Chapters={book.get('chapter_count', book.get('latest_index', 0))}")
    if app_key:
        log.info("  Decryption: ENABLED (APP_KEY provided)")
    else:
        log.info("  Decryption: DISABLED (no APP_KEY - content will be placeholder)")
    
    # Prepare directory
    book_dir = output_dir / safe_name(book_name)
    book_dir.mkdir(parents=True, exist_ok=True)
    
    # Load progress
    progress_file = book_dir / ".progress.json"
    downloaded_ids: set = set()
    if progress_file.exists():
        try:
            data = json.loads(progress_file.read_text("utf-8"))
            downloaded_ids = set(data.get("done", []))
            log.info(f"  Resume: {len(downloaded_ids)} chapters already done")
        except Exception:
            pass
    
    # Get chapter list
    log.info("Fetching chapter list...")
    try:
        all_chapters = get_all_chapters(session, book_id)
    except Exception as e:
        log.error(f"Cannot fetch chapters: {e}")
        return {"success": False}
    
    log.info(f"Total chapters: {len(all_chapters)}")
    
    # Apply range filter
    if end_ch is None:
        end_ch = len(all_chapters)
    
    to_download = [
        c for c in all_chapters
        if start_ch <= c.get("index", 0) <= end_ch
        and c["id"] not in downloaded_ids
        and not c.get("is_locked")  # Unlocked only
    ]
    
    locked = sum(1 for c in all_chapters 
                 if start_ch <= c.get("index", 0) <= end_ch and c.get("is_locked"))
    
    log.info(f"To download: {len(to_download)} | Locked: {locked} | Already done: {len(downloaded_ids)}")
    
    # Stats
    n_done = n_fail = n_enc = 0
    
    for i, ch in enumerate(to_download, 1):
        ch_id    = ch["id"]
        ch_idx   = ch.get("index", i)
        ch_name  = ch.get("name", f"Chuong {ch_idx}")
        
        # Output file path - use zero-padded index for proper sorting
        ch_file = book_dir / f"{ch_idx:06d}_{safe_name(ch_name)}.txt"
        
        log.info(f"[{i}/{len(to_download)}] {ch_name}")
        
        # Skip already downloaded (file exists + in progress)
        if ch_file.exists() and ch_id in downloaded_ids:
            log.info("  -> Skipped (exists)")
            n_done += 1
            continue
        
        # Fetch chapter
        ch_data = get_chapter(session, ch_id, delay)
        if not ch_data:
            log.error(f"  -> FAILED to fetch")
            n_fail += 1
            continue
        
        # Process content
        raw   = ch_data.get("content", "")
        text  = process_content(raw, app_key)
        
        if text is None and raw:
            n_enc += 1
            log.warning("  -> Encrypted (no key)")
        elif text:
            log.info(f"  -> OK ({len(text)} chars)")
        
        # Save file
        if write_chapter_file(ch_file, ch_data, text):
            downloaded_ids.add(ch_id)
            n_done += 1
        else:
            n_fail += 1
        
        # Save progress
        progress_file.write_text(
            json.dumps({"done": list(downloaded_ids)}, ensure_ascii=False),
            encoding="utf-8"
        )
    
    # Merge into single file
    if to_download:
        merged = merge_to_single_file(book_dir, book_name)
        log.info(f"Merged: {merged.name}")
    
    # Summary
    log.info("")
    log.info("=" * 50)
    log.info(f"DONE: {book_name}")
    log.info(f"  Downloaded: {n_done}")
    log.info(f"  Failed:     {n_fail}")
    if n_enc:
        log.warning(f"  Encrypted:  {n_enc} (use --app-key to decrypt)")
    log.info(f"  Output:     {book_dir}")
    log.info("=" * 50)
    
    return {
        "success": True,
        "downloaded": n_done,
        "failed":     n_fail,
        "encrypted":  n_enc,
        "output":     str(book_dir),
    }

# ─── CLI ─────────────────────────────────────────────────────────────────────
def print_books_table(books: List[Dict], title: str = ""):
    if title:
        print(f"\n{title}")
    print(f"\n{'ID':>10}  {'Ten Truyen':<52}  {'Ch.':>6}  {'Trang thai'}")
    print("-" * 85)
    for b in books:
        name = b["name"][:52]
        print(f"{b['id']:>10}  {name:<52}  {b.get('latest_index', 0):>6}  {b.get('status_name', '')}")

def cmd_list(args, session):
    data  = list_books(session, args.page, args.per_page)
    books = data.get("data", [])
    pagi  = data.get("pagination", {})
    print_books_table(books, f"Danh sach truyen - Trang {args.page}")
    if pagi:
        print(f"\nTotal: {pagi.get('total', '?')} | Page {args.page}/{pagi.get('last', '?')}")

def cmd_search(args, session):
    log.info(f"Searching: '{args.query}'")
    data  = search_books(session, args.query, args.page)
    books = data.get("data", [])
    if not books:
        print("No results found.")
        return
    print_books_table(books, f"Ket qua tim kiem: '{args.query}'")

def cmd_info(args, session):
    if hasattr(args, "slug") and args.slug:
        book = get_book_by_slug(session, args.slug)
    else:
        log.info(f"Looking up book ID {args.id}...")
        book = get_book_by_id(session, args.id)
    
    if not book:
        log.error("Book not found")
        return
    
    synopsis = book.get("synopsis", "No description") or "No description"
    if len(synopsis) > 600:
        synopsis = synopsis[:600] + "..."
    
    print(f"\n{'=' * 60}")
    print(f">> {book['name']}")
    print(f"{'=' * 60}")
    print(f"ID:          {book['id']}")
    print(f"Slug:        {book['slug']}")
    print(f"Status:      {book.get('status_name', 'N/A')}")
    print(f"Chapters:    {book.get('chapter_count', book.get('latest_index', 0))}")
    print(f"Views:       {book.get('view_count', 0):,}")
    print(f"Rating:      {book.get('review_score', 0)}/5 ({book.get('review_count', 0)} reviews)")
    print(f"\nSynopsis:")
    print(synopsis)
    print()

def cmd_download(args, session, app_key):
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    
    log.info("Finding book...")
    if hasattr(args, "slug") and args.slug:
        book = get_book_by_slug(session, args.slug)
    else:
        book = get_book_by_id(session, args.id)
    
    if not book:
        log.error("Book not found. Use 'list' or 'search' to find valid IDs/slugs.")
        return
    
    result = download_book(
        session   = session,
        book      = book,
        output_dir= out,
        start_ch  = args.start,
        end_ch    = args.end,
        delay     = args.delay,
        app_key   = app_key,
    )
    
    if result.get("encrypted", 0) > 0 and not app_key:
        print("\n[NOTE] Some chapters are encrypted.")
        print("  If you have the APP_KEY, use: --app-key <key>")
        print("  Format: base64:<32-byte-base64-string>")

def main():
    parser = argparse.ArgumentParser(
        prog="downloader",
        description=f"MTC Novel Downloader v{VERSION} - android.lonoapp.net",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  run.bat list
  run.bat list --page 2
  run.bat search "nhat kiep tien pham"
  run.bat info --id 140643
  run.bat info --slug lang-nhan-my-nu-moi-tu-van
  run.bat download --id 140643
  run.bat download --id 140643 --from 1 --to 100
  run.bat download --id 140643 --output D:\truyen
  run.bat download --id 140643 --app-key base64:xxxx
  run.bat download --id 140643 --email you@mail.com --password pass
        """
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    parser.add_argument("--email",    default=None, help="Login email")
    parser.add_argument("--password", default=None, help="Login password")
    parser.add_argument("--app-key",  default=None, dest="app_key",
                        help="Decryption key (format: base64:xxxxx)")
    
    sub = parser.add_subparsers(dest="cmd")
    
    # list
    lp = sub.add_parser("list", help="List all novels")
    lp.add_argument("--page", type=int, default=1)
    lp.add_argument("--per-page", type=int, default=20, dest="per_page")
    
    # search
    sp = sub.add_parser("search", help="Search novels by name")
    sp.add_argument("query", help="Search query")
    sp.add_argument("--page", type=int, default=1)
    
    # info
    ip = sub.add_parser("info", help="Show novel details")
    ig = ip.add_mutually_exclusive_group(required=True)
    ig.add_argument("--id",    type=int)
    ig.add_argument("--slug",  type=str)
    
    # download
    dp = sub.add_parser("download", help="Download novel chapters")
    dg = dp.add_mutually_exclusive_group(required=True)
    dg.add_argument("--id",    type=int)
    dg.add_argument("--slug",  type=str)
    dp.add_argument("--from",  dest="start", type=int, default=1)
    dp.add_argument("--to",    dest="end",   type=int, default=None)
    dp.add_argument("--output", "-o", default=str(OUTPUT_DIR), help="Output directory")
    dp.add_argument("--delay", type=float, default=DELAY, help="Delay between requests (s)")
    
    args = parser.parse_args()

    # No subcommand → print help
    if not args.cmd:
        parser.print_help()
        return

    setup_logging(args.verbose)
    
    # Auth
    token   = None
    app_key = args.app_key
    
    if args.email and args.password:
        log.info("Logging in...")
        auth = login(args.email, args.password)
        if auth:
            token = auth.get("token")
            if auth.get("key") and not app_key:
                app_key = auth["key"]
                log.info("Got decryption key from server!")
    
    session = make_session(token)
    
    try:
        if args.cmd == "list":
            cmd_list(args, session)
        elif args.cmd == "search":
            cmd_search(args, session)
        elif args.cmd == "info":
            cmd_info(args, session)
        elif args.cmd == "download":
            cmd_download(args, session, app_key)
    except KeyboardInterrupt:
        log.info("\nInterrupted by user")
    except requests.ConnectionError:
        log.error("Connection error. Check your internet connection.")
    except Exception as e:
        log.error(f"Unexpected error: {e}", exc_info=args.verbose)

if __name__ == "__main__":
    main()
