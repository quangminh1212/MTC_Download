#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deep scan of all completed books per RULES.md section 5.

Checks:
  1. Encrypted markers (eyJpdiI6, "iv":", "value":")
  2. U+FFFD replacement char
  3. Mojibake patterns (ChÆ°Æ¡ng, Ã¡Âº, Ã¡Â», Ãƒ, Ã‚)
  4. Control chars (except normal newlines/tabs)
  5. Header format: line1==...==, line2 title, line3==...==
  6. Duplicate title line right below header (line 5-7)
  7. Missing .txt files vs unique chapter indexes in info.json / manifest
"""
from __future__ import annotations
import json, re, sys, unicodedata
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Dev\MTC")
MANIFEST = Path(r"C:\Dev\MTC_DOWNLOAD\completed_books.json")
LOG_DIR = Path(r"C:\Dev\MTC_DOWNLOAD\logs")
REPORT = LOG_DIR / "deep_scan_completed.json"
LOG_DIR.mkdir(parents=True, exist_ok=True)

IGNORE_DIRS = {".git", ".githooks", ".vscode", "__pycache__"}

ENCRYPTED_MARKERS = ("eyJpdiI6", '"iv":"', '"value":"')
MOJIBAKE_PATTERNS = [
    re.compile(r"Ch\u00c6\u00b0\u00c6\u00a1ng"),
    re.compile(r"\u00c3\u00a1\u00c2\u00ba"),
    re.compile(r"\u00c3\u00a1\u00c2\u00bb"),
    re.compile(r"\u00c3\u0192"),
    re.compile(r"\u00c3\u201a"),
    re.compile(r"\u00c3\u00af\u00c2\u00bf\u00c2\u00bd"),
    re.compile(r"[\u0000-\u0008\u000b\u000c\u000e-\u001f\u007f]"),
]
FFFD_RE = re.compile(r"\ufffd")
CHAPTER_RE = re.compile(r"(?i)(?:ch\u01b0\u01a1ng|chuong)\s*(\d+)")
HEADER_LINE_RE = re.compile(r"^={30,}$")

def alnum_norm(v: str) -> str:
    import html
    text = unicodedata.normalize("NFC", html.unescape(str(v or ""))).casefold()
    return "".join(c for c in text if c.isalnum())

def local_folder_for_book(book: dict) -> Path | None:
    norm = alnum_norm(book.get("name") or "")
    for path in ROOT.iterdir():
        if path.is_dir() and path.name not in IGNORE_DIRS:
            if alnum_norm(path.name) == norm:
                return path
    return None

def expected_unique_count(folder: Path, book: dict) -> int:
    info_path = folder / 'info.json'
    if info_path.exists():
        try:
            payload = json.loads(info_path.read_text(encoding='utf-8'))
            chapters = payload.get('chapters') or []
            idxs = set()
            for seq, ch in enumerate(chapters, 1):
                try:
                    idxs.add(int(ch.get('index') or ch.get('number') or seq))
                except Exception:
                    pass
            if idxs:
                return len(idxs)
        except Exception:
            pass
    return int(book.get('chapter_count') or book.get('latest_index') or 0)

def scan_file(path: Path) -> list[dict]:
    issues = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        issues.append({"kind": "read_error", "file": path.name, "detail": str(exc)})
        return issues

    for marker in ENCRYPTED_MARKERS:
        if marker in text:
            issues.append({"kind": "encrypted_marker", "file": path.name, "marker": marker})

    if FFFD_RE.search(text):
        issues.append({"kind": "replacement_char", "file": path.name, "count": len(FFFD_RE.findall(text))})

    for i, pat in enumerate(MOJIBAKE_PATTERNS[:-1]):
        if pat.search(text):
            issues.append({"kind": "mojibake", "file": path.name, "pattern": i})

    if MOJIBAKE_PATTERNS[-1].search(text):
        issues.append({"kind": "control_char", "file": path.name})

    lines = text.splitlines()
    if lines:
        if not HEADER_LINE_RE.match(lines[0].rstrip()):
            issues.append({"kind": "missing_header_line1", "file": path.name, "got": lines[0][:80]})
        if len(lines) >= 3:
            if not HEADER_LINE_RE.match(lines[2].rstrip()):
                issues.append({"kind": "missing_header_line3", "file": path.name, "got": lines[2][:80]})
            title_line = lines[1].strip() if len(lines) > 1 else ""
            title_norm = alnum_norm(title_line)
            for li in range(4, min(7, len(lines))):
                check = alnum_norm(lines[li].strip())
                if check and title_norm and len(check) >= 6 and check in title_norm and check != title_norm:
                    issues.append({"kind": "duplicate_title_fragment", "file": path.name, "line": li + 1, "text": lines[li][:120]})
    return issues

def main() -> int:
    books = json.loads(MANIFEST.read_text(encoding="utf-8"))
    completed = [
        book for book in books
        if (book.get("status_name") == "Ho\u00e0n th\u00e0nh" or book.get("status") == 2)
        and int(book.get("chapter_count") or book.get("latest_index") or 0) > 0
    ]
    print(f"Scanning {len(completed)} completed books...", flush=True)

    report = []
    total_files = 0
    total_issues = 0

    for seq, book in enumerate(completed, 1):
        folder = local_folder_for_book(book)
        if folder is None:
            report.append({"book": book.get("name"), "id": int(book["id"]), "folder": None, "issues": [{"kind": "folder_missing"}]})
            total_issues += 1
            print(f"[{seq}/{len(completed)}] MISSING folder: {book.get('name')}", flush=True)
            continue

        txt_files = sorted(folder.glob("*.txt"))
        file_issues = []
        expected_count = expected_unique_count(folder, book)
        if len(txt_files) != expected_count:
            file_issues.append({"kind": "chapter_count_mismatch", "expected": expected_count, "actual": len(txt_files)})

        for path in txt_files:
            file_issues.extend(scan_file(path))
        total_files += len(txt_files)
        total_issues += len(file_issues)

        entry = {
            "book": book.get("name"),
            "id": int(book["id"]),
            "folder": folder.name,
            "files": len(txt_files),
            "expected": expected_count,
            "issue_count": len(file_issues),
            "issues": file_issues,
            "status": "ok" if not file_issues else "issue",
        }
        report.append(entry)
        if file_issues:
            print(f"[{seq}/{len(completed)}] ISSUE {folder.name}: {len(file_issues)} issues", flush=True)
        else:
            print(f"[{seq}/{len(completed)}] ok {folder.name}: {len(txt_files)} files", flush=True)

    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nScan complete: {total_files} files, {total_issues} total issues")
    print(f"REPORT={REPORT}")
    print(f"Books with issues: {sum(1 for e in report if e.get('issues'))}/{len(completed)}")
    return 0 if total_issues == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())
