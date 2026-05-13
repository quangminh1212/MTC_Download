import re, json, sys
from pathlib import Path
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
books = {
  'Devil\'S Path Quỷ Giới Và Nhẫn Giới': [32],
  'Marvel Ta Là Tiểu Chiến Sỹ Họ Stark': [47,48,49,50,51,52,53],
  'Nhị Thứ Nguyên Thần Tượng Âm Nhạc': [172],
  'Siêu Dự Bị': list(range(96,122)),
}
root = Path(r'C:\Dev\MTC')
pat = re.compile(r'(?i)(?:chương|chuong)\s*(\d+)')
out = {}
for folder, wanted in books.items():
    d = root / folder
    rows = []
    if d.exists():
        for p in sorted(d.glob('*.txt')):
            m = pat.search(p.name)
            idx = int(m.group(1)) if m else None
            rows.append({'name': p.name, 'idx': idx, 'size': p.stat().st_size})
    idx_map = {}
    for r in rows:
        idx_map.setdefault(r['idx'], []).append(r)
    out[folder] = {
        'count': len(rows),
        'missing_wanted': [x for x in wanted if x not in idx_map],
        'duplicates': {str(k): v for k,v in idx_map.items() if k is not None and len(v)>1},
        'around': [r for r in rows if r['idx'] is not None and ((wanted and min(wanted)-3) <= r['idx'] <= (wanted[-1]+3))],
    }
print(json.dumps(out, ensure_ascii=False, indent=2))
