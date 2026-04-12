#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
downloader.py – MTC API client (book listing & utilities only)
Dùng API android.lonoapp.net để lấy danh sách truyện cho sidebar.
Việc tải nội dung chương thực hiện qua ADB/BlueStacks trong auto.py.
"""
import sys, io, re, json, time, unicodedata, logging
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ─── Constants ───────────────────────────────────────────────────────────────
BASE_URL   = "https://android.lonoapp.net"
API_URL    = f"{BASE_URL}/api"
USER_AGENT = "Dart/3.0 (dart:io)"
TIMEOUT    = 30
MAX_RETRY  = 3

log = logging.getLogger("mtc")

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

# ─── API ─────────────────────────────────────────────────────────────────────
def api_get(session: requests.Session, path: str, params: dict = None) -> Dict:
    resp = session.get(f"{API_URL}/{path}", params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def search_books(session: requests.Session, query: str, page: int = 1) -> Dict:
    return api_get(session, "books", {"search": query, "per_page": 20, "page": page})

def list_books(session: requests.Session, page: int = 1, per_page: int = 20) -> Dict:
    return api_get(session, "books", {"per_page": per_page, "page": page})

# ─── File Utils ───────────────────────────────────────────────────────────────
def safe_name(name: str) -> str:
    """Create safe filesystem name."""
    name = unicodedata.normalize("NFC", name)
    for c in r'\/:*?"<>|':
        name = name.replace(c, "_")
    name = re.sub(r"\s+", " ", name).strip()
    return name[:200]

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
