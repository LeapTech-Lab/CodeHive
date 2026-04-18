from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .agents.directory_agent import DirectoryAgent
from .messaging import MessageBus
from .models import ArchitectureSummary, DirectorySpec


@dataclass
class AgentPool:
    """Dynamic pool: lazily create/reuse/destroy directory agents."""

    architecture: ArchitectureSummary
    bus: MessageBus
    _agents: dict[str, DirectoryAgent] = field(default_factory=dict)

    def get_agent(self, spec: DirectorySpec) -> DirectoryAgent:
        if spec.path not in self._agents:
            agent_path = (self.architecture.root_path / spec.path).resolve()
            self._agents[spec.path] = DirectoryAgent(
                name=spec.path,
                directory_path=agent_path,
                architecture=self.architecture,
                bus=self.bus,
            )
        return self._agents[spec.path]

    def release_agent(self, directory_path: str) -> None:
        self._agents.pop(directory_path, None)

    def active_count(self) -> int:
        return len(self._agents)

    def clear(self) -> None:
        self._agents.clear()
