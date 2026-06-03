from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import uuid
import time
from pathlib import Path

ROOT = Path(r'C:\Dev\MTC_Continune')
LOG = Path(r'C:\Dev\MTC_Download\logs\verified_commit_worker.log')
WORKER_LOCK = Path(r'C:\Dev\MTC_Download\tmp\verified_commit_worker.singleton.lock')
TMP_INDEX_DIR = Path(r'C:\Dev\MTC_Download\tmp\git-indexes')
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


def run_git(args: list[str]) -> subprocess.CompletedProcess:
    return run_git_with_env(args)


def run_git_with_env(args: list[str], extra_env: dict[str, str] | None = None, timeout: int = GIT_TIMEOUT_SECONDS) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    try:
        return subprocess.run(
            ['git', '-C', str(ROOT), *args],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout,
            env=env,
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
    TMP_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    index_path = TMP_INDEX_DIR / f'{os.getpid()}-{uuid.uuid4().hex}.index'
    env = {'GIT_INDEX_FILE': str(index_path)}
    try:
        head = run_git_with_env(['rev-parse', 'HEAD'], env)
        if head.returncode != 0:
            log(f'head_failed folder={folder.name} err={(head.stdout + head.stderr).strip()[:500]}')
            return False
        head_sha = head.stdout.strip()

        read_tree = run_git_with_env(['read-tree', head_sha], env)
        if read_tree.returncode != 0:
            log(f'read_tree_failed folder={folder.name} err={(read_tree.stdout + read_tree.stderr).strip()[:500]}')
            return False

        add = run_git_with_env(['add', '--', folder.name], env)
        if add.returncode != 0:
            log(f'add_failed folder={folder.name} err={(add.stdout + add.stderr).strip()[:500]}')
            return False

        new_tree = run_git_with_env(['write-tree'], env)
        if new_tree.returncode != 0:
            log(f'write_tree_failed folder={folder.name} err={(new_tree.stdout + new_tree.stderr).strip()[:500]}')
            return False
        new_tree_sha = new_tree.stdout.strip()

        head_tree = run_git_with_env(['rev-parse', f'{head_sha}^{{tree}}'], env)
        if head_tree.returncode != 0:
            log(f'head_tree_failed folder={folder.name} err={(head_tree.stdout + head_tree.stderr).strip()[:500]}')
            return False
        if new_tree_sha == head_tree.stdout.strip():
            SKIP_CACHE[folder.name] = (mtime, 'no_changes', now)
            return False

        commit = run_git_with_env(['commit-tree', new_tree_sha, '-p', head_sha, '-m', folder.name], env)
        if commit.returncode != 0:
            log(f'commit_tree_failed folder={folder.name} err={(commit.stdout + commit.stderr).strip()[:500]}')
            return False
        commit_sha = commit.stdout.strip()

        update_ref = run_git_with_env(['update-ref', 'refs/heads/main', commit_sha, head_sha], env)
        if update_ref.returncode != 0:
            log(f'update_ref_failed folder={folder.name} err={(update_ref.stdout + update_ref.stderr).strip()[:500]}')
            return False

        log(f'committed folder={folder.name}')
        return True
    finally:
        try:
            index_path.unlink(missing_ok=True)
            Path(str(index_path) + '.lock').unlink(missing_ok=True)
        except Exception:
            pass


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
