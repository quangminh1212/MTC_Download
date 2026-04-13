import os
import re
from pathlib import Path
imports = {}
for path in Path('.').rglob('*.py'):
    if '.venv' in path.parts or path.match('**/__pycache__/**'):
        continue
    try:
        txt = path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        continue
    for m in re.findall(r'^(?:from|import)\s+([A-Za-z0-9_\.]+)', txt, flags=re.MULTILINE):
        pkg = m.split('.')[0]
        imports[pkg] = imports.get(pkg, 0) + 1
for k, v in sorted(imports.items(), key=lambda x: (-x[1], x[0])):
    print(f'{k}: {v}')
