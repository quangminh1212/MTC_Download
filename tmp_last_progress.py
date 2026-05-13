import json
import sys
from pathlib import Path
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
p = Path(r'C:\Dev\MTC_Download\logs\completed_progress.json')
if not p.exists():
    print('NO_PROGRESS')
    raise SystemExit(0)
data = json.loads(p.read_text(encoding='utf-8-sig'))
if not data:
    print('EMPTY_PROGRESS')
    raise SystemExit(0)
last = data[-1]
print(json.dumps(last, ensure_ascii=False))
