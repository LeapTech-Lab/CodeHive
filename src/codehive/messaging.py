from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable


@dataclass(slots=True)
class BusMessage:
    topic: str
    sender: str
    payload: dict


class MessageBus:
    """Simple in-process pub/sub bus for cross-agent dependency notifications."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[BusMessage], None]]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Callable[[BusMessage], None]) -> None:
        self._subscribers[topic].append(handler)

    def publish(self, message: BusMessage) -> None:
        for handler in self._subscribers.get(message.topic, []):
            handler(message)


@dataclass(slots=True)
class NotificationCollector:
    """Collects messages received by an agent for traceability/debugging."""

    messages: list[BusMessage] = field(default_factory=list)

    def __call__(self, message: BusMessage) -> None:
        self.messages.append(message)
