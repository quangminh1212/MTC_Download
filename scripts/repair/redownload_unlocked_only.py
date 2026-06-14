from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, r"C:\Dev\mtc_download\scripts")
sys.path.insert(0, r"C:\Dev\mtc_download\scripts\download")

from download_top5_bookmarks_to_mtc import BASE, get_json, login_with_retry
from download_one_completed_live_decrypt import maybe_decrypt, normalize_chapter_title, sanitize_path_component, write_plain_chapter, chapter_filename

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BODY_MIN = 1200


def body_len(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return 0
    lines = text.splitlines()
    body = "\n".join(lines[4:]).strip() if len(lines) > 4 else ""
    return len(body)


def story_dir(root: Path, story: str) -> Path:
    path = root / story
    if not path.is_dir():
        raise FileNotFoundError(path)
    return path


def remote_chapters(session, book_id: int) -> list[dict]:
    rows = []
    seen = set()
    page = 1
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


def repair_story(root: Path, story: str, delay: float, report_path: Path | None = None) -> dict:
    email = os.environ.get("MTC_EMAIL")
    password = os.environ.get("MTC_PASS")
    if not email or not password:
        raise RuntimeError("Set MTC_EMAIL and MTC_PASS first")

    folder = story_dir(root, story)
    info = json.loads((folder / "info.json").read_text(encoding="utf-8"))
    session, _token = login_with_retry(email, password)
    remote = {int(row.get("index") or row.get("number") or 0): row for row in remote_chapters(session, int(info["id"]))}

    repaired, skipped, locked, failed = [], 0, [], []
    for chapter in info.get("chapters", []):
        idx = int(chapter.get("index") or 0)
        if idx <= 0:
            continue
        path = folder / sanitize_path_component(chapter_filename(chapter, idx))
        if body_len(path) >= BODY_MIN:
            skipped += 1
            continue
        row = remote.get(idx)
        if not row:
            failed.append({"index": idx, "error": "missing_remote_row"})
            continue
        detail = (get_json(session, BASE + f"/chapters/{row['id']}") or {}).get("data") or {}
        if detail.get("is_locked") not in (0, None) or int(detail.get("unlock_price") or 0) > 0 or int(detail.get("unlock_key_price") or 0) > 0:
            locked.append({"index": idx, "chapter_id": row["id"], "name": detail.get("name") or row.get("name")})
            continue
        content = detail.get("content") or detail.get("body") or ""
        if not content:
            failed.append({"index": idx, "chapter_id": row["id"], "error": "empty_content"})
            continue
        plain, _ = maybe_decrypt(content)
        title = normalize_chapter_title(detail.get("name") or row.get("name") or chapter.get("name") or f"Chương {idx}", idx)
        write_plain_chapter(path, sanitize_path_component(title), plain)
        repaired.append({"index": idx, "chapter_id": row["id"], "file": path.name, "chars": body_len(path)})
        print(f"repaired idx={idx} file={path.name} chars={repaired[-1]['chars']}", flush=True)
        time.sleep(delay)

    report = {
        "story": story,
        "book_id": info.get("id"),
        "repaired": repaired,
        "skipped_ok": skipped,
        "locked": locked,
        "failed": failed,
    }
    if report_path:
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"story": story, "repaired": len(repaired), "locked": len(locked), "failed": len(failed), "skipped_ok": skipped}, ensure_ascii=False))
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("story")
    ap.add_argument("--root", default=r"C:\Dev\MTC_Continune")
    ap.add_argument("--delay", type=float, default=0.1)
    ap.add_argument("--report", default=None)
    args = ap.parse_args()
    report = repair_story(Path(args.root), args.story, args.delay, Path(args.report) if args.report else None)
    return 0 if not report["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
