#!/usr/bin/env python3
"""Resolve the configured Markdown KB root.

Resolution order:
1. User-provided absolute path argument.
2. ~/.config/kb/kb-config.json `path`, when it is an existing directory.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


CONFIG_PATH = Path.home() / ".config" / "kb" / "kb-config.json"


def load_config(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    except OSError as exc:
        raise ValueError(f"Cannot read {path}: {exc}") from exc

    try:
        config = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(config, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return config


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

    config = load_config(CONFIG_PATH)
    configured = config.get("path") or config.get("kb_root") or config.get("root")
    if configured:
        if not isinstance(configured, str):
            raise ValueError(f"{CONFIG_PATH} path must be a string.")
        return valid_root(configured)
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve the configured KB root.")
    parser.add_argument("path", nargs="?", help="User-provided absolute KB path")
    args = parser.parse_args()

    try:
        root = resolve_root(args.path)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if root is None:
        print(
            "No valid KB root resolved. Provide an absolute path or configure "
            f"{CONFIG_PATH}.",
            file=sys.stderr,
        )
        return 1

    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
