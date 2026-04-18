from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass


class LLMClient(ABC):
    @abstractmethod
    def generate_json(self, prompt: str) -> dict:
        raise NotImplementedError


@dataclass(slots=True)
class MockLLMClient(LLMClient):
    """Deterministic fallback planner for offline use."""

    def generate_json(self, prompt: str) -> dict:
        if "REVERSE_ENGINEER_PROMPT" in prompt:
            return {
                "responsibility": "Maintain and improve legacy code in this directory.",
                "inputs": ["Existing source files", "Cross-directory API dependencies"],
                "outputs": ["Refactored modules", "Reduced duplication", "Improved tests"],
                "dependencies": ["internal modules"],
                "conventions": [
                    "Follow language best practices",
                    "Eliminate dead code",
                    "Ensure deterministic behavior",
                ],
            }

        return {
            "project_name": "generated_project",
            "tech_stack": ["Python", "TypeScript", "Go", "Rust", "C++"],
            "directories": [
                {
                    "path": ".",
                    "responsibility": "Root coordination and global governance.",
                    "inputs": ["project brief", "operator commands"],
                    "outputs": ["architecture summary", "agent scheduling decisions"],
                    "dependencies": [],
                    "conventions": ["Minimal root files", "Declarative orchestration config"],
                    "files_to_generate": ["README.md", "pyproject.toml"],
                    "language": "generic",
                },
                {
                    "path": "apps/api",
                    "responsibility": "Service APIs and request handlers.",
                    "inputs": ["HTTP/gRPC requests", "domain services"],
                    "outputs": ["API responses", "domain events"],
                    "dependencies": ["libs/core", "libs/shared"],
                    "conventions": ["Validate inputs", "Use thin controller pattern"],
                    "files_to_generate": ["main.py", "handlers.py"],
                    "language": "python",
                },
                {
                    "path": "apps/web",
                    "responsibility": "Web UI and user interactions.",
                    "inputs": ["backend APIs", "user actions"],
                    "outputs": ["rendered views", "telemetry"],
                    "dependencies": ["libs/shared"],
                    "conventions": ["Type-safe UI", "Component reusability"],
                    "files_to_generate": ["index.ts"],
                    "language": "typescript",
                },
                {
                    "path": "libs/core",
                    "responsibility": "Business domain rules and use cases.",
                    "inputs": ["commands", "entities", "events"],
                    "outputs": ["domain decisions", "state transitions"],
                    "dependencies": ["libs/shared"],
                    "conventions": ["Pure domain logic", "No framework coupling"],
                    "files_to_generate": ["core.py"],
                    "language": "python",
                },
                {
                    "path": "libs/shared",
                    "responsibility": "Cross-cutting utilities and contracts.",
                    "inputs": ["app/core module calls"],
                    "outputs": ["reusable helper APIs"],
                    "dependencies": [],
                    "conventions": ["Backwards-compatible interfaces", "Low coupling"],
                    "files_to_generate": ["README.md"],
                    "language": "generic",
                },
                {
                    "path": "tests",
                    "responsibility": "Cross-module regression and contract tests.",
                    "inputs": ["module APIs", "fixtures"],
                    "outputs": ["test reports"],
                    "dependencies": ["apps/api", "apps/web", "libs/core"],
                    "conventions": ["Fast and deterministic tests", "High signal failure output"],
                    "files_to_generate": ["test_smoke.py"],
                    "language": "python",
                },
            ],
        }


@dataclass(slots=True)
class AnthropicLLMClient(LLMClient):
    model: str = "claude-3-7-sonnet-latest"

    def generate_json(self, prompt: str) -> dict:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")

        try:
            from anthropic import Anthropic
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                "anthropic package is not installed. Install with `pip install codehive[anthropic]`."
            ) from exc

        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model=self.model,
            max_tokens=3500,
            temperature=0.1,
            system="Return strictly valid JSON.",
            messages=[{"role": "user", "content": prompt}],
        )
        text_parts = [b.text for b in response.content if getattr(b, "type", None) == "text"]
        return json.loads("".join(text_parts).strip())
