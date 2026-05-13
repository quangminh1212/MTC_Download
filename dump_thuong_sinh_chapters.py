import json
from pathlib import Path
from mtc_downloader import MTCDownloader

ids = [15405674, 15426215, 15624081, 26936462]
out = Path(r"C:\Dev\MTC_Download\logs\chapter_debug")
out.mkdir(parents=True, exist_ok=True)
d = MTCDownloader()

for cid in ids:
    data = d.get_chapter_content(cid)
    p = out / f"{cid}.json"
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(str(p))
