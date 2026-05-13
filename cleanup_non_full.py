#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Clean C:\\Dev\\MTC: keep only books confirmed completed by MTC API manifest.
Moves non-completed folders to a recoverable quarantine folder instead of deleting permanently.
"""
import json
import shutil
from datetime import datetime
from pathlib import Path

MTC = Path(r"C:\Dev\MTC")
MANIFEST = Path(r"C:\Dev\MTC_Download\completed_books.json")
STAMP = datetime.now().strftime("%Y%m%d-%H%M%S")
QUAR = Path(r"C:\Dev") / f"MTC_non_full_quarantine_{STAMP}"

import re

INVALID = '<>:"/\\|?*'

def clean_name(name: str) -> str:
    name = str(name or "").strip()
    for ch in INVALID:
        name = name.replace(ch, " ")
    name = re.sub(r"\s+", " ", name).strip(" .")
    return name

books = json.loads(MANIFEST.read_text(encoding="utf-8"))
valid = {
    clean_name(b["name"])
    for b in books
    if b.get("status_name") == "Hoàn thành"
    and int(b.get("status") or 0) == 2
    and int(b.get("chapter_count") or b.get("latest_index") or 0) >= 1
}

moved = []
kept = []
for d in MTC.iterdir():
    if not d.is_dir() or d.name == ".git":
        continue
    if d.name in valid:
        kept.append(d.name)
        continue
    QUAR.mkdir(parents=True, exist_ok=True)
    target = QUAR / d.name
    suffix = 1
    while target.exists():
        target = QUAR / f"{d.name} ({suffix})"
        suffix += 1
    shutil.move(str(d), str(target))
    moved.append({"from": str(d), "to": str(target)})

report = {
    "valid_completed_count": len(valid),
    "kept": kept,
    "moved_count": len(moved),
    "quarantine": str(QUAR) if moved else None,
    "moved": moved,
}
report_path = Path(r"C:\Dev\MTC_Download\logs") / "cleanup_non_full_report.json"
report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
