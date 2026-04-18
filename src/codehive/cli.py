from __future__ import annotations

import json
import logging
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .orchestrator import Orchestrator

app = typer.Typer(help="CodeHive dynamic directory-level multi-agent generator")
console = Console()


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s")


@app.command()
def generate(
    brief: str = typer.Argument(..., help="Project brief in natural language"),
    output_root: str = typer.Option("./generated", help="Output folder for generated project"),
    use_anthropic: bool = typer.Option(False, help="Use Anthropic Claude instead of deterministic mock planner"),
    max_workers: int = typer.Option(4, min=1, max=32, help="Maximum parallel directory agents"),
    verbose: bool = typer.Option(False, help="Enable debug logs"),
) -> None:
    """Generate multi-agent project scaffold from a single project brief."""
    _setup_logging(verbose)
    orchestrator = Orchestrator(use_anthropic=use_anthropic, max_workers=max_workers)
    summary, task_results = orchestrator.run(brief=brief, output_root=output_root)

    table = Table(title="Directory Agent Execution Results")
    table.add_column("Directory")
    table.add_column("Action")
    table.add_column("Success")
    table.add_column("Changed files")

    for result in task_results:
        table.add_row(result.directory, result.action, str(result.success), str(len(result.changed_files)))
    console.print(table)

    stats_json = json.dumps(orchestrator.stats.as_dict(), ensure_ascii=False, indent=2)
    console.print("\n[bold]Runtime Stats[/bold]")
    console.print(stats_json)

    console.print("\n[bold green]Done[/bold green]")
    console.print(f"Project: {summary.project_name}")
    console.print(f"Root: {Path(summary.root_path).resolve()}")


if __name__ == "__main__":
    app()
