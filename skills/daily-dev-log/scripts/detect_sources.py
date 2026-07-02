#!/usr/bin/env python3
"""Detect whether Codex, Claude, and KB evidence exists for a target date."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any


CODEX_ROOT = Path.home() / ".codex" / "sessions"
CLAUDE_ROOT = Path.home() / ".claude"
KB_CONFIG_PATH = Path.home() / ".config" / "kb" / "path"


def first_non_empty_line(path: Path) -> str | None:
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped:
                return stripped
    except OSError:
        return None
    return None


def valid_configured_dir(path: Path) -> str | None:
    raw = first_non_empty_line(path)
    if not raw:
        return None
    candidate = Path(raw).expanduser()
    if candidate.is_absolute() and candidate.is_dir():
        return str(candidate.resolve())
    return None


def codex_status(target_date: date) -> dict[str, Any]:
    day_dir = CODEX_ROOT / f"{target_date:%Y}" / f"{target_date:%m}" / f"{target_date:%d}"
    files = sorted(day_dir.glob("*.jsonl")) if day_dir.is_dir() else []
    return {
        "available": bool(files),
        "root": str(CODEX_ROOT),
        "date_dir": str(day_dir),
        "file_count": len(files),
        "files": [str(path) for path in files[:20]],
    }


def claude_status(target_date: date) -> dict[str, Any]:
    roots = []
    projects = CLAUDE_ROOT / "projects"
    if projects.is_dir():
        roots.append(projects)
    if CLAUDE_ROOT.is_dir():
        roots.append(CLAUDE_ROOT)

    files: list[Path] = []
    seen: set[Path] = set()
    date_fragment = f"{target_date:%Y-%m-%d}"
    for root in roots:
        for path in root.rglob("*.jsonl"):
            if path in seen:
                continue
            seen.add(path)
            try:
                if date.fromtimestamp(path.stat().st_mtime) == target_date or date_fragment in path.name:
                    files.append(path)
            except OSError:
                continue

    return {
        "available": bool(files),
        "root": str(CLAUDE_ROOT),
        "file_count": len(files),
        "files": [str(path) for path in sorted(files)[:20]],
        "note": "Claude detection uses file mtime/name as a fast first check; collection scripts inspect JSONL timestamps.",
    }


def kb_status() -> dict[str, Any]:
    root = valid_configured_dir(KB_CONFIG_PATH)
    return {
        "available": root is not None,
        "config": str(KB_CONFIG_PATH),
        "root": root,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect daily-dev-log evidence sources.")
    parser.add_argument("--date", required=True, help="Target date in YYYY-MM-DD")
    args = parser.parse_args()

    target_date = date.fromisoformat(args.date)
    result = {
        "date": args.date,
        "sources": {
            "codex": codex_status(target_date),
            "claude": claude_status(target_date),
            "kb": kb_status(),
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
