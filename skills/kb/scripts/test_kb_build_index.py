#!/usr/bin/env python3
"""Tests for index catalog generation.

Runs kb_build_index.py against throwaway KB fixtures.
Run with: python3 test_kb_build_index.py
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("kb_build_index.py")


def write_doc(root: Path, relpath: str) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    title = Path(relpath).stem
    path.write_text(
        "---\n"
        f'title: "{title}"\n'
        f'summary: "{title} summary"\n'
        "tags:\n"
        "  - test\n"
        "aliases: []\n"
        "created: 2026-07-04\n"
        "updated: 2026-07-04\n"
        "agent_edit_mode: editable\n"
        "---\n\n"
        f"# {title}\n",
        encoding="utf-8",
    )


def build(root: Path) -> str:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), str(root)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"exit={proc.returncode} stderr={proc.stderr}"
    return proc.stdout


def git_init(root: Path) -> None:
    for args in (
        ["init", "-q"],
        ["config", "user.email", "t@example.com"],
        ["config", "user.name", "t"],
    ):
        subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def case_git_ignored_doc_is_excluded() -> bool:
    """A git-ignored document must not appear in the catalog."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        git_init(root)
        (root / ".gitignore").write_text("_personal/\n", encoding="utf-8")
        write_doc(root, "dev/public-doc.md")
        write_doc(root, "_personal/private-doc.md")
        # Non-ASCII name: git quotes these as octal escapes unless quotePath is off,
        # which silently broke the relpath match.
        write_doc(root, "_personal/비공개_문서.md")

        out = build(root)
        ok = (
            "public-doc.md" in out
            and "private-doc.md" not in out
            and "비공개_문서.md" not in out
        )
        print(f"git_ignored_doc_is_excluded: {'PASS' if ok else 'FAIL'}")
        if not ok:
            print(out)
        return ok


def case_non_git_kb_excludes_private() -> bool:
    """Private scope exclusion must not depend on git being installed."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_doc(root, "dev/public-doc.md")
        write_doc(root, "_personal/private-doc.md")

        out = build(root)
        ok = "public-doc.md" in out and "private-doc.md" not in out
        print(f"non_git_kb_excludes_private: {'PASS' if ok else 'FAIL'}")
        if not ok:
            print(out)
        return ok


def case_readme_is_never_catalogued() -> bool:
    """README/index/AGENTS are folder notes, not catalog entries."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_doc(root, "dev/real-doc.md")
        write_doc(root, "dev/README.md")

        out = build(root)
        ok = "real-doc.md" in out and "dev/README.md" not in out
        print(f"readme_is_never_catalogued: {'PASS' if ok else 'FAIL'}")
        if not ok:
            print(out)
        return ok


def main() -> int:
    cases = [
        case_git_ignored_doc_is_excluded,
        case_non_git_kb_excludes_private,
        case_readme_is_never_catalogued,
    ]
    results = [case() for case in cases]
    print(f"\n{sum(results)}/{len(results)} passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
