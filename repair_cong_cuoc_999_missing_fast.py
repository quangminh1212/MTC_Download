import html
import json
import re
import time
from pathlib import Path

import requests

BASE = "https://android.lonoapp.net/api"
BOOK_ID = 100677
BOOK_DIR = Path(r"C:\Dev\MTC\Công Cuộc Bị 999 Em Gái Chinh Phục")
MISSING = {29, 127, 403, 404, 407}
OUT = Path(r"C:\Dev\MTC_Download\logs\repair_cong_cuoc_999_missing_fast.json")

INVALID = '<>:"/\\|?*!'
STRIP_PUNCT_RE = re.compile(r"[\(\)\[\]\{\}\+,\-–—]+")
WS_RE = re.compile(r"[ \t\r\f\v]+")
TAG_RE = re.compile(r"<[^>]+>")
CHAPTER_PREFIX_RE = re.compile(r"^\s*(?:chương|chuong)\s*\d+\s*[:.\-–—]?\s*", re.I)


def clean_filename(name: str, max_len: int = 170) -> str:
    name = html.unescape(str(name or "")).strip()
    name = STRIP_PUNCT_RE.sub(" ", name)
    for ch in INVALID:
        name = name.replace(ch, " ")
    name = re.sub(r"\s+", " ", name).strip(" .")
    return (name or "Untitled")[:max_len].strip(" .")


def clean_text(value):
    text = html.unescape(str(value or ""))
    text = text.replace("<br />", "\n").replace("<br/>", "\n").replace("<br>", "\n")
    text = re.sub(r"</p\s*>", "\n\n", text, flags=re.I)
    text = TAG_RE.sub("", text)
    lines = []
    for line in text.splitlines():
        lines.append(WS_RE.sub(" ", line).strip())
    out = []
    blanks = 0
    for line in lines:
        if line:
            blanks = 0
            out.append(line)
        else:
            blanks += 1
            if blanks <= 1:
                out.append("")
    return "\n".join(out).strip() + "\n"


def chapter_filename(chapter, idx):
    raw = chapter.get("name") or chapter.get("title") or ""
    title = CHAPTER_PREFIX_RE.sub("", str(raw)).strip(" :.\u2013\u2014-")
    title = clean_filename(title, 130)
    return f"Chương {idx} {title}.txt" if title and title != "Untitled" else f"Chương {idx}.txt"


def main():
    s = requests.Session()
    s.headers.update({"User-Agent": "MTC/Android", "Accept": "application/json"})
    chapters = []
    page = 1
    while True:
        r = s.get(f"{BASE}/chapters", params={"filter[book_id]": BOOK_ID, "page": page, "limit": 100}, timeout=20)
        r.raise_for_status()
        arr = r.json().get("data") or []
        chapters.extend(arr)
        print("page", page, "got", len(arr))
        if len(arr) < 100:
            break
        page += 1
        time.sleep(0.05)
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
            actions.append({"chapter": idx, "status": "not_in_remote_list"})
            continue
        cid = ch.get("id")
        r = s.get(f"{BASE}/chapters/{cid}", timeout=20)
        r.raise_for_status()
        data = r.json().get("data") or {}
        content = data.get("content") or data.get("body") or ""
        if not content:
            actions.append({"chapter": idx, "chapter_id": cid, "status": "empty_content"})
            continue
        fname = chapter_filename(ch, idx)
        path = BOOK_DIR / fname
        display_name = data.get("name") or ch.get("name") or f"Chương {idx}"
        body = clean_text(content)
        header = f"{'='*60}\n{display_name}\n{'='*60}\n\n"
        path.write_text(header + body, encoding="utf-8")
        actions.append({"chapter": idx, "chapter_id": cid, "status": "written", "file": fname, "size": path.stat().st_size})
        time.sleep(0.05)
    OUT.write_text(json.dumps(actions, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(actions, ensure_ascii=False))


if __name__ == "__main__":
    main()
