from pathlib import Path
import re
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(r'C:\Dev\MTC\Tiền Hạo Kiếp Tây Du')

REPLACEMENTS = {
    'Chư֡ng': 'Chương',
    'Chuong': 'Chương',
    'Ph�t': 'Phật',
    'T?': 'Tổ',
    'D?': 'Độ',
}


def fix_text(text: str) -> str:
    # common mojibake repair pass
    for enc in ('latin1', 'cp1252'):
        try:
            candidate = text.encode(enc, errors='ignore').decode('utf-8', errors='ignore')
            if candidate.count('�') <= text.count('�') and candidate.count('Ã') < text.count('Ã'):
                text = candidate
        except Exception:
            pass
    for a, b in REPLACEMENTS.items():
        text = text.replace(a, b)
    text = re.sub(r'^(Chương\s+\d+):\s*\1:\s*', r'\1: ', text, flags=re.M)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text

fixed = 0
for p in sorted(ROOT.glob('Chương *.txt')):
    s = p.read_text(encoding='utf-8', errors='replace')
    t = fix_text(s)
    if t != s:
        p.write_text(t, encoding='utf-8')
        fixed += 1
print('fixed_files=', fixed)
