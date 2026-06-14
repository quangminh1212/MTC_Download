from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, r"C:\Dev\mtc_download\scripts")
sys.path.insert(0, r"C:\Dev\mtc_download\scripts\download")

from download_top5_bookmarks_to_mtc import login_with_retry, get_json, BASE
from download_one_completed_live_decrypt import (
    maybe_decrypt,
    normalize_chapter_title,
    sanitize_path_component,
    write_plain_chapter,
    chapter_filename,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BODY_MIN_CHARS = 1200


def find_story_dir(root: Path, needle: str) -> Path:
    exact = root / needle
    if exact.is_dir():
        return exact
    lowered = needle.casefold()
    for item in root.iterdir():
        if item.is_dir() and item.name.casefold() == lowered:
            return item
    for item in root.iterdir():
        if item.is_dir() and lowered in item.name.casefold():
            return item
    raise FileNotFoundError(f"story dir not found: {needle}")


def get_chapters(session, book_id: int) -> list[dict]:
    page = 1
    seen = set()
    rows: list[dict] = []
    while True:
        payload = get_json(session, BASE + "/chapters", params={"filter[book_id]": book_id, "page": page, "limit": 100})
        data = payload.get("data") or []
        if not data:
            break
        for row in data:
            cid = row.get("id")
            if cid in seen:
                continue
            seen.add(cid)
            rows.append(row)
        if len(data) < 100:
            break
        page += 1
        time.sleep(0.1)
    rows.sort(key=lambda row: int(row.get("index") or row.get("number") or 0))
    return rows


def body_len_from_file(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return 0
    lines = text.splitlines()
    body = "\n".join(lines[4:]).strip() if len(lines) > 4 else ""
    return len(body)


def should_repair(path: Path) -> bool:
    return body_len_from_file(path) < BODY_MIN_CHARS


def fetch_detail(session, chapter_id: int) -> dict:
    payload = get_json(session, BASE + f"/chapters/{chapter_id}")
    return payload.get("data") or {}


def repair_story(root: Path, story_name: str, delay: float = 0.1, limit: int | None = None) -> dict:
    email = os.environ.get("MTC_EMAIL")
    password = os.environ.get("MTC_PASS")
    if not email or not password:
        raise RuntimeError("Missing MTC_EMAIL or MTC_PASS environment variables")

    story_dir = find_story_dir(root, story_name)
    info_path = story_dir / "info.json"
    info = json.loads(info_path.read_text(encoding="utf-8"))
    book_id = int(info["id"])

    session, _token = login_with_retry(email, password)
    remote_chapters = get_chapters(session, book_id)
    remote_by_index = {int(row.get("index") or row.get("number") or 0): row for row in remote_chapters}

    repaired = []
    skipped = []
    failed = []

    for chapter in info.get("chapters", []):
        idx = int(chapter.get("index") or 0)
        if idx <= 0:
            continue
        file_name = chapter_filename(chapter, idx)
        path = story_dir / sanitize_path_component(file_name)
        if not should_repair(path):
            skipped.append(idx)
            continue
        remote = remote_by_index.get(idx)
        if not remote:
            failed.append({"index": idx, "error": "missing_remote_index"})
            continue
        chapter_id = int(remote["id"])
        try:
            detail = fetch_detail(session, chapter_id)
            content = detail.get("content") or detail.get("body") or ""
            if not content:
                raise ValueError("empty content")
            plain, decrypted = maybe_decrypt(content)
            title = normalize_chapter_title(detail.get("name") or remote.get("name") or chapter.get("name") or f"Chương {idx}", idx)
            write_plain_chapter(path, sanitize_path_component(title), plain)
            repaired.append({
                "index": idx,
                "chapter_id": chapter_id,
                "file": path.name,
                "chars": body_len_from_file(path),
                "decrypted": decrypted,
                "is_locked": detail.get("is_locked"),
            })
            print(f"repaired idx={idx} file={path.name} chars={repaired[-1]['chars']} locked={detail.get('is_locked')}", flush=True)
        except Exception as exc:
            failed.append({"index": idx, "chapter_id": chapter_id, "error": str(exc)})
            print(f"failed idx={idx} chapter_id={chapter_id} error={exc}", flush=True)
        if limit is not None and len(repaired) >= limit:
            break
        time.sleep(delay)

    return {
        "story_dir": str(story_dir),
        "book_id": book_id,
        "story_name": info.get("name"),
        "repaired": repaired,
        "skipped": len(skipped),
        "failed": failed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("story_name")
    parser.add_argument("--root", default=r"C:\Dev\MTC_Continune")
    parser.add_argument("--delay", type=float, default=0.1)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--report", default=None)
    args = parser.parse_args()

    report = repair_story(Path(args.root), args.story_name, delay=args.delay, limit=args.limit)
    if args.report:
        Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"report={args.report}")
    print(json.dumps({
        "story_name": report["story_name"],
        "repaired": len(report["repaired"]),
        "skipped": report["skipped"],
        "failed": len(report["failed"]),
    }, ensure_ascii=False))
    return 0 if not report["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
