from pathlib import Path
import re
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

root = Path(r'C:\Dev\MTC\Tiền Hạo Kiếp Tây Du')
encrypted = []
for p in sorted(root.glob('*.txt')):
    if p.name.startswith('_'):
        continue
    text = p.read_text(encoding='utf-8', errors='replace')
    payload = None
    for line in text.splitlines():
        s = line.strip()
        if len(s) > 100 and re.fullmatch(r'[A-Za-z0-9+/=]+', s):
            payload = s
            break
    if payload:
        encrypted.append((p.name, len(payload), payload[:80]))

print('encrypted_count=', len(encrypted))
for name, ln, pre in encrypted[:20]:
    print('ENCRYPTED', name, 'len=', ln)
    print('PREFIX', pre)
