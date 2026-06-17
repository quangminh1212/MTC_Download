#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rename and clean up chapter files that ended up with 'Untitled'.

Old downloads stored chapters as `Chương N Untitled.txt` (and header line
"Chương 0N Untitled" / "Chương N Untitled") whenever the API returned a name
that was effectively just "Chương N:" with no real title. This script:

1. Renames any `Chương N Untitled.txt` to `Chương N.txt` (resolving conflicts
   in favour of the larger file).
2. Rewrites the chapter header so it reads "Chương N" (drops the leading 0
   and the bogus "Untitled" suffix) without touching the body content.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"D:\Dev\MTC_Done")
NAME_RE = re.compile(r"^(Chương\s+)0*(\d+)\s+Untitled\.txt$", re.IGNORECASE)
HEADER_RE = re.compile(r"^Chương\s+0*(\d+)(?:\s+Untitled)?\s*$", re.IGNORECASE)


def fix_header(text: str) -> str | None:
    lines = text.splitlines()
    # header lives on line 2 (between two ====== lines)
    if len(lines) < 4:
        return None
    if not lines[0].startswith("===") or not lines[2].startswith("==="):
        return None
    m = HEADER_RE.match(lines[1].strip())
    if not m:
        return None
    new_header = f"Chương {int(m.group(1))}"
    if lines[1] == new_header:
        return None
    lines[1] = new_header
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def process_folder(folder: Path) -> tuple[int, int]:
    renamed = headers = 0
    for path in list(folder.glob("Chương * Untitled.txt")):
        m = NAME_RE.match(path.name)
        if not m:
            continue
        target = folder / f"Chương {int(m.group(2))}.txt"
        if target.exists():
            try:
                if target.stat().st_size >= path.stat().st_size:
                    path.unlink()
                    continue
                target.unlink()
            except OSError:
                continue
        path.rename(target)
        renamed += 1
    for path in folder.glob("Chương *.txt"):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        new_text = fix_header(text)
        if new_text is not None:
            path.write_text(new_text, encoding="utf-8")
            headers += 1
    return renamed, headers


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    folders = [p for p in ROOT.iterdir() if p.is_dir() and not p.name.startswith(".")]
    folders.sort(key=lambda p: p.name)
    if args.limit is not None:
        folders = folders[: args.limit]

    total_renamed = total_headers = touched = 0
    for index, folder in enumerate(folders, 1):
        renamed, headers = process_folder(folder)
        if renamed or headers:
            touched += 1
        total_renamed += renamed
        total_headers += headers
        if index % 500 == 0:
            try:
                print(f"progress={index}/{len(folders)} touched={touched} renamed={total_renamed} headers={total_headers}", flush=True)
            except OSError:
                pass
    try:
        print(f"DONE folders={len(folders)} touched={touched} renamed={total_renamed} headers_fixed={total_headers}")
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
