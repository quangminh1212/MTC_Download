import html
import json
import re
import sys
import time
from pathlib import Path

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://android.lonoapp.net/api"
ROOT = Path(r"C:\Dev\MTC")
BOOK_DIR = ROOT / "Kỹ Năng Đổi Một Chữ Bọn Hắn Bị Ta Chơi Hỏng"
BOOK_ID = int(json.loads((BOOK_DIR / "info.json").read_text(encoding="utf-8"))["id"])
OUT = Path(r"C:\Dev\MTC_Download\logs\repair_ky_nang_doi_mot_chu_v2.json")

INVALID = '<>:"/\\|?*!'
STRIP_RE = re.compile(r"[\(\)\[\]\{\}\+,\-–—]+")
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"[ \t\r\f\v]+")
FILE_CHAP_RE = re.compile(r"(?i)(?:chương|chuong)\s*(\d+)")
TITLE_CHAP_RE = re.compile(r"^\s*(?:chương|chuong)\s*\d+\s*[:.\-–—]?\s*", re.I)


def clean_filename(s, max_len=170):
    s = html.unescape(str(s or "")).strip()
    s = STRIP_RE.sub(" ", s)
    for ch in INVALID:
        s = s.replace(ch, " ")
    s = re.sub(r"\s+", " ", s).strip(" .")
    return (s or "Untitled")[:max_len].strip(" .")


def clean_text(value):
    text = html.unescape(str(value or ""))
    text = text.replace("<br />", "\n").replace("<br/>", "\n").replace("<br>", "\n")
    text = re.sub(r"</p\s*>", "\n\n", text, flags=re.I)
    text = TAG_RE.sub("", text)
    lines = [WS_RE.sub(" ", line).strip() for line in text.splitlines()]
    out=[]; blanks=0
    for line in lines:
        if line:
            blanks=0; out.append(line)
        else:
            blanks += 1
            if blanks <= 1: out.append("")
    return "\n".join(out).strip()+"\n"


def local_indexes():
    nums=set()
    for p in BOOK_DIR.glob("*.txt"):
        m=FILE_CHAP_RE.search(p.name)
        if m: nums.add(int(m.group(1)))
    return nums


def fname_for(ch, idx):
    raw = ch.get("name") or ch.get("title") or ""
    title = TITLE_CHAP_RE.sub("", str(raw)).strip(" :.\u2013\u2014-")
    title = clean_filename(title, 130)
    return f"Chương {idx} {title}.txt" if title and title != "Untitled" else f"Chương {idx}.txt"


def main():
    s = requests.Session()
    s.headers.update({"User-Agent":"MTC/Android", "Accept":"application/json"})
    r=s.get(f"{BASE}/chapters", params={"filter[book_id]":BOOK_ID,"page":1,"limit":5000}, timeout=30)
    r.raise_for_status()
    chapters=r.json().get("data") or []
    present=local_indexes()
    actions=[]
    for pos,ch in enumerate(chapters,1):
        idx=int(ch.get("index") or ch.get("number") or pos)
        if idx in present:
            continue
        cid=ch.get("id")
        rr=s.get(f"{BASE}/chapters/{cid}", timeout=30)
        rr.raise_for_status()
        data=rr.json().get("data") or {}
        content=data.get("content") or data.get("body") or ""
        if not content:
            actions.append({"idx":idx,"id":cid,"status":"empty"}); continue
        fname=fname_for(ch, idx)
        path=BOOK_DIR/fname
        display=data.get("name") or ch.get("name") or f"Chương {idx}"
        path.write_text(f"{'='*60}\n{display}\n{'='*60}\n\n"+clean_text(content), encoding="utf-8")
        actions.append({"idx":idx,"id":cid,"status":"written","file":fname,"size":path.stat().st_size})
        print("written", idx, fname)
        time.sleep(0.05)
    OUT.write_text(json.dumps(actions, ensure_ascii=False, indent=2), encoding="utf-8")
    print("DONE", len(actions), OUT)

if __name__ == "__main__":
    main()
