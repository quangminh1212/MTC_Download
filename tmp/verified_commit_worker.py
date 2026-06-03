from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(r'C:\Dev\MTC_Continune')
COMMIT_ROOT = Path(r'C:\Dev\MTC_Continune_CommitWork')
LOG = Path(r'C:\Dev\MTC_Download\logs\verified_commit_worker.log')
WORKER_LOCK = Path(r'C:\Dev\MTC_Download\tmp\verified_commit_worker.singleton.lock')
SKIP_CACHE: dict[str, tuple[float, str, float]] = {}
PUSH_EVERY_COMMITS = 1
INCOMPLETE_RECHECK_SECONDS = 600
IGNORE = {'.git', '.claude', '.vscode', '_bad_quarantine', 'mtc_done'}
GIT_TIMEOUT_SECONDS = 180
PUSH_TIMEOUT_SECONDS = 300
COPY_TIMEOUT_SECONDS = 600
BRANCH = 'main'


def log(message: str) -> None:
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}"
    try:
        print(line, flush=True)
    except UnicodeEncodeError:
        safe = line.encode(sys.stdout.encoding or 'utf-8', errors='replace').decode(sys.stdout.encoding or 'utf-8', errors='replace')
        print(safe, flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open('a', encoding='utf-8') as f:
        f.write(line + '\n')


def run(cmd: list[str], cwd: Path | None = None, timeout: int = GIT_TIMEOUT_SECONDS) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.setdefault('GIT_OPTIONAL_LOCKS', '0')
    env.setdefault('PYTHONUTF8', '1')
    try:
        return subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
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
        log(f'timeout cmd={cmd!r} cwd={cwd} err={(stdout + stderr).strip()[:500]}')
        return subprocess.CompletedProcess(cmd, 124, stdout or '', stderr or 'timeout')


def git(repo: Path, args: list[str], timeout: int = GIT_TIMEOUT_SECONDS) -> subprocess.CompletedProcess:
    return run(['git', '-C', str(repo), *args], timeout=timeout)


def source_origin() -> str:
    result = git(ROOT, ['config', '--get', 'remote.origin.url'], timeout=30)
    origin = (result.stdout or '').strip()
    if result.returncode != 0 or not origin:
        raise RuntimeError(f'cannot read source origin: {(result.stdout + result.stderr).strip()}')
    return origin


def ensure_commit_clone() -> bool:
    if (COMMIT_ROOT / '.git').exists():
        return True
    if COMMIT_ROOT.exists() and any(COMMIT_ROOT.iterdir()):
        log(f'commit_clone_dirty_path path={COMMIT_ROOT}; remove it manually or choose empty path')
        return False
    COMMIT_ROOT.parent.mkdir(parents=True, exist_ok=True)
    origin = source_origin()
    log(f'clone_commit_worktree origin={origin} path={COMMIT_ROOT}')
    clone = run(['git', 'clone', '--filter=blob:none', '--sparse', '--branch', BRANCH, origin, str(COMMIT_ROOT)], timeout=1800)
    if clone.returncode != 0:
        log(f'clone_failed err={(clone.stdout + clone.stderr).strip()[:1000]}')
        return False
    git(COMMIT_ROOT, ['config', 'core.sparseCheckout', 'true'], timeout=30)
    git(COMMIT_ROOT, ['config', 'core.untrackedCache', 'true'], timeout=30)
    git(COMMIT_ROOT, ['config', 'core.fsmonitor', 'true'], timeout=30)
    return True


def refresh_commit_clone(folder_name: str) -> bool:
    if not ensure_commit_clone():
        return False
    fetch = git(COMMIT_ROOT, ['fetch', 'origin', BRANCH, '--depth=1'], timeout=300)
    if fetch.returncode != 0:
        log(f'fetch_failed err={(fetch.stdout + fetch.stderr).strip()[:800]}')
        return False
    reset = git(COMMIT_ROOT, ['reset', '--hard', f'origin/{BRANCH}'], timeout=300)
    if reset.returncode != 0:
        log(f'reset_failed err={(reset.stdout + reset.stderr).strip()[:800]}')
        return False
    sparse = git(COMMIT_ROOT, ['sparse-checkout', 'set', '--', folder_name], timeout=300)
    if sparse.returncode != 0:
        log(f'sparse_failed folder={folder_name} err={(sparse.stdout + sparse.stderr).strip()[:800]}')
        return False
    clean = git(COMMIT_ROOT, ['clean', '-fd', '--', folder_name], timeout=120)
    if clean.returncode != 0:
        log(f'clean_failed folder={folder_name} err={(clean.stdout + clean.stderr).strip()[:500]}')
        return False
    return True


def copy_folder_to_commit_clone(folder: Path) -> bool:
    destination = COMMIT_ROOT / folder.name
    if destination.exists():
        shutil.rmtree(destination)
    cmd = ['robocopy', str(folder), str(destination), '/MIR', '/R:2', '/W:1', '/NFL', '/NDL', '/NJH', '/NJS', '/NP', '/XD', '.git']
    result = run(cmd, timeout=COPY_TIMEOUT_SECONDS)
    if result.returncode >= 8:
        log(f'copy_failed folder={folder.name} code={result.returncode} err={(result.stdout + result.stderr).strip()[:800]}')
        return False
    return True


def candidate_folders() -> list[Path]:
    folders: list[tuple[float, Path]] = []
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
    folders.sort(key=lambda item: item[0])
    return [folder for _, folder in folders]


def commit_folder(folder: Path) -> bool:
    mtime = folder.stat().st_mtime if folder.exists() else 0
    cached = SKIP_CACHE.get(folder.name)
    now = time.time()
    if cached and cached[0] == mtime and now - cached[2] < INCOMPLETE_RECHECK_SECONDS:
        return False
    SKIP_CACHE.pop(folder.name, None)

    if not refresh_commit_clone(folder.name):
        return False
    if not copy_folder_to_commit_clone(folder):
        return False

    add = git(COMMIT_ROOT, ['add', '--', folder.name], timeout=GIT_TIMEOUT_SECONDS)
    if add.returncode != 0:
        log(f'add_failed folder={folder.name} err={(add.stdout + add.stderr).strip()[:800]}')
        return False
    diff = git(COMMIT_ROOT, ['diff', '--cached', '--quiet', '--', folder.name], timeout=GIT_TIMEOUT_SECONDS)
    if diff.returncode == 0:
        SKIP_CACHE[folder.name] = (mtime, 'no_changes', now)
        log(f'nothing_to_commit folder={folder.name}')
        return False
    if diff.returncode != 1:
        log(f'diff_cached_failed folder={folder.name} err={(diff.stdout + diff.stderr).strip()[:800]}')
        return False

    commit = git(COMMIT_ROOT, ['commit', '--untracked-files=no', '-m', folder.name, '--', folder.name], timeout=GIT_TIMEOUT_SECONDS)
    out = (commit.stdout + commit.stderr).strip()
    if commit.returncode != 0:
        if 'nothing to commit' in out or 'nothing added to commit' in out or 'no changes added to commit' in out:
            SKIP_CACHE[folder.name] = (mtime, 'no_changes', now)
            log(f'nothing_to_commit folder={folder.name}')
            return False
        log(f'commit_failed folder={folder.name} err={out[:1000]}')
        return False

    push = git(COMMIT_ROOT, ['push', 'origin', BRANCH], timeout=PUSH_TIMEOUT_SECONDS)
    if push.returncode == 0:
        log(f'committed_pushed folder={folder.name}')
        return True

    log(f'push_failed folder={folder.name} err={(push.stdout + push.stderr).strip()[:1000]}')
    recover = git(COMMIT_ROOT, ['pull', '--rebase', 'origin', BRANCH], timeout=300)
    if recover.returncode == 0:
        retry = git(COMMIT_ROOT, ['push', 'origin', BRANCH], timeout=PUSH_TIMEOUT_SECONDS)
        if retry.returncode == 0:
            log(f'committed_pushed_after_rebase folder={folder.name}')
            return True
        log(f'push_retry_failed folder={folder.name} err={(retry.stdout + retry.stderr).strip()[:1000]}')
    else:
        log(f'pull_rebase_failed folder={folder.name} err={(recover.stdout + recover.stderr).strip()[:1000]}')
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
    try:
        ensure_commit_clone()
        while True:
            folders = candidate_folders()
            if not folders:
                time.sleep(2)
                continue
            start = time.time()
            checked = 0
            committed = 0
            for folder in folders:
                checked += 1
                if folder.exists() and commit_folder(folder):
                    committed += 1
            log(f'cycle checked={checked} committed={committed} seconds={time.time()-start:.1f}')
            time.sleep(0.5)
    finally:
        WORKER_LOCK.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
