from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

DONE_DIR_NAME = 'mtc_done'
COMPLETED_LABELS = {'hoàn thành', 'hoan thanh', 'completed', 'full', 'finished'}
ONGOING_LABELS = {'còn tiếp', 'con tiep', 'ongoing', 'serializing'}
PAUSED_LABELS = {'tạm dừng', 'tam dung', 'paused', 'hiatus'}


def normalize_status_name(value: Any) -> str:
    return str(value or '').strip().lower()


def is_completed_status(book: dict[str, Any]) -> bool:
    status_name = normalize_status_name(book.get('status_name'))
    status = book.get('status')
    return status_name in COMPLETED_LABELS or status == 2


def is_ongoing_status(book: dict[str, Any]) -> bool:
    status_name = normalize_status_name(book.get('status_name'))
    status = book.get('status')
    return status_name in ONGOING_LABELS or status == 1


def is_paused_status(book: dict[str, Any]) -> bool:
    status_name = normalize_status_name(book.get('status_name'))
    status = book.get('status')
    return status_name in PAUSED_LABELS or status == 3


def is_unfinished_status(book: dict[str, Any]) -> bool:
    return not is_completed_status(book)


def ensure_done_folder(root: Path) -> Path:
    done_root = root / DONE_DIR_NAME
    done_root.mkdir(parents=True, exist_ok=True)
    return done_root


def move_completed_book_folder(root: Path, folder: Path) -> dict[str, Any]:
    done_root = ensure_done_folder(root)
    destination = done_root / folder.name
    if destination.exists():
        shutil.rmtree(folder)
        return {'status': 'deleted_existing_done', 'destination': str(destination)}
    shutil.move(str(folder), str(destination))
    return {'status': 'moved_to_done', 'destination': str(destination)}


def cleanup_root_completed_dirs(root: Path) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    done_root = ensure_done_folder(root)
    for story_dir in root.iterdir():
        if not story_dir.is_dir() or story_dir.name.startswith('.') or story_dir.name == done_root.name:
            continue
        info_path = story_dir / 'info.json'
        if not info_path.is_file():
            continue
        try:
            book = json.loads(info_path.read_text(encoding='utf-8'))
        except Exception:
            continue
        if not is_completed_status(book):
            continue
        action = move_completed_book_folder(root, story_dir)
        action['folder'] = story_dir.name
        actions.append(action)
    return actions
