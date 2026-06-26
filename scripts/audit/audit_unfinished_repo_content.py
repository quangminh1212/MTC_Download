#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(r'D:\\Dev\\MTC_Continune')
LOG_DIR = Path(r'C:\Dev\MTC_Download\logs')
REPORT = LOG_DIR / 'unfinished_repo_content_audit.json'
CHAPTER_RE = re.compile(r'(?i)(?:chương|chuong)\s*(\d+)')
MARKER_RE = re.compile(r'eyJpdiI6|"iv":"|"value":"')
MOJIBAKE_RE = re.compile(r'ChÃ|Ã¡|Ãº|Ã¢|Ãª|Ã´|Ã¹|Ã²|Ã |Ã¨|Ã­|Ã³|Ã½|Ã|Ã|Â|Æ°|Æ¡|áº|á»')
MIN_BYTES = 500
COMPLETED = {'hoàn thành', 'hoan thanh'}


def status_name(info: dict) -> str:
    return str(info.get('status_name') or '').strip()


def is_unfinished(info: dict) -> bool:
    return status_name(info).lower() not in COMPLETED and info.get('status') != 2


def parse_chapter_index(path: Path) -> int | None:
    match = CHAPTER_RE.search(path.stem)
    return int(match.group(1)) if match else None


def expected_indices(info: dict) -> set[int]:
    chapters = info.get('chapters') or []
    out = set()
    for seq, chapter in enumerate(chapters, 1):
        try:
            idx = int(chapter.get('index') or chapter.get('number') or seq)
        except Exception:
            idx = seq
        out.add(idx)
    if out:
        return out
    count = int(info.get('chapter_count') or info.get('latest_index') or 0)
    return set(range(1, count + 1)) if count > 0 else set()


def audit_folder(folder: Path) -> dict:
    info_path = folder / 'info.json'
    try:
        info = json.loads(info_path.read_text(encoding='utf-8'))
    except Exception as exc:
        return {'folder': folder.name, 'status': 'bad_info_json', 'error': str(exc)}

    if not is_unfinished(info):
        return {'folder': folder.name, 'status': 'skipped_completed', 'status_name': status_name(info)}

    expected = expected_indices(info)
    files = sorted(folder.glob('*.txt'))
    by_index: dict[int, list[Path]] = {}
    unknown = []
    small = []
    encrypted = []
    mojibake = []
    empty_body = []

    for path in files:
        idx = parse_chapter_index(path)
        if idx is None:
            unknown.append(path.name)
        else:
            by_index.setdefault(idx, []).append(path)
        size = path.stat().st_size
        if size < MIN_BYTES:
            small.append({'file': path.name, 'bytes': size})
        try:
            text = path.read_text(encoding='utf-8', errors='replace')
        except Exception as exc:
            encrypted.append({'file': path.name, 'error': str(exc)})
            continue
        if MARKER_RE.search(text):
            encrypted.append(path.name)
        if MOJIBAKE_RE.search(text[:4000]):
            mojibake.append(path.name)
        parts = text.split('=' * 60)
        body = parts[-1].strip() if len(parts) >= 3 else text.strip()
        if len(body) < 100:
            empty_body.append({'file': path.name, 'body_chars': len(body)})

    local_indices = set(by_index)
    missing = sorted(expected - local_indices)
    extra = sorted(local_indices - expected)
    duplicates = {str(idx): [p.name for p in paths] for idx, paths in by_index.items() if len(paths) > 1}
    status = 'ok'
    if missing or extra or duplicates or unknown or small or encrypted or empty_body:
        status = 'issue'

    return {
        'folder': folder.name,
        'book_id': info.get('id'),
        'name': info.get('name'),
        'status_name': status_name(info),
        'status': status,
        'expected_count': len(expected),
        'file_count': len(files),
        'unique_local_count': len(local_indices),
        'missing_count': len(missing),
        'missing': missing[:100],
        'extra_count': len(extra),
        'extra': extra[:100],
        'duplicate_count': len(duplicates),
        'duplicates': duplicates,
        'unknown_files': unknown[:50],
        'small_files': small[:50],
        'encrypted_files': encrypted[:50],
        'empty_body_files': empty_body[:50],
        'mojibake_sample_count': len(mojibake),
        'mojibake_samples': mojibake[:20],
        'mojibake_indices': sorted({idx for idx in (parse_chapter_index(Path(name)) for name in mojibake) if idx is not None})[:100],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=None)
    args = parser.parse_args()

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    folders = [p for p in ROOT.iterdir() if p.is_dir() and not p.name.startswith('.') and p.name != 'mtc_done' and (p / 'info.json').is_file()]
    folders.sort(key=lambda p: p.name.casefold())
    if args.limit:
        folders = folders[:args.limit]

    rows = []
    for idx, folder in enumerate(folders, 1):
        row = audit_folder(folder)
        rows.append(row)
        if idx % 50 == 0:
            print(f'audited={idx}/{len(folders)}', flush=True)

    unfinished = [r for r in rows if r.get('status') != 'skipped_completed']
    issues = [r for r in unfinished if r.get('status') != 'ok']
    summary = {
        'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'root': str(ROOT),
        'folders_scanned': len(rows),
        'unfinished_scanned': len(unfinished),
        'ok': sum(1 for r in unfinished if r.get('status') == 'ok'),
        'issues': len(issues),
        'missing_total': sum(int(r.get('missing_count') or 0) for r in issues),
        'extra_total': sum(int(r.get('extra_count') or 0) for r in issues),
        'small_file_total': sum(len(r.get('small_files') or []) for r in issues),
        'encrypted_file_total': sum(len(r.get('encrypted_files') or []) for r in issues),
        'empty_body_total': sum(len(r.get('empty_body_files') or []) for r in issues),
        'issue_folders': [r.get('folder') for r in issues[:100]],
        'folders': rows,
    }
    REPORT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in summary.items() if k != 'folders'}, ensure_ascii=False, indent=2))
    print(f'REPORT={REPORT}')
    return 0 if not issues else 1


if __name__ == '__main__':
    raise SystemExit(main())
