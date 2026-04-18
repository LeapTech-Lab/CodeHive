from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class DirectorySpec:
    """Description of a single directory in the generated project."""

    path: str
    responsibility: str
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    conventions: list[str] = field(default_factory=list)
    files_to_generate: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ArchitectureSummary:
    """Compact global architecture summary used by all directory agents."""

    project_name: str
    brief: str
    root_path: Path
    directories: list[DirectorySpec]
    tech_stack: list[str] = field(default_factory=lambda: ["Python"])

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "brief": self.brief,
            "root_path": str(self.root_path),
            "tech_stack": self.tech_stack,
            "directories": [
                {
                    "path": d.path,
                    "responsibility": d.responsibility,
                    "inputs": d.inputs,
                    "outputs": d.outputs,
                    "dependencies": d.dependencies,
                    "conventions": d.conventions,
                    "files_to_generate": d.files_to_generate,
                }
                for d in self.directories
            ],
        }


@dataclass(slots=True)
class AgentTask:
    """A unit of work assigned to a directory agent."""

    directory: DirectorySpec
    action: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TaskResult:
    """Result from running a task with a directory agent."""

    directory: str
    action: str
    success: bool
    changed_files: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    error: str | None = None
