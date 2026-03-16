"""
agent/cli.py — Typer-based CLI entrypoint.

Commands:
  agent run          Execute the engineering workflow
  agent list-tasks   List available tasks from tasks/issues.yaml
  agent doctor       Validate environment and configuration
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="agent",
    help="strands-multi-engineer-agent — multi-provider engineering assistant",
    no_args_is_help=True,
)
console = Console()


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------
@app.command()
def run(
    task_id: Optional[str] = typer.Option(
        None,
        "--task",
        "-t",
        help="Task ID from tasks/issues.yaml. If omitted, uses the first task.",
    ),
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        "-p",
        help="Override DEFAULT_PROVIDER for this run (anthropic | openai | ollama).",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Validate config and print the task without executing the workflow.",
    ),
) -> None:
    """Run the engineering workflow against a task."""
    from agent.config import load_config, Provider
    from tasks.task_runner import load_tasks

    # Allow provider override via CLI flag
    import os
    if provider:
        os.environ["DEFAULT_PROVIDER"] = provider

    try:
        config = load_config()
    except Exception as exc:
        console.print(f"[bold red]Config error:[/bold red] {exc}")
        console.print("Run [bold]agent doctor[/bold] for a full diagnostic.")
        raise typer.Exit(code=1)

    _configure_logging(config.log_level)

    tasks = load_tasks()
    if not tasks:
        console.print("[yellow]No tasks found in tasks/issues.yaml[/yellow]")
        raise typer.Exit(code=1)

    task = _select_task(tasks, task_id)
    if task is None:
        console.print(f"[red]Task '{task_id}' not found.[/red]")
        raise typer.Exit(code=1)

    console.print(f"\n[bold]Provider:[/bold]  {config.default_provider.value}")
    console.print(f"[bold]Model:[/bold]     {config.active_model()}")
    console.print(f"[bold]Task:[/bold]      {task['id']} — {task['title']}")
    console.print(f"[bold]Repo:[/bold]      {task.get('repo', 'N/A')}\n")

    if dry_run:
        console.print("[yellow]Dry run — skipping workflow execution.[/yellow]")
        return

    from agent.workflow import run_workflow
    from eval.metrics import record_result

    repo_path = task.get("repo", config.sample_repo_path)

    with console.status("[bold green]Running workflow…[/bold green]"):
        try:
            result = run_workflow(
                issue=task["description"],
                repo_path=repo_path,
                config=config,
            )
        except Exception as exc:
            console.print(f"[bold red]Workflow error:[/bold red] {exc}")
            raise typer.Exit(code=1)

    output_path = record_result(result, results_dir=config.results_dir)
    console.print(f"\n[bold green]Done![/bold green] Results saved to: {output_path}")
    console.print(f"Total time: {result.total_elapsed_seconds}s")


# ---------------------------------------------------------------------------
# list-tasks
# ---------------------------------------------------------------------------
@app.command("list-tasks")
def list_tasks() -> None:
    """List all available engineering tasks."""
    from tasks.task_runner import load_tasks

    tasks = load_tasks()
    if not tasks:
        console.print("[yellow]No tasks found in tasks/issues.yaml[/yellow]")
        return

    table = Table(title="Available Tasks", show_lines=True)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="bold")
    table.add_column("Repo", style="dim")
    table.add_column("Difficulty", justify="center")

    for task in tasks:
        table.add_row(
            task.get("id", "—"),
            task.get("title", "—"),
            task.get("repo", "—"),
            task.get("difficulty", "—"),
        )

    console.print(table)


# ---------------------------------------------------------------------------
# doctor
# ---------------------------------------------------------------------------
@app.command()
def doctor() -> None:
    """Validate environment configuration and provider connectivity."""
    from agent.config import load_config

    console.print("\n[bold]strands-multi-engineer-agent — environment check[/bold]\n")

    # Config validation
    try:
        config = load_config()
        report = config.doctor_report()
        console.print("[bold green]✓[/bold green]  Config loaded successfully\n")
    except Exception as exc:
        console.print(f"[bold red]✗  Config validation failed:[/bold red] {exc}\n")
        raise typer.Exit(code=1)

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="cyan")
    table.add_column("Value")

    for key, value in report.items():
        style = "red" if value == "NOT SET" else "green" if value == "set" else ""
        table.add_row(key, f"[{style}]{value}[/{style}]" if style else value)

    console.print(table)

    # Strands import check
    try:
        import strands  # noqa: F401
        console.print("\n[green]✓[/green]  strands-agents is importable")
    except ImportError:
        console.print("\n[red]✗[/red]  strands-agents is NOT installed — run: pip install strands-agents")

    console.print()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _select_task(tasks: list[dict], task_id: Optional[str]) -> Optional[dict]:
    if task_id is None:
        return tasks[0]
    return next((t for t in tasks if t.get("id") == task_id), None)


if __name__ == "__main__":
    app()
