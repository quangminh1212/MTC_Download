#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check status of all bookmarked books and save a summary."""
import json
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "logs"
BASE = "https://android.lonoapp.net/api"

if len(sys.argv) < 3:
    raise SystemExit("usage: python check_bookmark_statuses.py <email> <password>")

email, password = sys.argv[1], sys.argv[2]

session = requests.Session()
session.headers.update({"User-Agent": "MTC/Android", "Accept": "application/json", "Content-Type": "application/json"})
r = session.post(BASE + "/auth/login", json={"email": email, "password": password, "device_name": "OpenClaw Windows"}, timeout=30)
r.encoding = "utf-8"
r.raise_for_status()
token = r.json()["data"]["token"]
session.headers.update({"Authorization": f"Bearer {token}"})

manifest = json.loads((LOGS / "bookmarked_books_manifest.json").read_text(encoding="utf-8"))
books = manifest["books"]

completed = []
ongoing = []
paused = []
unknown = []
errors = []
for i, book in enumerate(books, 1):
    bid = int(book["id"])
    try:
        r = session.get(f"{BASE}/books/{bid}", timeout=15)
        r.encoding = "utf-8"
        r.raise_for_status()
        data = r.json().get("data", {})
        status_name = str(data.get("status_name") or "").lower()
        status = data.get("status")
        if status == 2 or status_name in {"hoàn thành", "hoan thanh", "completed", "full", "finished"}:
            completed.append(bid)
        elif status == 3 or status_name in {"tạm dừng", "tam dung", "paused", "hiatus"}:
            paused.append(bid)
        elif status == 1 or status_name in {"còn tiếp", "con tiep", "ongoing", "serializing"}:
            ongoing.append(bid)
        else:
            unknown.append((bid, status_name, status))
    except Exception as exc:
        errors.append((bid, str(exc)[:200]))
    if i % 50 == 0:
        print(f"checked {i}/{len(books)}: completed={len(completed)} ongoing={len(ongoing)} paused={len(paused)} unknown={len(unknown)} errors={len(errors)}", flush=True)
    time.sleep(0.05)

out = {
    "total": len(books),
    "completed": len(completed),
    "ongoing": len(ongoing),
    "paused": len(paused),
    "unknown": len(unknown),
    "errors": len(errors),
    "completed_ids": completed,
    "ongoing_ids": ongoing,
    "paused_ids": paused,
    "unknown_items": unknown,
    "error_items": errors,
}
(LOGS / "bookmark_statuses.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("summary", out)
