from pathlib import Path
import re, sys, unicodedata
if hasattr(sys.stdout,'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT=Path(r'C:\Dev\MTC')
OLD=ROOT/'Tien Hao Kiep Tay Du'
NEW=ROOT/'Tiền Hạo Kiếp Tây Du'
INVALID='<>:"/\\|?*!'
BAD=re.compile(r'[\x00-\x1f\x7f�]')

def clean_keep_vietnamese(s: str) -> str:
    s=unicodedata.normalize('NFC', s or '')
    s=BAD.sub('', s)
    for ch in INVALID:
        s=s.replace(ch, ' ')
    s=re.sub(r'\s+', ' ', s).strip(' .')
    return s or 'Untitled'

if not OLD.exists() and not NEW.exists():
    print('MISSING both source dirs')
    raise SystemExit(1)
base = OLD if OLD.exists() else NEW
if base != NEW:
    if NEW.exists():
        print(f'TARGET_EXISTS {NEW}')
        raise SystemExit(2)
    base.rename(NEW)
    print(f'RENAMED_DIR {base.name} -> {NEW.name}')
base=NEW

renamed=0
for p in sorted(base.glob('*.txt')):
    lines=p.read_text(encoding='utf-8', errors='replace').splitlines()
    if len(lines) >= 2 and lines[1].strip():
        title=lines[1].strip()
    else:
        title=p.stem
    filename=clean_keep_vietnamese(title)+'.txt'
    target=p.with_name(filename)
    if target == p:
        continue
    stem=target.stem; suffix=target.suffix; n=2
    while target.exists():
        target=p.with_name(f'{stem} ({n}){suffix}')
        n+=1
    p.rename(target)
    renamed+=1
    print(f'RENAMED_FILE {p.name} -> {target.name}')
print('renamed=',renamed)
print('final_dir=',base)
