#!/usr/bin/env python3
"""Tests for the agent_edit_mode guard.

Runs each scenario in a throwaway git repo and asserts the guard's exit code.
Run with: python3 test_check_agent_edit_mode.py
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("check_agent_edit_mode.py")


def sh(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def git(args: list[str], cwd: Path) -> None:
    result = sh(["git", *args], cwd)
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr}")


def doc(mode: str, body: str = "body") -> str:
    return f'---\ntitle: "Doc"\nagent_edit_mode: {mode}\n---\n\n# Doc\n{body}\n'


def new_repo() -> Path:
    root = Path(tempfile.mkdtemp(prefix="kb-guard-"))
    git(["init", "-q"], root)
    git(["config", "user.email", "t@t"], root)
    git(["config", "user.name", "t"], root)
    return root


def guard(root: Path) -> int:
    return sh(["python3", str(SCRIPT)], root).returncode


def check(name: str, got: int, want: int) -> bool:
    ok = got == want
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: exit={got} (want {want})")
    return ok


def main() -> int:
    results: list[bool] = []

    # 1. Archiving an editable doc (move + set read_only) must NOT be a violation.
    root = new_repo()
    (root / "old.md").write_text(doc("editable"), encoding="utf-8")
    git(["add", "."], root)
    git(["commit", "-qm", "init"], root)
    (root / "_archived").mkdir()
    git(["mv", "old.md", "_archived/old.md"], root)
    (root / "_archived/old.md").write_text(doc("read_only"), encoding="utf-8")
    results.append(check("archive editable->read_only", guard(root), 0))

    # 2. Creating a brand-new read_only doc must NOT be a violation.
    root = new_repo()
    (root / "seed.md").write_text(doc("editable"), encoding="utf-8")
    git(["add", "."], root)
    git(["commit", "-qm", "init"], root)
    (root / "new_protected.md").write_text(doc("read_only"), encoding="utf-8")
    results.append(check("create new read_only", guard(root), 0))

    # 3. Editing an already read_only doc MUST be a violation.
    root = new_repo()
    (root / "locked.md").write_text(doc("read_only"), encoding="utf-8")
    git(["add", "."], root)
    git(["commit", "-qm", "init"], root)
    (root / "locked.md").write_text(doc("read_only", body="tampered"), encoding="utf-8")
    results.append(check("edit existing read_only", guard(root), 1))

    # 4. Appending to an append_only doc must NOT be a violation.
    root = new_repo()
    (root / "acc.md").write_text(doc("append_only"), encoding="utf-8")
    git(["add", "."], root)
    git(["commit", "-qm", "init"], root)
    (root / "acc.md").write_text(doc("append_only") + "extra line\n", encoding="utf-8")
    results.append(check("append to append_only", guard(root), 0))

    # 5. Deleting a line from an append_only doc MUST be a violation.
    root = new_repo()
    (root / "acc.md").write_text(doc("append_only", body="line-a\nline-b"), encoding="utf-8")
    git(["add", "."], root)
    git(["commit", "-qm", "init"], root)
    (root / "acc.md").write_text(doc("append_only", body="line-a"), encoding="utf-8")
    results.append(check("delete from append_only", guard(root), 1))

    print(f"\n{sum(results)}/{len(results)} passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
