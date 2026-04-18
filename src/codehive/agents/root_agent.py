from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from ..analyzers import detect_language
from ..llm import LLMClient
from ..models import ArchitectureSummary, DirectorySpec, Mode


@dataclass
class RootAgent:
    """Queen bee: global planning, analysis, and final consistency review."""

    llm: LLMClient

    def plan_generation(self, brief: str, output_root: Path, paradigm: str | None = None) -> ArchitectureSummary:
        raw = self.llm.generate_json(self._generation_prompt(brief))
        project_name = self._slug(raw.get("project_name", "generated_project"))
        directories = [DirectorySpec(**d) for d in raw["directories"]]
        return ArchitectureSummary(
            project_name=project_name,
            brief=brief,
            root_path=output_root / project_name,
            mode=Mode.GENERATION,
            directories=directories,
            tech_stack=raw.get("tech_stack", ["Python"]),
            paradigm=paradigm,
        )

    def plan_refactor(self, repo_path: Path, paradigm: str) -> ArchitectureSummary:
        directories: list[DirectorySpec] = []
        repo_path = repo_path.resolve()

        for d in [repo_path] + [p for p in repo_path.rglob("*") if p.is_dir()]:
            if ".git" in d.parts or "__pycache__" in d.parts:
                continue
            rel = "." if d == repo_path else str(d.relative_to(repo_path))
            language = self._guess_directory_language(d)
            inferred = self._infer_prompt_for_directory(d)
            directories.append(
                DirectorySpec(
                    path=rel,
                    responsibility=inferred["responsibility"],
                    inputs=inferred["inputs"],
                    outputs=inferred["outputs"],
                    dependencies=inferred["dependencies"],
                    conventions=inferred["conventions"],
                    files_to_generate=["PROMPT.md"],
                    language=language,
                )
            )

        return ArchitectureSummary(
            project_name=repo_path.name,
            brief=f"Refactor existing repository at {repo_path}",
            root_path=repo_path,
            mode=Mode.REFACTOR,
            directories=directories,
            tech_stack=sorted({d.language for d in directories}),
            paradigm=paradigm,
        )

    def create_directory_tree(self, summary: ArchitectureSummary) -> None:
        for spec in summary.directories:
            (summary.root_path / spec.path).mkdir(parents=True, exist_ok=True)

    def persist_global_summary(self, summary: ArchitectureSummary) -> Path:
        target = summary.root_path / "architecture_summary.json"
        target.write_text(json.dumps(summary.to_json_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return target

    def review_consistency(self, summary: ArchitectureSummary) -> dict[str, int]:
        dependency_errors = 0
        all_paths = {d.path for d in summary.directories}
        for d in summary.directories:
            for dep in d.dependencies:
                if dep not in all_paths and dep != "internal modules":
                    dependency_errors += 1
        return {
            "directories": len(summary.directories),
            "dependency_errors": dependency_errors,
        }

    def _infer_prompt_for_directory(self, directory: Path) -> dict:
        file_names = sorted([p.name for p in directory.glob("*") if p.is_file()])[:40]
        prompt = (
            "REVERSE_ENGINEER_PROMPT: infer directory contract JSON with keys "
            "responsibility, inputs, outputs, dependencies, conventions. "
            f"Directory={directory.name}; files={file_names}"
        )
        return self.llm.generate_json(prompt)

    def _guess_directory_language(self, directory: Path) -> str:
        counts: dict[str, int] = {}
        for file_path in directory.glob("*"):
            if not file_path.is_file():
                continue
            lang = detect_language(file_path)
            counts[lang] = counts.get(lang, 0) + 1
        if not counts:
            return "generic"
        return max(counts.items(), key=lambda x: x[1])[0]

    def _generation_prompt(self, brief: str) -> str:
        return (
            "Create directory architecture JSON with project_name, tech_stack, directories[]. "
            "Each directory object must include path, responsibility, inputs, outputs, dependencies, conventions, "
            "files_to_generate, language. Include root '.' . Brief:\n"
            f"{brief}"
        )

    def _slug(self, raw: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9_-]", "_", raw.strip().lower())
        return cleaned.strip("_") or "generated_project"
