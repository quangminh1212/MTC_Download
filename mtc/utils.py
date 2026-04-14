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


def _chapter_sort_key(path: Path) -> tuple:
    """Extract chapter number for sorting; fallback to name."""
    m = re.search(r"Chương\s+(\d+)", path.stem)
    if m:
        return (0, int(m.group(1)), path.stem)
    # Old naming: leading digits
    m2 = re.match(r"(\d+)", path.stem)
    if m2:
        return (0, int(m2.group(1)), path.stem)
    return (1, 0, path.stem)


def merge_to_single_file(book_dir: Path, book_name: str) -> Path:
    """Merge all chapter TXT files into one."""
    chapter_files = sorted(
        [f for f in book_dir.glob("*.txt") if not f.name.startswith("_")],
        key=_chapter_sort_key,
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
