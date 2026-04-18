from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class Mode(str, Enum):
    GENERATION = "generation"
    REFACTOR = "refactor"


@dataclass(slots=True)
class DirectorySpec:
    """Directory-level contract managed by RootAgent."""

    path: str
    responsibility: str
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    conventions: list[str] = field(default_factory=list)
    files_to_generate: list[str] = field(default_factory=list)
    language: str = "generic"


@dataclass(slots=True)
class ArchitectureSummary:
    project_name: str
    brief: str
    root_path: Path
    mode: Mode
    directories: list[DirectorySpec]
    tech_stack: list[str] = field(default_factory=lambda: ["Python"])
    paradigm: str | None = None

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "brief": self.brief,
            "root_path": str(self.root_path),
            "mode": self.mode.value,
            "tech_stack": self.tech_stack,
            "paradigm": self.paradigm,
            "directories": [
                {
                    "path": d.path,
                    "responsibility": d.responsibility,
                    "inputs": d.inputs,
                    "outputs": d.outputs,
                    "dependencies": d.dependencies,
                    "conventions": d.conventions,
                    "files_to_generate": d.files_to_generate,
                    "language": d.language,
                }
                for d in self.directories
            ],
        }


@dataclass(slots=True)
class AgentTask:
    directory: DirectorySpec
    action: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Finding:
    file_path: str
    issue: str
    severity: str = "medium"


@dataclass(slots=True)
class TaskResult:
    directory: str
    action: str
    success: bool
    changed_files: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    error: str | None = None
