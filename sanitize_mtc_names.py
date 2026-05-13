#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import json, re, unicodedata

ROOT = Path(r'C:\Dev\MTC')
REPORT = Path(r'C:\Dev\MTC_Download\logs\sanitize_mtc_names_report.json')
REPORT.parent.mkdir(parents=True, exist_ok=True)

# Giữ tiếng Việt; chỉ bỏ ký tự punctuation dễ gây lỗi path/git/shell hoặc theo rule MTC.
REMOVE_CHARS = set('+()[]{}!?:;"\'`*<>|')
REPLACE_WITH_SPACE = set('/\\')
DASH_CHARS = '-–—―−'
CONTROL_RE = re.compile(r'[\x00-\x1f\x7f]')
SPACE_RE = re.compile(r'\s+')


def sanitize_name(name: str) -> str:
    stem = name
    suffix = ''
    # File có extension thì giữ extension, chỉ sanitize phần stem.
    if '.' in name and not name.startswith('.'):
        p = Path(name)
        stem = p.stem
        suffix = p.suffix
    s = unicodedata.normalize('NFC', stem)
    s = CONTROL_RE.sub('', s)
    out = []
    for ch in s:
        if ch in REMOVE_CHARS or ch in DASH_CHARS:
            out.append(' ')
        elif ch in REPLACE_WITH_SPACE:
            out.append(' ')
        else:
            out.append(ch)
    s = ''.join(out)
    s = SPACE_RE.sub(' ', s).strip(' .')
    if not s:
        s = 'unnamed'
    # Windows reserved device names.
    if s.upper() in {'CON','PRN','AUX','NUL',*(f'COM{i}' for i in range(1,10)),*(f'LPT{i}' for i in range(1,10))}:
        s = '_' + s
    return s + suffix


def unique_target(parent: Path, new_name: str, original: Path) -> Path:
    target = parent / new_name
    if target == original:
        return target
    if not target.exists():
        return target
    stem = Path(new_name).stem
    suffix = Path(new_name).suffix
    i = 2
    while True:
        cand = parent / f'{stem} {i}{suffix}'
        if cand == original or not cand.exists():
            return cand
        i += 1

items = sorted([p for p in ROOT.rglob('*')], key=lambda p: len(str(p)), reverse=True)
renamed = []
skipped = []
for p in items:
    old_name = p.name
    new_name = sanitize_name(old_name)
    if new_name == old_name:
        continue
    target = unique_target(p.parent, new_name, p)
    try:
        p.rename(target)
        renamed.append({'old': str(p), 'new': str(target)})
    except Exception as e:
        skipped.append({'path': str(p), 'target': str(target), 'error': str(e)})

REPORT.write_text(json.dumps({'root': str(ROOT), 'renamed_count': len(renamed), 'skipped_count': len(skipped), 'renamed': renamed, 'skipped': skipped}, ensure_ascii=False, indent=2), encoding='utf-8')
print('renamed_count', len(renamed))
print('skipped_count', len(skipped))
print('report', REPORT)
for row in renamed[:120]:
    print(row['old'], '=>', row['new'])
if len(renamed) > 120:
    print('... more in report')
