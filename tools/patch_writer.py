"""
tools/patch_writer.py — Strands tool for writing generated file contents.

Writes are sandboxed to the sample_repos directory. The agent uses this tool
to materialise generated code changes during the implement phase.
"""

from __future__ import annotations

from pathlib import Path

from strands import tool

# Anchored to this file's location so the sandbox boundary is independent of
# the process working directory. Works correctly in native, Docker, and test runs.
_WRITE_SANDBOX = (Path(__file__).parent.parent / "sample_repos").resolve()


@tool
def write_file(file_path: str, content: str) -> str:
    """
    Write content to a file within the sample_repos sandbox.

    Accepts a path relative to the project root (e.g. sample_repos/app/main.py)
    or an absolute path. The resolved path must fall inside sample_repos —
    writes outside that directory are denied.

    Overwrites the file if it already exists. The return message indicates
    whether the file was created or replaced.

    Args:
        file_path: Path to the target file (relative or absolute).
        content:   Full file content to write.

    Returns:
        A status string: "CREATED", "REPLACED", or "ERROR: <reason>".
    """
    target = Path(file_path).resolve()

    # Sandbox enforcement — deny writes outside sample_repos.
    try:
        target.relative_to(_WRITE_SANDBOX)
    except ValueError:
        return (
            f"ERROR: Write denied. '{file_path}' resolves outside the sandbox "
            f"('{_WRITE_SANDBOX}'). Only paths inside sample_repos are allowed."
        )

    existed = target.exists()

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    except OSError as exc:
        return f"ERROR: Could not write '{file_path}': {exc}"

    action = "REPLACED" if existed else "CREATED"
    return f"{action}: {target.relative_to(_WRITE_SANDBOX)} ({len(content)} bytes)"
