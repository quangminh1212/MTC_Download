import json
from pathlib import Path

src = Path(r'C:\Dev\MTC_Download\logs\mtc_careful_check.json')
out = Path(r'C:\Dev\MTC_Download\logs\short_chapter_repair_candidates.json')
rows = json.loads(src.read_text(encoding='utf-8'))

candidates = []
for r in rows:
    if not r.get('matched'):
        continue
    if r.get('missing_count', 0) != 0:
        continue
    if r.get('duplicate_index_count', 0) != 0:
        continue
    suspicious = r.get('small_suspicious_first20') or []
    notice = r.get('small_notice_first20') or []
    if suspicious or notice:
        candidates.append({
            'folder': r.get('folder'),
            'book_id': r.get('book_id'),
            'book_name': r.get('book_name'),
            'expected': r.get('expected'),
            'small_suspicious_count': r.get('small_suspicious_count', 0),
            'small_suspicious_first20': suspicious,
            'small_notice_count': r.get('small_notice_count', 0),
            'small_notice_first20': notice,
            'status': r.get('status'),
        })

out.write_text(json.dumps(candidates, ensure_ascii=False, indent=2), encoding='utf-8')
print(str(out))
print(len(candidates))
