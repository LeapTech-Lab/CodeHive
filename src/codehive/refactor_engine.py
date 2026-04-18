from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .models import Finding
from .training_sources import TrainingSource


@dataclass(slots=True)
class RefactorEngine:
    """Apply lightweight automated cleanup guided by paradigm and language constraints."""

    paradigm: str

    def refactor_directory(self, directory: Path, training: TrainingSource) -> tuple[list[str], list[Finding]]:
        changed_files: list[str] = []
        findings: list[Finding] = []

        for file_path in directory.rglob("*"):
            if not file_path.is_file() or file_path.name in {"PROMPT.md", "architecture_summary.json"}:
                continue
            if file_path.suffix.lower() not in {".py", ".ts", ".tsx", ".go", ".cc", ".cpp", ".hpp", ".h", ".rs"}:
                continue

            original = file_path.read_text(encoding="utf-8", errors="ignore")
            cleaned = self._apply_general_cleanup(original)
            cleaned = self._inject_paradigm_hint(cleaned, file_path, training)

            if cleaned != original:
                file_path.write_text(cleaned, encoding="utf-8")
                changed_files.append(str(file_path))
                findings.append(
                    Finding(
                        file_path=str(file_path),
                        issue=f"Refactored with paradigm={self.paradigm}, training={training.name}",
                        severity="info",
                    )
                )

        return changed_files, findings

    def _apply_general_cleanup(self, code: str) -> str:
        # Remove repeated blank lines and trailing spaces.
        lines = [line.rstrip() for line in code.splitlines()]
        compact: list[str] = []
        blank = 0
        for line in lines:
            if line.strip() == "":
                blank += 1
            else:
                blank = 0
            if blank <= 1:
                compact.append(line)
        return "\n".join(compact).strip() + "\n"

    def _inject_paradigm_hint(self, code: str, file_path: Path, training: TrainingSource) -> str:
        header = f"// Refactored by CodeHive paradigm={self.paradigm} training={training.name}"
        if file_path.suffix == ".py":
            header = f"# Refactored by CodeHive paradigm={self.paradigm} training={training.name}"
        if code.startswith(header):
            return code
        return f"{header}\n{code}"
