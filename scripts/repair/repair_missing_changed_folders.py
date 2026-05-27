from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

from download_completed_to_mtc import MTCDownloader, chapter_filename, write_chapter
from download_one_completed_live_decrypt import maybe_decrypt

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

REPO = Path(r"C:\Dev\MTC")
LOG = Path(r"C:\Dev\MTC_DOWNLOAD\logs\repair_missing_changed_folders.json")
NUM_RE = re.compile(r"(\d+)")


def changed_story_folders() -> list[str]:
    out = subprocess.check_output(["git", "status", "--porcelain=v1", "-z"], cwd=REPO)
    names: list[str] = []
    seen: set[str] = set()
    for item in [x for x in out.split(b"\x00") if x]:
        path = item[3:].decode("utf-8", "replace")
        if " -> " in path:
            path = path.split(" -> ")[-1]
        top = path.replace("\\", "/").split("/")[0]
        if not top or top in seen:
            continue
        folder = REPO / top
        if folder.is_dir() and (folder / "chapters_manifest.json").exists():
            seen.add(top)
            names.append(top)
    return names


def local_index_map(folder: Path) -> dict[int, list[Path]]:
    out: dict[int, list[Path]] = {}
    for path in folder.glob("*.txt"):
        match = NUM_RE.search(path.stem)
        if not match:
            continue
        index = int(match.group(1))
        out.setdefault(index, []).append(path)
    return out


def load_manifest(folder: Path) -> list[dict]:
    manifest_path = folder / "chapters_manifest.json"
    if not manifest_path.exists():
        return []
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    return payload.get("data") or []


def manifest_by_index(chapters: list[dict]) -> dict[int, dict]:
    out: dict[int, dict] = {}
    for chapter in chapters:
        idx = chapter.get("index", chapter.get("number"))
        try:
            index = int(idx)
        except Exception:
            continue
        if index > 0 and index not in out:
            out[index] = chapter
    return out


def repair_folder(downloader: MTCDownloader, folder_name: str, delay: float) -> dict:
    folder = REPO / folder_name
    manifest = load_manifest(folder)
    if not manifest:
        return {
            "folder": folder_name,
            "missing_before": 0,
            "downloaded": [],
            "failed": [],
            "missing_after": 0,
            "remaining_first20": [],
            "skipped": "missing_manifest",
        }
    remote = manifest_by_index(manifest)
    local = local_index_map(folder)
    missing = sorted(index for index in remote if index not in local)
    result = {
        "folder": folder_name,
        "missing_before": len(missing),
        "downloaded": [],
        "failed": [],
    }
    if not missing:
        return result

    for index in missing:
        chapter = remote[index]
        chapter_id = chapter.get("id")
        try:
            detail = downloader.get_chapter_content(chapter_id)
            data = (detail or {}).get("data") or {}
            content = data.get("content") or data.get("body") or ""
            if not content:
                result["failed"].append({"index": index, "chapter_id": chapter_id, "reason": "empty_content"})
                continue
            content, decrypted = maybe_decrypt(content)
            display_name = data.get("name") or chapter.get("name") or f"Chương {index}"
            filename = chapter_filename(chapter, index)
            path = folder / filename
            write_chapter(path, folder_name, display_name, content)
            result["downloaded"].append({"index": index, "chapter_id": chapter_id, "file": filename, "decrypted": decrypted})
        except Exception as exc:
            result["failed"].append({"index": index, "chapter_id": chapter_id, "reason": str(exc)})
        time.sleep(delay)

    remaining = sorted(index for index in remote if index not in local_index_map(folder))
    result["missing_after"] = len(remaining)
    result["remaining_first20"] = remaining[:20]
    return result


def main() -> int:
    downloader = MTCDownloader()
    folders = changed_story_folders()
    results = []
    total_downloaded = 0
    total_failed = 0
    for idx, folder_name in enumerate(folders, 1):
        print(f"[{idx}/{len(folders)}] repair {folder_name}")
        result = repair_folder(downloader, folder_name, delay=0.12)
        results.append(result)
        total_downloaded += len(result["downloaded"])
        total_failed += len(result["failed"])
        print(
            f"  missing_before={result['missing_before']} downloaded={len(result['downloaded'])} "
            f"failed={len(result['failed'])} missing_after={result.get('missing_after', 0)}"
        )
    payload = {
        "folders": len(folders),
        "total_downloaded": total_downloaded,
        "total_failed": total_failed,
        "results": results,
    }
    LOG.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(LOG)
    print(json.dumps({"total_downloaded": total_downloaded, "total_failed": total_failed}, ensure_ascii=False))
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
