"""
tools/search_tools.py — Strands tools for searching within a repository.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from strands import tool


@tool
def search_in_repo(repo_path: str, pattern: str, file_extension: str = "") -> str:
    """
    Search for a regex pattern across files in a repository.

    Args:
        repo_path:       Path to the repository root.
        pattern:         Regular expression to search for.
        file_extension:  Optional extension filter, e.g. ".py".

    Returns:
        Matching lines in the format  file:line_number: content
    """
    root = Path(repo_path).resolve()
    if not root.is_dir():
        return f"ERROR: '{repo_path}' is not a directory."

    try:
        regex = re.compile(pattern)
    except re.error as exc:
        return f"ERROR: Invalid regex pattern '{pattern}': {exc}"

    matches: list[str] = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames
            if not d.startswith(".")
            and d not in {"__pycache__", "node_modules", "venv", ".venv", "dist", "build"}
        ]
        for filename in sorted(filenames):
            if file_extension and not filename.endswith(file_extension):
                continue

            full_path = Path(dirpath) / filename
            rel_path = full_path.relative_to(root)

            try:
                text = full_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            for line_no, line in enumerate(text.splitlines(), start=1):
                if regex.search(line):
                    matches.append(f"{rel_path}:{line_no}: {line.rstrip()}")

    if not matches:
        return f"No matches found for pattern '{pattern}' in '{repo_path}'."

    return "\n".join(matches)
