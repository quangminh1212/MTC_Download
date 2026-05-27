from pathlib import Path
import re, sys
if hasattr(sys.stdout,'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT=Path(r'C:\Dev\MTC\Tiền Hạo Kiếp Tây Du')
BAD=re.compile(r'[�\x00-\x08\x0b\x0c\x0e-\x1f]|[ÃÂÆÐ]|eyJpdiI6|"iv":"')
issues=[]
files=sorted([p for p in ROOT.glob('*.txt') if not p.name.startswith('_')])
for p in files:
    lines=p.read_text(encoding='utf-8', errors='replace').splitlines()
    if len(lines)<5:
        issues.append((p.name,'too_few_lines',str(len(lines))))
        continue
    if lines[1].strip()!=lines[4].strip():
        issues.append((p.name,'line2_line5_mismatch',f'2={lines[1]!r} | 5={lines[4]!r}'))
    for i,line in enumerate(lines,1):
        if BAD.search(line):
            issues.append((p.name,f'bad_marker_line_{i}',line[:160]))
print('chapter_count=',len(files))
print('issues_count=',len(issues))
for it in issues[:200]:
    print('ISSUE',it[0],it[1],it[2])
print('--- first 8 lines sample ---')
for p in [files[0], files[7], files[-1]]:
    print('FILE',p.name)
    for n,l in enumerate(p.read_text(encoding='utf-8', errors='replace').splitlines()[:8],1):
        print(f'{n}: {l}')
    print('---')
