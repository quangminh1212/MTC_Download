#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, re, unicodedata
from pathlib import Path

ROOT = Path(r'C:\Dev\MTC\Từ Đội Sản Xuất Đuổi Đại Xa Bắt Đầu')
REPORT = ROOT / '_dedupe_report.json'
pat = re.compile(r'Chương\s*(\d+)', re.I)

BAD_CHARS = set('�?')

def extract_num(name: str):
    m = pat.search(name)
    return int(m.group(1)) if m else None

def score_name(name: str, size: int):
    base = name
    score = 0
    score += size // 100
    score -= sum(ch in BAD_CHARS for ch in base) * 200
    score -= sum(ord(ch) < 32 for ch in base) * 200
    score -= base.count('__') * 20
    score -= base.count('  ') * 5
    score += sum(1 for ch in base if ch.isalpha())
    score += sum(1 for ch in base if ch in 'àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ()[],-')
    norm = unicodedata.normalize('NFKC', base)
    if norm == base:
        score += 10
    return score

files = [p for p in ROOT.glob('*.txt') if p.is_file()]
groups = {}
for p in files:
    n = extract_num(p.name)
    if n is None:
        continue
    groups.setdefault(n, []).append(p)

removed = []
kept = []
for n, arr in sorted(groups.items()):
    if len(arr) <= 1:
        continue
    ranked = sorted(arr, key=lambda p: (score_name(p.name, p.stat().st_size), p.stat().st_size, -len(p.name)), reverse=True)
    keep = ranked[0]
    kept.append({'chapter': n, 'keep': keep.name, 'candidates': [p.name for p in ranked]})
    for p in ranked[1:]:
        removed.append({'chapter': n, 'remove': p.name, 'keep': keep.name})
        p.unlink(missing_ok=True)

REPORT.write_text(json.dumps({'removed_count': len(removed), 'removed': removed[:2000], 'kept_multi': kept[:2000]}, ensure_ascii=False, indent=2), encoding='utf-8')
print('groups_with_dupes', sum(1 for v in groups.values() if len(v) > 1))
print('removed_count', len(removed))
for row in removed[:80]:
    print(f"chapter {row['chapter']}: remove={row['remove']} keep={row['keep']}")
print('report', REPORT)
