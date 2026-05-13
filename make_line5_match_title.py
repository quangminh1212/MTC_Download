from pathlib import Path
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = Path(r'C:\Dev\MTC\Tiền Hạo Kiếp Tây Du')
changed = 0
for p in sorted(ROOT.glob('*.txt')):
    if p.name.startswith('_'):
        continue
    lines = p.read_text(encoding='utf-8', errors='replace').splitlines()
    if len(lines) < 3:
        continue
    title = lines[1].strip()
    # Normalize file to:
    # 1 border
    # 2 title
    # 3 border
    # 4 blank
    # 5 duplicate title
    # 6 blank
    # 7+ content
    content_start = 4
    # If line 5 already equals title, keep file.
    if len(lines) >= 5 and lines[4].strip() == title:
        continue
    # Remove any existing line 5 if it looks like a title/garbage or prose placeholder.
    body = lines[4:] if len(lines) >= 5 else []
    # Rebuild with duplicate title on line 5.
    new_lines = lines[:4] + [title, ''] + body
    p.write_text('\n'.join(new_lines).rstrip() + '\n', encoding='utf-8')
    changed += 1
print(f'changed={changed}')
