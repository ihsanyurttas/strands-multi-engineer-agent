"""
tasks/task_runner.py — load and dispatch engineering tasks from issues.yaml.
"""

from __future__ import annotations

from pathlib import Path

import yaml

_TASKS_FILE = Path(__file__).parent / "issues.yaml"


def load_tasks() -> list[dict]:
    """Load all tasks from issues.yaml. Returns an empty list on failure."""
    if not _TASKS_FILE.exists():
        return []

    with _TASKS_FILE.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    return data.get("tasks", []) if isinstance(data, dict) else []


def get_task(task_id: str) -> dict | None:
    """Return a single task by ID, or None if not found."""
    return next((t for t in load_tasks() if t.get("id") == task_id), None)
