"""
tools/test_runner.py — Strands tool for running tests inside a sample repo.

Executes tests in an isolated subprocess so failures cannot affect the agent
process. Output is captured and returned as a string for the agent to analyse.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from strands import tool

_SANDBOX = Path("sample_repos").resolve()
_TIMEOUT_SECONDS = 60


@tool
def run_tests(repo_path: str, test_command: str = "") -> str:
    """
    Run tests for a sample repository and return the output.

    Args:
        repo_path:     Path to the repository (must be inside sample_repos).
        test_command:  Shell command to run tests. Auto-detected if empty.
                       Examples: "pytest", "npm test", "python -m pytest -v"

    Returns:
        Combined stdout + stderr from the test run, plus exit code.
    """
    root = Path(repo_path).resolve()

    # Sandbox check
    try:
        root.relative_to(_SANDBOX)
    except ValueError:
        return (
            f"ERROR: '{repo_path}' is outside sample_repos. "
            "Only sample repos may be tested via this tool."
        )

    if not root.is_dir():
        return f"ERROR: '{repo_path}' is not a directory."

    cmd = test_command.strip() if test_command else _detect_test_command(root)
    if not cmd:
        return (
            f"Could not detect a test command for '{repo_path}'. "
            "Pass test_command explicitly (e.g. 'pytest' or 'npm test')."
        )

    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return f"ERROR: Test command timed out after {_TIMEOUT_SECONDS}s."
    except OSError as exc:
        return f"ERROR: Could not run '{cmd}': {exc}"

    output_parts = []
    if proc.stdout:
        output_parts.append(proc.stdout)
    if proc.stderr:
        output_parts.append(proc.stderr)
    output_parts.append(f"\nExit code: {proc.returncode}")

    return "\n".join(output_parts)


def _detect_test_command(root: Path) -> str:
    """Heuristically detect the test command for a repository."""
    if (root / "pytest.ini").exists() or (root / "pyproject.toml").exists():
        return f"{sys.executable} -m pytest -v"
    if (root / "package.json").exists():
        return "npm test"
    if any(root.glob("test_*.py")) or any(root.glob("*_test.py")):
        return f"{sys.executable} -m pytest -v"
    return ""
