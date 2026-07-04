#!/usr/bin/env python3
"""Tests for deterministic KB search helper behavior.

Runs kb-search scripts against throwaway KB fixtures.
Run with: python3 test_kb_search.py
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


def write_doc(
    root: Path,
    relpath: str,
    *,
    title: str,
    created: str = "2026-07-04",
    updated: str = "2026-07-04",
    tags: list[str] | None = None,
) -> Path:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    tags = tags or []
    tag_lines = "\n".join(f"  - {tag}" for tag in tags) or "  []"
    frontmatter = (
        "---\n"
        f'title: "{title}"\n'
        f'summary: "{title} summary"\n'
        "tags:\n"
        f"{tag_lines}\n"
        "aliases: []\n"
        f'created: "{created}"\n'
        f'updated: "{updated}"\n'
        "agent_edit_mode: editable\n"
        "---\n"
    )
    path.write_text(f"{frontmatter}\n# {title}\n", encoding="utf-8")
    return path


def new_kb() -> Path:
    return Path(tempfile.mkdtemp(prefix="kb-search-"))


def run_script(script_name: str, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT_DIR / script_name), str(root), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def check(name: str, cond: bool, detail: str = "") -> bool:
    ok = cond
    suffix = f" — {detail}" if detail else ""
    print(f"[{'PASS' if ok else 'FAIL'}] {name}{suffix}")
    return ok


def case_single_tag_filter_matches() -> bool:
    root = new_kb()
    write_doc(root, "kafka.md", title="Kafka", tags=["kafka", "infra"])
    write_doc(root, "redis.md", title="Redis", tags=["redis", "infra"])
    result = run_script("kb_meta_search.py", root, "--tag", "kafka")
    return check(
        "single tag filter matches",
        result.returncode == 0 and "kafka.md" in result.stdout and "redis.md" not in result.stdout,
        f"exit={result.returncode}",
    )


def case_multi_tag_is_and() -> bool:
    root = new_kb()
    write_doc(root, "kafka.md", title="Kafka", tags=["kafka", "infra"])
    write_doc(root, "kafka-notes.md", title="Kafka Notes", tags=["kafka"])
    result = run_script("kb_meta_search.py", root, "--tag", "kafka", "--tag", "infra")
    return check(
        "multi tag is AND",
        result.returncode == 0 and "kafka.md" in result.stdout and "kafka-notes.md" not in result.stdout,
        f"exit={result.returncode}",
    )


def case_recent_activity_since_until_range() -> bool:
    root = new_kb()
    write_doc(root, "created-in.md", title="Created In", created="2026-06-28", updated="2026-07-10")
    write_doc(root, "updated-in.md", title="Updated In", created="2026-05-01", updated="2026-06-30")
    write_doc(root, "outside.md", title="Outside", created="2026-06-01", updated="2026-07-05")
    result = run_script("kb_recent_activity.py", root, "--since", "2026-06-28", "--until", "2026-06-30")
    return check(
        "recent activity since/until range",
        result.returncode == 0
        and "created-in.md" in result.stdout
        and "updated-in.md" in result.stdout
        and "outside.md" not in result.stdout,
        f"exit={result.returncode}",
    )


def case_recent_activity_open_ended_since() -> bool:
    root = new_kb()
    write_doc(root, "new.md", title="New", created="2026-07-02", updated="2026-07-02")
    write_doc(root, "old.md", title="Old", created="2026-06-01", updated="2026-06-01")
    result = run_script("kb_recent_activity.py", root, "--since", "2026-07-01")
    return check(
        "recent activity open-ended since",
        result.returncode == 0 and "new.md" in result.stdout and "old.md" not in result.stdout,
        f"exit={result.returncode}",
    )


def case_date_and_range_conflict_errors() -> bool:
    root = new_kb()
    write_doc(root, "alpha.md", title="Alpha")
    result = run_script("kb_recent_activity.py", root, "--date", "2026-07-04", "--since", "2026-07-01")
    return check(
        "date and range conflict errors",
        result.returncode == 2 and "--date cannot be used with --since/--until" in result.stderr,
        f"exit={result.returncode}",
    )


def case_meta_search_created_range_inclusive_boundary() -> bool:
    root = new_kb()
    write_doc(root, "since.md", title="Since", created="2026-06-01")
    write_doc(root, "until.md", title="Until", created="2026-06-30")
    write_doc(root, "before.md", title="Before", created="2026-05-31")
    write_doc(root, "after.md", title="After", created="2026-07-01")
    result = run_script("kb_meta_search.py", root, "--created-since", "2026-06-01", "--created-until", "2026-06-30")
    return check(
        "meta search created range inclusive boundary",
        result.returncode == 0
        and "since.md" in result.stdout
        and "until.md" in result.stdout
        and "before.md" not in result.stdout
        and "after.md" not in result.stdout,
        f"exit={result.returncode}",
    )


def case_meta_search_range_and_exact() -> bool:
    root = new_kb()
    write_doc(root, "exact.md", title="Exact", created="2026-06-15")
    write_doc(root, "other-in-range.md", title="Other In Range", created="2026-06-20")
    result = run_script(
        "kb_meta_search.py",
        root,
        "--created",
        "2026-06-15",
        "--created-since",
        "2026-06-01",
        "--created-until",
        "2026-06-30",
    )
    return check(
        "meta search range AND exact",
        result.returncode == 0
        and "exact.md" in result.stdout
        and "other-in-range.md" not in result.stdout,
        f"exit={result.returncode}",
    )


def case_meta_search_invalid_date_warns_and_skips() -> bool:
    root = new_kb()
    write_doc(root, "invalid.md", title="Invalid", created="언젠가")
    write_doc(root, "valid.md", title="Valid", created="2026-06-15")
    result = run_script("kb_meta_search.py", root, "--created-since", "2026-06-01")
    return check(
        "meta search invalid date warns and skips",
        result.returncode == 0
        and "valid.md" in result.stdout
        and "invalid.md" not in result.stdout
        and "invalid date skipped: 1 files" in result.stderr,
        f"exit={result.returncode}",
    )


def main() -> int:
    cases = [
        case_single_tag_filter_matches,
        case_multi_tag_is_and,
        case_recent_activity_since_until_range,
        case_recent_activity_open_ended_since,
        case_date_and_range_conflict_errors,
        case_meta_search_created_range_inclusive_boundary,
        case_meta_search_range_and_exact,
        case_meta_search_invalid_date_warns_and_skips,
    ]
    results = [case() for case in cases]
    print(f"\n{sum(results)}/{len(results)} passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
