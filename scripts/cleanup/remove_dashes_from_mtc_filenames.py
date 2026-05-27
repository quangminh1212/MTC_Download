import re
from pathlib import Path
import json

ROOT = Path(r'C:\Dev\MTC')
changed=[]
skipped=[]

# remove ASCII hyphen-minus and common dash variants from chapter filenames
DASH_RE = re.compile(r'[-\u2010\u2011\u2012\u2013\u2014\u2015]')

for p in ROOT.rglob('*.txt'):
    if '.git' in p.parts:
        continue
    new_name = DASH_RE.sub(' ', p.name)
    new_name = re.sub(r'\s{2,}', ' ', new_name).strip()
    if new_name == p.name:
        continue
    target = p.with_name(new_name)
    if target.exists() and target.resolve() != p.resolve():
        skipped.append({'from': str(p), 'to': str(target), 'reason': 'target_exists'})
        continue
    p.rename(target)
    changed.append({'from': str(p), 'to': str(target)})

log = ROOT / '_rename_dashes_report.json'
log.write_text(json.dumps({'changed': changed, 'skipped': skipped}, ensure_ascii=False, indent=2), encoding='utf-8')
print(str(log))
print(f'changed={len(changed)} skipped={len(skipped)}')
