import json
import sys
import time
from pathlib import Path

sys.path.insert(0, r"C:\Dev\MTC_Download")
from download_completed_to_mtc import MTCDownloader, chapter_filename, write_chapter  # type: ignore

BOOK_ID = 100677
BOOK_DIR = Path(r"C:\Dev\MTC\Công Cuộc Bị 999 Em Gái Chinh Phục")
MISSING = {29, 127, 403, 404, 407}
OUT = Path(r"C:\Dev\MTC_Download\logs\repair_cong_cuoc_999_missing.json")


def get_all_chapters(d: MTCDownloader, book_id: int):
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


def main():
    d = MTCDownloader()
    detail = (d.get_book_detail(BOOK_ID) or {}).get("data") or {}
    chapters = get_all_chapters(d, BOOK_ID)
    by_idx = {}
    for i, ch in enumerate(chapters, 1):
        try:
            idx = int(ch.get("index") or ch.get("number") or i)
        except Exception:
            idx = i
        by_idx[idx] = ch

    actions = []
    for idx in sorted(MISSING):
        ch = by_idx.get(idx)
        if not ch:
            actions.append({"chapter": idx, "status": "remote_missing_index"})
            continue
        cid = ch.get("id")
        data = (d.get_chapter_content(cid) or {}).get("data") or {}
        content = data.get("content") or data.get("body") or ""
        if not content:
            actions.append({"chapter": idx, "chapter_id": cid, "status": "no_content"})
            continue
        fname = chapter_filename(ch, idx)
        path = BOOK_DIR / fname
        display_name = data.get("name") or ch.get("name") or f"Chương {idx}"
        write_chapter(path, detail.get("name") or BOOK_DIR.name, display_name, content)
        actions.append({"chapter": idx, "chapter_id": cid, "status": "written", "file": str(path.name), "size": path.stat().st_size})
        time.sleep(0.1)

    OUT.write_text(json.dumps(actions, ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUT)
    print(json.dumps(actions, ensure_ascii=False))


if __name__ == "__main__":
    main()
