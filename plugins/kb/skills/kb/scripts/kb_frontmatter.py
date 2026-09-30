#!/usr/bin/env python3
"""Shared frontmatter helpers for the unified kb skill."""

from __future__ import annotations

import datetime as dt
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    import frontmatter
    from yaml import YAMLError
except ModuleNotFoundError:  # pragma: no cover - exercised by CLI usage.
    frontmatter = None
    YAMLError = ValueError


IGNORED_DIRS = {"node_modules"}
GUIDANCE_NAMES = {"index.md", "readme.md", "agents.md", "claude.md"}
VALID_STATUSES = {"maintained", "draft", "historical"}
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
    content_line_offset: int


def require_frontmatter() -> None:
    if frontmatter is not None:
        return
    if sys.prefix != getattr(sys, "base_prefix", sys.prefix):
        recovery = f'  "{sys.executable}" -m pip install -r "{REQUIREMENTS_FILE}"'
    else:
        recovery = (
            f'  "{sys.executable}" -m venv "{DEFAULT_VENV_PYTHON.parent.parent}"\n'
            f'  "{DEFAULT_VENV_PYTHON}" -m pip install -r "{REQUIREMENTS_FILE}"\n'
            f'  "{DEFAULT_VENV_PYTHON}" <kb-script> [args]'
        )
    print(
        "Missing dependency: python-frontmatter (import name: frontmatter). "
        "Use the dedicated KB virtual environment after user approval:\n"
        f"{recovery}",
        file=sys.stderr,
    )
    raise SystemExit(3)


def iter_files(root: Path, *, shared: bool = False) -> Iterable[Path]:
    """Prune hidden/dependency trees before walking; never follow symlinks."""
    if not root.is_dir():
        print("KB root is not a directory", file=sys.stderr)
        raise SystemExit(2)
    def walk_error(error: OSError) -> None:
        print(f"Cannot scan KB directory: {error.filename}", file=sys.stderr)
        raise SystemExit(2)

    for directory, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
        dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in IGNORED_DIRS
                         and not (shared and d == "_personal")
                         and not (Path(directory) / d).is_symlink())
        for name in sorted(files):
            path = Path(directory) / name
            if not name.startswith(".") and not path.is_symlink():
                yield path


def iter_markdown_files(root: Path, *, shared: bool = False) -> Iterable[Path]:
    return (p for p in iter_files(root, shared=shared) if p.suffix.lower() in {".md", ".markdown"})


def git_ignored(root: Path, paths: Iterable[Path]) -> set[str]:
    if not any((parent / ".git").exists() for parent in (root, *root.parents)):
        return set()  # Non-git KBs do not require the optional git executable.
    names = [p.relative_to(root).as_posix() for p in paths]
    if not names:
        return set()
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "check-ignore", "-z", "--stdin"],
            input="\0".join(names) + "\0", text=True, capture_output=True, timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        print("Cannot determine git ignore rules; refusing shared discovery", file=sys.stderr)
        raise SystemExit(2)
    if result.returncode in (0, 1):
        return set(result.stdout.split("\0")) - {""}
    print("Cannot determine git ignore rules; refusing shared discovery", file=sys.stderr)
    raise SystemExit(2)


def load_docs(root: Path, *, shared: bool = True, errors: list[str] | None = None,
              files: set[str] | None = None) -> list[KbDoc]:
    require_frontmatter()
    docs: list[KbDoc] = []
    paths = list(iter_markdown_files(root, shared=shared))
    ignored = git_ignored(root, paths) if shared else set()
    for path in paths:
        relpath = path.relative_to(root).as_posix()
        if relpath in ignored or (files is not None and relpath not in files):
            continue
        try:
            raw = path.read_text(encoding="utf-8")
            post = frontmatter.loads(raw)  # type: ignore[union-attr]
        except (OSError, UnicodeError, YAMLError, ValueError, TypeError) as exc:
            # Parser exceptions may contain source lines, including secret values.
            if errors is None:
                print(f"Cannot read/parse Markdown: {relpath} ({type(exc).__name__})", file=sys.stderr)
                raise SystemExit(2)
            errors.append(relpath)
            continue
        content_start = raw.rfind(post.content)
        docs.append(
            KbDoc(
                path=path,
                relpath=path.relative_to(root).as_posix(),
                metadata=dict(post.metadata),
                content=post.content,
                content_line_offset=(raw[:content_start].count("\n") if content_start >= 0 else 0),
            )
        )
    return docs


def document_status(doc: KbDoc) -> str:
    top = doc.relpath.split("/", 1)[0]
    if top == "_inbox":
        return "draft"
    if top == "_archived":
        return "historical"
    status = doc.metadata.get("status")
    return status if isinstance(status, str) and status in VALID_STATUSES else "unspecified"


def is_knowledge_doc(doc: KbDoc) -> bool:
    return (doc.path.name.lower() not in GUIDANCE_NAMES
            and not any(p in {"_personal", "_src", "_images"} for p in Path(doc.relpath).parts))


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
        "status": document_status(doc),
    }
