from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(r'C:\Dev\MTC_Continune')
LOG = Path(r'C:\Dev\MTC_Download\logs\verified_commit_worker.log')
WORKER_LOCK = Path(r'C:\Dev\MTC_Download\tmp\verified_commit_worker.singleton.lock')
SKIP_CACHE: dict[str, tuple[float, str, float]] = {}
PUSH_EVERY_COMMITS = 1
PUSH_EVERY_SECONDS = 30
INCOMPLETE_RECHECK_SECONDS = 600
CHAP_RE = re.compile(r'(?i)^Chương\s+(\d+)\b')
IGNORE = {'.git', '.claude', '.vscode', '_bad_quarantine', 'mtc_done'}
GIT_TIMEOUT_SECONDS = 120
PUSH_TIMEOUT_SECONDS = 300


def log(message: str) -> None:
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    try:
        print(line, flush=True)
    except UnicodeEncodeError:
        safe = line.encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8', errors='replace')
        print(safe, flush=True)
    with LOG.open('a', encoding='utf-8') as f:
        f.write(line + '\n')


def run_git(args: list[str], timeout: int = GIT_TIMEOUT_SECONDS) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ['git', '-C', str(ROOT), *args],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ''
        stderr = exc.stderr if isinstance(exc.stderr, str) else ''
        log(f'git_timeout args={args!r} err={(stdout + stderr).strip()[:500]}')
        return subprocess.CompletedProcess(['git', '-C', str(ROOT), *args], 124, stdout or '', stderr or 'timeout')


def run_git_push() -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ['git', '-C', str(ROOT), 'push'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=PUSH_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ''
        stderr = exc.stderr if isinstance(exc.stderr, str) else ''
        log(f'git_push_timeout err={(stdout + stderr).strip()[:500]}')
        return subprocess.CompletedProcess(['git', '-C', str(ROOT), 'push'], 124, stdout or '', stderr or 'timeout')

def candidate_folders() -> list[Path]:
    folders = []
    now = time.time()
    with os.scandir(ROOT) as entries:
        for entry in entries:
            if not entry.is_dir() or entry.name in IGNORE:
                continue
            folder = ROOT / entry.name
            if not (folder / 'info.json').exists():
                continue
            try:
                mtime = entry.stat().st_mtime
            except OSError:
                continue
            cached = SKIP_CACHE.get(entry.name)
            if cached and cached[0] == mtime and now - cached[2] < INCOMPLETE_RECHECK_SECONDS:
                continue
            folders.append((mtime, folder))
    folders.sort(key=lambda item: item[0], reverse=True)
    return [folder for _, folder in folders]


def commit_folder(folder: Path) -> bool:
    mtime = folder.stat().st_mtime if folder.exists() else 0
    cached = SKIP_CACHE.get(folder.name)
    now = time.time()
    if cached and cached[0] == mtime and now - cached[2] < INCOMPLETE_RECHECK_SECONDS:
        return False
    SKIP_CACHE.pop(folder.name, None)
    add = run_git(['add', '--', folder.name])
    if add.returncode != 0:
        log(f'add_failed folder={folder.name} err={(add.stdout + add.stderr).strip()[:500]}')
        return False
    diff = run_git(['diff', '--cached', '--quiet', '--', folder.name])
    if diff.returncode == 0:
        SKIP_CACHE[folder.name] = (mtime, 'no_changes', now)
        return False
    if diff.returncode != 1:
        log(f'diff_cached_failed folder={folder.name} err={(diff.stdout + diff.stderr).strip()[:500]}')
        return False
    commit = run_git(['commit', '--untracked-files=no', '-m', folder.name, '--', folder.name])
    out = (commit.stdout + commit.stderr).strip()
    if commit.returncode == 0:
        log(f'committed folder={folder.name}')
        return True
    if 'nothing to commit' in out or 'nothing added to commit' in out or 'no changes added to commit' in out:
        SKIP_CACHE[folder.name] = (mtime, 'no_changes', now)
        log(f'nothing_to_commit folder={folder.name}')
        return False
    log(f'commit_failed folder={folder.name} err={out[:500]}')
    return False


def main() -> None:
    try:
        fd = os.open(str(WORKER_LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode('ascii', errors='ignore'))
        os.close(fd)
    except FileExistsError:
        try:
            age = time.time() - WORKER_LOCK.stat().st_mtime
            if age > 1800:
                WORKER_LOCK.unlink(missing_ok=True)
                return main()
        except Exception:
            pass
        log('another verified_commit_worker is already running; exit')
        return
    last_push = 0.0
    commits_since_push = 0
    try:
        while True:
            folders = candidate_folders()
            if not folders:
                if time.time() - last_push >= PUSH_EVERY_SECONDS:
                    push = run_git(['push'])
                    if push.returncode == 0 and push.stdout.strip():
                        log(push.stdout.strip())
                    last_push = time.time()
                time.sleep(1)
                continue
            start = time.time()
            checked = 0
            for folder in folders:
                checked += 1
                if folder.exists() and commit_folder(folder):
                    commits_since_push += 1
                    if commits_since_push >= PUSH_EVERY_COMMITS:
                        run_git_push()
                        last_push = time.time()
                        commits_since_push = 0
            if commits_since_push and time.time() - last_push >= PUSH_EVERY_SECONDS:
                run_git_push()
                last_push = time.time()
                commits_since_push = 0
            log(f'cycle checked={checked} commits_pending_push={commits_since_push} seconds={time.time()-start:.1f}')
            time.sleep(0.5)
    finally:
        WORKER_LOCK.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
