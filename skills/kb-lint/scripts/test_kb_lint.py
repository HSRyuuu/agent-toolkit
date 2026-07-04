#!/usr/bin/env python3
"""Tests for deterministic KB lint behavior.

Runs kb_lint.py against throwaway KB fixtures.
Run with: python3 test_kb_lint.py
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path
from urllib.parse import quote

SCRIPT = Path(__file__).with_name("kb_lint.py")


def write_doc(
    root: Path,
    relpath: str,
    *,
    title: str | None = None,
    body: str = "",
    extra_frontmatter: str = "",
) -> Path:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    title = title or Path(relpath).stem
    frontmatter = (
        "---\n"
        f'title: "{title}"\n'
        f'summary: "{title} summary"\n'
        "tags:\n"
        "  - test\n"
        "aliases: []\n"
        "created: 2026-07-04\n"
        "updated: 2026-07-04\n"
        "agent_edit_mode: editable\n"
    )
    if extra_frontmatter:
        frontmatter += extra_frontmatter
        if not frontmatter.endswith("\n"):
            frontmatter += "\n"
    path.write_text(f"{frontmatter}---\n\n# {title}\n{body}\n", encoding="utf-8")
    return path


def write_index(root: Path, links: list[str]) -> None:
    lines = ["# Index", ""]
    lines.extend(f"- [{Path(link).stem}]({link})" for link in links)
    (root / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_log(root: Path) -> None:
    (root / "log.jsonl").write_text('{"event":"test"}\n', encoding="utf-8")


def new_kb() -> Path:
    root = Path(tempfile.mkdtemp(prefix="kb-lint-"))
    write_log(root)
    return root


def run_lint(root: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(root)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=merged_env,
    )


def check(name: str, cond: bool, detail: str = "") -> bool:
    ok = cond
    suffix = f" — {detail}" if detail else ""
    print(f"[{'PASS' if ok else 'FAIL'}] {name}{suffix}")
    return ok


def case_missing_dependency_exits_3() -> bool:
    root = new_kb()
    write_index(root, [])
    stub = Path(tempfile.mkdtemp(prefix="kb-frontmatter-stub-"))
    (stub / "frontmatter.py").write_text('raise ModuleNotFoundError("frontmatter")\n', encoding="utf-8")
    result = run_lint(root, {"PYTHONPATH": str(stub)})
    return check(
        "missing dependency exits 3",
        result.returncode == 3 and "Missing dependency: python-frontmatter" in result.stderr,
        f"exit={result.returncode}",
    )


def case_clean_kb_exits_0() -> bool:
    root = new_kb()
    write_doc(root, "alpha.md", title="Alpha")
    write_index(root, ["alpha.md"])
    result = run_lint(root)
    return check("clean kb exits 0", result.returncode == 0, f"exit={result.returncode}")


def case_finding_exits_1() -> bool:
    root = new_kb()
    write_doc(root, "alpha.md", title="Alpha")
    write_index(root, [])
    result = run_lint(root)
    return check(
        "finding exits 1",
        result.returncode == 1 and "[index-missing-entry]" in result.stdout,
        f"exit={result.returncode}",
    )


def case_aws_key_exits_2() -> bool:
    root = new_kb()
    write_doc(root, "alpha.md", title="Alpha", body="AKIA1234567890ABCDEF")
    write_index(root, ["alpha.md"])
    result = run_lint(root)
    return check(
        "aws key exits 2",
        result.returncode == 2 and "[secret:aws-access-key-id]" in result.stdout,
        f"exit={result.returncode}",
    )


def case_percent_encoded_link_resolves() -> bool:
    root = new_kb()
    filename = "한글 파일.md"
    encoded = quote(filename)
    write_doc(root, filename, title="한글 파일")
    write_doc(root, "source.md", title="Source", body=f"[target](./{encoded})")
    write_index(root, [encoded, "source.md"])
    result = run_lint(root)
    return check(
        "percent-encoded link resolves",
        result.returncode == 0 and "broken-link" not in result.stdout,
        f"exit={result.returncode}",
    )


def case_percent_encoded_missing_link_reports() -> bool:
    root = new_kb()
    encoded = quote("없는 파일.md")
    write_doc(root, "source.md", title="Source", body=f"[target](./{encoded})")
    write_index(root, ["source.md"])
    result = run_lint(root)
    return check(
        "percent-encoded link to missing file reports broken-link",
        result.returncode == 1 and "[broken-link]" in result.stdout,
        f"exit={result.returncode}",
    )


def case_nfd_filename_matches_nfc_link() -> bool:
    root = new_kb()
    nfc_name = "한글.md"
    nfd_name = unicodedata.normalize("NFD", nfc_name)
    write_doc(root, nfd_name, title="한글")
    write_doc(root, "source.md", title="Source", body=f"[target](./{nfc_name})")
    write_index(root, [nfc_name, "source.md"])
    result = run_lint(root)
    return check(
        "nfd filename matches nfc link",
        result.returncode == 0 and "broken-link" not in result.stdout,
        f"exit={result.returncode}",
    )


def case_index_coverage_exact_match() -> bool:
    root = new_kb()
    write_doc(root, "foo/bar.md", title="Nested Bar")
    write_doc(root, "bar.md", title="Bar")
    write_index(root, ["foo/bar.md"])
    result = run_lint(root)
    return check(
        "index coverage exact match",
        result.returncode == 1
        and "[index-missing-entry] bar.md" in result.stdout
        and "[index-missing-entry] foo/bar.md" not in result.stdout,
        f"exit={result.returncode}",
    )


def case_archived_not_in_index_has_no_coverage_warn() -> bool:
    root = new_kb()
    write_doc(root, "alpha.md", title="Alpha")
    write_doc(
        root,
        "_archived/old.md",
        title="Old",
        extra_frontmatter="agent_edit_mode: read_only\n",
    )
    write_index(root, ["alpha.md"])
    result = run_lint(root)
    return check(
        "archived not in index has no coverage warn",
        result.returncode == 0 and "[index-missing-entry] _archived/old.md" not in result.stdout,
        f"exit={result.returncode}",
    )


def case_absolute_path_link_warns() -> bool:
    root = new_kb()
    write_doc(root, "alpha.md", title="Alpha", body="[abs](/etc/foo.md)")
    write_index(root, ["alpha.md"])
    result = run_lint(root)
    return check(
        "absolute path link warns",
        result.returncode == 1
        and "[absolute-path-link]" in result.stdout
        and "[broken-link]" not in result.stdout,
        f"exit={result.returncode}",
    )


def case_password_placeholders_not_detected() -> bool:
    root = new_kb()
    body = "\n".join(
        [
            "password: 확인 필요",
            "password: [REDACTED]",
            "password: ${DB_PASSWORD}",
            "password: <value>",
            "password: ****",
            "password: see vault",
        ]
    )
    write_doc(root, "alpha.md", title="Alpha", body=body)
    write_index(root, ["alpha.md"])
    result = run_lint(root)
    return check(
        "password placeholders not detected",
        result.returncode == 0 and "secret:password-assignment" not in result.stdout,
        f"exit={result.returncode}",
    )


def case_password_values_detected() -> bool:
    root = new_kb()
    body = "\n".join(
        [
            "password: Str0ngP@ssw0rd!",
            "비밀번호: abcd1234!",
            "passwd=hunter2secret",
        ]
    )
    write_doc(root, "alpha.md", title="Alpha", body=body)
    write_index(root, ["alpha.md"])
    result = run_lint(root)
    matches = result.stdout.count("[secret:password-assignment]")
    return check(
        "password values detected",
        result.returncode == 2 and matches == 3,
        f"exit={result.returncode}, matches={matches}",
    )


def main() -> int:
    cases = [
        case_missing_dependency_exits_3,
        case_clean_kb_exits_0,
        case_finding_exits_1,
        case_aws_key_exits_2,
        case_percent_encoded_link_resolves,
        case_percent_encoded_missing_link_reports,
        case_nfd_filename_matches_nfc_link,
        case_index_coverage_exact_match,
        case_archived_not_in_index_has_no_coverage_warn,
        case_absolute_path_link_warns,
        case_password_placeholders_not_detected,
        case_password_values_detected,
    ]
    results = [case() for case in cases]
    print(f"\n{sum(results)}/{len(results)} passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
