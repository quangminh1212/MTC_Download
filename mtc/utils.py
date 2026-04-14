"""utils.py - Utility functions."""
import re
from pathlib import Path


def safe_name(name: str) -> str:
    """Convert book/chapter name to safe filename."""
    # Remove invalid characters
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Replace multiple spaces with single space
    name = re.sub(r'\s+', ' ', name)
    # Trim
    name = name.strip()
    # Limit length
    if len(name) > 200:
        name = name[:200]
    return name or "untitled"


def ensure_dir(path: Path) -> Path:
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)
    return path
