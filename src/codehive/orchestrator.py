from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from .agents.root_agent import RootAgent
from .llm import AnthropicLLMClient, MockLLMClient
from .messaging import BusMessage, MessageBus
from .models import AgentTask, ArchitectureSummary, Mode, TaskResult
from .pool import AgentPool
from .stats import RuntimeStats

LOGGER = logging.getLogger(__name__)


@dataclass
class Orchestrator:
    """Coordinates generation and refactor workflows around RootAgent and AgentPool."""

    use_anthropic: bool = False
    max_workers: int = 4

    def __post_init__(self) -> None:
        llm = AnthropicLLMClient() if self.use_anthropic else MockLLMClient()
        self.root_agent = RootAgent(llm=llm)
        self.bus = MessageBus()
        self.stats = RuntimeStats()
        self.bus.subscribe("directory.changed", self._handle_bus_event)

    def run_generation(
        self,
        brief: str,
        output_root: str | Path,
        paradigm: str | None = None,
    ) -> tuple[ArchitectureSummary, list[TaskResult], dict[str, int]]:
        summary = self.root_agent.plan_generation(brief=brief, output_root=Path(output_root), paradigm=paradigm)
        self.root_agent.create_directory_tree(summary)
        self.root_agent.persist_global_summary(summary)
        results = self._run_directory_tasks(summary=summary, action="generate")
        review = self.root_agent.review_consistency(summary)
        return summary, results, review

    def run_refactor(
        self,
        repo_path: str | Path,
        paradigm: str,
    ) -> tuple[ArchitectureSummary, list[TaskResult], dict[str, int]]:
        summary = self.root_agent.plan_refactor(repo_path=Path(repo_path), paradigm=paradigm)
        self.root_agent.persist_global_summary(summary)

        analyze_results = self._run_directory_tasks(summary=summary, action="analyze")
        refactor_results = self._run_directory_tasks(summary=summary, action="refactor")
        review = self.root_agent.review_consistency(summary)

        merged = analyze_results + refactor_results
        return summary, merged, review

    def _run_directory_tasks(self, summary: ArchitectureSummary, action: str) -> list[TaskResult]:
        pool = AgentPool(architecture=summary, bus=self.bus, max_active=max(self.max_workers, 1))
        results: list[TaskResult] = []

        def _execute(directory):
            pool.acquire_slot()
            try:
                task = AgentTask(directory=directory, action=action)
                agent = pool.get_agent(directory)
                self.stats.active_agents = pool.active_count()
                return agent.run_task(task)
            finally:
                pool.release_slot()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(_execute, directory) for directory in summary.directories]
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                self.stats.mark_task(result.success)
                if not result.success:
                    LOGGER.error("Task failed directory=%s action=%s err=%s", result.directory, result.action, result.error)

        self.stats.active_agents = pool.active_count()
        pool.clear()
        self.stats.active_agents = pool.active_count()
        return sorted(results, key=lambda r: (r.directory, r.action))

    def _handle_bus_event(self, message: BusMessage) -> None:
        self.stats.mark_event()
        LOGGER.info("Bus event topic=%s sender=%s", message.topic, message.sender)

    @staticmethod
    def mode_label(mode: Mode) -> str:
        return mode.value
