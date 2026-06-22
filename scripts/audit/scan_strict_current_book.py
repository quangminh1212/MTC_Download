from pathlib import Path
import re
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(r'C:\Dev\MTC\Tiền Hạo Kiếp Tây Du')
BAD = re.compile(r'[�\x00-\x08\x0b\x0c\x0e-\x1f]')

issues = []
for p in sorted(ROOT.glob('*.txt')):
    if p.name.startswith('_'):
        continue
    lines = p.read_text(encoding='utf-8', errors='replace').splitlines()
    # Check line 5 specifically
    l5 = lines[4] if len(lines) >= 5 else ''
    if BAD.search(l5):
        issues.append((p.name, 'line5_bad_chars', l5))
    # Check whole file
    bad_lines = [i for i, line in enumerate(lines, 1) if BAD.search(line)]
    if bad_lines:
        issues.append((p.name, 'bad_lines', ','.join(map(str, bad_lines))))

print('issues_count=', len(issues))
for it in issues:
    print('ISSUE', it[0], it[1], it[2])
