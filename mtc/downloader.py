"""downloader.py - Download logic for books and chapters."""
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from .api import create_session, get_book_info, get_chapters, get_chapter_content, get_all_books, search_books
from .config import DATA_DIR, log
from .utils import safe_name, ensure_dir


def load_catalog() -> List[Dict[str, Any]]:
    """Load catalog from local cache."""
    from .config import CATALOG
    if not CATALOG.exists():
        return []
    try:
        return json.loads(CATALOG.read_text(encoding="utf-8"))
    except Exception as e:
        log.error(f"Load catalog failed: {e}")
        return []


def save_catalog(books: List[Dict[str, Any]]) -> None:
    """Save catalog to local cache."""
    from .config import CATALOG
    ensure_dir(CATALOG.parent)
    CATALOG.write_text(json.dumps(books, ensure_ascii=False, indent=2), encoding="utf-8")


def refresh_catalog(log_fn: Optional[Callable] = None) -> List[Dict[str, Any]]:
    """Refresh catalog from API."""
    if log_fn:
        log_fn("Đang cập nhật catalog từ API...")
    session = create_session()
    books = get_all_books(session)
    if books:
        save_catalog(books)
        if log_fn:
            log_fn(f"✓ Đã cập nhật {len(books)} truyện")
    return books


def download_book(
    book_name: str = "",
    book_id: Optional[int] = None,
    ch_start: int = 1,
    ch_end: Optional[int] = None,
    output_dir: Path = None,
    log_fn: Optional[Callable] = None,
) -> Dict[str, Any]:
    """Download a single book."""
    session = create_session()
    
    # Find book
    if book_id:
        book = get_book_info(session, book_id)
        if not book:
            return {"success": False, "reason": f"Book ID {book_id} not found"}
    else:
        results = search_books(session, book_name)
        if not results:
            return {"success": False, "reason": f"Book '{book_name}' not found"}
        book = results[0]
    
    book_id = book["id"]
    book_title = book["name"]
    
    if log_fn:
        log_fn(f"📖 {book_title} (ID: {book_id})")
    
    # Get chapters
    chapters = get_chapters(session, book_id)
    if not chapters:
        return {"success": False, "reason": "No chapters found"}
    
    # Filter chapters
    if ch_end is None:
        ch_end = len(chapters)
    chapters = chapters[ch_start - 1:ch_end]
    
    if log_fn:
        log_fn(f"   Tải {len(chapters)} chương...")
    
    # Create output directory
    book_dir = ensure_dir(output_dir / safe_name(book_title))
    
    # Download chapters
    success_count = 0
    for i, chapter in enumerate(chapters, ch_start):
        ch_id = chapter["id"]
        ch_title = chapter.get("title", f"Chương {i}")
        
        content = get_chapter_content(session, book_id, ch_id)
        if content:
            ch_file = book_dir / f"{i:04d}_{safe_name(ch_title)}.txt"
            ch_file.write_text(content, encoding="utf-8")
            success_count += 1
            if log_fn and i % 10 == 0:
                log_fn(f"   ... {i}/{len(chapters)}")
        else:
            log.warning(f"Failed to download chapter {i}")
    
    if log_fn:
        log_fn(f"   ✓ Hoàn thành {success_count}/{len(chapters)} chương")
    
    return {
        "success": True,
        "book_id": book_id,
        "book_name": book_title,
        "chapters": success_count,
    }


def download_batch(
    books: List[Dict[str, Any]],
    output_dir: Path,
    log_fn: Optional[Callable] = None,
    skip_existing: bool = True,
    status_filter: Optional[str] = None,
) -> Dict[str, int]:
    """Download multiple books."""
    result = {"total": 0, "ok": 0, "fail": 0, "skipped": 0}
    
    for book in books:
        # Filter by status
        if status_filter:
            status = book.get("status_name", "").lower()
            if status_filter.lower() not in status:
                continue
        
        result["total"] += 1
        book_name = book["name"]
        book_id = book["id"]
        
        # Check if already downloaded
        book_dir = output_dir / safe_name(book_name)
        if skip_existing and book_dir.exists():
            chapter_count = len(list(book_dir.glob("*.txt")))
            expected = book.get("chapter_count", 0)
            if chapter_count >= expected:
                result["skipped"] += 1
                if log_fn:
                    log_fn(f"⊘ Bỏ qua: {book_name} (đã có {chapter_count} chương)")
                continue
        
        # Download
        res = download_book(book_id=book_id, output_dir=output_dir, log_fn=log_fn)
        if res["success"]:
            result["ok"] += 1
        else:
            result["fail"] += 1
    
    return result
