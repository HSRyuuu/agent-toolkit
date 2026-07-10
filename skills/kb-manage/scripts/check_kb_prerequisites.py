#!/usr/bin/env python3
"""Check the runtime prerequisites shared by all KB skills.

This script intentionally has no third-party dependencies. It can therefore
explain how to install the locked KB runtime even when it is missing.
"""

from __future__ import print_function

import importlib
import importlib.util
import os
import shlex
import shutil
import sys
from importlib import metadata
from pathlib import Path
from typing import Optional


MIN_PYTHON = (3, 10)
PINNED_FRONTMATTER = "1.3.0"
PINNED_PYYAML = "6.0.3"
DEFAULT_VENV_ROOT = Path.home() / ".venvs" / "agent-toolkit-kb"
DEFAULT_VENV_PYTHON = DEFAULT_VENV_ROOT / (
    "Scripts/python.exe" if os.name == "nt" else "bin/python"
)
REQUIREMENTS_FILE = Path(__file__).with_name("requirements.txt")


def frontmatter_version() -> Optional[str]:
    if importlib.util.find_spec("frontmatter") is None:
        return None
    try:
        return metadata.version("python-frontmatter")
    except metadata.PackageNotFoundError:
        return "unknown"


def pyyaml_version() -> Optional[str]:
    if importlib.util.find_spec("yaml") is None:
        return None
    try:
        return metadata.version("PyYAML")
    except metadata.PackageNotFoundError:
        return "unknown"


def module_import_error(module_name: str) -> Optional[str]:
    """Return an import failure description, or None when import succeeds."""
    try:
        importlib.import_module(module_name)
    except Exception as exc:  # Import-time dependency and binary errors matter here.
        return f"{type(exc).__name__}: {exc}"
    return None


def quoted(value: object) -> str:
    return shlex.quote(str(value))


def running_in_venv() -> bool:
    return sys.prefix != getattr(sys, "base_prefix", sys.prefix)


def install_command(python: Optional[Path] = None) -> str:
    selected = python or Path(sys.executable)
    return f"{quoted(selected)} -m pip install -r {quoted(REQUIREMENTS_FILE)}"


def venv_setup_guidance(base_python: Optional[str] = None) -> str:
    base = base_python or sys.executable
    return "\n".join(
        (
            f"  {quoted(base)} -m venv {quoted(DEFAULT_VENV_ROOT)}",
            f"  {install_command(DEFAULT_VENV_PYTHON)}",
            "Use this interpreter for every KB helper:",
            f"  {quoted(DEFAULT_VENV_PYTHON)} <skill-script> [args]",
        )
    )


def dependency_recovery_guidance() -> str:
    if running_in_venv():
        return "Install after user approval with the active virtual environment:\n  " + install_command()
    return (
        "Create the dedicated KB virtual environment after user approval:\n"
        + venv_setup_guidance()
    )


def main() -> int:
    failed = False
    in_venv = running_in_venv()
    current_python = sys.version_info[:3]
    python_text = ".".join(str(part) for part in current_python)

    print("KB prerequisite check")
    print(f"Interpreter: {sys.executable}")
    if current_python >= MIN_PYTHON:
        print(f"[ok] Python {python_text} (required: >= 3.10)")
    else:
        print(f"[missing] Python {python_text}; Python >= 3.10 is required")
        failed = True

    if in_venv:
        print(f"[ok] Isolated virtual environment: {sys.prefix}")
    else:
        print("[missing] KB helper is not running in a virtual environment")
        print("Create the dedicated KB virtual environment after user approval:")
        print(venv_setup_guidance())
        failed = True

    runtime_failed = False
    installed = frontmatter_version()
    if installed is None:
        print(f"[missing] python-frontmatter == {PINNED_FRONTMATTER} (import name: frontmatter)")
        runtime_failed = True
    elif installed == "unknown":
        print("[missing] frontmatter imports, but python-frontmatter version metadata is unavailable")
        runtime_failed = True
    elif installed == PINNED_FRONTMATTER:
        import_error = module_import_error("frontmatter")
        if import_error is not None:
            print(f"[missing] frontmatter cannot be imported: {import_error}")
            runtime_failed = True
        else:
            print(f"[ok] python-frontmatter {installed}")
    else:
        print(f"[missing] python-frontmatter {installed}; pinned version {PINNED_FRONTMATTER} is required")
        runtime_failed = True

    yaml_installed = pyyaml_version()
    if yaml_installed is None:
        print(f"[missing] PyYAML == {PINNED_PYYAML} (import name: yaml)")
        runtime_failed = True
    elif yaml_installed == "unknown":
        print("[missing] yaml imports, but PyYAML version metadata is unavailable")
        runtime_failed = True
    elif yaml_installed == PINNED_PYYAML:
        import_error = module_import_error("yaml")
        if import_error is not None:
            print(f"[missing] yaml cannot be imported: {import_error}")
            runtime_failed = True
        else:
            print(f"[ok] PyYAML {yaml_installed}")
    else:
        print(f"[missing] PyYAML {yaml_installed}; pinned version {PINNED_PYYAML} is required")
        runtime_failed = True

    if runtime_failed:
        if in_venv:
            print(dependency_recovery_guidance())
        failed = True

    for command, purpose in (
        ("rg", "fast text search"),
        ("jq", "convenient log.jsonl validation"),
        ("git", "edit-mode guard and supplementary history"),
    ):
        path = shutil.which(command)
        if path:
            print(f"[optional:ok] {command}: {path} ({purpose})")
        else:
            print(f"[optional:missing] {command} ({purpose})")

    if failed:
        print("Result: not ready")
        return 1
    print("Result: ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
