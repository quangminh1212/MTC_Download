import json
import pathlib
import re

book_dir = pathlib.Path(r"C:\Dev\MTC\Thương Sinh Giang Đạo")
pat = re.compile(r"(?i)(?:chương|chuong)\s*(\d+)")
check = {136, 207, 220, 338, 953}
out = []
for p in book_dir.glob("*.txt"):
    m = pat.search(p.name)
    n = int(m.group(1)) if m else None
    if n in check:
        out.append({"chapter": n, "name": p.name, "size": p.stat().st_size})
out.sort(key=lambda x: (x['chapter'], x['name']))
path = pathlib.Path(r"C:\Dev\MTC_Download\logs\thuong_sinh_samples.json")
path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
print(str(path))
