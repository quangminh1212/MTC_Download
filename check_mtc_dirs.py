import json
import re
from pathlib import Path

M = Path(r'C:\Dev\MTC_Download\completed_books.json')
R = Path(r'C:\Dev\MTC')
INVALID = '<>:"/\\|?*'

def clean(s):
    s = str(s or '').strip()
    for ch in INVALID:
        s = s.replace(ch, ' ')
    return re.sub(r'\s+', ' ', s).strip(' .')

books = json.loads(M.read_text(encoding='utf-8'))
valid = {
    clean(b['name'])
    for b in books
    if (b.get('status_name') == 'Hoàn thành' or int(b.get('status') or 0) == 2)
    and int(b.get('chapter_count') or b.get('latest_index') or 0) >= 1
}
dirs = [d.name for d in R.iterdir() if d.is_dir() and d.name != '.git']
extra = sorted([d for d in dirs if d not in valid])
print('dirs', len(dirs), 'valid', len(valid), 'extra', len(extra))
for n in extra:
    print('EXTRA', n)
