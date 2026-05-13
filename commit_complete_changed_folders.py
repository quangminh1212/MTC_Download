import json
import subprocess
from pathlib import Path

repo = Path(r"C:\Dev\MTC")
careful = json.loads(Path(r"C:\Dev\MTC_Download\logs\mtc_careful_check.json").read_text(encoding='utf-8'))
changed = json.loads(Path(r"C:\Dev\MTC_Download\logs\mtc_changed_folders_vs_complete.json").read_text(encoding='utf-8'))

careful_by_folder = {row['folder']: row for row in careful if row.get('folder')}
complete_folders = [row['folder'] for row in changed['rows'] if row.get('is_complete')]

results = []
for folder in complete_folders:
    meta = careful_by_folder.get(folder)
    if not meta:
        results.append({'folder': folder, 'status': 'missing_meta'})
        continue
    msg = meta.get('book_name') or folder

    add = subprocess.run(
        ['git', 'add', '-A', '--', folder],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if add.returncode != 0:
        results.append({
            'folder': folder,
            'message': msg,
            'status': 'add_failed',
            'stderr': add.stderr.decode('utf-8', 'replace'),
        })
        continue

    diff = subprocess.run(
        ['git', 'diff', '--cached', '--name-only', '--', folder],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    staged = [line for line in diff.stdout.decode('utf-8', 'replace').splitlines() if line.strip()]
    if not staged:
        results.append({'folder': folder, 'message': msg, 'status': 'nothing_staged'})
        continue

    commit = subprocess.run(
        ['git', 'commit', '-m', msg, '--', folder],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    results.append({
        'folder': folder,
        'message': msg,
        'status': 'committed' if commit.returncode == 0 else 'commit_failed',
        'staged_count': len(staged),
        'stdout': commit.stdout.decode('utf-8', 'replace'),
        'stderr': commit.stderr.decode('utf-8', 'replace'),
    })
    if commit.returncode != 0:
        break

out = Path(r"C:\Dev\MTC_Download\logs\mtc_auto_commit_results.json")
out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
print(str(out))
for row in results:
    print(f"{row['folder']} :: {row['status']} :: {row.get('message','')}")
