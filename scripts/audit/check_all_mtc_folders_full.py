import json
import re
import html
import time
import sys
from pathlib import Path
from collections import Counter

from mtc_downloader import MTCDownloader

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Dev\MTC")
OUT = Path(r"C:\Dev\MTC_Download\logs\mtc_full_crosscheck_after_sanitize.json")

INVALID = '<>:"/\\|?*!'
STRIP_PUNCT_RE = re.compile(r"[\(\)\[\]\{\}\+,\-–—]+")
WS_RE = re.compile(r"\s+")
CHAP_RE = re.compile(r"(?i)(?:chương|chuong)\s*(\d+)")

IGNORE_DIRS = {".git", ".githooks", ".vscode", "git"}


def norm(name: str) -> str:
    s = html.unescape(str(name or "")).strip()
    s = STRIP_PUNCT_RE.sub(" ", s)
    for ch in INVALID:
        s = s.replace(ch, " ")
    s = WS_RE.sub(" ", s).strip(" .").lower()
    return s


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
        time.sleep(0.1)
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
        time.sleep(0.08)
    return sorted(set(out))


def local_indexes(folder: Path):
    seen = set()
    for p in folder.glob("*.txt"):
        m = CHAP_RE.search(p.name)
        if not m:
            continue
        try:
            seen.add(int(m.group(1)))
        except Exception:
            pass
    return sorted(seen)


def choose_book(cands: list[dict], local_count: int):
    if len(cands) == 1:
        return cands[0]
    def score(b):
        expected = int(b.get("chapter_count") or b.get("latest_index") or 0)
        return abs(expected - local_count)
    return sorted(cands, key=score)[0]


def main():
    d = MTCDownloader()
    books = get_all_books(d)

    by_norm = {}
    for b in books:
        key = norm(b.get("name") or "")
        if not key:
            continue
        by_norm.setdefault(key, []).append(b)

    report = []
    folders = [p for p in ROOT.iterdir() if p.is_dir() and p.name not in IGNORE_DIRS]
    folders.sort(key=lambda p: p.name.lower())

    for i, folder in enumerate(folders, 1):
        lidx = local_indexes(folder)
        if not lidx:
            # skip non-story directory
            continue
        key = norm(folder.name)
        cands = by_norm.get(key, [])
        row = {
            "folder": folder.name,
            "local_count": len(lidx),
            "local_min": lidx[0] if lidx else None,
            "local_max": lidx[-1] if lidx else None,
        }
        if not cands:
            row["status"] = "unmatched_remote"
            report.append(row)
            print(f"[{i}] {folder.name}: unmatched_remote")
            continue

        b = choose_book(cands, len(lidx))
        bid = int(b.get("id"))
        ridx = get_remote_indexes(d, bid)
        rset = set(ridx)
        lset = set(lidx)

        missing = sorted(rset - lset)
        extra = sorted(lset - rset)

        row.update({
            "book_id": bid,
            "book_name": b.get("name"),
            "remote_count": len(ridx),
            "remote_max": ridx[-1] if ridx else 0,
            "missing_count": len(missing),
            "missing_first200": missing[:200],
            "extra_count": len(extra),
            "extra_first200": extra[:200],
        })
        if not missing and not extra:
            row["status"] = "complete_vs_remote"
        else:
            row["status"] = "mismatch_vs_remote"

        report.append(row)
        print(f"[{i}] {folder.name}: {row['status']} missing={len(missing)} extra={len(extra)}")
        time.sleep(0.05)

    counts = Counter(r["status"] for r in report)
    out = {
        "total_story_folders": len(report),
        "status_counts": dict(counts),
        "report": report,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUT)
    print(json.dumps(out["status_counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
