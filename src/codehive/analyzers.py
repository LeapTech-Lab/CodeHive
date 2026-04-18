from __future__ import annotations

from pathlib import Path

from .models import Finding


LANG_EXTENSIONS: dict[str, str] = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "typescript",
    ".go": "go",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".h": "cpp",
    ".rs": "rust",
}


def detect_language(file_path: Path) -> str:
    return LANG_EXTENSIONS.get(file_path.suffix.lower(), "generic")


def static_scan_file(file_path: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return findings

    lines = content.splitlines()
    if len(lines) > 600:
        findings.append(Finding(file_path=str(file_path), issue="Very large file, consider splitting.", severity="high"))

    if "TODO" in content or "FIXME" in content:
        findings.append(Finding(file_path=str(file_path), issue="Contains unresolved TODO/FIXME.", severity="medium"))

    if "print(" in content and file_path.suffix in {".py", ".ts", ".js"}:
        findings.append(Finding(file_path=str(file_path), issue="Debug print statements detected.", severity="low"))

    if "pass" in lines and file_path.suffix == ".py":
        findings.append(Finding(file_path=str(file_path), issue="Potential incomplete python implementation (`pass`).", severity="medium"))

    return findings
