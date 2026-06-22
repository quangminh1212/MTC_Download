import json, re, sys
from pathlib import Path
if hasattr(sys.stdout,'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

d = Path(r'C:\Dev\MTC\Siêu Dự Bị')
pat = re.compile(r'(?i)(?:chương|chuong)\s*(\d+)')
rows = {}
for p in d.glob('*.txt'):
    m = pat.search(p.name)
    if not m:
        continue
    idx = int(m.group(1))
    rows.setdefault(idx, []).append(p)

removed = []
kept = []
for idx, arr in sorted(rows.items()):
    if len(arr) <= 1:
        continue
    arr = sorted(arr, key=lambda p: (('(' in p.name) or (')' in p.name), len(p.name), p.name))
    keep = arr[0]
    kept.append(keep.name)
    for p in arr[1:]:
        p.unlink()
        removed.append(p.name)

out = {
    'kept': kept,
    'removed': removed,
    'duplicate_index_count': len(kept),
}
p = Path(r'C:\Dev\MTC_Download\logs\sieu_du_bi_dedup.json')
p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
print(str(p))
print(f"removed={len(removed)} kept={len(kept)}")
