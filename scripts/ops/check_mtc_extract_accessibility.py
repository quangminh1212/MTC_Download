#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check how many books in mtc_extract_discovered_books.json are reachable on the live API."""
import json
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "logs"
OUT = LOGS / "mtc_extract_accessibility_check.json"

session = requests.Session()
session.headers.update({
    "User-Agent": "MTC/Android",
    "Accept": "application/json",
    "Content-Type": "application/json",
})
session.mount("https://", requests.adapters.HTTPAdapter(max_retries=0))
session.mount("http://", requests.adapters.HTTPAdapter(max_retries=0))

books = json.loads((LOGS / "mtc_extract_discovered_books.json").read_text(encoding="utf-8"))["books"]

results = []
ok = not_found = forbidden = error = 0
for i, book in enumerate(books, 1):
    bid = int(book["id"])
    detail_status = None
    chapters_status = None
    try:
        r = session.get(f"https://android.lonoapp.net/api/books/{bid}", timeout=8)
        detail_status = r.status_code
        if r.status_code == 200:
            ok += 1
            status = "ok"
        elif r.status_code == 404:
            status = "not_found"
            not_found += 1
        elif r.status_code == 403:
            status = "forbidden"
            forbidden += 1
        else:
            status = f"http_{r.status_code}"
            error += 1
    except Exception as exc:
        status = f"err_{type(exc).__name__}"
        error += 1

    if status != "ok":
        try:
            r = session.get(
                "https://android.lonoapp.net/api/chapters",
                params={"filter[book_id]": bid, "page": 1, "limit": 10},
                timeout=8,
            )
            chapters_status = r.status_code
            if r.status_code == 200 and r.json().get("data"):
                status = "chapters_only"
        except Exception:
            pass

    results.append({
        "id": bid,
        "name": book.get("name"),
        "status": status,
        "detail_status": detail_status,
        "chapters_status": chapters_status,
    })
    if i % 50 == 0:
        print(f"progress {i}/{len(books)} ok={ok} not_found={not_found} forbidden={forbidden} error={error}", flush=True)
    time.sleep(0.05)

summary = {
    "total": len(books),
    "ok": ok,
    "not_found": not_found,
    "forbidden": forbidden,
    "error": error,
    "by_status": {},
}
for r in results:
    summary["by_status"][r["status"]] = summary["by_status"].get(r["status"], 0) + 1

OUT.write_text(json.dumps({"summary": summary, "books": results}, ensure_ascii=False, indent=2), encoding="utf-8")
print("summary", summary)
print("saved", OUT)
