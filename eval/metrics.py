"""
eval/metrics.py — record and compare workflow run results.

Writes each WorkflowResult to a JSON file so runs from different providers
can be loaded and compared later.

File naming: eval/results/<provider>_<model>_<timestamp>.json
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from eval.result_schema import WorkflowResult


def record_result(result: WorkflowResult, results_dir: str = "eval/results") -> Path:
    """
    Serialise a WorkflowResult to a JSON file.

    Args:
        result:      The completed workflow result to save.
        results_dir: Directory to write into (created if absent).

    Returns:
        Path to the written JSON file.
    """
    output_dir = Path(results_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_model = re.sub(r"[^\w.-]", "_", result.model)
    filename = f"{result.provider}_{safe_model}_{timestamp}.json"
    output_path = output_dir / filename

    output_path.write_text(
        json.dumps(result.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )
    return output_path


def load_results(results_dir: str = "eval/results") -> list[WorkflowResult]:
    """Load all previously recorded results from the results directory."""
    output_dir = Path(results_dir)
    if not output_dir.is_dir():
        return []

    results: list[WorkflowResult] = []
    for json_file in sorted(output_dir.glob("*.json")):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            results.append(WorkflowResult.model_validate(data))
        except Exception:
            pass  # Skip malformed files silently

    return results


def compare_results(results: list[WorkflowResult]) -> list[dict]:
    """
    Return a list of summary dicts sorted by total elapsed time.
    Useful for rendering a comparison table.
    """
    return sorted(
        [r.summary() for r in results],
        key=lambda s: s["total_elapsed_seconds"],
    )
