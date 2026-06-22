from pathlib import Path
import re
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(r'C:\Dev\MTC\Tiền Hạo Kiếp Tây Du')


def looks_like_duplicate_or_bad_title(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    # line 5 in these files is usually a duplicate chapter title; sometimes it contains mojibake/replacement chars
    if re.match(r'^(Chương|Chuong|Chư|Ch\S*)\s*\d+\s*[:：]', s, re.I):
        return True
    if '�' in s and len(s) < 160:
        return True
    bad_ratio = sum(1 for ch in s if ord(ch) < 32 and ch not in '\t\r\n') / max(1, len(s))
    if bad_ratio > 0.02:
        return True
    if len(s) < 40:
        letters = sum(1 for ch in s if ch.isalpha())
        if letters < max(3, len(s) // 3):
            return True
    return False

fixed = 0
checked = 0
report = []
for p in sorted(ROOT.glob('*.txt')):
    if p.name.startswith('_'):
        continue
    lines = p.read_text(encoding='utf-8', errors='replace').splitlines()
    checked += 1
    # Expected layout:
    # 1 =====
    # 2 title
    # 3 =====
    # 4 blank
    # 5 duplicate/garbled title -> remove
    # 6 blank
    # 7 content...
    if len(lines) >= 5 and looks_like_duplicate_or_bad_title(lines[4]):
        removed = lines[4]
        del lines[4]
        # remove extra blank left after duplicate title if present
        if len(lines) >= 5 and lines[4].strip() == '':
            del lines[4]
        p.write_text('\n'.join(lines).rstrip() + '\n', encoding='utf-8')
        fixed += 1
        report.append(f'FIX {p.name}: removed line5={removed!r}')

print(f'checked={checked}')
print(f'fixed={fixed}')
for row in report[:80]:
    print(row)
