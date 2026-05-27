#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, r'C:\Dev\MTC_DOWNLOAD\scripts\download')
sys.path.insert(0, r'C:\Dev\MTC_DOWNLOAD\scripts')

from mtc_downloader import MTCDownloader
from download_all_missing_books import strict_chapter_filename, strict_component
from download_one_completed_live_decrypt import maybe_decrypt, normalize_chapter_title, sanitize_path_component, write_plain_chapter
from download_ongoing_to_repo import ROOT, commit_folder, local_index_set

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

AUDIT = Path(r'C:\Dev\MTC_Download\logs\unfinished_repo_content_audit.json')
REPORT = Path(r'C:\Dev\MTC_Download\logs\repair_unfinished_repo_issues_report.json')
CHAPTER_RE = re.compile(r'(?i)(?:chương|chuong)\s*(\d+)')
MIN_BYTES = 500
MIN_BODY_CHARS = 100


def chapter_index(path: Path) -> int | None:
    match = CHAPTER_RE.search(path.stem)
    return int(match.group(1)) if match else None


def body_chars(path: Path) -> int:
    text = path.read_text(encoding='utf-8', errors='replace')
    parts = text.split('=' * 60)
    body = parts[-1].strip() if len(parts) >= 3 else text.strip()
    return len(body)


def load_info(folder: Path) -> dict:
    return json.loads((folder / 'info.json').read_text(encoding='utf-8'))


def chapter_map(info: dict) -> dict[int, tuple[int, dict]]:
    out = {}
    for seq, chapter in enumerate(info.get('chapters') or [], 1):
        idx = int(chapter.get('index') or chapter.get('number') or seq)
        out[idx] = (seq, chapter)
    return out


def bad_local_indices(folder: Path) -> set[int]:
    bad = set()
    for path in folder.glob('*.txt'):
        idx = chapter_index(path)
        if idx is None:
            continue
        try:
            if path.stat().st_size < MIN_BYTES or body_chars(path) < MIN_BODY_CHARS:
                bad.add(idx)
        except Exception:
            bad.add(idx)
    return bad


def prune_folder(folder: Path, expected: set[int]) -> dict:
    by_index = {}
    unknown_deleted = []
    extra_deleted = []
    duplicate_deleted = []
    for path in sorted(folder.glob('*.txt')):
        idx = chapter_index(path)
        if idx is None:
            path.unlink(missing_ok=True)
            unknown_deleted.append(path.name)
            continue
        if idx not in expected:
            path.unlink(missing_ok=True)
            extra_deleted.append(path.name)
            continue
        by_index.setdefault(idx, []).append(path)

    for idx, paths in by_index.items():
        if len(paths) <= 1:
            continue
        paths.sort(key=lambda p: (-p.stat().st_size, p.name.casefold()))
        for extra in paths[1:]:
            extra.unlink(missing_ok=True)
            duplicate_deleted.append(extra.name)
    return {
        'unknown_deleted': unknown_deleted,
        'extra_deleted': extra_deleted,
        'duplicate_deleted': duplicate_deleted,
    }


def download_index(downloader: MTCDownloader, folder: Path, idx: int, seq: int, chapter: dict) -> tuple[bool, str]:
    chapter_id = chapter.get('id')
    for attempt in range(1, 6):
        try:
            detail = downloader.get_chapter_content(chapter_id)
            data = (detail or {}).get('data') or {}
            content = data.get('content') or data.get('body') or ''
            if not content:
                raise ValueError('empty content')
            plain, _ = maybe_decrypt(content)
            title = normalize_chapter_title(data.get('name') or chapter.get('name') or f'Chương {idx}', idx)
            safe_title = sanitize_path_component(strict_component(title, default=f'Chương {idx}'))
            path = folder / sanitize_path_component(strict_chapter_filename(data or chapter, seq))
            write_plain_chapter(path, safe_title, plain)
            if path.stat().st_size < MIN_BYTES or body_chars(path) < MIN_BODY_CHARS:
                raise ValueError(f'content too short after write bytes={path.stat().st_size} body={body_chars(path)}')
            return True, path.name
        except Exception as exc:
            if attempt == 5:
                return False, f'idx={idx} chapter_id={chapter_id}: {exc}'
            time.sleep(0.5 * attempt)
    return False, f'idx={idx} chapter_id={chapter_id}: unknown'


def repair_folder(downloader: MTCDownloader, issue: dict, delay: float, dry_run: bool) -> dict:
    folder = ROOT / issue['folder']
    info = load_info(folder)
    remote = chapter_map(info)
    expected = set(remote)
    result = {
        'folder': folder.name,
        'id': info.get('id'),
        'pruned': {},
        'redownloaded': [],
        'failed': [],
        'commit': None,
    }
    if dry_run:
        result['dry_run'] = True
        return result

    result['pruned'] = prune_folder(folder, expected)
    have = local_index_set(folder)
    targets = set(issue.get('missing') or []) | (expected - have) | bad_local_indices(folder)
    for idx in sorted(targets):
        if idx not in remote:
            result['failed'].append(f'idx={idx}: not in info.json chapters')
            continue
        seq, chapter = remote[idx]
        ok, message = download_index(downloader, folder, idx, seq, chapter)
        if ok:
            result['redownloaded'].append(message)
        else:
            result['failed'].append(message)
        time.sleep(delay)

    result['commit'] = commit_folder(folder, folder.name)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--delay', type=float, default=0.05)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    audit = json.loads(AUDIT.read_text(encoding='utf-8'))
    issues = [row for row in audit.get('folders', []) if row.get('status') == 'issue']
    if args.limit:
        issues = issues[:args.limit]

    downloader = MTCDownloader()
    rows = []
    summary = {
        'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'processed': 0,
        'failed_folders': [],
        'rows': rows,
    }
    for pos, issue in enumerate(issues, 1):
        print(f'[{pos}/{len(issues)}] repair {issue["folder"]}', flush=True)
        try:
            row = repair_folder(downloader, issue, delay=args.delay, dry_run=args.dry_run)
        except Exception as exc:
            row = {'folder': issue.get('folder'), 'status': 'repair_error', 'error': str(exc)}
        rows.append(row)
        summary['processed'] = len(rows)
        summary['failed_folders'] = [item['folder'] for item in rows if item.get('failed') or item.get('status') == 'repair_error']
        REPORT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"  redownloaded={len(row.get('redownloaded') or [])} failed={len(row.get('failed') or [])} commit={(row.get('commit') or {}).get('status')}", flush=True)

    print(f'REPORT={REPORT}')
    return 0 if not summary['failed_folders'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
