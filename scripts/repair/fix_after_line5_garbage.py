from pathlib import Path
import re, sys
if hasattr(sys.stdout,'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT=Path(r'C:\Dev\MTC\Tiền Hạo Kiếp Tây Du')
BAD=re.compile(r'[�\x00-\x08\x0b\x0c\x0e-\x1f]|[ÃÂÆÐ]|eyJpdiI6|"iv":"')

def is_garbage_title_fragment(s):
    t=s.strip()
    if not t: return False
    if BAD.search(t): return True
    if len(t) < 30 and not re.search(r'[.!?]$', t): return True
    return False

fixed=0
for p in sorted(ROOT.glob('*.txt')):
    if p.name.startswith('_'): continue
    lines=p.read_text(encoding='utf-8', errors='replace').splitlines()
    if len(lines)<3: continue
    title=lines[1].strip()
    # collect existing body after header; remove current duplicate title if present and remove garbage fragments before prose
    rest=lines[4:] if len(lines)>4 else []
    if rest and rest[0].strip()==title:
        rest=rest[1:]
    while rest and rest[0].strip()=='' :
        rest=rest[1:]
    removed=[]
    while rest and is_garbage_title_fragment(rest[0]):
        removed.append(rest[0])
        rest=rest[1:]
        while rest and rest[0].strip()=='' :
            rest=rest[1:]
    new_lines=[lines[0], title, lines[2], '', title, ''] + rest
    if new_lines != lines:
        p.write_text('\n'.join(new_lines).rstrip()+'\n', encoding='utf-8')
        fixed+=1
        if removed:
            print('FIX', p.name, 'removed', len(removed), removed[:5])
print('fixed_files=', fixed)
