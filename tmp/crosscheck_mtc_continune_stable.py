from __future__ import annotations

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
TMP = Path(r"c:\Dev\MTC_Download\logs\mtc_continune_full_crosscheck.partial.json")
CHAP_RE = re.compile(r"(?i)(?:chương|chuong)\s*(\d+)")
IGNORE_DIRS = {".git", ".githooks", ".vscode", "git", ".claude"}


def local_indexes(folder: Path) -> list[int]:
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


def expected_from_info(info: dict) -> tuple[int | None, list[int]]:
    chapters = info.get("chapters") or []
    out = []
    for seq, chapter in enumerate(chapters, 1):
        try:
            idx = int(chapter.get("index") or chapter.get("number") or seq)
        except Exception:
            idx = seq
        if idx > 0:
            out.append(idx)
    out = sorted(set(out))
    book_id = info.get("id")
    try:
        book_id = int(book_id)
    except Exception:
        book_id = None
    return book_id, out


def fetch_remote_indexes(d: MTCDownloader, book_id: int, retries: int = 5) -> tuple[list[int], str | None]:
    page = 1
    seen_ids = set()
    out = []
    while True:
        data = None
        last_error = None
        for attempt in range(1, retries + 1):
            data = d.get_chapters(book_id, page=page, limit=500)
            arr = (data or {}).get("data") or []
            if data is not None:
                break
            last_error = f"page={page} attempt={attempt} failed"
            time.sleep(min(2.0, 0.4 * attempt))
        if data is None:
            return sorted(set(out)), last_error or f"page={page} failed"
        arr = (data or {}).get("data") or []
        if not arr:
            break

        new_on_page = 0
        for seq, c in enumerate(arr, 1):
            cid = c.get("id")
            if cid in seen_ids:
                continue
            seen_ids.add(cid)
            try:
                idx = int(c.get("index") or c.get("number") or seq)
            except Exception:
                idx = seq
            if idx > 0:
                out.append(idx)
                new_on_page += 1

        if len(arr) < 500:
            break
        if new_on_page == 0:
            break
        page += 1
        time.sleep(0.05)
    return sorted(set(out)), None


def save_partial(rows: list[dict]) -> None:
    payload = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_story_folders": len(rows),
        "status_counts": dict(Counter(r["status"] for r in rows)),
        "report": rows,
    }
    TMP.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    d = MTCDownloader()
    rows = []
    folders = [p for p in ROOT.iterdir() if p.is_dir() and p.name not in IGNORE_DIRS and (p / "info.json").is_file()]
    folders.sort(key=lambda p: p.name.lower())

    for i, folder in enumerate(folders, 1):
        lidx = local_indexes(folder)
        if not lidx:
            continue
        try:
            info = json.loads((folder / "info.json").read_text(encoding="utf-8"))
        except Exception as exc:
            row = {"folder": folder.name, "status": "bad_info_json", "error": str(exc), "local_count": len(lidx)}
            rows.append(row)
            save_partial(rows)
            print(f"[{i}] {folder.name}: bad_info_json", flush=True)
            continue

        book_id, info_idx = expected_from_info(info)
        row = {
            "folder": folder.name,
            "book_id": book_id,
            "book_name": info.get("name"),
            "local_count": len(lidx),
            "local_min": lidx[0],
            "local_max": lidx[-1],
            "info_count": len(info_idx),
            "info_max": info_idx[-1] if info_idx else 0,
        }
        if not book_id:
            row["status"] = "missing_book_id"
            rows.append(row)
            save_partial(rows)
            print(f"[{i}] {folder.name}: missing_book_id", flush=True)
            continue

        ridx, error = fetch_remote_indexes(d, book_id)
        row["remote_count"] = len(ridx)
        row["remote_max"] = ridx[-1] if ridx else 0
        if error and not ridx:
            row["status"] = "remote_error"
            row["error"] = error
            rows.append(row)
            save_partial(rows)
            print(f"[{i}] {folder.name}: remote_error {error}", flush=True)
            continue

        missing = sorted(set(ridx) - set(lidx))
        extra = sorted(set(lidx) - set(ridx))
        row["missing_count"] = len(missing)
        row["missing_first200"] = missing[:200]
        row["extra_count"] = len(extra)
        row["extra_first200"] = extra[:200]
        row["error"] = error
        row["status"] = "complete_vs_remote" if not missing and not extra else "mismatch_vs_remote"
        rows.append(row)
        save_partial(rows)
        print(f"[{i}] {folder.name}: {row['status']} missing={len(missing)} extra={len(extra)}", flush=True)

    out = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_story_folders": len(rows),
        "status_counts": dict(Counter(r["status"] for r in rows)),
        "report": rows,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OUT={OUT}")
    print(json.dumps(out["status_counts"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
