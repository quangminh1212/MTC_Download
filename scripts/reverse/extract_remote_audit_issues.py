import json
from pathlib import Path
p=Path(r'C:\Dev\MTC_Download\logs\mtc_remote_full_audit.json')
data=json.loads(p.read_text(encoding='utf-8'))
rows=data['report'] if isinstance(data, dict) and 'report' in data else data
out=[r for r in rows if r.get('status')!='remote_index_complete']
outp=Path(r'C:\Dev\MTC_Download\logs\mtc_remote_full_audit_issues.json')
outp.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(str(outp))
print(json.dumps(out,ensure_ascii=False,indent=2))
