#!/usr/bin/env python3
"""Check KB Markdown edits against agent_edit_mode frontmatter.

This guard is intentionally conservative. It cannot tell whether a human or an
agent made a git diff; it reports policy conflicts so an agent can stop and ask.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


VALID_MODES = {"read_only", "append_only", "editable"}
GUARDED_MODES = {"read_only", "append_only"}


@dataclass
class Change:
    status: str
    old_path: str | None
    new_path: str | None
    untracked: bool = False


@dataclass
class Finding:
    path: str
    mode: str
    message: str


def run_git(args: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result


def inside_git_repo(cwd: Path) -> bool:
    return run_git(["rev-parse", "--is-inside-work-tree"], cwd, check=False).returncode == 0


def git_root(cwd: Path) -> Path:
    result = run_git(["rev-parse", "--show-toplevel"], cwd)
    return Path(result.stdout.strip())


def base_exists(root: Path, base: str) -> bool:
    return run_git(["rev-parse", "--verify", "--quiet", f"{base}^{{commit}}"], root, check=False).returncode == 0


def is_markdown(path: str | None) -> bool:
    if path is None:
        return False
    return path.lower().endswith((".md", ".markdown"))


def parse_name_status(output: str) -> list[Change]:
    changes: list[Change] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        code = status[0]
        if code in {"R", "C"} and len(parts) >= 3:
            changes.append(Change(status=status, old_path=parts[1], new_path=parts[2]))
        elif len(parts) >= 2:
            path = parts[1]
            if code == "D":
                changes.append(Change(status=status, old_path=path, new_path=None))
            else:
                changes.append(Change(status=status, old_path=path, new_path=path))
    return changes


def changed_files(root: Path, base: str, staged: bool) -> list[Change]:
    args = ["diff", "--name-status", "-M"]
    if staged:
        args.append("--cached")
    args.extend([base, "--"])
    changes = parse_name_status(run_git(args, root).stdout)

    if not staged:
        untracked = run_git(["ls-files", "--others", "--exclude-standard"], root).stdout
        for path in untracked.splitlines():
            changes.append(Change(status="??", old_path=None, new_path=path, untracked=True))

    return [
        change
        for change in changes
        if is_markdown(change.old_path) or is_markdown(change.new_path)
    ]


def read_base_file(root: Path, base: str, path: str | None) -> str | None:
    if path is None:
        return None
    result = run_git(["show", f"{base}:{path}"], root, check=False)
    if result.returncode != 0:
        return None
    return result.stdout


def read_new_file(root: Path, path: str | None, staged: bool) -> str | None:
    if path is None:
        return None
    if staged:
        result = run_git(["show", f":{path}"], root, check=False)
        return result.stdout if result.returncode == 0 else None
    file_path = root / path
    if not file_path.exists() or not file_path.is_file():
        return None
    return file_path.read_text(encoding="utf-8")


def parse_agent_edit_mode(text: str | None) -> str | None:
    if text is None:
        return None
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        stripped = line.strip()
        if stripped in {"---", "..."}:
            return None
        if stripped.startswith("agent_edit_mode:"):
            value = stripped.split(":", 1)[1].strip()
            if "#" in value:
                value = value.split("#", 1)[0].strip()
            return value.strip("\"'")
    return None


def old_content_is_preserved(old_text: str | None, new_text: str | None) -> bool:
    if old_text is None:
        return True
    if new_text is None:
        return False

    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)
    old_index = 0
    for new_line in new_lines:
        if old_index < len(old_lines) and new_line == old_lines[old_index]:
            old_index += 1
    return old_index == len(old_lines)


def first_missing_old_line(old_text: str | None, new_text: str | None) -> int | None:
    if old_text is None or new_text is None:
        return None
    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)
    old_index = 0
    for new_line in new_lines:
        if old_index < len(old_lines) and new_line == old_lines[old_index]:
            old_index += 1
    if old_index < len(old_lines):
        return old_index + 1
    return None


def evaluate(root: Path, base: str, staged: bool) -> tuple[list[Finding], list[Finding], list[Finding]]:
    violations: list[Finding] = []
    warnings: list[Finding] = []
    notes: list[Finding] = []

    for change in changed_files(root, base, staged):
        old_text = read_base_file(root, base, change.old_path)
        new_text = read_new_file(root, change.new_path, staged)
        old_mode = parse_agent_edit_mode(old_text)
        new_mode = parse_agent_edit_mode(new_text)
        display_path = change.new_path or change.old_path or "<unknown>"

        for mode in {old_mode, new_mode} - {None}:
            if mode not in VALID_MODES:
                warnings.append(
                    Finding(
                        path=display_path,
                        mode=str(mode),
                        message="unknown agent_edit_mode value; expected read_only, append_only, or editable",
                    )
                )

        # Protection is defined by the file's PRIOR (baseline) mode, not its new
        # mode. Creating a new protected file, or moving an editable file into a
        # protected mode (for example archiving a document as read_only), is a
        # legitimate transition, not a change to already-protected content.
        if old_mode not in GUARDED_MODES:
            if new_mode in GUARDED_MODES and old_mode != new_mode:
                notes.append(
                    Finding(
                        path=display_path,
                        mode=str(new_mode),
                        message="file entered a protected mode; future agent edits to it will be guarded",
                    )
                )
            continue

        if old_mode == "read_only":
            if old_text != new_text or change.old_path != change.new_path:
                violations.append(
                    Finding(
                        path=display_path,
                        mode="read_only",
                        message="file content changed; read_only allows no additions, deletions, metadata edits, renames, or rewrites",
                    )
                )
            continue

        if old_mode == "append_only" and not old_content_is_preserved(old_text, new_text):
            missing_line = first_missing_old_line(old_text, new_text)
            line_hint = f" first non-preserved original line: {missing_line}." if missing_line else ""
            violations.append(
                Finding(
                    path=display_path,
                    mode="append_only",
                    message=(
                        "original tracked content is not preserved as an exact ordered subsequence;"
                        " append_only permits additions anywhere but not deletion, text edits, reordering, or frontmatter value changes."
                        + line_hint
                    ),
                )
            )

    return violations, warnings, notes


def print_findings(title: str, findings: list[Finding]) -> None:
    if not findings:
        return
    print(title)
    for finding in findings:
        print(f"- [{finding.mode}] {finding.path}: {finding.message}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check Markdown git changes against agent_edit_mode frontmatter.",
    )
    parser.add_argument("--base", default="HEAD", help="git commit/ref to compare against (default: HEAD)")
    parser.add_argument("--staged", action="store_true", help="check staged/index changes instead of the worktree")
    args = parser.parse_args()

    cwd = Path.cwd()
    if not inside_git_repo(cwd):
        print(
            "agent_edit_mode guard: not inside a git repository.\n"
            "Cannot verify read_only or append_only preservation without a tracked baseline.",
            file=sys.stderr,
        )
        return 2

    root = git_root(cwd)
    os.chdir(root)
    if not base_exists(root, args.base):
        print(
            f"agent_edit_mode guard: base ref not found: {args.base}\n"
            "Cannot verify read_only or append_only preservation without an existing commit baseline.",
            file=sys.stderr,
        )
        return 2

    violations, warnings, notes = evaluate(root, args.base, args.staged)
    print_findings("Warnings:", warnings)
    print_findings("Notes:", notes)

    if violations:
        print_findings("Agent edit mode violations:", violations)
        print(
            "Stop and ask the user before proceeding:\n"
            "이 git 변경에는 read_only/append_only 문서의 보호 규칙을 벗어난 변경이 있습니다. "
            "사람이 의도해서 바꾼 내용이면 그대로 진행할 수 있지만, agent가 만든 변경이면 승인 없이는 반영하면 안 됩니다. "
            "이 변경이 맞나요?"
        )
        return 1

    if warnings:
        print("No guarded edit-mode violations found, but warnings should be reviewed.")
    else:
        print("No guarded edit-mode violations found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
