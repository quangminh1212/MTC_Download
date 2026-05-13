import json
import subprocess
from pathlib import Path

repo = Path(r"C:\Dev\MTC")
careful_path = Path(r"C:\Dev\MTC_Download\logs\mtc_careful_check.json")
out_path = Path(r"C:\Dev\MTC_Download\logs\mtc_changed_folders_vs_complete.json")

careful = json.loads(careful_path.read_text(encoding='utf-8'))
status_by_folder = {row.get('folder'): row.get('status') for row in careful if row.get('folder')}

# git porcelain -z parser (v1)
proc = subprocess.run(
    ['git', 'status', '--porcelain=v1', '-z', '-uall'],
    cwd=repo,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    check=False,
)
if proc.returncode != 0:
    raise SystemExit(proc.stderr.decode('utf-8', 'replace'))

data = proc.stdout
parts = data.split(b'\x00')
entries = []
i = 0
while i < len(parts) and parts[i]:
    rec = parts[i]
    i += 1
    if len(rec) < 4:
        continue
    status = rec[:2].decode('ascii', 'replace')
    path1 = rec[3:]  # skip "XY "
    path2 = None
    if status[0] == 'R' or status[0] == 'C':
        if i < len(parts):
            path2 = parts[i]
            i += 1
    entries.append((status, path1, path2))

changed = {}
for st, p1, p2 in entries:
    p = p2 if p2 else p1
    try:
        path = p.decode('utf-8')
    except Exception:
        path = p.decode('utf-8', 'replace')
    top = path.split('\\', 1)[0].split('/', 1)[0]
    if not top:
        continue
    if top.startswith('.'):
        continue
    rec = changed.setdefault(top, {'count': 0, 'statuses': set()})
    rec['count'] += 1
    rec['statuses'].add(st)

rows = []
for folder, info in sorted(changed.items(), key=lambda kv: kv[0].lower()):
    rows.append({
        'folder': folder,
        'changed_entries': info['count'],
        'statuses': sorted(info['statuses']),
        'careful_status': status_by_folder.get(folder),
        'is_complete': status_by_folder.get(folder) == 'complete',
    })

summary = {
    'total_changed_folders': len(rows),
    'complete_changed_folders': sum(1 for r in rows if r['is_complete']),
    'rows': rows,
}
out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(str(out_path))
print(f"total_changed_folders={summary['total_changed_folders']}")
print(f"complete_changed_folders={summary['complete_changed_folders']}")
