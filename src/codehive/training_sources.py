from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TrainingSource:
    name: str
    language: str
    constraints: list[str]


LANGUAGE_TRAINING_SOURCES: dict[str, TrainingSource] = {
    "python": TrainingSource(
        name="PythonStrictAgent",
        language="python",
        constraints=[
            "Use type hints for public APIs.",
            "Keep functions small and single-purpose.",
            "Prefer dataclasses/pydantic for data contracts.",
            "Avoid duplicated logic; extract helpers.",
        ],
    ),
    "typescript": TrainingSource(
        name="TypeScriptStrictAgent",
        language="typescript",
        constraints=[
            "Use strict mode and explicit types.",
            "Prefer pure functions and avoid side-effect-heavy modules.",
            "Keep interfaces close to domain boundaries.",
        ],
    ),
    "go": TrainingSource(
        name="GoStrictAgent",
        language="go",
        constraints=[
            "Prefer small packages with focused responsibilities.",
            "Check every error path explicitly.",
            "Favor composition over deep inheritance-like patterns.",
        ],
    ),
    "cpp": TrainingSource(
        name="CppStrictAgent",
        language="cpp",
        constraints=[
            "Prefer RAII and smart pointers.",
            "Avoid raw owning pointers.",
            "Use const-correctness and explicit interfaces.",
        ],
    ),
    "rust": TrainingSource(
        name="RustStrictAgent",
        language="rust",
        constraints=[
            "Embrace ownership/borrowing rules over clones.",
            "Use Result-based error handling.",
            "Prefer traits and modules with clear boundaries.",
        ],
    ),
    "generic": TrainingSource(
        name="GenericQualityAgent",
        language="generic",
        constraints=[
            "Remove dead code and duplicated code paths.",
            "Keep module APIs minimal and cohesive.",
            "Enforce deterministic tests and structured logging.",
        ],
    ),
}


def select_training_source(language: str) -> TrainingSource:
    return LANGUAGE_TRAINING_SOURCES.get(language.lower(), LANGUAGE_TRAINING_SOURCES["generic"])
