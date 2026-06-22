from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(r'C:\Dev\MTC_Continune')
BARE_ROOT = Path(r'C:\Dev\MTC_Continune_CommitBare.git')
LOG = Path(r'C:\Dev\MTC_Download\logs\verified_commit_worker.log')
WORKER_LOCK = Path(r'C:\Dev\MTC_Download\tmp\verified_commit_worker.singleton.lock')
SKIP_CACHE: dict[str, tuple[float, str, float]] = {}
INCOMPLETE_RECHECK_SECONDS = 600
IGNORE = {'.git', '.claude', '.vscode', '_bad_quarantine', 'mtc_done'}
GIT_TIMEOUT_SECONDS = 180
PUSH_TIMEOUT_SECONDS = 300
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


def run(cmd: list[str], timeout: int = GIT_TIMEOUT_SECONDS, input_data: bytes | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.setdefault('GIT_OPTIONAL_LOCKS', '0')
    env.setdefault('PYTHONUTF8', '1')
    try:
        return subprocess.run(
            cmd,
            input=input_data,
            capture_output=True,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        out = (exc.stdout or b'') + (exc.stderr or b'')
        log(f'timeout cmd={cmd!r} err={out.decode("utf-8", "replace")[:500]}')
        return subprocess.CompletedProcess(cmd, 124, exc.stdout or b'', exc.stderr or b'timeout')


def text(result: subprocess.CompletedProcess) -> str:
    return ((result.stdout or b'') + (result.stderr or b'')).decode('utf-8', 'replace')


def git(args: list[str], timeout: int = GIT_TIMEOUT_SECONDS, input_data: bytes | None = None) -> subprocess.CompletedProcess:
    return run(['git', '--git-dir', str(BARE_ROOT), *args], timeout=timeout, input_data=input_data)


def source_origin() -> str:
    result = run(['git', '-C', str(ROOT), 'config', '--get', 'remote.origin.url'], timeout=30)
    origin = (result.stdout or b'').decode('utf-8', 'replace').strip()
    if result.returncode != 0 or not origin:
        raise RuntimeError(f'cannot read source origin: {text(result)}')
    return origin


def ensure_bare_repo() -> bool:
    if (BARE_ROOT / 'HEAD').exists():
        return True
    if BARE_ROOT.exists() and any(BARE_ROOT.iterdir()):
        log(f'bare_repo_dirty_path path={BARE_ROOT}')
        return False
    BARE_ROOT.parent.mkdir(parents=True, exist_ok=True)
    origin = source_origin()
    log(f'clone_bare_commit_repo origin={origin} path={BARE_ROOT}')
    clone = run(['git', 'clone', '--bare', '--filter=blob:none', origin, str(BARE_ROOT)], timeout=1800)
    if clone.returncode != 0:
        log(f'clone_bare_failed err={text(clone)[:1000]}')
        return False
    return True


def refresh_bare_repo() -> str | None:
    if not ensure_bare_repo():
        return None
    fetch = git(['fetch', 'origin', BRANCH], timeout=300)
    if fetch.returncode != 0:
        log(f'fetch_failed err={text(fetch)[:1000]}')
        return None
    parent = git(['rev-parse', 'FETCH_HEAD'], timeout=30)
    if parent.returncode != 0:
        log(f'rev_parse_failed err={text(parent)[:500]}')
        return None
    return (parent.stdout or b'').decode('ascii', 'replace').strip()


def mktree(entries: list[tuple[str, str, str, str]]) -> str | None:
    entries.sort(key=lambda item: item[3].encode('utf-8'))
    payload = b''.join(f'{mode} {kind} {oid}\t{name}'.encode('utf-8') + b'\0' for mode, kind, oid, name in entries)
    result = git(['mktree', '-z'], input_data=payload)
    if result.returncode != 0:
        log(f'mktree_failed err={text(result)[:800]}')
        return None
    return (result.stdout or b'').decode('ascii', 'replace').strip()


def build_tree_for_dir(path: Path) -> str | None:
    entries: list[tuple[str, str, str, str]] = []
    try:
        children = list(os.scandir(path))
    except OSError as exc:
        log(f'scandir_failed path={path} err={exc}')
        return None
    for child in children:
        if child.name == '.git':
            continue
        child_path = Path(child.path)
        if child.is_dir(follow_symlinks=False):
            oid = build_tree_for_dir(child_path)
            if not oid:
                return None
            entries.append(('040000', 'tree', oid, child.name))
        elif child.is_file(follow_symlinks=False):
            hashed = git(['hash-object', '-w', '--', str(child_path)], timeout=60)
            if hashed.returncode != 0:
                log(f'hash_failed file={child_path} err={text(hashed)[:500]}')
                return None
            oid = (hashed.stdout or b'').decode('ascii', 'replace').strip()
            entries.append(('100644', 'blob', oid, child.name))
    return mktree(entries)


def parse_ls_tree_z(data: bytes) -> list[tuple[str, str, str, str]]:
    entries: list[tuple[str, str, str, str]] = []
    for record in data.split(b'\0'):
        if not record:
            continue
        meta, name = record.split(b'\t', 1)
        mode, kind, oid = meta.decode('ascii').split(' ', 2)
        entries.append((mode, kind, oid, name.decode('utf-8', 'surrogateescape')))
    return entries


def build_root_tree(parent: str, folder_name: str, folder_tree: str) -> str | None:
    listed = git(['ls-tree', '-z', f'{parent}^{{tree}}'], timeout=120)
    if listed.returncode != 0:
        log(f'ls_root_failed err={text(listed)[:800]}')
        return None
    entries = [entry for entry in parse_ls_tree_z(listed.stdout or b'') if entry[3] != folder_name]
    entries.append(('040000', 'tree', folder_tree, folder_name))
    return mktree(entries)


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
    folders.sort(key=lambda item: item[0], reverse=True)
    return [folder for _, folder in folders]


def commit_folder(folder: Path) -> bool:
    mtime = folder.stat().st_mtime if folder.exists() else 0
    cached = SKIP_CACHE.get(folder.name)
    now = time.time()
    if cached and cached[0] == mtime and now - cached[2] < INCOMPLETE_RECHECK_SECONDS:
        return False
    SKIP_CACHE.pop(folder.name, None)

    parent = refresh_bare_repo()
    if not parent:
        return False
    folder_tree = build_tree_for_dir(folder)
    if not folder_tree:
        return False
    current = git(['rev-parse', f'refs/heads/{BRANCH}'], timeout=30)
    if current.returncode == 0:
        current_head = (current.stdout or b'').decode('ascii', 'replace').strip()
        if current_head != parent:
            update_base = git(['update-ref', f'refs/heads/{BRANCH}', parent], timeout=60)
            if update_base.returncode != 0:
                log(f'update_base_ref_failed err={text(update_base)[:800]}')
                return False
    root_tree = build_root_tree(parent, folder.name, folder_tree)
    if not root_tree:
        return False

    same = git(['diff-tree', '--quiet', parent, root_tree, '--', folder.name], timeout=120)
    if same.returncode == 0:
        SKIP_CACHE[folder.name] = (mtime, 'no_changes', now)
        log(f'nothing_to_commit folder={folder.name}')
        return False
    if same.returncode not in (1,):
        log(f'diff_tree_failed folder={folder.name} err={text(same)[:800]}')
        return False

    commit = git(['commit-tree', root_tree, '-p', parent, '-m', folder.name], timeout=120)
    if commit.returncode != 0:
        log(f'commit_tree_failed folder={folder.name} err={text(commit)[:1000]}')
        return False
    commit_id = (commit.stdout or b'').decode('ascii', 'replace').strip()
    update = git(['update-ref', f'refs/heads/{BRANCH}', commit_id], timeout=60)
    if update.returncode != 0:
        log(f'update_ref_failed folder={folder.name} err={text(update)[:800]}')
        return False
    push = git(['push', 'origin', f'refs/heads/{BRANCH}:refs/heads/{BRANCH}'], timeout=PUSH_TIMEOUT_SECONDS)
    if push.returncode == 0:
        log(f'committed_pushed folder={folder.name} commit={commit_id[:12]}')
        return True
    log(f'push_failed folder={folder.name} err={text(push)[:1000]}')
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
        ensure_bare_repo()
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


