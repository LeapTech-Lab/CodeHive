from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from ..messaging import BusMessage, MessageBus, NotificationCollector
from ..models import AgentTask, ArchitectureSummary, TaskResult
from ..sandbox import DirectorySandbox


@dataclass
class DirectoryAgent:
    """Directory-scoped worker with strict filesystem sandboxing."""

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
            if task.action == "generate_scaffold":
                changed_files = self._generate_scaffold(task.directory.path)
            elif task.action == "refresh_contract":
                changed_files = [self._write_contract_doc(task.directory.path)]
            else:
                return TaskResult(
                    directory=task.directory.path,
                    action=task.action,
                    success=False,
                    error=f"Unsupported action: {task.action}",
                )

            self.bus.publish(
                BusMessage(
                    topic="directory.changed",
                    sender=task.directory.path,
                    payload={"changed_files": changed_files},
                )
            )
            return TaskResult(
                directory=task.directory.path,
                action=task.action,
                success=True,
                changed_files=changed_files,
            )
        except Exception as exc:
            return TaskResult(
                directory=task.directory.path,
                action=task.action,
                success=False,
                error=str(exc),
            )

    def _generate_scaffold(self, relative_dir: str) -> list[str]:
        changed: list[str] = []
        contract_file = self._write_contract_doc(relative_dir)
        changed.append(contract_file)

        marker = self.directory_path / ".codehive.generated"
        self.sandbox.safe_write_text(marker, "generated=true\n")
        changed.append(str(marker))

        if relative_dir.startswith("src"):
            init_file = self.directory_path / "__init__.py"
            if not init_file.exists():
                self.sandbox.safe_write_text(init_file, '"""Generated package."""\n')
                changed.append(str(init_file))
        return changed

    def _write_contract_doc(self, relative_dir: str) -> str:
        spec = next((d for d in self.architecture.directories if d.path == relative_dir), None)
        if spec is None:
            raise ValueError(f"No directory spec found for {relative_dir}")

        content = [
            f"# CLAUDE.md - {relative_dir}",
            "",
            "## 目录职责与目标",
            spec.responsibility,
            "",
            "## 输入/输出契约",
            "### 输入",
            *[f"- {item}" for item in spec.inputs],
            "### 输出",
            *[f"- {item}" for item in spec.outputs],
            "",
            "## 依赖关系",
            *[f"- {dep}" for dep in (spec.dependencies or ["(无)"])],
            "",
            "## 本目录编码规范",
            *[f"- {rule}" for rule in spec.conventions],
            "",
            "## 全局架构摘要（压缩版）",
            f"- 项目: {self.architecture.project_name}",
            f"- 技术栈: {', '.join(self.architecture.tech_stack)}",
            f"- 目录总数: {len(self.architecture.directories)}",
            "- 变更后请通过消息总线通知相关依赖目录。",
        ]
        target = self.directory_path / "CLAUDE.md"
        self.sandbox.safe_write_text(target, "\n".join(content) + "\n")
        return str(target)
