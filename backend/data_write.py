import json
import os
import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable


JsonValidator = Callable[[Any], None]


def _prune_backups(backup_dir: Path, max_backups: int) -> None:
    backups = sorted(backup_dir.glob("*.json"), key=lambda item: item.name)
    for obsolete in backups[:-max_backups] if max_backups else backups:
        obsolete.unlink()


def atomic_write_json(
    path: Path,
    payload: Any,
    *,
    validator: JsonValidator | None = None,
    backup_root: Path | None = None,
    max_backups: int = 5,
) -> None:
    """Validate, optionally back up, and atomically replace one JSON file."""

    if validator is not None:
        validator(payload)
    serialized = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.is_file() and backup_root is not None:
        backup_dir = backup_root / path.parent.name / path.name
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        shutil.copy2(path, backup_dir / f"{timestamp}-{uuid.uuid4().hex}.json")
        if max_backups >= 0:
            _prune_backups(backup_dir, max_backups)

    temporary_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary_path.open("w", encoding="utf-8", newline="\n") as target:
            target.write(serialized)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
