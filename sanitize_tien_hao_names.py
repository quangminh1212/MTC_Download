from pathlib import Path
import re
import sys
import unicodedata

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(r'C:\Dev\MTC')
OLD = ROOT / 'Tiền Hạo Kiếp Tây Du'
NEW = ROOT / 'Tien Hao Kiep Tay Du'


def ascii_slug(s: str) -> str:
    s = s.replace('Đ', 'D').replace('đ', 'd')
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
    s = s.encode('ascii', 'ignore').decode('ascii')
    s = re.sub(r'[^A-Za-z0-9 ._()\-]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip(' .')
    return s or 'untitled'

if not OLD.exists():
    print(f'MISSING_DIR {OLD}')
    raise SystemExit(1)

if OLD != NEW:
    if NEW.exists():
        print(f'TARGET_EXISTS {NEW}')
        raise SystemExit(2)
    OLD.rename(NEW)
    print(f'RENAMED_DIR {OLD.name} -> {NEW.name}')

count = 0
for p in sorted(NEW.iterdir()):
    if not p.is_file():
        continue
    new_name = ascii_slug(p.name)
    target = p.with_name(new_name)
    if target == p:
        continue
    base = target.stem
    suffix = target.suffix
    i = 2
    while target.exists():
        target = p.with_name(f'{base} ({i}){suffix}')
        i += 1
    p.rename(target)
    count += 1
    print(f'RENAMED_FILE {p.name} -> {target.name}')

print(f'files_renamed={count}')
print(f'final_dir={NEW}')
