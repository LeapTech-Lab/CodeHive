from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass


class LLMClient(ABC):
    """Abstract text generation backend."""

    @abstractmethod
    def generate_json(self, prompt: str) -> dict:
        raise NotImplementedError


@dataclass(slots=True)
class MockLLMClient(LLMClient):
    """Deterministic fallback planner for offline use."""

    def generate_json(self, prompt: str) -> dict:
        # Kept intentionally simple and deterministic.
        return {
            "project_name": "generated_project",
            "tech_stack": ["Python", "Typer", "Pydantic"],
            "directories": [
                {
                    "path": ".",
                    "responsibility": "Project-level orchestration and shared architecture.",
                    "inputs": ["Project brief", "CLI arguments"],
                    "outputs": ["Global architecture summary", "System config"],
                    "dependencies": [],
                    "conventions": ["Keep root lightweight", "Prefer typed Python"],
                    "files_to_generate": ["README.md", "pyproject.toml"],
                },
                {
                    "path": "src",
                    "responsibility": "Application source code.",
                    "inputs": ["Architecture summary"],
                    "outputs": ["Reusable packages"],
                    "dependencies": ["."],
                    "conventions": ["Use src layout", "Module-level docstrings"],
                    "files_to_generate": ["__init__.py"],
                },
                {
                    "path": "tests",
                    "responsibility": "Automated validation of generated modules.",
                    "inputs": ["Public APIs"],
                    "outputs": ["Test reports"],
                    "dependencies": ["src"],
                    "conventions": ["Fast unit tests", "Deterministic fixtures"],
                    "files_to_generate": ["test_smoke.py"],
                },
                {
                    "path": "docs",
                    "responsibility": "Documentation and architecture decision records.",
                    "inputs": ["Module contracts", "Release notes"],
                    "outputs": ["Human-readable docs"],
                    "dependencies": ["."],
                    "conventions": ["Keep docs concise", "Prefer examples"],
                    "files_to_generate": ["overview.md"],
                },
            ],
        }


@dataclass(slots=True)
class AnthropicLLMClient(LLMClient):
    """Anthropic Claude JSON planner."""

    model: str = "claude-3-7-sonnet-latest"

    def generate_json(self, prompt: str) -> dict:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")

        try:
            from anthropic import Anthropic
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "anthropic package is not installed. Install with `pip install codehive[anthropic]`."
            ) from exc

        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model=self.model,
            max_tokens=3000,
            temperature=0.1,
            system="Respond with valid JSON only.",
            messages=[{"role": "user", "content": prompt}],
        )

        text_parts = [b.text for b in response.content if getattr(b, "type", None) == "text"]
        raw = "".join(text_parts).strip()
        return json.loads(raw)
