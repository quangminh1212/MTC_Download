"""List all downloaded chapters with their first real content line."""
import os, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

DOWNLOADS = Path(__file__).resolve().parent.parent / 'downloads'
for d in sorted(os.listdir(DOWNLOADS)):
    sub = DOWNLOADS / d
    if not os.path.isdir(sub):
        continue
    files = sorted(os.listdir(sub))
    print(f'{d}: {len(files)} files')
    for f in files[:3]:
        fpath = sub / f
        with open(fpath, encoding='utf-8', errors='replace') as fp:
            content = fp.read(500)
        lines = [l.strip() for l in content.split('\n') if l.strip() and not l.startswith('=')]
        first = lines[0][:100] if lines else 'EMPTY'
        print(f'  {f[:40]}: {first}')
