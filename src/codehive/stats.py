from __future__ import annotations

from dataclasses import dataclass, field
from time import time


@dataclass(slots=True)
class RuntimeStats:
    start_ts: float = field(default_factory=time)
    tasks_total: int = 0
    tasks_success: int = 0
    tasks_failed: int = 0
    active_agents: int = 0
    bus_events: int = 0

    def mark_task(self, success: bool) -> None:
        self.tasks_total += 1
        if success:
            self.tasks_success += 1
        else:
            self.tasks_failed += 1

    def mark_event(self) -> None:
        self.bus_events += 1

    @property
    def elapsed_seconds(self) -> float:
        return time() - self.start_ts

    def as_dict(self) -> dict:
        return {
            "tasks_total": self.tasks_total,
            "tasks_success": self.tasks_success,
            "tasks_failed": self.tasks_failed,
            "active_agents": self.active_agents,
            "bus_events": self.bus_events,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
        }
