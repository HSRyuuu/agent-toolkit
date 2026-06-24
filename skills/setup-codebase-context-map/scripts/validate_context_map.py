#!/usr/bin/env python3
"""Validate generated codebase context map path references."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


PATH_HINT = re.compile(r"`([^`\n]+\.[A-Za-z0-9]{1,8}(?:[/A-Za-z0-9._()@:+-]*)?)`")
SKIP_PREFIXES = ("http://", "https://", "file://", "app://")


def looks_like_path(value: str) -> bool:
    if value.startswith(SKIP_PREFIXES):
        return False
    if value.startswith(".codesight/"):
        return False
    if " " in value or value.startswith("$"):
        return False
    return "/" in value or value.startswith(".") or "." in Path(value).name


def validate_file(root: Path, path: Path) -> list[str]:
    if not path.exists():
        return [f"Missing document: {path}"]
    text = path.read_text(encoding="utf-8", errors="ignore")
    errors: list[str] = []
    for match in PATH_HINT.finditer(text):
        candidate = match.group(1).strip()
        if not looks_like_path(candidate):
            continue
        if "*" in candidate or "<" in candidate or ">" in candidate:
            continue
        target = (root / candidate).resolve()
        try:
            target.relative_to(root.resolve())
        except ValueError:
            continue
        if not target.exists():
            errors.append(f"{path.relative_to(root)} references missing path: {candidate}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", nargs="?", default=".", help="Project root")
    parser.add_argument("--docs-dir", default="docs", help="Docs directory relative to project root")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    docs = root / args.docs_dir
    targets = [docs / "SOURCE_MAP.md", docs / "CODEBASE_CONTEXT.md"]
    errors: list[str] = []
    for target in targets:
        errors.extend(validate_file(root, target))

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Context map validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
