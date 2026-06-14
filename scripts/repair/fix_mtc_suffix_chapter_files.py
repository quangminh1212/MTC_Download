#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import re
import time
import zipfile
from pathlib import Path

ROOT = Path(r'C:\Dev\MTC')
LOG_DIR = Path(r'C:\Dev\MTC_Download\logs')
SUFFIX_RE = re.compile(r'^(Chương\s+\d+\s+.+)\s+([12])\.txt$', re.IGNORECASE)
HEADER_LINE = '=' * 60


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='replace')


def write_text(path: Path, text: str):
    path.write_text(text, encoding='utf-8')


def strip_header(text: str) -> tuple[str | None, str]:
    lines = text.splitlines()
    if len(lines) >= 4 and lines[0].strip('=') == '' and lines[2].strip('=') == '':
        title = lines[1].strip()
        body = '\n'.join(lines[4:]).strip()
        return title, body
    return None, text.strip()


def make_chapter_text(title: str, bodies: list[str]) -> str:
    merged = []
    seen = set()
    for body in bodies:
        clean = body.strip()
        if not clean or clean in seen:
            continue
        seen.add(clean)
        merged.append(clean)
    body_text = '\n\n'.join(merged).strip()
    return f'{HEADER_LINE}\n{title}\n{HEADER_LINE}\n\n{body_text}\n'


def backup_files(paths: list[Path], backup_zip: Path):
    with zipfile.ZipFile(backup_zip, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for path in paths:
            zf.write(path, path.relative_to(ROOT).as_posix())


def collect_groups(root: Path):
    groups = {}
    for path in root.rglob('*.txt'):
        if any(part.startswith('_') for part in path.relative_to(root).parts[:-1]):
            continue
        match = SUFFIX_RE.match(path.name)
        if not match:
            continue
        base_title = match.group(1).strip()
        suffix = int(match.group(2))
        key = (path.parent, base_title.casefold())
        groups.setdefault(key, {'parent': path.parent, 'title': base_title, 'items': []})['items'].append({
            'path': path,
            'suffix': suffix,
        })
    for group in groups.values():
        group['items'].sort(key=lambda item: (item['suffix'], item['path'].name))
    return list(groups.values())


def apply_fix(groups: list[dict], dry_run: bool):
    actions = []
    skipped = []
    for group in groups:
        parent = group['parent']
        title = group['title']
        target = parent / f'{title}.txt'
        items = group['items']
        source_paths = [item['path'] for item in items]
        if target.exists() and target not in source_paths:
            skipped.append({
                'reason': 'target_exists',
                'target': str(target),
                'sources': [str(path) for path in source_paths],
            })
            continue
        if len(items) == 1:
            source = items[0]['path']
            old_text = read_text(source)
            old_title, body = strip_header(old_text)
            new_text = make_chapter_text(title, [body]) if old_title else old_text
            actions.append({'action': 'rename', 'source': str(source), 'target': str(target)})
            if not dry_run:
                if source == target:
                    write_text(target, new_text)
                else:
                    source.rename(target)
                    write_text(target, new_text)
            continue
        bodies = []
        for item in items:
            text = read_text(item['path'])
            _, body = strip_header(text)
            bodies.append(body)
        actions.append({
            'action': 'merge',
            'target': str(target),
            'sources': [str(path) for path in source_paths],
        })
        if not dry_run:
            write_text(target, make_chapter_text(title, bodies))
            for source in source_paths:
                if source.exists() and source != target:
                    source.unlink()
    return actions, skipped


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default=str(ROOT))
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    root = Path(args.root).resolve()
    expected = ROOT.resolve()
    if root != expected:
        raise SystemExit(f'refusing to modify unexpected root: {root}')

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    groups = collect_groups(root)
    source_paths = sorted({item['path'] for group in groups for item in group['items']})
    stamp = time.strftime('%Y%m%d_%H%M%S')
    backup_zip = LOG_DIR / f'mtc_suffix_chapter_backup_{stamp}.zip'
    report_path = LOG_DIR / f'mtc_suffix_chapter_fix_report_{stamp}.json'

    if source_paths and not args.dry_run:
        backup_files(source_paths, backup_zip)
    actions, skipped = apply_fix(groups, args.dry_run)
    report = {
        'root': str(root),
        'dry_run': args.dry_run,
        'groups': len(groups),
        'source_files': len(source_paths),
        'actions_count': len(actions),
        'skipped_count': len(skipped),
        'backup_zip': str(backup_zip) if source_paths and not args.dry_run else None,
        'actions': actions,
        'skipped': skipped,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({
        'groups': report['groups'],
        'source_files': report['source_files'],
        'actions_count': report['actions_count'],
        'skipped_count': report['skipped_count'],
        'backup_zip': report['backup_zip'],
        'report': str(report_path),
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
