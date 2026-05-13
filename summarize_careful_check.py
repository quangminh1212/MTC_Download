import json, sys
from pathlib import Path
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
p = Path(r'C:\Dev\MTC_Download\logs\mtc_careful_check.json')
rows = json.loads(p.read_text(encoding='utf-8'))
summary = {}
for r in rows:
    summary[r['status']] = summary.get(r['status'], 0) + 1
out = {
    'total_books': len(rows),
    'status_counts': summary,
    'problem_books': [
        {
            'folder': r['folder'],
            'book_id': r.get('book_id'),
            'book_name': r.get('book_name'),
            'status': r['status'],
            'expected': r.get('expected'),
            'chapter_files': r.get('chapter_files'),
            'unique_indexes': r.get('unique_indexes'),
            'missing_count': r.get('missing_count'),
            'missing_first20': r.get('missing_first20'),
            'duplicate_index_count': r.get('duplicate_index_count'),
            'duplicate_indexes_first20': r.get('duplicate_indexes_first20'),
            'small_suspicious_count': r.get('small_suspicious_count'),
            'small_suspicious_first20': r.get('small_suspicious_first20'),
            'small_notice_count': r.get('small_notice_count'),
            'small_notice_first20': r.get('small_notice_first20'),
        }
        for r in rows if r['status'] != 'complete'
    ]
}
outp = Path(r'C:\Dev\MTC_Download\logs\mtc_careful_summary.json')
outp.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
print(str(outp))
print(json.dumps(out, ensure_ascii=False, indent=2))
