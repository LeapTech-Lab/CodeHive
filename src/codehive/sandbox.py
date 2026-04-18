from __future__ import annotations

from pathlib import Path


class DirectorySandbox:
    """Enforces that a directory agent can only read/write inside its own scope."""

    def __init__(self, scope_root: Path):
        self.scope_root = scope_root.resolve()

    def assert_within_scope(self, target: Path) -> None:
        resolved = target.resolve()
        if self.scope_root == resolved or self.scope_root in resolved.parents:
            return
        raise PermissionError(f"Path {resolved} is outside sandbox scope {self.scope_root}")

    def safe_write_text(self, target: Path, content: str) -> None:
        self.assert_within_scope(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def safe_read_text(self, target: Path) -> str:
        self.assert_within_scope(target)
        return target.read_text(encoding="utf-8")
