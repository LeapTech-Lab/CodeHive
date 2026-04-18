from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from ..llm import LLMClient
from ..models import ArchitectureSummary, DirectorySpec


@dataclass
class RootAgent:
    """Analyzes project brief and creates global architecture + directory contracts."""

    llm: LLMClient

    def plan_architecture(self, brief: str, output_root: Path) -> ArchitectureSummary:
        prompt = self._build_prompt(brief)
        raw = self.llm.generate_json(prompt)
        project_name = self._derive_project_name(raw.get("project_name", "generated_project"))
        directories = [DirectorySpec(**d) for d in raw["directories"]]
        return ArchitectureSummary(
            project_name=project_name,
            brief=brief,
            root_path=output_root / project_name,
            directories=directories,
            tech_stack=raw.get("tech_stack", ["Python"]),
        )

    def persist_global_summary(self, summary: ArchitectureSummary) -> Path:
        summary.root_path.mkdir(parents=True, exist_ok=True)
        target = summary.root_path / "architecture_summary.json"
        target.write_text(
            json.dumps(summary.to_json_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return target

    def create_directory_tree(self, summary: ArchitectureSummary) -> None:
        for spec in summary.directories:
            path = summary.root_path / spec.path
            path.mkdir(parents=True, exist_ok=True)

    def _build_prompt(self, brief: str) -> str:
        return (
            "You are a software architect. Convert the project brief into JSON with keys:"
            " project_name, tech_stack, directories. Each directory item must include"
            " path, responsibility, inputs, outputs, dependencies, conventions, files_to_generate."
            " Ensure '.' root directory is included. Brief:\n"
            f"{brief}"
        )

    def _derive_project_name(self, raw: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9_-]", "_", raw.strip().lower())
        cleaned = cleaned.strip("_") or "generated_project"
        return cleaned
