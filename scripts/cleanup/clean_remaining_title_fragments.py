#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Dev\MTC")
REPORT = Path(r"C:\Dev\MTC_DOWNLOAD\logs\deep_scan_completed.json")
OUT = Path(r"C:\Dev\MTC_DOWNLOAD\logs\clean_remaining_title_fragments.json")
CHAPTER_RE = re.compile(r"(?i)(?:chương|chuong)\s*(\d+)")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def alnum_norm(v: str) -> str:
    text = unicodedata.normalize("NFC", str(v or "")).casefold()
    return "".join(c for c in text if c.isalnum())


def title_core_words(title: str) -> set[str]:
    t = re.sub(r"(?i)^chương\s*\d+\s*", "", title or "").strip()
    return {w for w in re.findall(r"\w+", t.casefold(), flags=re.UNICODE) if w}


def parse_index(title: str) -> int:
    m = CHAPTER_RE.search(title)
    return int(m.group(1)) if m else 0


def looks_like_title_fragment(line: str, title: str, index: int) -> bool:
    s = CONTROL_RE.sub("", (line or "")).strip()
    if not s:
        return False
    compact = alnum_norm(s)
    title_norm = alnum_norm(title)
    core = title_core_words(title)
    if len(s) <= 3:
        return True
    if re.match(rf"(?i)^chương\s*0*{index}(?:\b|\s*[:.\-])", s):
        return True
    if compact and title_norm and len(compact) >= 4 and compact in title_norm:
        return True
    words = {w for w in re.findall(r"\w+", s.casefold(), flags=re.UNICODE) if w}
    if words and core and words.issubset(core):
        return True
    alpha = sum(ch.isalpha() for ch in s)
    if len(s) < 60 and alpha < max(4, len(s) // 3):
        return True
    return False


def clean_file(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    orig = text
    text = CONTROL_RE.sub("", text)
    lines = text.splitlines()
    if len(lines) < 5:
        if text != orig:
            path.write_text(text, encoding="utf-8")
            return {"file": path.name, "removed": ["control_chars"]}
        return None

    title = lines[1].strip()
    index = parse_index(title)
    removed = []
    changed = True
    # repeatedly clean only in the danger zone below the header
    while changed:
        changed = False
        for pos in range(4, min(8, len(lines))):
            if looks_like_title_fragment(lines[pos], title, index):
                removed.append({"line": pos + 1, "text": lines[pos]})
                del lines[pos]
                changed = True
                break
        # collapse duplicate leading blanks after header
        while len(lines) > 5 and lines[4] == '' and lines[5] == '':
            removed.append({"line": 6, "text": ''})
            del lines[5]
            changed = True

    new_text = "\n".join(lines)
    if text.endswith("\n"):
        new_text += "\n"
    if new_text != orig:
        path.write_text(new_text, encoding="utf-8")
        return {"file": path.name, "removed": removed}
    return None


def main() -> int:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    changes = []
    for entry in report:
        if not any(i["kind"] in ("duplicate_title_fragment", "control_char") for i in entry.get("issues", [])):
            continue
        folder = ROOT / entry["folder"]
        seen = set()
        for issue in entry.get("issues", []):
            fn = issue.get("file")
            if not fn or fn in seen:
                continue
            seen.add(fn)
            path = folder / fn
            if path.exists():
                result = clean_file(path)
                if result:
                    changes.append({"folder": entry["folder"], **result})
    OUT.write_text(json.dumps(changes, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"changed={len(changes)}")
    print(f"report={OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
