import json, sys
from pathlib import Path
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
p=Path(r'C:\Dev\MTC_Download\logs\mtc_careful_check.json')
rows=json.loads(p.read_text(encoding='utf-8'))
out=[]
for r in rows:
    if r.get('status')=='missing_chapters':
        out.append({
            'folder': r.get('folder'),
            'book_id': r.get('book_id'),
            'book_name': r.get('book_name'),
            'expected': r.get('expected'),
            'chapter_files': r.get('chapter_files'),
            'unique_indexes': r.get('unique_indexes'),
            'missing_count': r.get('missing_count'),
            'missing_first20': r.get('missing_first20'),
        })
outp=Path(r'C:\Dev\MTC_Download\logs\missing_books_after_cleanup.json')
outp.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
print(str(outp))
print(f'missing_books={len(out)}')
