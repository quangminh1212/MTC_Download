from pathlib import Path
import re, sys
if hasattr(sys.stdout,'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT=Path(r'C:\Dev\MTC\Tiền Hạo Kiếp Tây Du')
# Typical mojibake markers / encryption residue markers
pat = re.compile(r'[�]|[ÃÂÆÐ]|\uFFFD|eyJpdiI6|"iv":"|\x00')
found=[]
for p in sorted(ROOT.glob('*.txt')):
    if p.name.startswith('_'): continue
    for i,line in enumerate(p.read_text(encoding='utf-8', errors='replace').splitlines(),1):
        if pat.search(line):
            found.append((p.name,i,line[:180]))
print('found=',len(found))
for f in found[:200]:
    print(f'{f[0]} :: line {f[1]} :: {f[2]}')
