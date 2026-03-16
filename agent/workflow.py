"""
agent/workflow.py — Strands-based orchestration loop.

This module drives the 4-phase engineering workflow using an AWS Strands Agent.
The provider is injected via the config, so the same workflow runs against
Anthropic, OpenAI, or Ollama without changing this file.

Phase order:
  1. Inspect  — read repo files, understand the issue
  2. Plan     — produce a numbered implementation plan
  3. Implement — generate code changes
  4. Review   — self-review and confidence score
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

from agent.config import AgentConfig
from agent.prompts import (
    SYSTEM_PROMPT,
    implement_prompt,
    inspect_prompt,
    plan_prompt,
    review_prompt,
)
from eval.result_schema import PhaseResult, WorkflowResult
from providers.base_provider import get_strands_model

logger = logging.getLogger(__name__)


@dataclass
class WorkflowContext:
    """Mutable context passed between workflow phases."""

    issue: str
    repo_path: str
    provider: str
    model: str

    inspection: str = ""
    plan: str = ""
    implementation: str = ""
    review: str = ""
    phase_results: list[PhaseResult] = field(default_factory=list)


def run_workflow(
    issue: str,
    repo_path: str,
    config: AgentConfig,
) -> WorkflowResult:
    """
    Execute the full 4-phase engineering workflow for a given issue.

    Args:
        issue:     Natural-language description of the engineering task.
        repo_path: Path to the repository to inspect (relative or absolute).
        config:    Validated agent configuration.

    Returns:
        WorkflowResult with all phase outputs and timing metrics.
    """
    # ------------------------------------------------------------------
    # Import Strands here so the rest of the codebase can be imported
    # without Strands installed (useful for testing stubs).
    # ------------------------------------------------------------------
    try:
        from strands import Agent
        from tools.repo_reader import read_file, list_files
        from tools.search_tools import search_in_repo
        from tools.patch_writer import write_patch
    except ImportError as exc:
        raise RuntimeError(
            "strands-agents is not installed. Run: pip install strands-agents"
        ) from exc

    model = get_strands_model(config)
    ctx = WorkflowContext(
        issue=issue,
        repo_path=repo_path,
        provider=config.default_provider.value,
        model=config.active_model(),
    )

    workflow_start = time.perf_counter()

    # Strands Agent with shared tool set
    agent = Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[read_file, list_files, search_in_repo, write_patch],
        max_parallel_tool_uses=1,  # sequential for deterministic output comparison
    )

    # ------------------------------------------------------------------
    # Phase 1: Inspect
    # ------------------------------------------------------------------
    ctx = _run_phase(
        agent=agent,
        ctx=ctx,
        phase_name="inspect",
        prompt=inspect_prompt(issue, repo_path),
        output_attr="inspection",
        max_iterations=config.max_iterations,
    )

    # ------------------------------------------------------------------
    # Phase 2: Plan
    # ------------------------------------------------------------------
    ctx = _run_phase(
        agent=agent,
        ctx=ctx,
        phase_name="plan",
        prompt=plan_prompt(issue, ctx.inspection),
        output_attr="plan",
        max_iterations=config.max_iterations,
    )

    # ------------------------------------------------------------------
    # Phase 3: Implement
    # ------------------------------------------------------------------
    ctx = _run_phase(
        agent=agent,
        ctx=ctx,
        phase_name="implement",
        prompt=implement_prompt(ctx.plan),
        output_attr="implementation",
        max_iterations=config.max_iterations,
    )

    # ------------------------------------------------------------------
    # Phase 4: Review
    # ------------------------------------------------------------------
    ctx = _run_phase(
        agent=agent,
        ctx=ctx,
        phase_name="review",
        prompt=review_prompt(ctx.implementation),
        output_attr="review",
        max_iterations=config.max_iterations,
    )

    total_elapsed = time.perf_counter() - workflow_start

    return WorkflowResult(
        provider=ctx.provider,
        model=ctx.model,
        issue=ctx.issue,
        repo_path=ctx.repo_path,
        phases=ctx.phase_results,
        total_elapsed_seconds=round(total_elapsed, 3),
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _run_phase(
    agent: object,
    ctx: WorkflowContext,
    phase_name: str,
    prompt: str,
    output_attr: str,
    max_iterations: int,
) -> WorkflowContext:
    """Run a single workflow phase, record timing, and store the result."""
    logger.info("[%s] Starting phase: %s", ctx.provider, phase_name)
    start = time.perf_counter()

    # Strands Agent is callable — returns an AgentResult
    result = agent(prompt)  # type: ignore[operator]

    elapsed = time.perf_counter() - start
    output_text = str(result)

    setattr(ctx, output_attr, output_text)
    ctx.phase_results.append(
        PhaseResult(
            phase=phase_name,
            prompt=prompt,
            output=output_text,
            elapsed_seconds=round(elapsed, 3),
        )
    )

    logger.info(
        "[%s] Phase '%s' completed in %.2fs (%d chars)",
        ctx.provider,
        phase_name,
        elapsed,
        len(output_text),
    )
    return ctx
