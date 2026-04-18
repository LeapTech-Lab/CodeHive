from __future__ import annotations

import json
import logging
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .orchestrator import Orchestrator

app = typer.Typer(help="CodeHive dynamic directory-level multi-agent framework")
console = Console()


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )


def _print_results(title: str, mode: str, root: Path, review: dict[str, int], results) -> None:
    table = Table(title=title)
    table.add_column("Directory")
    table.add_column("Action")
    table.add_column("Success")
    table.add_column("Changed")
    table.add_column("Findings")
    for result in results:
        table.add_row(
            result.directory,
            result.action,
            str(result.success),
            str(len(result.changed_files)),
            str(len(result.findings)),
        )
    console.print(table)
    console.print(f"\n[bold]Mode:[/bold] {mode}")
    console.print(f"[bold]Root:[/bold] {root.resolve()}")
    console.print(f"[bold]Consistency Review:[/bold] {json.dumps(review, ensure_ascii=False)}")


@app.command()
def generate(
    brief: str = typer.Option(..., "--brief", help="Project brief in natural language"),
    output_root: str = typer.Option("./generated", help="Output folder"),
    paradigm: str = typer.Option("clean-architecture", help="Target paradigm (factory/mvc/ddd/...)"),
    use_anthropic: bool = typer.Option(False, help="Use Anthropic Claude planning"),
    max_workers: int = typer.Option(4, min=1, max=32, help="Parallel directory workers"),
    verbose: bool = typer.Option(False, help="Enable debug logs"),
) -> None:
    _setup_logging(verbose)
    orchestrator = Orchestrator(use_anthropic=use_anthropic, max_workers=max_workers)
    summary, results, review = orchestrator.run_generation(brief=brief, output_root=output_root, paradigm=paradigm)
    _print_results("Generation Results", summary.mode.value, Path(summary.root_path), review, results)
    console.print("\n[bold]Runtime Stats[/bold]")
    console.print(json.dumps(orchestrator.stats.as_dict(), ensure_ascii=False, indent=2))


@app.command()
def refactor(
    path: str = typer.Option(..., "--path", help="Existing messy repository path"),
    paradigm: str = typer.Option("factory", "--paradigm", help="Refactor paradigm (factory/builder/mvc/ddd/...)"),
    use_anthropic: bool = typer.Option(False, help="Use Anthropic Claude reverse engineering"),
    max_workers: int = typer.Option(4, min=1, max=32, help="Parallel directory workers"),
    verbose: bool = typer.Option(False, help="Enable debug logs"),
) -> None:
    _setup_logging(verbose)
    orchestrator = Orchestrator(use_anthropic=use_anthropic, max_workers=max_workers)
    summary, results, review = orchestrator.run_refactor(repo_path=path, paradigm=paradigm)
    _print_results("Refactor Results", summary.mode.value, Path(summary.root_path), review, results)
    console.print("\n[bold]Runtime Stats[/bold]")
    console.print(json.dumps(orchestrator.stats.as_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    app()
