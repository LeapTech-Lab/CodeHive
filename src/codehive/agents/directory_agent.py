from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..analyzers import static_scan_file
from ..messaging import BusMessage, MessageBus, NotificationCollector
from ..models import AgentTask, ArchitectureSummary, Finding, TaskResult
from ..refactor_engine import RefactorEngine
from ..sandbox import DirectorySandbox
from ..training_sources import select_training_source


@dataclass
class DirectoryAgent:
    """Hive worker: only reads/writes inside its own hive (directory)."""

    name: str
    directory_path: Path
    architecture: ArchitectureSummary
    bus: MessageBus
    collector: NotificationCollector = field(default_factory=NotificationCollector)

    def __post_init__(self) -> None:
        self.sandbox = DirectorySandbox(self.directory_path)
        self.bus.subscribe(self.name, self.collector)

    def run_task(self, task: AgentTask) -> TaskResult:
        try:
            if task.action == "generate":
                changed_files = self._generate_code(task.directory.path)
                findings: list[Finding] = []
            elif task.action == "analyze":
                findings = self._analyze_directory()
                changed_files = [self._write_prompt_doc(task.directory.path)]
            elif task.action == "refactor":
                changed_files, findings = self._refactor_directory(task.directory.path)
            else:
                return TaskResult(directory=task.directory.path, action=task.action, success=False, error="Unsupported action")

            self.bus.publish(
                BusMessage(topic="directory.changed", sender=task.directory.path, payload={"action": task.action, "changed_files": changed_files})
            )
            return TaskResult(
                directory=task.directory.path,
                action=task.action,
                success=True,
                changed_files=changed_files,
                findings=findings,
            )
        except Exception as exc:
            return TaskResult(directory=task.directory.path, action=task.action, success=False, error=str(exc))

    def _generate_code(self, relative_dir: str) -> list[str]:
        changed: list[str] = [self._write_prompt_doc(relative_dir)]
        spec = self._get_spec(relative_dir)
        for name in spec.files_to_generate:
            if name.upper() == "PROMPT.MD":
                continue
            target = self.directory_path / name
            if target.exists():
                continue
            content = self._default_file_content(name, spec.responsibility)
            self.sandbox.safe_write_text(target, content)
            changed.append(str(target))
        return changed

    def _analyze_directory(self) -> list[Finding]:
        findings: list[Finding] = []
        for file_path in self.directory_path.rglob("*"):
            if not file_path.is_file() or file_path.name == "PROMPT.md":
                continue
            self.sandbox.assert_within_scope(file_path)
            findings.extend(static_scan_file(file_path))
        return findings

    def _refactor_directory(self, relative_dir: str) -> tuple[list[str], list[Finding]]:
        spec = self._get_spec(relative_dir)
        training = select_training_source(spec.language)
        engine = RefactorEngine(paradigm=self.architecture.paradigm or "clean-architecture")
        changed, findings = engine.refactor_directory(self.directory_path, training)

        prompt_file = self._write_prompt_doc(relative_dir, extra_constraints=training.constraints)
        changed.append(prompt_file)
        return changed, findings

    def _write_prompt_doc(self, relative_dir: str, extra_constraints: list[str] | None = None) -> str:
        spec = self._get_spec(relative_dir)
        constraints = spec.conventions + (extra_constraints or [])
        content = [
            f"# PROMPT.md - {relative_dir}",
            "",
            "## 目录职责",
            spec.responsibility,
            "",
            "## 输入/输出契约",
            "### 输入",
            *[f"- {i}" for i in (spec.inputs or ["(待补充输入契约)"])],
            "### 输出",
            *[f"- {o}" for o in (spec.outputs or ["(待补充输出契约)"])],
            "",
            "## 依赖关系",
            *[f"- {dep}" for dep in (spec.dependencies or ["(无)"])],
            "",
            "## 编码规范与约束",
            *[f"- {rule}" for rule in (constraints or ["遵循语言最佳实践，移除冗余并保持可测试性"])],
            "",
            "## 全局架构摘要",
            f"- 模式: {self.architecture.mode.value}",
            f"- 项目: {self.architecture.project_name}",
            f"- 技术栈: {', '.join(self.architecture.tech_stack)}",
            f"- 范式: {self.architecture.paradigm or '默认'}",
            "- 如目录变更影响依赖方，请发布 directory.changed 消息。",
        ]
        target = self.directory_path / "PROMPT.md"
        self.sandbox.safe_write_text(target, "\n".join(content) + "\n")
        return str(target)

    def _default_file_content(self, filename: str, responsibility: str) -> str:
        if filename.endswith(".py"):
            return f'"""{responsibility}"""\n\n\ndef main() -> None:\n    pass\n'
        if filename.endswith(".ts"):
            return f"// {responsibility}\nexport function main(): void {{}}\n"
        if filename.endswith(".go"):
            return "package main\n\nfunc main() {}\n"
        if filename.endswith(".rs"):
            return "fn main() {}\n"
        if filename.endswith((".cpp", ".cc")):
            return "int main() { return 0; }\n"
        return f"# {responsibility}\n"

    def _get_spec(self, relative_dir: str):
        spec = next((d for d in self.architecture.directories if d.path == relative_dir), None)
        if not spec:
            raise ValueError(f"Directory spec missing for {relative_dir}")
        return spec
