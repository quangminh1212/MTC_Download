from pathlib import Path
import re, sys, unicodedata
if hasattr(sys.stdout,'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT=Path(r'C:\Dev\MTC')
TARGET_NAME='Công Cuộc Bị 999 Em Gái Chinh Phục'
INVALID='<>:"/\\|?*!'
BAD=re.compile(r'[\x00-\x1f\x7f�]')

def clean_keep_vietnamese(s: str) -> str:
    s=unicodedata.normalize('NFC', s or '')
    s=BAD.sub('', s)
    for ch in INVALID:
        s=s.replace(ch, ' ')
    s=re.sub(r'\s+', ' ', s).strip(' .')
    return s or 'Untitled'

# Find target robustly by comparing accent-stripped ascii too.
def key(s):
    s=s.replace('Đ','D').replace('đ','d')
    s=unicodedata.normalize('NFKD', s)
    s=''.join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r'\W+', '', s).lower()

dirs=[p for p in ROOT.iterdir() if p.is_dir()]
base=None
for d in dirs:
    if d.name==TARGET_NAME or key(d.name)==key(TARGET_NAME):
        base=d; break
if not base:
    print('MISSING_DIR')
    for d in dirs: print('DIR', d.name)
    raise SystemExit(1)

proper=ROOT/TARGET_NAME
if base != proper:
    if proper.exists():
        print('TARGET_EXISTS', proper)
        raise SystemExit(2)
    base.rename(proper)
    print(f'RENAMED_DIR {base.name} -> {proper.name}')
base=proper

renamed=0
for p in sorted(base.glob('*.txt')):
    lines=p.read_text(encoding='utf-8', errors='replace').splitlines()
    title=None
    if len(lines)>=2 and lines[1].strip().lower().startswith(('chương','chuong')):
        title=lines[1].strip()
    elif p.stem:
        title=p.stem
    name=clean_keep_vietnamese(title or p.stem)+'.txt'
    target=p.with_name(name)
    if target==p: continue
    stem=target.stem; suffix=target.suffix; n=2
    while target.exists():
        target=p.with_name(f'{stem} ({n}){suffix}')
        n+=1
    p.rename(target)
    renamed+=1
    print(f'RENAMED_FILE {p.name} -> {target.name}')
print('renamed=',renamed)
print('final_dir=',base)
