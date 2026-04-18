from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from .agents.root_agent import RootAgent
from .llm import AnthropicLLMClient, MockLLMClient
from .messaging import BusMessage, MessageBus
from .models import AgentTask, ArchitectureSummary, TaskResult
from .pool import AgentPool
from .stats import RuntimeStats

LOGGER = logging.getLogger(__name__)


@dataclass
class Orchestrator:
    """Coordinates root and directory agents with concurrency + message bus."""

    use_anthropic: bool = False
    max_workers: int = 4

    def __post_init__(self) -> None:
        llm = AnthropicLLMClient() if self.use_anthropic else MockLLMClient()
        self.root_agent = RootAgent(llm=llm)
        self.bus = MessageBus()
        self.stats = RuntimeStats()
        self.bus.subscribe("directory.changed", self._handle_directory_changed)

    def run(self, brief: str, output_root: str | Path) -> tuple[ArchitectureSummary, list[TaskResult]]:
        output_path = Path(output_root)
        summary = self.root_agent.plan_architecture(brief, output_path)
        self.root_agent.create_directory_tree(summary)
        summary_file = self.root_agent.persist_global_summary(summary)
        LOGGER.info("Global architecture summary created at %s", summary_file)

        pool = AgentPool(architecture=summary, bus=self.bus)
        results: list[TaskResult] = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for directory in summary.directories:
                task = AgentTask(directory=directory, action="generate_scaffold")
                agent = pool.get_agent(directory)
                futures.append(executor.submit(agent.run_task, task))
                self.stats.active_agents = pool.active_count()

            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                self.stats.mark_task(result.success)
                if not result.success:
                    LOGGER.error("Task failed: %s", result)

        self.stats.active_agents = pool.active_count()
        pool.clear()
        self.stats.active_agents = pool.active_count()
        return summary, sorted(results, key=lambda r: r.directory)

    def _handle_directory_changed(self, message: BusMessage) -> None:
        sender = message.sender
        LOGGER.info("Directory changed: %s (%s)", sender, message.payload.get("changed_files", []))
