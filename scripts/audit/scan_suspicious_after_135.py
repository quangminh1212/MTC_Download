from pathlib import Path
import re, sys, unicodedata
if hasattr(sys.stdout,'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
root=Path(r'C:\Dev\MTC\Thương Sinh Giang Đạo')

def first_body_line(lines):
    # expected layout: 1 border,2 title,3 border,4 blank,5 title,6 blank,7 body
    return lines[6].strip() if len(lines)>=7 else ''

def looks_suspicious(s):
    if not s:
        return True
    if len(s) < 8:
        return True
    # too many non-letter symbols in first 20 chars
    head=s[:20]
    sym=sum(1 for ch in head if not ch.isalnum() and ch not in ' .,:;!?"“”‘’()-')
    if sym>=2:
        return True
    # starts mid-word lowercase with weird pattern
    if s[0].islower() and not s.startswith(('“','"','- ')):
        return True
    # common corruption signs
    if any(tok in s for tok in ['�', 'ks4;', 'Chư', 'Chuong', 'iv":"']):
        return True
    return False

bad=[]
for p in sorted(root.glob('Chương *.txt')):
    m=re.match(r'^Chương\s+(\d+)', p.name)
    if not m: continue
    idx=int(m.group(1))
    if idx<=135: continue
    lines=p.read_text(encoding='utf-8', errors='replace').splitlines()
    s=first_body_line(lines)
    if looks_suspicious(s):
        bad.append((idx,p.name,s))

print('suspect_count=',len(bad))
for idx,name,s in bad[:120]:
    print(f'{idx}: {name}')
    print('  line7=',repr(s[:180]))
