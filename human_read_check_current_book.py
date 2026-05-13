from pathlib import Path
import re, sys, unicodedata
if hasattr(sys.stdout,'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT=Path(r'C:\Dev\MTC\Tiền Hạo Kiếp Tây Du')

BAD_CHARS=re.compile(r'[�\x00-\x08\x0b\x0c\x0e-\x1f]')
MOJI=re.compile(r'[ÃÂÄÅÐÑÒÓÔÕÖØÙÚÛÜÝÞßð]|\u061d|\u0590|\u05ff|\u07ff')
# chars that are weird in Vietnamese prose when appearing in body
WEIRD=set('�֡�')

issues=[]
summary=[]
for p in sorted(ROOT.glob('*.txt')):
    if p.name.startswith('_'): continue
    text=p.read_text(encoding='utf-8', errors='replace')
    lines=text.splitlines()
    chap_issue=[]
    if len(lines)<5:
        chap_issue.append(f'too_few_lines={len(lines)}')
    if len(lines)>=3:
        if set(lines[0])!={'='} or set(lines[2])!={'='}:
            chap_issue.append('bad_header_border')
        if not lines[1].startswith('Chương '):
            chap_issue.append(f'bad_header_title={lines[1]!r}')
    # first content line expected at line 5 and should look like prose/dialogue, not title fragment or garbage
    if len(lines)>=5:
        l5=lines[4].strip()
        if not l5:
            chap_issue.append('line5_blank')
        if BAD_CHARS.search(l5):
            chap_issue.append(f'line5_bad_chars={l5!r}')
        if len(l5)<20 and not l5.startswith('-'):
            chap_issue.append(f'line5_too_short={l5!r}')
        if re.match(r'^(Chương|Chuong|Chư)', l5, re.I):
            chap_issue.append(f'line5_duplicate_title={l5!r}')
    for i,line in enumerate(lines,1):
        if BAD_CHARS.search(line):
            chap_issue.append(f'bad_control_or_replacement_line_{i}={line[:120]!r}')
        # detect Arabic/Hebrew/Cyrillic chunks that should not be in Vietnamese novel text
        for ch in line:
            o=ord(ch)
            if (0x0590<=o<=0x08FF) or ch in WEIRD:
                chap_issue.append(f'weird_unicode_line_{i}=U+{o:04X} {line[:120]!r}')
                break
        if MOJI.search(line):
            # allow normal Vietnamese Đ/đ etc; regex excludes them, catches mojibake latin remnants mostly
            chap_issue.append(f'possible_mojibake_line_{i}={line[:120]!r}')
    # check encrypted residue
    if any(len(x.strip())>200 and re.fullmatch(r'[A-Za-z0-9+/=]+', x.strip()) for x in lines):
        chap_issue.append('encrypted_base64_residue')
    summary.append((p.name, len(lines), len(text), chap_issue[:10]))
    for issue in chap_issue:
        issues.append((p.name, issue))

print('chapters=', len(summary))
print('issues=', len(issues))
for name, issue in issues[:200]:
    print('ISSUE', name, '::', issue)
print('--- SAMPLE OPENINGS ---')
for idx in [0,1,7,12,24,37,50]:
    if idx < len(summary):
        p=sorted([x for x in ROOT.glob('*.txt') if not x.name.startswith('_')])[idx]
        lines=p.read_text(encoding='utf-8', errors='replace').splitlines()
        print('FILE', p.name)
        for n in range(1, min(9,len(lines))+1):
            print(f'{n}: {lines[n-1]}')
        print('---')
