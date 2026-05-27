import re, json, sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(r'C:\Dev\MTC')
PAT = re.compile(r'(?i)^(?:chương|chuong)\s*(\d+)\s*(.*)\.txt$')

# Keywords that usually indicate final chapter / ending note
ENDING_KEYWORDS = [
    'kết cục', 'đại kết cục', 'kết thúc', 'hết', 'hoàn', 'end',
    'lời cuối', 'đóng sách', 'hoàn thành', 'the end', 'finale', 'epilogue'
]

rows = []
for folder in sorted([p for p in ROOT.iterdir() if p.is_dir() and p.name != '.git'], key=lambda p: p.name.lower()):
    best = None
    for f in folder.glob('*.txt'):
        m = PAT.match(f.name)
        if not m:
            continue
        idx = int(m.group(1))
        title = (m.group(2) or '').strip()
        rec = {
            'chapter': idx,
            'title': title,
            'filename': f.name,
            'size': f.stat().st_size,
        }
        if best is None or idx > best['chapter']:
            best = rec

    if not best:
        rows.append({
            'folder': folder.name,
            'latest_chapter': None,
            'latest_title': None,
            'looks_like_ending': False,
            'reason': 'no_chapter_files',
        })
        continue

    t = best['title'].lower()
    looks_like = any(k in t for k in ENDING_KEYWORDS)
    rows.append({
        'folder': folder.name,
        'latest_chapter': best['chapter'],
        'latest_title': best['title'],
        'latest_filename': best['filename'],
        'looks_like_ending': looks_like,
    })

not_ending = [r for r in rows if not r.get('looks_like_ending')]
ending = [r for r in rows if r.get('looks_like_ending')]

out = {
    'total_folders': len(rows),
    'ending_title_count': len(ending),
    'not_ending_title_count': len(not_ending),
    'not_ending_title_folders': not_ending,
    'ending_title_folders': ending,
}

out_path = Path(r'C:\Dev\MTC_Download\logs\mtc_latest_chapter_title_ending_check.json')
out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

print(str(out_path))
print(f"total_folders={out['total_folders']}")
print(f"ending_title_count={out['ending_title_count']}")
print(f"not_ending_title_count={out['not_ending_title_count']}")
