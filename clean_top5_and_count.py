#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import json, re, unicodedata, hashlib

MTC = Path(r'C:\Dev\MTC')
MANIFEST = Path(r'C:\Dev\MTC_Download\logs\bookmarked_books_manifest.json')
REPORT = Path(r'C:\Dev\MTC_Download\logs\clean_top5_and_count_report.json')
REPORT.parent.mkdir(parents=True, exist_ok=True)

TOP_N = 5
BOOKS = json.loads(MANIFEST.read_text(encoding='utf-8'))['books'][:TOP_N]

HEADER_PAT = re.compile(r'^\s*Chương\s*(\d+)\s*[:., ]*\s*(.*)$', re.I)
NAME_NUM_PAT = re.compile(r'Chương\s*(\d+)', re.I)
BAD_HEAD_PAT = re.compile(r'[�\x00-\x08\x0b\x0c\x0e-\x1f]')

BAD_CHARS = set('+()[]{}!?:;"\'`*<>|')
DASH = set('-–—―−')

def sanitize_component(s: str) -> str:
    s = unicodedata.normalize('NFC', s or '')
    s = re.sub(r'[\x00-\x1f\x7f]', '', s)
    out=[]
    for ch in s:
        if ch in BAD_CHARS or ch in DASH or ch in '/\\': out.append(' ')
        else: out.append(ch)
    s=''.join(out)
    s=re.sub(r'\s+', ' ', s).strip(' .')
    return s


def book_folder_name(name: str) -> str:
    return sanitize_component(name.replace('?', ''))


def first_header(p: Path):
    try:
        lines = p.read_text(encoding='utf-8', errors='replace').splitlines()
    except Exception:
        return None
    for line in lines[:12]:
        s = line.strip().strip('= ').strip()
        m = HEADER_PAT.match(s)
        if m:
            title = sanitize_component(m.group(2).strip())
            return int(m.group(1)), title, s
    # fallback name number
    m = NAME_NUM_PAT.search(p.name)
    if m:
        return int(m.group(1)), sanitize_component(Path(p.name).stem), ''
    return None


def normalized_body_hash(p: Path) -> str:
    txt = p.read_text(encoding='utf-8', errors='replace')
    txt = re.sub(r'^=+\s*$', '', txt, flags=re.M)
    txt = re.sub(r'\s+', ' ', txt).strip()
    return hashlib.sha1(txt.encode('utf-8', errors='replace')).hexdigest()


def score(p: Path) -> int:
    txt = p.read_text(encoding='utf-8', errors='replace')[:1000]
    sc = p.stat().st_size
    if '============================================================' in txt: sc += 500
    if BAD_HEAD_PAT.search(txt): sc -= 5000
    if 'Untitled' in p.name: sc -= 2000
    if re.search(r'\b2\.txt$', p.name): sc -= 500
    return sc


def desired_name(num: int, title: str) -> str:
    return f'Chương {num} {title}.txt' if title else f'Chương {num}.txt'


def safe_rename(p: Path, target: Path, actions):
    if p == target:
        return target
    if target.exists():
        # choose better target; delete worse duplicate if same chapter
        if score(p) > score(target):
            tmp = target.with_name(target.stem + ' __replace_tmp.txt')
            p.rename(tmp)
            target.unlink(missing_ok=True)
            tmp.rename(target)
            actions.append({'action':'replace', 'old':str(p), 'new':str(target)})
            return target
        else:
            p.unlink(missing_ok=True)
            actions.append({'action':'delete_duplicate_target_exists', 'old':str(p), 'keep':str(target)})
            return target
    p.rename(target)
    actions.append({'action':'rename', 'old':str(p), 'new':str(target)})
    return target

report=[]
for b in BOOKS:
    folder = MTC / book_folder_name(b['name'])
    if not folder.exists():
        # try startswith id-independent rough match
        cand = [p for p in MTC.iterdir() if p.is_dir() and sanitize_component(p.name).lower() == book_folder_name(b['name']).lower()]
        folder = cand[0] if cand else folder
    entry={'id':b['id'], 'name':b['name'], 'folder':str(folder), 'expected_remote_latest_index':b.get('latest_index'), 'exists':folder.exists(), 'actions':[]}
    if not folder.exists():
        report.append(entry); continue

    # pass 1 rename by header
    for p in sorted(folder.glob('*.txt')):
        meta = first_header(p)
        if not meta: continue
        num,title,_ = meta
        safe_rename(p, p.with_name(desired_name(num,title)), entry['actions'])

    # pass 2 group by chapter, remove duplicates; if distinct title under same num, still keep best because chapter num must be unique
    groups={}
    for p in folder.glob('*.txt'):
        meta = first_header(p)
        if not meta: continue
        groups.setdefault(meta[0], []).append(p)
    removed=[]
    for num, arr in sorted(groups.items()):
        if len(arr)<=1: continue
        # Prefer non-garbled, larger, header wrapper; exact duplicate hashes first don't matter since keep best
        arr=sorted(arr, key=score, reverse=True)
        keep=arr[0]
        for p in arr[1:]:
            removed.append({'chapter':num, 'remove':str(p), 'keep':str(keep), 'same_hash': normalized_body_hash(p)==normalized_body_hash(keep)})
            p.unlink(missing_ok=True)
    entry['removed_duplicate_chapters']=removed

    # final stats
    nums=[]
    no_num=[]
    for p in folder.glob('*.txt'):
        meta=first_header(p)
        if meta: nums.append(meta[0])
        else: no_num.append(p.name)
    nums_sorted=sorted(set(nums))
    expected=b.get('latest_index') or 0
    missing=[n for n in range(1, expected+1) if n not in nums_sorted]
    extra=[n for n in nums_sorted if expected and n>expected]
    entry.update({
        'local_files': len(list(folder.glob('*.txt'))),
        'unique_chapters': len(nums_sorted),
        'min_chapter': nums_sorted[0] if nums_sorted else None,
        'max_chapter': nums_sorted[-1] if nums_sorted else None,
        'missing_count': len(missing),
        'missing_ranges': [],
        'extra_chapters': extra[:50],
        'no_num_files': no_num[:50],
        'dupe_after_count': sum(1 for v in groups.values() if len(v)>1),
    })
    # compress missing ranges
    ranges=[]
    if missing:
        start=prev=missing[0]
        for n in missing[1:]:
            if n==prev+1: prev=n
            else:
                ranges.append(f'{start}' if start==prev else f'{start}-{prev}')
                start=prev=n
        ranges.append(f'{start}' if start==prev else f'{start}-{prev}')
    entry['missing_ranges']=ranges[:80]
    report.append(entry)

REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
for e in report:
    print('---')
    print(e['name'])
    print('folder_exists', e['exists'])
    if e['exists']:
        print('files', e['local_files'], 'unique', e['unique_chapters'], 'remote_latest', e['expected_remote_latest_index'], 'missing', e['missing_count'], 'dupe_after', e['dupe_after_count'], 'actions', len(e['actions']), 'removed', len(e.get('removed_duplicate_chapters',[])))
        if e['missing_ranges'][:10]: print('missing_ranges', ', '.join(e['missing_ranges'][:10]))
print('REPORT', REPORT)
