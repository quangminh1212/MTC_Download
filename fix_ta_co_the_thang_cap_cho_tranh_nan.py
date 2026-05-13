#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import json, re

ROOT = Path(r'C:\Dev\MTC\Ta Có Thể Thăng Cấp Chỗ Tránh Nạn')
REPORT = Path(r'C:\Dev\MTC_Download\logs\fix_ta_co_the_thang_cap_cho_tranh_nan_report.json')
REPORT.parent.mkdir(parents=True, exist_ok=True)
pat = re.compile(r'^\s*Chương\s*(\d+)\s*[:., ]*\s*(.*)$', re.I)
name_num_pat = re.compile(r'Chương\s*(\d+)', re.I)


def first_chapter_line(p: Path):
    try:
        lines = p.read_text(encoding='utf-8', errors='replace').splitlines()
    except Exception:
        return None
    for line in lines[:8]:
        s = line.strip().strip('= ').strip()
        m = pat.match(s)
        if m:
            num = int(m.group(1))
            title = (m.group(2) or '').strip(' .')
            return num, title, s
    return None


def sanitize_title(title: str) -> str:
    s = title.strip()
    s = s.replace('/', ' ').replace('\\', ' ')
    s = re.sub(r'[<>:"|?*\[\]{}()+!;\'`]', ' ', s)
    s = re.sub(r'[-–—]+', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip(' .')
    return s


def desired_name(num: int, title: str) -> str:
    title = sanitize_title(title)
    return f'Chương {num} {title}.txt' if title else f'Chương {num}.txt'


def score_file(p: Path):
    txt = p.read_text(encoding='utf-8', errors='replace')[:600]
    score = p.stat().st_size
    if '============================================================' in txt:
        score += 500
    if 'Untitled' in p.name:
        score -= 2000
    if '�' in txt or '�' in p.name:
        score -= 3000
    if re.search(r'Chương\s*\d+[.,]\d+', p.name):
        score -= 1000
    return score

files = sorted([p for p in ROOT.glob('*.txt') if p.is_file()])
renamed = []
unchanged = []
manual = []
for p in files:
    meta = first_chapter_line(p)
    if not meta:
        continue
    actual_num, actual_title, raw = meta
    want = desired_name(actual_num, actual_title)
    if p.name == want:
        unchanged.append(p.name)
        continue
    target = p.with_name(want)
    if target.exists() and target != p:
        # keep the better file under target name, remove/rename the weaker one
        keep = target if score_file(target) >= score_file(p) else p
        drop = p if keep == target else target
        if keep == p:
            p.rename(target.with_name(target.stem + ' __tmpreplace.txt'))
            target.unlink(missing_ok=True)
            (target.with_name(target.stem + ' __tmpreplace.txt')).rename(target)
            renamed.append({'old': str(p), 'new': str(target), 'replaced': str(drop)})
        else:
            drop.unlink(missing_ok=True)
            renamed.append({'old': str(drop), 'new': '(deleted duplicate kept existing target)'})
    else:
        p.rename(target)
        renamed.append({'old': str(p), 'new': str(target)})

# pass 2 dedupe by chapter number, keep best-scoring file
by_num = {}
for p in ROOT.glob('*.txt'):
    m = name_num_pat.search(p.name)
    if not m:
        continue
    by_num.setdefault(int(m.group(1)), []).append(p)
removed = []
for num, arr in by_num.items():
    if len(arr) <= 1:
        continue
    arr = sorted(arr, key=score_file, reverse=True)
    keep = arr[0]
    for p in arr[1:]:
        removed.append({'chapter': num, 'remove': str(p), 'keep': str(keep)})
        p.unlink(missing_ok=True)

REPORT.write_text(json.dumps({'renamed_count': len(renamed), 'removed_count': len(removed), 'renamed': renamed, 'removed': removed, 'unchanged_count': len(unchanged)}, ensure_ascii=False, indent=2), encoding='utf-8')
print('renamed_count', len(renamed))
print('removed_count', len(removed))
print('report', REPORT)
for row in renamed[:120]:
    print('RENAME', row)
for row in removed[:120]:
    print('REMOVE', row)
