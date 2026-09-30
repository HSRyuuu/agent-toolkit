#!/usr/bin/env python3
"""Search scope, partial reads, and migration quality regressions (stdlib only)."""
import json
import subprocess
import tempfile
from pathlib import Path

from test_kb_lint import write_doc, write_index, write_log
from test_kb_search import run_script


def case_content_and_scope(root):
    write_doc(root, "booking.md", body="## Cancellation\nRefund uses region_id.")
    write_doc(root, "summary.md", title="Refund")
    write_doc(root, "_personal/private.md", title="Refund")
    write_doc(root, "README.md", title="Refund")
    write_doc(root, "proposal.md", title="Refund", extra_frontmatter="status: draft\n")
    write_doc(root, "_archived/old.md", title="Refund")
    result = run_script("kb_meta_search.py", root, "--query", "Refund", "--content", "--json")
    assert result.returncode == 0, result.stderr
    rows = json.loads(result.stdout)
    assert {r["path"] for r in rows} == {"summary.md", "booking.md"}, rows
    hit = next(r for r in rows if r["path"] == "booking.md")
    assert hit["status"] == "unspecified" and hit["line"] > 10 and "region_id" in hit["snippet"]
    assert "body" in hit["matched_fields"]
    result = run_script("kb_meta_search.py", root, "--query", "Refund", "--content", "--scope", "all", "--json")
    rows = json.loads(result.stdout)
    assert {r["status"] for r in rows} == {"unspecified", "draft", "historical"}
    assert all("_personal" not in r["path"] for r in rows)


def case_private_and_ignored_across_readers(root):
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / ".gitignore").write_text("excluded/\n")
    write_doc(root, "public.md")
    write_doc(root, "excluded/note.md")
    write_doc(root, "_personal/note.md")
    for script in ("kb_meta_search.py", "kb_recent_activity.py", "kb_build_index.py"):
        args = ("--since", "2026-01-01") if "recent" in script else ()
        result = run_script(script, root, *args)
        assert result.returncode == 0, result.stderr
        assert "public.md" in result.stdout and "excluded/" not in result.stdout and "_personal/" not in result.stdout


def case_parse_failure_is_partial_and_index_unchanged(root):
    write_doc(root, "good.md", body="region_id is here")
    (root / "bad.md").write_text('---\ntitle: [broken\n---\nDO_NOT_ECHO_SOURCE\n')
    (root / "index.md").write_text("# Existing catalog\n")
    result = run_script("kb_meta_search.py", root, "--query", "region_id", "--content", "--json")
    assert result.returncode == 2 and json.loads(result.stdout)[0]["path"] == "good.md"
    assert "bad.md" in result.stderr and "DO_NOT_ECHO_SOURCE" not in result.stderr
    result = run_script("kb_build_index.py", root, "--write")
    assert result.returncode != 0 and (root / "index.md").read_text() == "# Existing catalog\n"
    result = run_script("kb_lint.py", root)
    assert "[parse-error] bad.md" in result.stdout and "Traceback" not in result.stderr


def case_scoped_lint_and_reserved_status(root):
    write_doc(root, "good.md", extra_frontmatter="status: maintained\n")
    write_doc(root, "bad.md", extra_frontmatter="status: wrong\n")
    write_doc(root, "_inbox/note.md", extra_frontmatter="status: maintained\n")
    write_index(root, ["good.md", "bad.md"])
    assert run_script("kb_lint.py", root, "--files", "good.md", "--require-status").returncode == 0
    result = run_script("kb_lint.py", root, "--require-status")
    assert "[invalid-status] bad.md" in result.stdout and "[status-path-conflict] _inbox/note.md" in result.stdout
    assert run_script("kb_lint.py", root, "--files", "../outside.md").returncode == 2


def case_reserved_security_and_assets(root):
    write_doc(root, "good.md", body="[image](_images/missing.png)")
    write_doc(root, "_personal/note.md", body="AKIA" + "1234567890ABCDEF")
    write_index(root, ["good.md"])
    result = run_script("kb_lint.py", root)
    assert result.returncode == 2 and "[broken-link] good.md" in result.stdout
    assert "[secret:aws-access-key-id] _personal/note.md" in result.stdout
    assert "1234567890ABCDEF" not in result.stdout


def case_status_catalog_and_non_git_privacy(root):
    write_doc(root, "guide.md", extra_frontmatter="status: maintained\n")
    write_doc(root, "plan.md", extra_frontmatter="status: draft\n")
    write_doc(root, "decision.md", extra_frontmatter="status: historical\n")
    write_doc(root, "_personal/hidden.md")
    result = run_script("kb_build_index.py", root)
    assert result.returncode == 0
    assert "Status" in result.stdout and "## Drafts" in result.stdout and "## Historical" in result.stdout
    assert "_personal/" not in result.stdout


def case_index_read_boundaries(root):
    write_doc(root, "good.md")
    (root / "index.md").write_bytes(b"\xff")
    result = run_script("kb_lint.py", root, "--files", "good.md")
    assert "[parse-error] index.md" in result.stdout and "Traceback" not in result.stderr
    (root / "index.md").unlink()
    target = root / "untouched.txt"
    target.write_text("DO_NOT_READ_OR_REPLACE")
    (root / "index.md").symlink_to(target)
    result = run_script("kb_build_index.py", root, "--write")
    assert result.returncode == 2 and "DO_NOT_READ_OR_REPLACE" not in result.stdout
    assert target.read_text() == "DO_NOT_READ_OR_REPLACE"
    result = run_script("kb_lint.py", root)
    assert "[index-symlink]" in result.stdout


def case_template_index_is_current(root):
    templates = Path(__file__).parents[1] / "templates"
    for name in ("AGENTS.md", "index.md"):
        (root / name).write_bytes((templates / name).read_bytes())
    result = run_script("kb_build_index.py", root, "--check")
    assert result.returncode == 0, result.stderr


def main():
    cases = [v for k, v in globals().items() if k.startswith("case_") and callable(v)]
    failed = 0
    for case in cases:
        with tempfile.TemporaryDirectory(prefix="kb-quality-") as tmp:
            root = Path(tmp)
            write_log(root)
            try:
                case(root)
                print(f"PASS {case.__name__}")
            except (AssertionError, KeyError, ValueError) as exc:
                failed += 1
                print(f"FAIL {case.__name__}: {exc}")
    print(f"{len(cases) - failed}/{len(cases)} passed")
    return int(bool(failed))


if __name__ == "__main__":
    raise SystemExit(main())
