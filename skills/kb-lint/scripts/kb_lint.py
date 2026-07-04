#!/usr/bin/env python3
"""Deterministic KB lint checks.

Covers only what a machine can decide reliably: frontmatter completeness, valid
agent_edit_mode, date format, title/H1 match, _archived/ rules, index.md link
targets, broken relative Markdown links, log.jsonl validity, and high-confidence
secret patterns. Judgement checks (duplicate topics, conflicting claims, split
candidates) stay with the kb-lint LLM workflow.

Exit codes:
    0  no findings
    1  findings present (any level)
    2  high-risk secret candidates present (implies findings)

Reuses the shared frontmatter loader from the kb-search scripts.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

SEARCH_SCRIPTS = Path(__file__).resolve().parents[2] / "kb-search" / "scripts"
sys.path.insert(0, str(SEARCH_SCRIPTS))

from kb_frontmatter import KbDoc, load_docs, normalize_date  # noqa: E402

REQUIRED_FIELDS = ("title", "summary", "tags", "aliases", "created", "updated", "agent_edit_mode")
# aliases may be an empty list by design; only its absence is a finding.
ALLOW_EMPTY_FIELDS = {"aliases"}
# Root entrypoints and folder notes do not carry KB document frontmatter.
ENTRYPOINT_NAMES = {"index.md", "readme.md", "agents.md", "claude.md"}
VALID_MODES = {"read_only", "append_only", "editable"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")

# High-confidence secret shapes. Value-form matches, not context keywords.
SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("aws-access-key-id", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private-key-block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("github-token", re.compile(r"gh[pousr]_[A-Za-z0-9]{36}")),
    ("slack-token", re.compile(r"xox[bpoa]-[A-Za-z0-9-]{10,}")),
    ("jwt", re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{6,}")),
    ("bearer-token", re.compile(r"[Bb]earer\s+[A-Za-z0-9._~+/=-]{20,}")),
    ("password-assignment", re.compile(r"(?i)password\s*[:=]\s*['\"]?\S{4,}")),
]


@dataclass
class Finding:
    level: str  # "high" | "error" | "warn"
    category: str
    path: str
    line: int | None
    message: str


def check_frontmatter(doc: KbDoc) -> list[Finding]:
    out: list[Finding] = []
    meta = doc.metadata
    if not meta:
        out.append(Finding("error", "missing-frontmatter", doc.relpath, None, "no YAML frontmatter"))
        return out

    for field in REQUIRED_FIELDS:
        if field not in meta:
            out.append(Finding("error", "missing-field", doc.relpath, None, f"missing `{field}`"))
        elif meta.get(field) in (None, "", []) and field not in ALLOW_EMPTY_FIELDS:
            out.append(Finding("error", "empty-field", doc.relpath, None, f"empty `{field}`"))

    mode = meta.get("agent_edit_mode")
    if mode is not None and mode not in VALID_MODES:
        out.append(Finding("error", "invalid-edit-mode", doc.relpath, None, f"invalid agent_edit_mode: {mode}"))

    for field in ("created", "updated"):
        raw = meta.get(field)
        if raw is None:
            continue
        norm = normalize_date(raw)
        if norm is None or not DATE_RE.match(norm):
            out.append(Finding("warn", "bad-date", doc.relpath, None, f"`{field}` is not YYYY-MM-DD"))

    title = meta.get("title")
    if title:
        h1 = next((ln[2:].strip() for ln in doc.content.splitlines() if ln.startswith("# ")), None)
        if h1 is not None and h1 != str(title).strip():
            out.append(Finding("warn", "title-h1-mismatch", doc.relpath, None, f"title vs H1 differ ({title!r} / {h1!r})"))
    return out


def check_archived(doc: KbDoc) -> list[Finding]:
    parts = doc.relpath.split("/")
    if parts[0] != "_archived":
        return []
    out: list[Finding] = []
    if len(parts) != 2:
        out.append(Finding("error", "archived-depth", doc.relpath, None, "_archived/ files must be exactly one level deep"))
    if doc.metadata.get("agent_edit_mode") != "read_only":
        out.append(Finding("error", "archived-not-read-only", doc.relpath, None, "_archived/ documents must be agent_edit_mode: read_only"))
    return out


def check_links(root: Path, doc: KbDoc) -> list[Finding]:
    out: list[Finding] = []
    base = (root / doc.relpath).parent
    for lineno, line in enumerate(doc.content.splitlines(), 1):
        for target in LINK_RE.findall(line):
            target = target.strip()
            if not target or target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            path_part = target.split("#", 1)[0]
            if not path_part or not path_part.endswith((".md", ".markdown")):
                continue
            resolved = (base / path_part).resolve()
            if not resolved.exists():
                out.append(Finding("error", "broken-link", doc.relpath, lineno, f"link target missing: {path_part}"))
    return out


def scan_secrets_in_text(relpath: str, text: str) -> list[Finding]:
    out: list[Finding] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for label, pattern in SECRET_PATTERNS:
            if pattern.search(line):
                out.append(Finding("high", f"secret:{label}", relpath, lineno, "high-confidence secret candidate (value not shown)"))
    return out


def check_log(root: Path) -> list[Finding]:
    log_path = root / "log.jsonl"
    if not log_path.exists():
        return []
    out: list[Finding] = []
    for lineno, line in enumerate(log_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            json.loads(line)
        except json.JSONDecodeError:
            out.append(Finding("error", "log-malformed", "log.jsonl", lineno, "line is not valid JSON"))
    out += scan_secrets_in_text("log.jsonl", log_path.read_text(encoding="utf-8"))
    return out


def check_index(root: Path) -> list[Finding]:
    index_path = root / "index.md"
    if not index_path.exists():
        return []
    out: list[Finding] = []
    text = index_path.read_text(encoding="utf-8")
    for lineno, line in enumerate(text.splitlines(), 1):
        for target in LINK_RE.findall(line):
            path_part = target.strip().split("#", 1)[0]
            if not path_part or path_part.startswith(("http://", "https://")):
                continue
            if not path_part.endswith((".md", ".markdown", ".jsonl")):
                continue
            if not (root / path_part).resolve().exists():
                out.append(Finding("error", "index-broken-link", "index.md", lineno, f"missing target: {path_part}"))
    return out


def collect(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    docs = load_docs(root)
    listed = {doc.relpath for doc in docs}

    for doc in docs:
        is_entrypoint = doc.path.name.lower() in ENTRYPOINT_NAMES
        if not is_entrypoint:
            findings += check_frontmatter(doc)
            findings += check_archived(doc)
        # index.md links are validated by check_index; avoid double-reporting.
        if doc.relpath != "index.md":
            findings += check_links(root, doc)
        findings += scan_secrets_in_text(doc.relpath, doc.content)

    findings += check_index(root)
    findings += check_log(root)

    # index coverage: catalog docs not linked from index.md
    index_path = root / "index.md"
    if index_path.exists():
        index_text = index_path.read_text(encoding="utf-8")
        for doc in docs:
            top = doc.relpath.split("/", 1)[0]
            if top in {"_inbox"} or doc.path.name.lower() in {"index.md", "readme.md", "agents.md", "claude.md"}:
                continue
            if doc.relpath not in index_text:
                findings.append(Finding("warn", "index-missing-entry", doc.relpath, None, "not listed in index.md"))
    return findings


def report(findings: list[Finding], root: Path) -> None:
    order = {"high": 0, "error": 1, "warn": 2}
    findings = sorted(findings, key=lambda f: (order.get(f.level, 3), f.path, f.line or 0))
    print("===== KB Lint (deterministic) =====")
    print(f"Root: {root}")
    print(f"Findings: {len(findings)}\n")
    if not findings:
        print("Clean.")
        return
    for f in findings:
        loc = f"{f.path}:{f.line}" if f.line else f.path
        print(f"[{f.level}] [{f.category}] {loc} — {f.message}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic KB lint checks.")
    parser.add_argument("root", nargs="?", default=".", help="KB root directory")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    findings = collect(root)
    report(findings, root)

    if any(f.level == "high" for f in findings):
        return 2
    if findings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
