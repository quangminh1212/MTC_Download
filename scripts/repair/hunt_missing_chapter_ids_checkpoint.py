#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, r"C:\Dev\MTC_Download\scripts")
sys.path.insert(0, r"C:\Dev\MTC_Download\scripts\download")

from mtc_downloader import MTCDownloader
from download_completed_to_mtc import chapter_filename
from download_one_completed_live_decrypt import (
    maybe_decrypt,
    normalize_chapter_title,
    sanitize_path_component,
    write_plain_chapter,
)

ROOT = Path(r"C:\Dev\MTC_Continune")
TARGETS_PATH = Path(r"C:\Dev\MTC_Download\logs\remaining_missing_36_with_ids.json")
STATE_PATH = Path(r"C:\Dev\MTC_Download\logs\hunt_missing_state.json")
RESULT_PATH = Path(r"C:\Dev\MTC_Download\logs\hunt_missing_results.json")
CH_RE = re.compile(r"(?i)^chương\s+(\d+)")


def load_targets() -> list[dict]:
    rows = json.loads(TARGETS_PATH.read_text(encoding="utf-8"))
    out = []
    for row in rows:
        folder = row["folder"]
        book_id = int(row["book_id"])
        missing = [int(x) for x in row["missing"]]
        out.append({"folder": folder, "book_id": book_id, "missing": missing})
    return out


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"cursor": 0, "found": {}, "attempts": 0, "tried": {}}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_local_indexes(folder: Path) -> set[int]:
    out = set()
    for p in folder.glob("*.txt"):
        m = CH_RE.search(p.stem)
        if m:
            out.add(int(m.group(1)))
    return out


def write_chapter(folder: Path, chapter: dict, chapter_id: int) -> str:
    dl = MTCDownloader()
    detail = dl.get_chapter_content(chapter_id)
    data = (detail or {}).get("data") or {}
    content = data.get("content") or data.get("body") or ""
    if not content:
        raise ValueError("empty content")
    plain, _ = maybe_decrypt(content)
    idx = int(chapter.get("index") or chapter.get("number") or 0)
    title = normalize_chapter_title(data.get("name") or chapter.get("name") or f"Chương {idx}", idx)
    filename = sanitize_path_component(chapter_filename(data or chapter, idx))
    out = folder / filename
    write_plain_chapter(out, sanitize_path_component(title), plain)
    return out.name


def get_neighbors(info_chapters: list[dict], missing_index: int) -> tuple[tuple[int, int] | None, tuple[int, int] | None]:
    pairs = []
    for ch in info_chapters:
        try:
            idx = int(ch.get("index") or ch.get("number") or 0)
            cid = int(ch.get("id") or 0)
        except Exception:
            continue
        if idx > 0 and cid > 0:
            pairs.append((idx, cid))
    if not pairs:
        return None, None
    prev = None
    nxt = None
    for idx, cid in pairs:
        if idx < missing_index and (prev is None or idx > prev[0]):
            prev = (idx, cid)
        if idx > missing_index and (nxt is None or idx < nxt[0]):
            nxt = (idx, cid)
    return prev, nxt


def probe_window(dl: MTCDownloader, target_index: int, left_id: int, right_id: int, max_probe: int = 120) -> int | None:
    if left_id > right_id:
        left_id, right_id = right_id, left_id
    span = right_id - left_id
    if span <= 1:
        return None
    if span > max_probe:
        step = max(1, span // max_probe)
        candidates = range(left_id + 1, right_id, step)
    else:
        candidates = range(left_id + 1, right_id)
    for cid in candidates:
        try:
            data = (dl.get_chapter_content(cid) or {}).get("data") or {}
        except Exception:
            continue
        idx = data.get("index") or data.get("number")
        if isinstance(idx, int) and idx == target_index:
            return cid
        time.sleep(0.01)
    return None


def main() -> int:
    batch_books = int(os.getenv("HUNT_BATCH_BOOKS", "4"))
    max_seconds = int(os.getenv("HUNT_MAX_SECONDS", "480"))
    run_started = time.time()
    targets = load_targets()
    state = load_state()
    dl = MTCDownloader()

    start = int(state.get("cursor", 0))
    end = min(start + batch_books, len(targets))
    chunk = targets[start:end]
    print(f"processing books {start}..{end-1} / {len(targets)-1}", flush=True)

    for row in chunk:
        folder = ROOT / row["folder"]
        if not folder.exists():
            continue
        info_path = folder / "info.json"
        try:
            info = json.loads(info_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        info_chapters = info.get("chapters") or []
        missing = row["missing"]
        have = parse_local_indexes(folder)
        bid = int(row["book_id"])
        tried = state.setdefault("tried", {}).setdefault(str(bid), [])
        need = [m for m in missing if m not in have and m not in tried]
        if not need:
            continue

        print(f"book={bid} {row['folder']} need={len(need)}", flush=True)
        for m in need:
            if time.time() - run_started > max_seconds:
                save_state(state)
                RESULT_PATH.write_text(json.dumps(state.get("found", {}), ensure_ascii=False, indent=2), encoding="utf-8")
                print("time budget reached, checkpoint saved", flush=True)
                return 0
            prev, nxt = get_neighbors(info_chapters, m)
            if not prev or not nxt:
                continue
            cid = probe_window(dl, m, prev[1], nxt[1], max_probe=int(os.getenv("HUNT_MAX_PROBE", "40")))
            state["attempts"] = int(state.get("attempts", 0)) + 1
            tried.append(m)
            if not cid:
                save_state(state)
                continue
            try:
                ch = {"index": m, "id": cid, "name": f"Chương {m}"}
                filename = write_chapter(folder, ch, cid)
                key = f"{bid}:{m}"
                state.setdefault("found", {})[key] = {"chapter_id": cid, "file": filename}
                print(f"  FOUND idx={m} cid={cid} file={filename}", flush=True)
            except Exception:
                save_state(state)
                continue

        save_state(state)

    state["cursor"] = 0 if end >= len(targets) else end
    save_state(state)
    RESULT_PATH.write_text(json.dumps(state.get("found", {}), ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved state={STATE_PATH} found={len(state.get('found', {}))} attempts={state.get('attempts',0)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
