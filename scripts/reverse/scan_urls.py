import re
import pathlib
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
root = pathlib.Path(r'C:\Dev\MTC_Download\mtc_extracted')
pat = re.compile(b"https?://[^\\s\\\"'<>\\\\)\\]]+")
seen = set()
for p in root.rglob('*'):
    if p.is_file():
        try:
            b = p.read_bytes()
        except Exception:
            continue
        for m in pat.findall(b):
            u = m.decode('latin1', 'ignore')
            seen.add(u)
for u in sorted(seen):
    print(u)
print('TOTAL', len(seen))
