#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures as cf
import html
import json
import re
import sys
import threading
import time
import unicodedata
from pathlib import Path

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://android.lonoapp.net/api"
REPO = Path(r"C:\Dev\MTC_Continune")
LOG_DIR = Path(r"C:\Dev\MTC_Download\logs")
STATE = LOG_DIR / "unfinished_id_scan_state.json"
OUT = LOG_DIR / "all_id_unfinished_scan.json"
MISSING = LOG_DIR / "all_id_unfinished_missing_repo.json"

_thread_local = threading.local()


def session() -> requests.Session:
    current = getattr(_thread_local, "session", None)
    if current is None:
        current = requests.Session()
        current.headers.update({"User-Agent": "MTC/Android", "Accept": "application/json"})
        _thread_local.session = current
    return current


def norm(value: object) -> str:
    text = unicodedata.normalize("NFC", html.unescape(str(value or ""))).casefold()
    return "".join(ch for ch in text if ch.isalnum())


def clean(value: object, default: str = "Untitled") -> str:
    text = unicodedata.normalize("NFC", html.unescape(str(value or "")))
    text = "".join(ch if (ch.isalnum() or ch.isspace()) else " " for ch in text)
    text = re.sub(r"\s+", " ", text).strip(" .")
    return text or default


def local_norms() -> set[str]:
    return {norm(path.name) for path in REPO.iterdir() if path.is_dir() and path.name != ".git"}


def scan_one(book_id: int) -> dict | None:
    try:
        response = session().get(
            BASE + "/chapters",
            params={"filter[book_id]": book_id, "limit": 1, "page": 1},
            timeout=8,
        )
        if response.status_code != 200:
            return None
        payload = response.json()
        book = (payload.get("extra") or {}).get("book") or {}
        if not book:
            return None
        status = int(book.get("status") or 0)
        latest = int(book.get("latest_index") or book.get("chapter_count") or 0)
        if status == 2 or latest <= 0:
            return None
        name = book.get("name") or f"book {book_id}"
        return {
            "id": int(book.get("id") or book_id),
            "name": name,
            "status": status,
            "status_name": book.get("status_name"),
            "chapter_count": latest,
            "folder": clean(name),
        }
    except Exception as exc:
        return {"id": book_id, "error": str(exc)[:160]}


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"scanned_blocks": [], "items": [], "errors": []}


def save_outputs(state: dict) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    seen: dict[int, dict] = {}
    for item in state.get("items", []):
        seen[int(item["id"])] = item
    items = [seen[key] for key in sorted(seen)]
    norms = local_norms()
    for item in items:
        item["has_local"] = norm(item.get("folder")) in norms
    missing = [item for item in items if not item.get("has_local")]
    state["items"] = items
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT.write_text(
        json.dumps(
            {
                "found": len(items),
                "errors": len(state.get("errors", [])),
                "items": items,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    MISSING.write_text(json.dumps(missing, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=100000)
    parser.add_argument("--end", type=int, default=154000)
    parser.add_argument("--block-size", type=int, default=2000)
    parser.add_argument("--workers", type=int, default=32)
    args = parser.parse_args()

    state = load_state()
    done = {tuple(block) for block in state.get("scanned_blocks", [])}
    started = time.time()
    for block_start in range(args.start, args.end + 1, args.block_size):
        block_end = min(args.end, block_start + args.block_size - 1)
        block_key = (block_start, block_end)
        if block_key in done:
            print(f"skip block={block_start}-{block_end}", flush=True)
            continue
        ids = list(range(block_start, block_end + 1))
        found = []
        errors = []
        with cf.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
            for row in pool.map(scan_one, ids):
                if not row:
                    continue
                if row.get("error"):
                    errors.append(row)
                else:
                    found.append(row)
        state.setdefault("items", []).extend(found)
        state.setdefault("errors", []).extend(errors)
        state.setdefault("scanned_blocks", []).append([block_start, block_end])
        save_outputs(state)
        print(
            f"block={block_start}-{block_end} found={len(found)} "
            f"errors={len(errors)} total_found={len(state['items'])} "
            f"elapsed={round(time.time() - started, 1)}s",
            flush=True,
        )
    save_outputs(state)
    missing = json.loads(MISSING.read_text(encoding="utf-8"))
    print(f"found_unfinished={len(state.get('items', []))}")
    print(f"missing_repo={len(missing)}")
    print(f"missing_chapters={sum(int(item.get('chapter_count') or 0) for item in missing)}")
    print(f"missing_report={MISSING}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
