#!/usr/bin/env python3
"""Local frontmatter helpers for kb-lint."""

from __future__ import annotations

import datetime as dt
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    import frontmatter
except ModuleNotFoundError:  # pragma: no cover - exercised by CLI usage.
    frontmatter = None


IGNORED_DIRS = {"node_modules"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DEFAULT_VENV_PYTHON = Path.home() / ".venvs" / "agent-toolkit-kb" / (
    "Scripts/python.exe" if os.name == "nt" else "bin/python"
)
REQUIREMENTS_FILE = Path(__file__).with_name("requirements.txt")


@dataclass(frozen=True)
class KbDoc:
    path: Path
    relpath: str
    metadata: dict[str, Any]
    content: str


def require_frontmatter() -> None:
    if frontmatter is not None:
        return
    if sys.prefix != getattr(sys, "base_prefix", sys.prefix):
        recovery = f'  "{sys.executable}" -m pip install -r "{REQUIREMENTS_FILE}"'
    else:
        recovery = (
            f'  "{sys.executable}" -m venv "{DEFAULT_VENV_PYTHON.parent.parent}"\n'
            f'  "{DEFAULT_VENV_PYTHON}" -m pip install -r "{REQUIREMENTS_FILE}"\n'
            f'  "{DEFAULT_VENV_PYTHON}" <kb-lint-script> [args]'
        )
    print(
        "Missing dependency: python-frontmatter (import name: frontmatter). "
        "Use the dedicated KB virtual environment after user approval:\n"
        f"{recovery}",
        file=sys.stderr,
    )
    raise SystemExit(3)


def iter_markdown_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if path.suffix.lower() not in {".md", ".markdown"}:
            continue
        rel_parts = path.relative_to(root).parts
        if any(part.startswith(".") or part in IGNORED_DIRS for part in rel_parts):
            continue
        yield path


def load_docs(root: Path) -> list[KbDoc]:
    require_frontmatter()
    docs: list[KbDoc] = []
    for path in iter_markdown_files(root):
        post = frontmatter.load(path)  # type: ignore[union-attr]
        docs.append(
            KbDoc(
                path=path,
                relpath=path.relative_to(root).as_posix(),
                metadata=dict(post.metadata),
                content=post.content,
            )
        )
    return docs


def normalize_date(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, dt.datetime):
        return value.date().isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()
    text = str(value).strip().strip('"').strip("'")
    if not text:
        return None
    return text[:10]
