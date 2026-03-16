"""
tools/repo_reader.py — Strands tools for reading files from a repository.

These functions are decorated with @tool so Strands can invoke them inside
the agent loop. They are intentionally read-only to keep the inspect and
plan phases safe.
"""

from __future__ import annotations

import os
from pathlib import Path

from strands import tool


@tool
def list_files(repo_path: str, extension: str = "") -> str:
    """
    List files in a repository directory.

    Args:
        repo_path:  Path to the repository root (relative or absolute).
        extension:  Optional file extension filter, e.g. ".py" or ".js".
                    If empty, all files are listed.

    Returns:
        Newline-separated list of relative file paths.
    """
    root = Path(repo_path).resolve()
    if not root.is_dir():
        return f"ERROR: '{repo_path}' is not a directory or does not exist."

    files: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip hidden directories and common noise dirs
        dirnames[:] = [
            d for d in dirnames
            if not d.startswith(".")
            and d not in {"__pycache__", "node_modules", "venv", ".venv", "dist", "build"}
        ]
        for filename in sorted(filenames):
            if extension and not filename.endswith(extension):
                continue
            full_path = Path(dirpath) / filename
            files.append(str(full_path.relative_to(root)))

    if not files:
        return f"No files found in '{repo_path}'" + (f" with extension '{extension}'" if extension else "")

    return "\n".join(files)


@tool
def read_file(file_path: str, max_lines: int = 500) -> str:
    """
    Read the contents of a file.

    Args:
        file_path:  Absolute or relative path to the file.
        max_lines:  Maximum number of lines to return (default 500).
                    Use this to avoid overwhelming the context window.

    Returns:
        File contents as a string, or an error message.
    """
    path = Path(file_path).resolve()

    if not path.exists():
        return f"ERROR: File '{file_path}' does not exist."
    if not path.is_file():
        return f"ERROR: '{file_path}' is not a file."
    if path.stat().st_size > 1_000_000:  # 1 MB guard
        return f"ERROR: File '{file_path}' is too large to read directly (> 1 MB)."

    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        return f"ERROR: Could not read '{file_path}': {exc}"

    if len(lines) > max_lines:
        truncated = lines[:max_lines]
        truncated.append(f"\n… [truncated — {len(lines) - max_lines} more lines]")
        return "\n".join(truncated)

    return "\n".join(lines)
