from pathlib import Path
import re, sys
if hasattr(sys.stdout,'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT=Path(r'C:\Dev\MTC\Tiền Hạo Kiếp Tây Du')
BAD=re.compile(r'[�\x00-\x08\x0b\x0c\x0e-\x1f]')
for p in sorted(ROOT.glob('*.txt')):
    if p.name.startswith('_'): continue
    lines=p.read_text(encoding='utf-8', errors='replace').splitlines()
    l5=lines[4] if len(lines)>=5 else ''
    bad_lines=[]
    for i,l in enumerate(lines,1):
        if BAD.search(l): bad_lines.append(i)
    if l5.strip() or bad_lines:
        print(p.name)
        print('  line5=',repr(l5))
        print('  bad_lines=',bad_lines[:20], 'count=',len(bad_lines))
