import json
import re
from pathlib import Path

from mtc_downloader import MTCDownloader

ROOT = Path(r"C:\Dev\MTC")
TARGET = ROOT / "Từ Đội Sản Xuất Đuổi Đại Xa Bắt Đầu"
OUT = Path(r"C:\Dev\MTC_Download\logs\identify_tu_doi_bookid.json")
PAT = re.compile(r"(?i)(?:chương|chuong)\s*(\d+)")


def local_stats():
    nums = []
    for p in TARGET.glob("*.txt"):
        m = PAT.search(p.name)
        if not m:
            continue
        nums.append(int(m.group(1)))
    uniq = sorted(set(nums))
    max_idx = max(uniq)
    missing = [i for i in range(1, max_idx + 1) if i not in set(uniq)]
    return {
        "count": len(uniq),
        "max": max_idx,
        "missing": missing,
    }


def main():
    ls = local_stats()
    d = MTCDownloader()
    candidates = []
    for page in range(1, 80):
        data = d.get_books(limit=100, page=page)
        rows = (data or {}).get("data") or []
        if not rows:
            break
        for b in rows:
            cc = int(b.get("chapter_count") or b.get("latest_index") or 0)
            # local: 1763 unique and max 1770 => likely remote around 1770
            if 1700 <= cc <= 1800:
                candidates.append({
                    "id": b.get("id"),
                    "name": b.get("name"),
                    "chapter_count": b.get("chapter_count"),
                    "latest_index": b.get("latest_index"),
                    "status_name": b.get("status_name"),
                })
    out = {
        "local": ls,
        "candidates": candidates,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUT)
    print("local", ls)
    print("candidates", len(candidates))
    for c in candidates[:100]:
        print(c)


if __name__ == "__main__":
    main()
