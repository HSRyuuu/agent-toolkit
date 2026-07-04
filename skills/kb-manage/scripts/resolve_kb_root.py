#!/usr/bin/env python3
"""Resolve the configured Markdown KB root.

Resolution order:
1. Positional argument: an absolute path, or the name of a registered KB.
2. If the current working directory is inside a registered KB root, that root.
3. The configured `default` KB, when set.
4. The only registered KB, when exactly one is configured.

The config file `~/.config/kb/kb-config.json` is a UTF-8 JSON object. Two shapes
are supported:

Single KB (back-compatible):
    {"path": "/absolute/path/to/kb"}   # `kb_root` and `root` are aliases

Multiple KBs:
    {"kbs": {"personal": "/abs/personal", "work": "/abs/work"},
     "default": "personal"}

The cwd auto-select in step 2 only ever picks a root the user explicitly
registered; it never infers an arbitrary directory as a KB.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


CONFIG_PATH = Path.home() / ".config" / "kb" / "kb-config.json"
SINGLE_KEYS = ("path", "kb_root", "root")


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


def collect_roots(config: dict[str, Any]) -> tuple[dict[str, Path], str | None]:
    """Return registered {name: root} plus the configured default name."""
    roots: dict[str, Path] = {}

    kbs = config.get("kbs")
    if kbs is not None:
        if not isinstance(kbs, dict):
            raise ValueError("kb-config.json `kbs` must be an object of name -> path.")
        for name, raw in kbs.items():
            if not isinstance(raw, str):
                raise ValueError(f"kb-config.json kbs[{name!r}] must be a string path.")
            root = valid_root(raw)
            if root is not None:
                roots[str(name)] = root

    for key in SINGLE_KEYS:
        raw = config.get(key)
        if raw is None:
            continue
        if not isinstance(raw, str):
            raise ValueError(f"kb-config.json `{key}` must be a string path.")
        root = valid_root(raw)
        if root is not None:
            roots.setdefault("default", root)
        break

    default_name = config.get("default")
    if default_name is not None and not isinstance(default_name, str):
        raise ValueError("kb-config.json `default` must be a string KB name.")
    return roots, default_name


def resolve_root(user_arg: str | None) -> tuple[Path | None, str | None]:
    """Return (root, error_message). Exactly one is non-None on a decisive result;
    (None, None) means nothing is configured at all."""
    config = load_config(CONFIG_PATH)
    roots, default_name = collect_roots(config)

    if user_arg:
        direct = valid_root(user_arg)
        if direct is not None:
            return direct, None
        if user_arg in roots:
            return roots[user_arg], None
        if Path(user_arg).expanduser().is_absolute():
            return None, f"Path is not an existing directory: {user_arg}"
        known = ", ".join(sorted(roots)) or "none"
        return None, f"No KB named {user_arg!r}. Registered KBs: {known}."

    if not roots:
        return None, None

    cwd = Path.cwd().resolve()
    for root in roots.values():
        if cwd == root or root in cwd.parents:
            return root, None

    if default_name:
        if default_name in roots:
            return roots[default_name], None
        return None, f"Configured default {default_name!r} is not a valid registered KB."

    if len(roots) == 1:
        return next(iter(roots.values())), None

    names = ", ".join(sorted(roots))
    return None, f"Multiple KBs registered ({names}); pass a name or absolute path, or set `default`."


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve the configured KB root.")
    parser.add_argument("path", nargs="?", help="Absolute KB path or a registered KB name")
    args = parser.parse_args()

    try:
        root, error = resolve_root(args.path)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if root is None:
        if error is None:
            error = (
                "No valid KB root resolved. Provide an absolute path or configure "
                f"{CONFIG_PATH}."
            )
        print(error, file=sys.stderr)
        return 1

    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
