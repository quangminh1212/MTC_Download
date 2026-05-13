import json
import re
from pathlib import Path

root = Path(r'C:\Dev\MTC')
out = Path(r'C:\Dev\MTC_Download\logs\downloaded_books_registry.json')
pat = re.compile(r'(?i)(?:chương|chuong)\s*(\d+)')
books = []
for d in root.iterdir():
    if not d.is_dir():
        continue
    chapters = []
    good = 0
    for p in d.glob('*.txt'):
        m = pat.search(p.name)
        if m:
            chapters.append(int(m.group(1)))
            if p.stat().st_size >= 5000:
                good += 1
    if chapters:
        books.append({
            'folder': d.name,
            'chapter_files': len(chapters),
            'good_files': good,
            'max_chapter': max(chapters),
        })
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(books, ensure_ascii=False, indent=2), encoding='utf-8')
print(str(out))
