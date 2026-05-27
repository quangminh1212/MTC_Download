#!/usr/bin/env python3
import sys, time
sys.path.insert(0, r'C:\Dev\MTC_DOWNLOAD')
from mtc_downloader import MTCDownloader

d=MTCDownloader()
for cid in range(14965617,14974876):
    detail=d.get_chapter_content(cid)
    data=(detail or {}).get('data') or {}
    if int(data.get('book_id') or 0)==110466:
        print(f'FOUND cid={cid} idx={data.get("index")} name={data.get("name")}', flush=True)
    if cid % 500 == 0:
        print(f'progress {cid}', flush=True)
    time.sleep(0.005)
