import json
from pathlib import Path
src = Path(r'C:\Dev\MTC_Download\logs\mtc_auto_commit_results.json')
out = Path(r'C:\Dev\MTC_Download\logs\mtc_auto_commit_results_slim.json')
rows = json.loads(src.read_text(encoding='utf-8'))
slim = []
for r in rows:
    slim.append({
        'folder': r.get('folder'),
        'message': r.get('message'),
        'status': r.get('status'),
        'staged_count': r.get('staged_count'),
    })
out.write_text(json.dumps(slim, ensure_ascii=False, indent=2), encoding='utf-8')
print(str(out))
print('total', len(slim))
print('committed', sum(1 for x in slim if x.get('status')=='committed'))
print('failed', sum(1 for x in slim if x.get('status') not in ('committed','nothing_staged')))
