"""utils.py – File system utilities."""
import re, unicodedata
from pathlib import Path
from datetime import datetime


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
