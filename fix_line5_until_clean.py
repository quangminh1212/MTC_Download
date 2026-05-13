from pathlib import Path
import re, sys
if hasattr(sys.stdout,'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT=Path(r'C:\Dev\MTC\Tiền Hạo Kiếp Tây Du')
BAD=re.compile(r'[�\x00-\x08\x0b\x0c\x0e-\x1f]')

def bad_line(s: str) -> bool:
    t=s.strip()
    if not t: return False
    if BAD.search(t): return True
    # damaged duplicate title fragments around line 5 are short and title-like, not prose
    if len(t) < 80 and any(x in t for x in ['Chương','Chuong','trời xuống mặt đất','Kim Sí','Hồng Hài','Dương Tiễn']):
        if not re.search(r'[.!?]$', t) or ':' in t:
            return True
    return False

fixed=0
for p in sorted(ROOT.glob('*.txt')):
    if p.name.startswith('_'): continue
    lines=p.read_text(encoding='utf-8', errors='replace').splitlines()
    removed=[]
    changed=True
    while changed and len(lines)>=5:
        changed=False
        if bad_line(lines[4]):
            removed.append(lines[4])
            del lines[4]
            if len(lines)>=5 and lines[4].strip()=='' :
                del lines[4]
            changed=True
    if removed:
        p.write_text('\n'.join(lines).rstrip()+'\n', encoding='utf-8')
        fixed+=1
        print('FIX', p.name, 'removed=', removed)
print('fixed_files=', fixed)
