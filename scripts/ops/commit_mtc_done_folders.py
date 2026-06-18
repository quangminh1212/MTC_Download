#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Commit completed MTC_Done folders one-by-one using git plumbing.

This avoids `git status`/`git add` on the huge worktree. Each commit message is
exactly the folder name. It can also push in small batches.
"""
from __future__ import annotations

import argparse
import html
import json
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"D:\Dev\MTC_Done")
STATE = Path(r"C:\Dev\MTC_Download\logs\download_missing_to_done_state.json")
DONE = Path(r"C:\Dev\MTC_Download\logs\commit_mtc_done_folders_done.json")


def norm_name(value: str) -> str:
    text = unicodedata.normalize("NFC", html.unescape(str(value or ""))).casefold()
    return "".join(ch for ch in text if ch.isalnum())


def build_folder_lookup() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for path in ROOT.iterdir():
        if path.is_dir() and not path.name.startswith('.'):
            mapping.setdefault(norm_name(path.name), path.name)
    return mapping


def run(args: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=str(ROOT), capture_output=True, encoding="utf-8", errors="replace", **kwargs)


def hash_batch_files(files: list[Path]) -> list[str]:
    if not files:
        return []
    input_data = "\n".join(str(path) for path in files) + "\n"
    proc = subprocess.run(
        ["git", "hash-object", "-w", "--stdin-paths", "--no-filters"],
        input=input_data.encode("utf-8"),
        capture_output=True,
        cwd=str(ROOT),
        timeout=900,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", errors="replace")[:500])
    shas = proc.stdout.decode("ascii", errors="replace").splitlines()
    if len(shas) != len(files):
        raise RuntimeError(f"hash count mismatch: {len(shas)} != {len(files)}")
    return shas


def make_tree_for_dir(dirpath: Path) -> str | None:
    files: list[Path] = []
    subdirs: list[Path] = []
    for item in sorted(dirpath.iterdir(), key=lambda p: p.name):
        if item.name.startswith("."):
            continue
        if item.is_file():
            files.append(item)
        elif item.is_dir():
            subdirs.append(item)
    entries: list[str] = []
    for path, sha in zip(files, hash_batch_files(files)):
        entries.append(f"100644 blob {sha}\t{path.name}")
    for subdir in subdirs:
        tree_sha = make_tree_for_dir(subdir)
        if tree_sha:
            entries.append(f"040000 tree {tree_sha}\t{subdir.name}")
    if not entries:
        return None
    proc = subprocess.run(
        ["git", "mktree"],
        input=("\n".join(entries) + "\n").encode("utf-8"),
        capture_output=True,
        cwd=str(ROOT),
        timeout=120,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", errors="replace")[:500])
    return proc.stdout.decode("ascii", errors="replace").strip()


def get_head() -> str:
    proc = run(["git", "rev-parse", "HEAD"], timeout=60)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[:500])
    return proc.stdout.strip()


def get_current_branch() -> str:
    proc = run(["git", "branch", "--show-current"], timeout=60)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[:500])
    return proc.stdout.strip() or "main"


def get_root_tree_entries() -> dict[str, str]:
    proc = run(["git", "ls-tree", "HEAD"], timeout=300)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[:500])
    entries: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        meta, name = line.split("\t", 1)
        entries[name] = meta
    return entries


def commit_folder(folder_name: str, root_entries: dict[str, str], branch: str, folder_lookup: dict[str, str]) -> str | None:
    actual_name = folder_lookup.get(norm_name(folder_name), folder_name)
    folder = ROOT / actual_name
    if not folder.is_dir():
        return None
    tree_sha = make_tree_for_dir(folder)
    if not tree_sha:
        return None
    new_entry = f"040000 tree {tree_sha}"
    if root_entries.get(actual_name) == new_entry:
        return None
    root_entries[actual_name] = new_entry
    tree_lines = [f"{meta}\t{name}" for name, meta in sorted(root_entries.items())]
    proc = subprocess.run(
        ["git", "mktree"],
        input=("\n".join(tree_lines) + "\n").encode("utf-8"),
        capture_output=True,
        cwd=str(ROOT),
        timeout=300,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", errors="replace")[:500])
    new_root_tree = proc.stdout.decode("ascii", errors="replace").strip()
    parent = get_head()
    proc = run(["git", "commit-tree", new_root_tree, "-p", parent, "-m", actual_name], timeout=120)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[:500])
    commit_sha = proc.stdout.strip()
    proc = run(["git", "update-ref", f"refs/heads/{branch}", commit_sha], timeout=60)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[:500])
    return commit_sha


def load_completed_folders() -> list[str]:
    payload = json.loads(STATE.read_text(encoding="utf-8"))
    folders: list[str] = []
    seen: set[str] = set()
    for row in payload.get("done", []):
        status = row.get("status")
        folder = row.get("folder") or row.get("name")
        if status not in {"ok", "exists", "no_chapters"} or not folder:
            continue
        if folder in seen:
            continue
        seen.add(folder)
        folders.append(folder)
    return folders


def load_done() -> set[str]:
    if DONE.exists():
        try:
            return set(json.loads(DONE.read_text(encoding="utf-8")))
        except Exception:
            pass
    return set()


def save_done(done: set[str]) -> None:
    DONE.parent.mkdir(parents=True, exist_ok=True)
    DONE.write_text(json.dumps(sorted(done), ensure_ascii=False, indent=2), encoding="utf-8")


def get_ref(ref: str) -> str | None:
    proc = run(["git", "rev-parse", ref], timeout=60)
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def push_current_main() -> None:
    fetch = run(["git", "fetch", "origin", "--prune"], timeout=1800)
    if fetch.returncode != 0:
        raise RuntimeError(f"fetch failed: {fetch.stderr[:300]}")
    remote_sha = get_ref("origin/main")
    local_sha = get_ref("main")
    if not remote_sha or not local_sha:
        raise RuntimeError("cannot resolve main/origin/main before push")
    ts = time.strftime("%Y%m%d-%H%M%S")
    run(["git", "update-ref", f"refs/backup/pre-batch-push-local-{ts}", local_sha], timeout=60)
    run(["git", "update-ref", f"refs/backup/pre-batch-push-origin-{ts}", remote_sha], timeout=60)
    push = run([
        "git", "push",
        f"--force-with-lease=refs/heads/main:{remote_sha}",
        "origin", "main",
    ], timeout=3600)
    if push.returncode != 0:
        raise RuntimeError(f"push failed: {push.stderr[:500]}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--start-after", default=None)
    parser.add_argument("--push-every", type=int, default=50)
    args = parser.parse_args()

    branch = get_current_branch()
    root_entries = get_root_tree_entries()
    folder_lookup = build_folder_lookup()
    folders = load_completed_folders()
    if args.start_after:
        if args.start_after in folders:
            folders = folders[folders.index(args.start_after) + 1:]
    done = load_done()
    todo = [folder for folder in folders if folder not in done]
    if args.limit is not None:
        todo = todo[: args.limit]
    print(f"start branch={branch} folders={len(folders)} done={len(done)} todo={len(todo)}")

    ok = skipped = errors = 0
    since_push = 0
    t0 = time.time()
    for index, folder in enumerate(todo, 1):
        try:
            sha = commit_folder(folder, root_entries, branch, folder_lookup)
            done.add(folder)
            save_done(done)
            if sha:
                ok += 1
                since_push += 1
                elapsed = max(time.time() - t0, 0.001)
                print(f"ok {index}/{len(todo)} rate={ok/elapsed:.2f}/s {folder}", flush=True)
                if args.push_every > 0 and since_push >= args.push_every:
                    push_current_main()
                    since_push = 0
                    print(f"push ok after {ok} commits", flush=True)
            else:
                skipped += 1
        except Exception as exc:
            errors += 1
            print(f"fail {index}/{len(todo)} {folder}: {exc}", flush=True)
    if args.push_every > 0 and since_push > 0 and errors == 0:
        push_current_main()
        print(f"final push ok after {ok} commits", flush=True)
    print(f"done ok={ok} skipped={skipped} errors={errors} total_done={len(done)}")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
