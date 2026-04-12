"""utils.py – File system utilities."""
import re, unicodedata
from pathlib import Path
from datetime import datetime


_ADB_MOJIBAKE_MARKERS = ("├", "┤", "┐", "└", "┴", "┬", "╞", "╣", "║", "ß", "�")


def _repair_score(text: str) -> int:
    viet_chars = "ăâêôơưđĂÂÊÔƠƯĐáàảãạắằẳẵặấầẩẫậéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ"
    score = sum(text.count(ch) for ch in viet_chars)
    score -= sum(text.count(ch) for ch in _ADB_MOJIBAKE_MARKERS)
    score -= text.count("�") * 2
    return score


def repair_adb_text(text: str) -> str:
    """Best-effort fix for Vietnamese mojibake returned by ADB/UIAutomator."""
    if not text or not any(marker in text for marker in _ADB_MOJIBAKE_MARKERS):
        return text

    best = text
    best_score = _repair_score(text)

    for legacy_encoding in ("cp437", "cp850"):
        try:
            fixed = text.encode(legacy_encoding).decode("utf-8")
        except UnicodeError:
            continue
        score = _repair_score(fixed)
        if score > best_score:
            best = fixed
            best_score = score

    return best


def safe_name(name: str) -> str:
    """Create filesystem-safe name."""
    name = unicodedata.normalize("NFC", name)
    for c in r'\/:*?"<>|':
        name = name.replace(c, "_")
    name = re.sub(r"\s+", " ", name).strip()
    return name[:200]


def merge_to_single_file(book_dir: Path, book_name: str) -> Path:
    """Merge all chapter TXT files into one."""
    chapter_files = sorted(
        [f for f in book_dir.glob("[0-9]*.txt")],
        key=lambda f: f.name,
    )
    merged = book_dir / f"_{safe_name(book_name)}_FULL.txt"
    with merged.open("w", encoding="utf-8") as out:
        out.write(f"{'=' * 70}\n")
        out.write(f"TRUYEN: {book_name}\n")
        out.write(f"Tao luc: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        out.write(f"So chuong: {len(chapter_files)}\n")
        out.write(f"{'=' * 70}\n\n")
        for fpath in chapter_files:
            out.write(fpath.read_text(encoding="utf-8"))
            out.write("\n")
    return merged
