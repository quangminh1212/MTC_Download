#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import json, re, sys, time, unicodedata
from pathlib import Path
sys.path.insert(0, r"C:\Dev\MTC_DOWNLOAD")
from mtc_downloader import MTCDownloader
from download_one_completed_live_decrypt import get_chapters_once_safe
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"C:\Dev\MTC")
OUT = Path("C:/Dev/MTC_DOWNLOAD/logs/full_library_chapter_audit_v2.json")
IGNORE = {".git", ".githooks", ".vscode", "__pycache__"}

def norm(s: str) -> str:
    s = unicodedata.normalize("NFC", str(s)).casefold()
    return "".join(ch for ch in s if ch.isalnum())

def parse_index_from_name(name: str) -> int | None:
    stem = Path(name).stem
    parts = stem.replace("-", " ").replace("_", " ").split()
    if not parts:
        return None
    # expected format: Ch??ng <index> ... ; take first pure-digit token after token 0 when possible
    for token in parts[1:4]:
        if token.isdigit():
            return int(token)
    # fallback: any pure-digit token
    for token in parts:
        if token.isdigit():
            return int(token)
    return None

def main() -> int:
    folder_map = {norm(p.name): p for p in ROOT.iterdir() if p.is_dir() and p.name not in IGNORE}
    d = MTCDownloader()
    books=[]; page=1
    while True:
        data=d.get_books(limit=100, page=page)
        rows=(data or {}).get("data") or []
        if not rows: break
        books.extend(rows)
        print(f"scan_page {page} rows {len(rows)} total {len(books)}", flush=True)
        if len(rows) < 100: break
        page += 1
        time.sleep(0.05)
    results=[]; repair=[]
    for i,b in enumerate(books,1):
        bid=int(b["id"])
        name=b.get("name") or ""
        folder=folder_map.get(norm(name))
        item={"id":bid,"name":name,"status_name":b.get("status_name"),"folder": folder.name if folder else None}
        if not folder:
            item["status"]="no_folder"
            repair.append({"id":bid,"reason":"no_folder","name":name})
            results.append(item)
            continue
        try:
            chapters=get_chapters_once_safe(d, bid)
        except Exception as exc:
            item["status"]="api_error"; item["error"]=str(exc); results.append(item); continue
        remote_set=set()
        for seq,ch in enumerate(chapters,1):
            try: remote_set.add(int(ch.get("index") or ch.get("number") or seq))
            except: pass
        local_files=list(folder.glob("*.txt"))
        local_set=set()
        unparsable=[]
        for f in local_files:
            idx=parse_index_from_name(f.name)
            if idx is None: unparsable.append(f.name)
            else: local_set.add(idx)
        missing=sorted(remote_set-local_set)
        extra=sorted(local_set-remote_set)
        item.update({
            "status":"ok" if not missing and not extra and not unparsable else "needs_repair",
            "remote_count":len(remote_set),
            "local_unique_count":len(local_set),
            "local_file_count":len(local_files),
            "missing_count":len(missing),
            "extra_count":len(extra),
            "unparsable_count":len(unparsable),
            "missing_sample":missing[:20],
            "extra_sample":extra[:20],
            "unparsable_sample":unparsable[:10],
        })
        if missing or extra or unparsable:
            repair.append({
                "id":bid, "reason":"missing_or_extra", "name":name,
                "missing_count":len(missing), "extra_count":len(extra), "unparsable_count":len(unparsable)
            })
        results.append(item)
        if i % 25 == 0:
            print(f"audited {i}/{len(books)} repair_so_far {len(repair)}", flush=True)
    report={"books_total":len(books),"repair_count":len(repair),"repair":repair,"results":results}
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"books_total {len(books)}")
    print(f"repair_count {len(repair)}")
    for r in repair[:60]: print(r)
    print(f"report {OUT}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

