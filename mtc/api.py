"""api.py - API client for MTC/NovelFever."""
import requests
from typing import Optional, Dict, List, Any
from .config import API_BASE, USER_AGENT, TOKEN_FILE, log


def create_session() -> requests.Session:
    """Create a requests session with proper headers."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    })
    
    # Load token if exists
    if TOKEN_FILE.exists():
        token = TOKEN_FILE.read_text().strip()
        if token:
            session.headers["Authorization"] = f"Bearer {token}"
    
    return session


def search_books(session: requests.Session, keyword: str) -> List[Dict[str, Any]]:
    """Search books by keyword."""
    try:
        url = f"{API_BASE}/books/search"
        resp = session.get(url, params={"q": keyword}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", [])
    except Exception as e:
        log.error(f"Search failed: {e}")
        return []


def get_book_info(session: requests.Session, book_id: int) -> Optional[Dict[str, Any]]:
    """Get book information by ID."""
    try:
        url = f"{API_BASE}/books/{book_id}"
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data")
    except Exception as e:
        log.error(f"Get book info failed: {e}")
        return None


def get_chapters(session: requests.Session, book_id: int) -> List[Dict[str, Any]]:
    """Get all chapters of a book."""
    try:
        url = f"{API_BASE}/books/{book_id}/chapters"
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", [])
    except Exception as e:
        log.error(f"Get chapters failed: {e}")
        return []


def get_chapter_content(session: requests.Session, book_id: int, chapter_id: int) -> Optional[str]:
    """Get chapter content."""
    try:
        url = f"{API_BASE}/books/{book_id}/chapters/{chapter_id}"
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", {}).get("content")
    except Exception as e:
        log.error(f"Get chapter content failed: {e}")
        return None


def get_all_books(session: requests.Session) -> List[Dict[str, Any]]:
    """Get all books from catalog."""
    try:
        url = f"{API_BASE}/books"
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", [])
    except Exception as e:
        log.error(f"Get all books failed: {e}")
        return []
