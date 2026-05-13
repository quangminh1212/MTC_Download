import hashlib
import json
from pathlib import Path

REPORT = Path(r"C:\Dev\MTC_Download\logs\mtc_sanitize_report.json")
OUT = Path(r"C:\Dev\MTC_Download\logs\mtc_sanitize_fix_report.json")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    data = json.loads(REPORT.read_text(encoding='utf-8'))
    actions = []

    # 1) Fix accidental "Untitled" chapter names from previous sanitize pass
    root = Path(r"C:\Dev\MTC")
    untitled = list(root.rglob("Chương * Untitled.txt"))
    for p in untitled:
        stem = p.stem  # e.g. "Chương 1009 Untitled"
        if stem.endswith(" Untitled"):
            new_stem = stem[: -len(" Untitled")]
            dst = p.with_name(new_stem + p.suffix)
            if dst.exists():
                actions.append({
                    'type': 'untitled_conflict',
                    'src': str(p),
                    'dst': str(dst),
                })
            else:
                p.rename(dst)
                actions.append({
                    'type': 'untitled_renamed',
                    'src': str(p),
                    'dst': str(dst),
                })

    # 2) Resolve sanitize collisions
    #    If src/dst have identical bytes -> delete src duplicate.
    #    If different -> keep both and record manual review.
    for c in data.get('collisions', []):
        if c.get('type') != 'file':
            actions.append({'type': 'collision_skip_non_file', **c})
            continue
        src = Path(c['src'])
        dst = Path(c['dst'])
        if not src.exists() or not dst.exists():
            actions.append({'type': 'collision_missing_path', **c, 'src_exists': src.exists(), 'dst_exists': dst.exists()})
            continue

        same = (src.stat().st_size == dst.stat().st_size and sha256(src) == sha256(dst))
        if same:
            src.unlink()
            actions.append({'type': 'collision_deleted_duplicate_src', **c})
        else:
            actions.append({'type': 'collision_content_diff_keep_both', **c})

    summary = {
        'actions_count': len(actions),
        'actions': actions,
    }
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(OUT)


if __name__ == '__main__':
    main()
