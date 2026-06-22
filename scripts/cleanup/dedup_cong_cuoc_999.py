import json, re, sys, hashlib
from pathlib import Path
if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8', errors='replace')

d = Path(r'C:\Dev\MTC\Công Cuộc Bị 999 Em Gái Chinh Phục')
pat = re.compile(r'(?i)(?:chương|chuong)\s*(\d+)')

def norm_name(name: str) -> str:
    s = name.replace('(', '').replace(')', '').replace('[', '').replace(']', '')
    s = s.replace('-', ' ').replace('–', ' ').replace('—', ' ')
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def score(p: Path) -> tuple:
    n = p.name
    normalized = (n == norm_name(n))
    size = p.stat().st_size
    # Prefer filename already obeying rule, then larger content, then shorter cleaner filename.
    return (1 if normalized else 0, size, -len(n), n)

by_idx = {}
for p in d.glob('*.txt'):
    m = pat.search(p.name)
    if not m:
        continue
    by_idx.setdefault(int(m.group(1)), []).append(p)

removed=[]
kept=[]
for idx, files in sorted(by_idx.items()):
    if len(files) <= 1:
        continue
    files = sorted(files, key=score, reverse=True)
    keep = files[0]
    kept.append({'chapter': idx, 'keep': keep.name, 'size': keep.stat().st_size, 'candidates': [f.name for f in files]})
    for f in files[1:]:
        removed.append({'chapter': idx, 'removed': f.name, 'size': f.stat().st_size, 'kept': keep.name})
        f.unlink()

out={'folder': d.name, 'duplicate_groups': len(kept), 'removed_count': len(removed), 'kept': kept, 'removed': removed}
p=Path(r'C:\Dev\MTC_Download\logs\cong_cuoc_999_dedup.json')
p.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(str(p))
print(f"duplicate_groups={len(kept)} removed={len(removed)}")
