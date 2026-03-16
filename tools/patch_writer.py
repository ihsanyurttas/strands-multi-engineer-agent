"""
tools/patch_writer.py — Strands tool for writing generated code patches.

Writes are scoped to the sample_repos directory to prevent the agent from
accidentally modifying project infrastructure files.
"""

from __future__ import annotations

from pathlib import Path

from strands import tool

# Only allow writes inside this directory tree
_WRITE_SANDBOX = Path("sample_repos").resolve()


@tool
def write_patch(file_path: str, content: str) -> str:
    """
    Write generated code content to a file within the sample_repos sandbox.

    Args:
        file_path:  Target file path (relative to the project root).
                    Must be inside the sample_repos directory.
        content:    Full file content to write.

    Returns:
        Success message or error description.
    """
    target = Path(file_path).resolve()

    # Sandbox enforcement — prevent writes outside sample_repos
    try:
        target.relative_to(_WRITE_SANDBOX)
    except ValueError:
        return (
            f"ERROR: Write denied. '{file_path}' is outside the allowed sandbox "
            f"('{_WRITE_SANDBOX}'). Only files under sample_repos may be written."
        )

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    except OSError as exc:
        return f"ERROR: Could not write '{file_path}': {exc}"

    return f"OK: Written {len(content)} bytes to '{file_path}'."
