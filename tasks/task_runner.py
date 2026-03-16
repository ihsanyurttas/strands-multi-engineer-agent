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


def task_from_file(path: Path) -> dict | None:
    """
    Load a task from a user-supplied YAML file.

    Required fields: repo, description
    Optional fields: id, title, difficulty, tags

    Returns the task dict on success, None (after printing an error) on failure.
    The caller is responsible for printing errors via the console — here we
    raise ValueError so the CLI can catch and display them cleanly.
    """
    if not path.exists():
        raise FileNotFoundError(f"Task file not found: {path}")

    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    if not isinstance(data, dict):
        raise ValueError(f"Task file must be a YAML mapping, got: {type(data).__name__}")

    missing = [f for f in ("repo", "description") if not data.get(f)]
    if missing:
        raise ValueError(f"Task file is missing required fields: {', '.join(missing)}")

    return {
        "id": data.get("id", path.stem),
        "title": data.get("title", data["description"][:72]),
        "description": data["description"],
        "repo": data["repo"],
        "difficulty": data.get("difficulty", "medium"),
        "tags": data.get("tags", []),
    }
