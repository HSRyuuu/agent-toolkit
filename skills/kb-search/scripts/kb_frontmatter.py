#!/usr/bin/env python3
"""Shared helpers for KB frontmatter search scripts."""

from __future__ import annotations

import datetime as dt
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    import frontmatter
except ModuleNotFoundError:  # pragma: no cover - exercised by CLI usage.
    frontmatter = None


IGNORED_DIRS = {".git", ".obsidian", ".venv", "node_modules"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class KbDoc:
    path: Path
    relpath: str
    metadata: dict[str, Any]
    content: str


def require_frontmatter() -> None:
    if frontmatter is not None:
        return
    print(
        "Missing dependency: python-frontmatter. Install with: "
        "python3 -m pip install python-frontmatter",
        file=sys.stderr,
    )
    raise SystemExit(3)


def iter_markdown_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if path.suffix.lower() not in {".md", ".markdown"}:
            continue
        if any(part in IGNORED_DIRS for part in path.relative_to(root).parts):
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


def date_in_range(value: Any, since: str | None, until: str | None) -> bool | None:
    normalized = normalize_date(value)
    if normalized is None or not DATE_RE.match(normalized):
        return None
    if since is not None and normalized < since:
        return False
    if until is not None and normalized > until:
        return False
    return True


def coerce_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def matches_all_needles(haystack: Iterable[str], needles: list[str]) -> bool:
    """AND semantics: every needle must substring-match at least one value."""
    values = [value.casefold() for value in haystack]
    return all(any(needle.casefold() in value for value in values) for needle in needles)


def scalar_contains(value: Any, needle: str | None) -> bool:
    if needle is None:
        return True
    if value is None:
        return False
    return needle.casefold() in str(value).casefold()


def metadata_row(doc: KbDoc) -> dict[str, Any]:
    return {
        "path": doc.relpath,
        "title": doc.metadata.get("title"),
        "summary": doc.metadata.get("summary"),
        "tags": coerce_list(doc.metadata.get("tags")),
        "aliases": coerce_list(doc.metadata.get("aliases")),
        "created": normalize_date(doc.metadata.get("created")),
        "updated": normalize_date(doc.metadata.get("updated")),
        "source": doc.metadata.get("source"),
        "agent_edit_mode": doc.metadata.get("agent_edit_mode"),
    }
