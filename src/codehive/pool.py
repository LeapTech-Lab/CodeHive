from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .agents.directory_agent import DirectoryAgent
from .messaging import MessageBus
from .models import ArchitectureSummary, DirectorySpec


@dataclass
class AgentPool:
    """Dynamic create/reuse/destroy with idle recycle and concurrency gate."""

    architecture: ArchitectureSummary
    bus: MessageBus
    max_active: int = 8
    idle_ttl_seconds: int = 300
    _agents: dict[str, DirectoryAgent] = field(default_factory=dict)
    _last_used: dict[str, datetime] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._lock = threading.Lock()
        self._semaphore = threading.Semaphore(self.max_active)

    def get_agent(self, spec: DirectorySpec) -> DirectoryAgent:
        with self._lock:
            self._recycle_idle_locked()
            if spec.path not in self._agents:
                directory_path = (self.architecture.root_path / spec.path).resolve()
                self._agents[spec.path] = DirectoryAgent(
                    name=spec.path,
                    directory_path=directory_path,
                    architecture=self.architecture,
                    bus=self.bus,
                )
            self._last_used[spec.path] = datetime.utcnow()
            return self._agents[spec.path]

    def release_agent(self, path: str) -> None:
        with self._lock:
            self._agents.pop(path, None)
            self._last_used.pop(path, None)

    def acquire_slot(self) -> None:
        self._semaphore.acquire()

    def release_slot(self) -> None:
        self._semaphore.release()

    def active_count(self) -> int:
        with self._lock:
            return len(self._agents)

    def clear(self) -> None:
        with self._lock:
            self._agents.clear()
            self._last_used.clear()

    def _recycle_idle_locked(self) -> None:
        threshold = datetime.utcnow() - timedelta(seconds=self.idle_ttl_seconds)
        stale = [path for path, ts in self._last_used.items() if ts < threshold]
        for path in stale:
            self._agents.pop(path, None)
            self._last_used.pop(path, None)
