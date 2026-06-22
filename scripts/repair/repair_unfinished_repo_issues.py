#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
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
from download_top5_bookmarks_to_mtc import BASE, get_json, login_with_retry

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

AUDIT = Path(r'C:\Dev\MTC_Download\logs\unfinished_repo_content_audit.json')
REPORT = Path(r'C:\Dev\MTC_Download\logs\repair_unfinished_repo_issues_report.json')
CHAPTER_RE = re.compile(r'(?i)(?:chương|chuong)\s*(\d+)')
MARKER_RE = re.compile(r'eyJpdiI6|"iv":"|"value":"')
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


def fetch_detail(session, downloader: MTCDownloader, chapter_id: int) -> dict:
    if session is not None:
        payload = get_json(session, BASE + f'/chapters/{chapter_id}')
        return payload.get('data') or {}
    payload = downloader.get_chapter_content(chapter_id)
    return (payload or {}).get('data') or {}


def issue_target_indices(issue: dict) -> set[int]:
    targets = set(int(idx) for idx in (issue.get('missing') or []) if idx)
    for item in issue.get('small_files') or []:
        idx = chapter_index(Path(item.get('file') or ''))
        if idx is not None:
            targets.add(idx)
    for item in issue.get('empty_body_files') or []:
        idx = chapter_index(Path(item.get('file') or ''))
        if idx is not None:
            targets.add(idx)
    for item in issue.get('encrypted_files') or []:
        name = item.get('file') if isinstance(item, dict) else item
        idx = chapter_index(Path(name or ''))
        if idx is not None:
            targets.add(idx)
    for idx in issue.get('mojibake_indices') or []:
        if idx:
            targets.add(int(idx))
    for name in issue.get('mojibake_samples') or []:
        idx = chapter_index(Path(name or ''))
        if idx is not None:
            targets.add(idx)
    for names in (issue.get('duplicates') or {}).values():
        for name in names:
            idx = chapter_index(Path(name or ''))
            if idx is not None:
                targets.add(idx)
    return targets


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



def download_index(session, downloader: MTCDownloader, folder: Path, idx: int, seq: int, chapter: dict) -> tuple[bool, dict]:
    chapter_id = chapter.get('id')
    for attempt in range(1, 6):
        try:
            data = fetch_detail(session, downloader, chapter_id)
            content = data.get('content') or data.get('body') or ''
            if not content:
                if data.get('is_locked'):
                    raise ValueError('locked_unavailable_for_account')
                raise ValueError('empty_content')
            plain, _ = maybe_decrypt(content)
            title = normalize_chapter_title(data.get('name') or chapter.get('name') or f'Chương {idx}', idx)
            safe_title = sanitize_path_component(strict_component(title, default=f'Chương {idx}'))
            path = folder / sanitize_path_component(strict_chapter_filename(data or chapter, seq))
            write_plain_chapter(path, safe_title, plain)
            size = path.stat().st_size
            chars = body_chars(path)
            if size < MIN_BYTES or chars < MIN_BODY_CHARS or MARKER_RE.search(path.read_text(encoding='utf-8', errors='replace')[:4000]):
                raise ValueError(f'content_too_short_after_write bytes={size} body={chars}')
            return True, {
                'index': idx,
                'chapter_id': chapter_id,
                'file': path.name,
                'bytes': size,
                'body_chars': chars,
                'locked': bool(data.get('is_locked')),
            }
        except Exception as exc:
            if attempt == 5:
                return False, {
                    'index': idx,
                    'chapter_id': chapter_id,
                    'locked': None,
                    'error': str(exc),
                }
            time.sleep(0.5 * attempt)
    return False, {
        'index': idx,
        'chapter_id': chapter_id,
        'locked': None,
        'error': 'unknown',
    }


def repair_folder(session, downloader: MTCDownloader, issue: dict, delay: float, dry_run: bool, do_commit: bool) -> dict:
    folder = ROOT / issue['folder']
    info = load_info(folder)
    remote = chapter_map(info)
    expected = set(remote)
    result = {
        'folder': folder.name,
        'id': info.get('id'),
        'pruned': {},
        'targets': [],
        'redownloaded': [],
        'failed': [],
        'commit': None,
    }
    targets = issue_target_indices(issue)
    if dry_run:
        result['dry_run'] = True
        result['targets'] = sorted(targets)
        return result

    result['pruned'] = prune_folder(folder, expected)
    have = local_index_set(folder)
    targets |= (expected - have) | bad_local_indices(folder)
    result['targets'] = sorted(targets)
    for idx in result['targets']:
        if idx not in remote:
            result['failed'].append({'index': idx, 'error': 'not_in_info_json_chapters'})
            continue
        seq, chapter = remote[idx]
        ok, payload = download_index(session, downloader, folder, idx, seq, chapter)
        if ok:
            result['redownloaded'].append(payload)
        else:
            result['failed'].append(payload)
        time.sleep(delay)

    result['commit'] = commit_folder(folder, folder.name) if do_commit else {'status': 'skipped'}
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--delay', type=float, default=0.05)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--folder', default=None)
    parser.add_argument('--no-commit', action='store_true')
    args = parser.parse_args()

    audit = json.loads(AUDIT.read_text(encoding='utf-8'))
    issues = [row for row in audit.get('folders', []) if row.get('status') == 'issue']
    if args.folder:
        wanted = args.folder.casefold()
        issues = [row for row in issues if str(row.get('folder') or '').casefold() == wanted]
    if args.limit:
        issues = issues[:args.limit]

    session = None
    email = os.environ.get('MTC_EMAIL')
    password = os.environ.get('MTC_PASS')
    if email and password:
        session, _token = login_with_retry(email, password)
    downloader = MTCDownloader()
    rows = []
    summary = {
        'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'processed': 0,
        'authenticated': bool(session),
        'failed_folders': [],
        'rows': rows,
    }
    for pos, issue in enumerate(issues, 1):
        print(f'[{pos}/{len(issues)}] repair {issue["folder"]}', flush=True)
        try:
            row = repair_folder(session, downloader, issue, delay=args.delay, dry_run=args.dry_run, do_commit=not args.no_commit)
        except Exception as exc:
            row = {'folder': issue.get('folder'), 'status': 'repair_error', 'error': str(exc)}
        rows.append(row)
        summary['processed'] = len(rows)
        summary['failed_folders'] = [item['folder'] for item in rows if item.get('failed') or item.get('status') == 'repair_error']
        REPORT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"  targets={len(row.get('targets') or [])} redownloaded={len(row.get('redownloaded') or [])} failed={len(row.get('failed') or [])} commit={(row.get('commit') or {}).get('status')}", flush=True)

    print(f'REPORT={REPORT}')
    return 0 if not summary['failed_folders'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
