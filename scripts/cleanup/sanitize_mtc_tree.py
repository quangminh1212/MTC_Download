import html
import json
import re
from pathlib import Path

ROOT = Path(r'C:\Dev\MTC')
OUT = Path(r'C:\Dev\MTC_Download\logs\mtc_sanitize_report.json')

INVALID = '<>:"/\\|?*!'
STRIP_PUNCT_RE = re.compile(r'[^\w\sÀ-ỹà-ỹĐđ]+', re.UNICODE)
WS_RE = re.compile(r'\s+')
CHAPTER_RE = re.compile(r'^\s*(?:chương|chuong)\s*(\d+)\s*[:.\-–—]?\s*(.*)$', re.I)


def clean_name(name: str, max_len: int = 170) -> str:
    name = html.unescape(str(name or '')).strip()
    name = STRIP_PUNCT_RE.sub(' ', name)
    for ch in INVALID:
        name = name.replace(ch, ' ')
    name = WS_RE.sub(' ', name).strip(' .')
    return (name or 'Untitled')[:max_len].strip(' .')


def unique_target(path: Path) -> Path | None:
    if not path.exists():
        return path
    return None


def main():
    changes = []
    collisions = []

    # Rename chapter/text files first so folder rename does not invalidate paths.
    for d in sorted([p for p in ROOT.iterdir() if p.is_dir()], key=lambda p: p.name.lower()):
        if d.name in {'.git', '.githooks', '.vscode'}:
            continue
        for f in sorted(d.iterdir(), key=lambda p: p.name.lower()):
            if not f.is_file():
                continue
            if f.name in {'info.json', 'chapters_manifest.json', '.gitkeep'}:
                continue

            stem, suffix = f.stem, f.suffix
            m = CHAPTER_RE.match(stem)
            if suffix.lower() == '.txt' and m:
                idx = int(m.group(1))
                title = clean_name(m.group(2), 130)
                new_name = f'Chương {idx} {title}.txt' if title else f'Chương {idx}.txt'
            else:
                new_name = clean_name(stem, 170) + suffix

            if new_name != f.name:
                target = f.with_name(new_name)
                if target.exists():
                    collisions.append({'type': 'file', 'src': str(f), 'dst': str(target)})
                else:
                    f.rename(target)
                    changes.append({'type': 'file', 'from': str(f), 'to': str(target)})

    # Rename book folders after files.
    for d in sorted([p for p in ROOT.iterdir() if p.is_dir()], key=lambda p: p.name.lower(), reverse=True):
        if d.name in {'.git', '.githooks', '.vscode'}:
            continue
        new_name = clean_name(d.name, 170)
        if new_name != d.name:
            target = d.with_name(new_name)
            if target.exists():
                collisions.append({'type': 'dir', 'src': str(d), 'dst': str(target)})
            else:
                d.rename(target)
                changes.append({'type': 'dir', 'from': str(d), 'to': str(target)})

    report = {
        'changed_count': len(changes),
        'collision_count': len(collisions),
        'changes': changes,
        'collisions': collisions,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(OUT)
    print('changed', len(changes))
    print('collisions', len(collisions))
    for c in collisions[:50]:
        print('COLLISION', c['type'], c['src'], '=>', c['dst'])


if __name__ == '__main__':
    main()
