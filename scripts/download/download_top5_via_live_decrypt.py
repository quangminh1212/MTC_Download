#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, subprocess, sys, time
from pathlib import Path

from mtc_status_utils import is_ongoing_status

EMAIL=sys.argv[1]
PASSWORD=sys.argv[2]
TOP_N=int(sys.argv[3]) if len(sys.argv)>3 else 5
MANIFEST=Path(r'C:\Dev\MTC_Download\logs\bookmarked_books_manifest.json')
RUNNER=Path(r'C:\Dev\MTC_Download\download_one_completed_live_decrypt.py')
manifest_books=json.loads(MANIFEST.read_text(encoding='utf-8'))['books']
books=[]
for book in manifest_books:
    if not is_ongoing_status(book):
        continue
    books.append(book)
    if len(books) >= TOP_N:
        break
for i,b in enumerate(books,1):
    bid=str(b['id'])
    print(f'=== [{i}/{len(books)}] START {bid} {b["name"]}', flush=True)
    p=subprocess.run([sys.executable, str(RUNNER), '--book-id', bid, '--delay', '0.15'], check=False)
    print(f'=== [{i}/{len(books)}] EXIT {bid} code={p.returncode}', flush=True)
    if p.returncode not in (0,4):
        raise SystemExit(p.returncode)
    time.sleep(2)
print('ALL_DONE', flush=True)
