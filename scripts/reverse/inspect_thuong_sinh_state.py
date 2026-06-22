import json
import pathlib
import re

book_dir = pathlib.Path(r"C:\Dev\MTC\Thương Sinh Giang Đạo")
out_path = pathlib.Path(r"C:\Dev\MTC_Download\logs\thuong_sinh_state.json")
pat = re.compile(r"(?i)(?:chương|chuong)\s*(\d+)")
rows = []
for p in book_dir.glob("*.txt"):
    m = pat.search(p.name)
    n = int(m.group(1)) if m else None
    rows.append({"chapter": n, "name": p.name, "size": p.stat().st_size})

parsed = [r for r in rows if r["chapter"] is not None]
parsed.sort(key=lambda r: r["chapter"])
lt1 = [r for r in parsed if r["size"] < 1000]
lt5 = [r for r in parsed if r["size"] < 5000]
missing = []
seen = {r['chapter'] for r in parsed}
if seen:
    for i in range(1, max(seen) + 1):
        if i not in seen:
            missing.append(i)

report = {
    "total_txt": len(rows),
    "parsed_chapters": len(parsed),
    "min_chapter": parsed[0]['chapter'] if parsed else None,
    "max_chapter": parsed[-1]['chapter'] if parsed else None,
    "lt1kb": len(lt1),
    "lt5kb": len(lt5),
    "missing_within_range": len(missing),
    "first_missing": missing[:20],
    "first_small": lt1[:20],
    "last_rows": parsed[-10:],
}
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(str(out_path))
