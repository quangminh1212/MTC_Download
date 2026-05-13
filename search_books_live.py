import json
import sys
from pathlib import Path

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

OUT = Path(r"C:\Dev\MTC_Download\logs\search_books_live.json")
BASE = "https://android.lonoapp.net/api/books"
QUERIES = [
    "Đội Sản Xuất",
    "Đuổi Đại Xa",
    "Đổi Một Chữ",
    "Bọn Hắn Bị Ta Chơi Hỏng",
    "Kỹ Năng Đổi Một Chữ",
]


def main():
    s = requests.Session()
    s.headers.update({"User-Agent": "MTC/Android", "Accept": "application/json"})
    out = {}
    for q in QUERIES:
        hits = []
        for page in range(1, 6):
            r = s.get(BASE, params={"limit": 100, "page": page, "search": q}, timeout=20)
            r.raise_for_status()
            data = r.json().get("data") or []
            for b in data:
                hits.append({
                    "id": b.get("id"),
                    "name": b.get("name"),
                    "chapter_count": b.get("chapter_count"),
                    "latest_index": b.get("latest_index"),
                    "status_name": b.get("status_name"),
                })
            if len(data) < 100:
                break
        out[q] = hits
        print(q, len(hits))
        for row in hits[:20]:
            print(row)
            
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
