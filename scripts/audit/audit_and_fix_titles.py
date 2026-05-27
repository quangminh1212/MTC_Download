import html
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

from mtc_downloader import MTCDownloader

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\Dev\MTC")
OUT = Path(r"C:\Dev\MTC_Download\logs\mtc_title_and_count_audit.json")
IGNORE_DIRS = {".git", ".githooks", ".vscode", "git"}
INVALID = '<>:"/\\|?*!'
STRIP_PUNCT_RE = re.compile(r"[\(\)\[\]\{\}\+,\-–—]+")
WS_RE = re.compile(r"\s+")
TITLELESS_RE = re.compile(r"^(?i:chương|chuong)\s+(\d+)\.txt$")
CHAP_RE = re.compile(r"(?i)(?:chương|chuong)\s*(\d+)")
CHAPTER_PREFIX_RE = re.compile(r"^\s*(?:chương|chuong)\s*\d+\s*[:.\-–—]?\s*", re.I)


def clean_filename(name: str, max_len: int = 170) -> str:
    name = html.unescape(str(name or "")).strip()
    name = STRIP_PUNCT_RE.sub(" ", name)
    for ch in INVALID:
        name = name.replace(ch, " ")
    name = WS_RE.sub(" ", name).strip(" .")
    return (name or "Untitled")[:max_len].strip(" .")


def norm(name: str) -> str:
    return clean_filename(name, 170).lower()


def get_all_books(d: MTCDownloader) -> list[dict]:
    books = []
    page = 1
    while True:
        data = d.get_books(limit=100, page=page)
        rows = (data or {}).get("data") or []
        if not rows:
            break
        books.extend(rows)
        if len(rows) < 100:
            break
        page += 1
        time.sleep(0.1)
    return books


def get_all_chapters(d: MTCDownloader, book_id: int) -> list[dict]:
    rows = []
    page = 1
    while True:
        data = d.get_chapters(book_id, page=page, limit=500)
        arr = (data or {}).get("data") or []
        if not arr:
            break
        rows.extend(arr)
        if len(arr) < 500:
            break
        page += 1
        time.sleep(0.05)
    return rows


def local_index_map(folder: Path):
    mp = {}
    for p in folder.glob("*.txt"):
        m = CHAP_RE.search(p.name)
        if not m:
            continue
        try:
            idx = int(m.group(1))
        except Exception:
            continue
        mp.setdefault(idx, []).append(p)
    return mp


def choose_book(cands: list[dict], local_unique_count: int):
    if len(cands) == 1:
        return cands[0]
    def score(b):
        expected = int(b.get("chapter_count") or b.get("latest_index") or 0)
        return abs(expected - local_unique_count)
    return sorted(cands, key=score)[0]


def main():
    d = MTCDownloader()
    books = get_all_books(d)
    by_norm = {}
    for b in books:
        by_norm.setdefault(norm(b.get("name") or ""), []).append(b)

    report = []

    for folder in sorted([p for p in ROOT.iterdir() if p.is_dir() and p.name not in IGNORE_DIRS], key=lambda p: p.name.lower()):
        local_map = local_index_map(folder)
        if not local_map:
            continue
        local_idxs = sorted(local_map)
        local_count = len(local_idxs)
        row = {
            "folder": folder.name,
            "local_unique_indexes": local_count,
            "local_file_count": sum(len(v) for v in local_map.values()),
        }
        cands = by_norm.get(norm(folder.name), [])
        if not cands:
            row["status"] = "unmatched_remote"
            row["titleless_files"] = [p.name for arr in local_map.values() for p in arr if TITLELESS_RE.match(p.name)]
            report.append(row)
            continue

        book = choose_book(cands, local_count)
        chapters = get_all_chapters(d, int(book["id"]))
        remote = {}
        for i, ch in enumerate(chapters, 1):
            try:
                idx = int(ch.get("index") or ch.get("number") or i)
            except Exception:
                idx = i
            remote[idx] = ch
        remote_idxs = sorted(remote)
        missing = sorted(set(remote_idxs) - set(local_idxs))
        extra = sorted(set(local_idxs) - set(remote_idxs))
        titleless = []
        retitled = []
        retitle_conflicts = []

        for idx, files in sorted(local_map.items()):
            for p in files:
                if not TITLELESS_RE.match(p.name):
                    continue
                titleless.append(p.name)
                ch = remote.get(idx)
                if not ch:
                    continue
                raw = ch.get("name") or ch.get("title") or ""
                title = CHAPTER_PREFIX_RE.sub("", str(raw)).strip(" :.\u2013\u2014-")
                title = clean_filename(title, 130)
                if not title or title == "Untitled":
                    continue
                new_name = f"Chương {idx} {title}.txt"
                dst = p.with_name(new_name)
                if dst.exists() and dst.resolve() != p.resolve():
                    retitle_conflicts.append({"src": p.name, "dst": new_name})
                    continue
                p.rename(dst)
                retitled.append({"from": p.name, "to": new_name})

        row.update({
            "book_id": int(book["id"]),
            "book_name": book.get("name"),
            "remote_count": len(remote_idxs),
            "missing_count": len(missing),
            "missing_first50": missing[:50],
            "extra_count": len(extra),
            "extra_first50": extra[:50],
            "titleless_count_before": len(titleless),
            "retitled_count": len(retitled),
            "retitle_conflicts": retitle_conflicts,
        })
        remaining_titleless = [p.name for arr in local_index_map(folder).values() for p in arr if TITLELESS_RE.match(p.name)]
        row["titleless_count_after"] = len(remaining_titleless)
        row["titleless_remaining_first50"] = remaining_titleless[:50]

        if not missing and not extra and not remaining_titleless:
            row["status"] = "complete_with_titles"
        elif not missing and not extra:
            row["status"] = "complete_but_titleless_remaining"
        else:
            row["status"] = "mismatch_or_missing"
        report.append(row)

    out = {
        "status_counts": dict(Counter(r["status"] for r in report)),
        "report": report,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUT)
    print(json.dumps(out["status_counts"], ensure_ascii=False))


if __name__ == "__main__":
    main()
