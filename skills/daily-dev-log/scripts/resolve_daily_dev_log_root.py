#!/usr/bin/env python3
"""Resolve the configured daily-dev-log journal root.

Resolution order:
1. User-provided absolute path argument.
2. First non-empty line of ~/.config/daily-dev-log/path, when it is an existing directory.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


CONFIG_PATH = Path.home() / ".config" / "daily-dev-log" / "path"


def first_non_empty_line(path: Path) -> str | None:
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped:
                return stripped
    except OSError:
        return None
    return None


def valid_root(raw_path: str) -> Path | None:
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        return None
    if not candidate.is_dir():
        return None
    return candidate.resolve()


def resolve_root(user_path: str | None) -> Path | None:
    if user_path:
        return valid_root(user_path)

    configured = first_non_empty_line(CONFIG_PATH)
    if configured:
        return valid_root(configured)
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve the daily-dev-log journal root.")
    parser.add_argument("path", nargs="?", help="User-provided absolute journal path")
    args = parser.parse_args()

    root = resolve_root(args.path)
    if root is None:
        print(
            "No valid daily-dev-log root resolved. Provide an absolute path or "
            f"configure {CONFIG_PATH}.",
            file=sys.stderr,
        )
        return 1

    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
