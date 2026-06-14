from pathlib import Path
import re, sys
if hasattr(sys.stdout,'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
root=Path(r'C:\Dev\MTC\Thương Sinh Giang Đạo')
BAD=re.compile(r'[�\x00-\x08\x0b\x0c\x0e-\x1f]')
files=[]
for p in sorted(root.glob('Chương *.txt')):
    m=re.match(r'^Chương\s+(\d+)', p.name)
    if not m: continue
    idx=int(m.group(1))
    if idx<=135: continue
    lines=p.read_text(encoding='utf-8', errors='replace').splitlines()
    sample=''
    bad=[]
    for i,l in enumerate(lines[:20],1):
        if BAD.search(l): bad.append((i,l[:120]))
    if len(lines)>=7:
        sample=lines[6][:160]
    print(f'FILE {idx} {p.name}')
    print('LINE7', repr(sample))
    print('BAD', bad[:5])
    if idx>=145: break
