#!/usr/bin/env python3
"""Regression tests for Markdown file discovery in this skill."""

from __future__ import annotations

import tempfile
from pathlib import Path

from kb_frontmatter import iter_markdown_files


def main() -> int:
    root = Path(tempfile.mkdtemp(prefix="kb-search-filter-"))
    expected = {
        "note.md",
    }
    ignored = {
        ".hidden-note.md",
        ".claude/project-note.md",
        ".agents/rules/kb-rule.md",
        ".claude/skills/obsidian-markdown/SKILL.md",
        ".claude/skills/obsidian-markdown/references/syntax.md",
        ".codex/skills/json-canvas/SKILL.md",
        ".agents/skills/obsidian-bases/SKILL.md",
    }

    for relpath in expected | ignored:
        path = root / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {path.stem}\n", encoding="utf-8")

    found = {path.relative_to(root).as_posix() for path in iter_markdown_files(root)}
    ok = expected <= found and found.isdisjoint(ignored)
    print(f"[{'PASS' if ok else 'FAIL'}] hidden trees are excluded")
    if not ok:
        print(f"expected included: {sorted(expected)}")
        print(f"expected ignored: {sorted(ignored)}")
        print(f"found: {sorted(found)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
