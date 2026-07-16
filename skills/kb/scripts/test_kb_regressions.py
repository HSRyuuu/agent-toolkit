#!/usr/bin/env python3
"""Expose the existing script-style KB regression suite to pytest."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT_DIR = Path(__file__).parent
REGRESSION_SCRIPTS = [
    "test_kb_frontmatter_filter.py",
    "test_kb_lint.py",
    "test_kb_search.py",
    "test_resolve_kb_root.py",
    "test_check_kb_prerequisites.py",
    "test_check_agent_edit_mode.py",
]


@pytest.mark.parametrize("script_name", REGRESSION_SCRIPTS)
def test_regression_script(script_name: str) -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / script_name)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode == 0, (
        f"{script_name} failed with exit={result.returncode}\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )
