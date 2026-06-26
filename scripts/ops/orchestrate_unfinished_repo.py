#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(r'C:\\Dev\\MTC_Download')
PYTHON = sys.executable
ENV_PYTHONPATH = r'C:\Dev\MTC_DOWNLOAD\scripts\download;C:\Dev\MTC_DOWNLOAD\scripts'
LOG_DIR = BASE / 'logs'
ORCH_LOG = LOG_DIR / 'orchestrate_unfinished_repo.log'

AUDIT = BASE / 'scripts' / 'audit' / 'audit_unfinished_repo_content.py'
REPAIR = BASE / 'scripts' / 'repair' / 'repair_unfinished_repo_issues.py'
DOWNLOAD = BASE / 'scripts' / 'download' / 'download_ongoing_to_repo.py'


def run_step(label: str, cmd: list[str]) -> int:
    with ORCH_LOG.open('a', encoding='utf-8') as log:
        stamp = time.strftime('%Y-%m-%d %H:%M:%S')
        log.write(f'\n=== {stamp} {label} START ===\n')
        log.write('CMD: ' + ' '.join(cmd) + '\n')
        proc = subprocess.run(
            cmd,
            cwd=str(BASE),
            text=True,
            encoding='utf-8',
            errors='replace',
            env={**dict(**__import__('os').environ), 'PYTHONPATH': ENV_PYTHONPATH, 'PYTHONIOENCODING': 'utf-8'},
            stdout=log,
            stderr=log,
            check=False,
        )
        log.write(f'=== {label} END rc={proc.returncode} ===\n')
        return proc.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description='Run audit -> repair -> downloader -> audit for unfinished MTC repo.')
    parser.add_argument('--repair-limit', type=int, default=None)
    parser.add_argument('--download-limit', type=int, default=None)
    parser.add_argument('--include-paused', action='store_true', default=True)
    parser.add_argument('--passes', type=int, default=2)
    args = parser.parse_args()

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    for current_pass in range(1, max(1, args.passes) + 1):
        run_step(f'pass_{current_pass}_audit_before', [PYTHON, str(AUDIT)])

        repair_cmd = [PYTHON, str(REPAIR), '--delay', '0.03']
        if args.repair_limit is not None:
            repair_cmd += ['--limit', str(args.repair_limit)]
        run_step(f'pass_{current_pass}_repair', repair_cmd)

        download_cmd = [PYTHON, str(DOWNLOAD), '--rebuild-queue']
        if args.include_paused:
            download_cmd.append('--include-paused')
        if args.download_limit is not None:
            download_cmd += ['--limit', str(args.download_limit)]
        run_step(f'pass_{current_pass}_download', download_cmd)

        run_step(f'pass_{current_pass}_audit_after', [PYTHON, str(AUDIT)])

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
