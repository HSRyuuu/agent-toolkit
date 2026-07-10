#!/usr/bin/env python3
"""Regression tests for the isolated KB Python runtime guidance."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).with_name("check_kb_prerequisites.py")
SPEC = importlib.util.spec_from_file_location("check_kb_prerequisites", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def check(name: str, condition: bool) -> bool:
    print(f"[{'PASS' if condition else 'FAIL'}] {name}")
    return condition


def main() -> int:
    expected_root = Path.home() / ".venvs" / "agent-toolkit-kb"
    expected_python = expected_root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    requirements = SCRIPT.with_name("requirements.txt")
    requirement_lines = {
        line.strip()
        for line in requirements.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    skills_root = SCRIPT.parents[2]
    requirement_copies = [
        skills_root / skill / "scripts" / "requirements.txt"
        for skill in ("kb-manage", "kb-search", "kb-lint")
    ]
    base_python = getattr(sys, "_base_executable", sys.executable)
    system_run = subprocess.run(
        [base_python, str(SCRIPT)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    import_probe = getattr(MODULE, "module_import_error", None)
    if import_probe is None:
        broken_import_error = None
    else:
        with mock.patch("importlib.import_module", side_effect=ModuleNotFoundError("No module named 'yaml'")):
            broken_import_error = import_probe("frontmatter")
    results = [
        check("default KB venv root", MODULE.DEFAULT_VENV_ROOT == expected_root),
        check(
            "default KB Python lives inside the venv",
            MODULE.DEFAULT_VENV_PYTHON == expected_python,
        ),
        check(
            "setup guidance creates the dedicated venv",
            "-m venv" in MODULE.venv_setup_guidance(),
        ),
        check(
            "runtime requirements pin python-frontmatter and PyYAML",
            requirement_lines == {"python-frontmatter==1.3.0", "PyYAML==6.0.3"},
        ),
        check(
            "all KB skills bundle the same runtime lock",
            len({path.read_text(encoding="utf-8") for path in requirement_copies}) == 1,
        ),
        check(
            "setup guidance installs the locked requirements into the venv",
            str(MODULE.DEFAULT_VENV_PYTHON) in MODULE.venv_setup_guidance()
            and "-m pip install -r" in MODULE.venv_setup_guidance()
            and str(requirements) in MODULE.venv_setup_guidance(),
        ),
        check(
            "prerequisite checker exposes the pinned PyYAML version",
            MODULE.PINNED_PYYAML == "6.0.3",
        ),
        check(
            "system Python is rejected for KB helper execution",
            system_run.returncode == 1
            and "not running in a virtual environment" in system_run.stdout,
        ),
        check(
            "broken runtime imports are rejected",
            broken_import_error is not None and "yaml" in broken_import_error,
        ),
    ]
    print(f"\n{sum(results)}/{len(results)} passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
