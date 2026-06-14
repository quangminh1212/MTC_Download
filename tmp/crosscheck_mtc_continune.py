from __future__ import annotations

import html
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, r"c:\Dev\MTC_Download\scripts")
from mtc_downloader import MTCDownloader

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"c:\Dev\mtc_continune")
OUT = Path(r"c:\Dev\MTC_Download\logs\mtc_continune_full_crosscheck.json")
INVALID = '<>:"/\\|?*!'
STRIP_PUNCT_RE = re.compile(r"[\(\)\[\]\{\}\+,\-–—]+")
WS_RE = re.compile(r"\s+")
CHAP_RE = re.compile(r"(?i)(?:chương|chuong)\s*(\d+)")
IGNORE_DIRS = {".git", ".githooks", ".vscode", "git", ".claude"}


def norm(name: str) -> str:
    s = html.unescape(str(name or "")).strip()
    s = STRIP_PUNCT_RE.sub(" ", s)
    for ch in INVALID:
        s = s.replace(ch, " ")
    return WS_RE.sub(" ", s).strip(" .").lower()


def get_all_books(d: MTCDownloader) -> list[dict]:
    rows = []
    page = 1
    while True:
        data = d.get_books(limit=100, page=page)
        arr = (data or {}).get("data") or []
        if not arr:
            break
        rows.extend(arr)
        if len(arr) < 100:
            break
        page += 1
        time.sleep(0.05)
    return rows


def get_remote_indexes(d: MTCDownloader, book_id: int) -> list[int]:
    out = []
    page = 1
    while True:
        data = d.get_chapters(book_id, page=page, limit=500)
        arr = (data or {}).get("data") or []
        if not arr:
            break
        for c in arr:
            idx = c.get("index") or c.get("number")
            try:
                iv = int(idx)
            except Exception:
                iv = 0
            if iv > 0:
                out.append(iv)
        if len(arr) < 500:
            break
        page += 1
        time.sleep(0.03)
    return sorted(set(out))


def local_indexes(folder: Path) -> list[int]:
    seen = set()
    for p in folder.glob("*.txt"):
        m = CHAP_RE.search(p.name)
        if m:
            try:
                seen.add(int(m.group(1)))
            except Exception:
                pass
    return sorted(seen)


def choose_book(cands: list[dict], local_count: int) -> dict:
    if len(cands) == 1:
        return cands[0]
    return sorted(cands, key=lambda b: abs(int(b.get("chapter_count") or b.get("latest_index") or 0) - local_count))[0]


def main() -> int:
    d = MTCDownloader()
    books = get_all_books(d)
    by_norm = {}
    for b in books:
        key = norm(b.get("name") or "")
        if key:
            by_norm.setdefault(key, []).append(b)

    report = []
    folders = [p for p in ROOT.iterdir() if p.is_dir() and p.name not in IGNORE_DIRS]
    folders.sort(key=lambda p: p.name.lower())

    for i, folder in enumerate(folders, 1):
        lidx = local_indexes(folder)
        if not lidx:
            continue
        key = norm(folder.name)
        cands = by_norm.get(key, [])
        row = {"folder": folder.name, "local_count": len(lidx), "local_min": lidx[0], "local_max": lidx[-1]}
        if not cands:
            row["status"] = "unmatched_remote"
            report.append(row)
            print(f"[{i}] {folder.name}: unmatched_remote", flush=True)
            continue
        b = choose_book(cands, len(lidx))
        bid = int(b.get("id"))
        ridx = get_remote_indexes(d, bid)
        missing = sorted(set(ridx) - set(lidx))
        extra = sorted(set(lidx) - set(ridx))
        row.update({
            "book_id": bid,
            "book_name": b.get("name"),
            "remote_count": len(ridx),
            "remote_max": ridx[-1] if ridx else 0,
            "missing_count": len(missing),
            "missing_first200": missing[:200],
            "extra_count": len(extra),
            "extra_first200": extra[:200],
            "status": "complete_vs_remote" if not missing and not extra else "mismatch_vs_remote",
        })
        report.append(row)
        print(f"[{i}] {folder.name}: {row['status']} missing={len(missing)} extra={len(extra)}", flush=True)
        time.sleep(0.02)

    out = {"total_story_folders": len(report), "status_counts": dict(Counter(r["status"] for r in report)), "report": report}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OUT={OUT}")
    print(json.dumps(out["status_counts"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
