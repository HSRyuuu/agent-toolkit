#!/usr/bin/env python3
"""Read-only validator for KB LLM wiki conventions."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DATE_SUFFIX_RE = re.compile(r"\d{4}-\d{2}-\d{2}(?:\.md)?$")
WIKI_LINK_RE = re.compile(r"!?\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
KNOWN_KINDS = {"source", "inbox", "archive", "daily-log", "canonical"}


@dataclass(frozen=True)
class Document:
    path: Path
    rel: str
    body: str
    frontmatter: dict[str, object]
    links: set[str]
    kind: str


def validate_root(root: Path | str) -> list[dict[str, str]]:
    root_path = Path(root)
    docs = [_read_document(root_path, path) for path in sorted(root_path.rglob("*.md"))]
    all_text = "\n".join(doc.body for doc in docs)
    issues: list[dict[str, str]] = []

    for doc in docs:
        issues.extend(_frontmatter_issues(doc))
        if doc.kind == "daily-log" and not _has_canonical_link(doc):
            issues.append(_issue("daily-log-without-canonical-link", doc))
        if doc.kind == "canonical" and not _has_related_section(doc):
            issues.append(_issue("canonical-missing-related-section", doc))
        if doc.kind == "unknown":
            issues.append(_issue("unknown-kind", doc))

    for doc in docs:
        if doc.kind == "source" and not _raw_is_linked(doc, all_text):
            issues.append(_issue("raw-source-unlinked", doc))

    return issues


def _read_document(root: Path, path: Path) -> Document:
    rel = path.relative_to(root).as_posix()
    body = path.read_text(encoding="utf-8")
    frontmatter = _parse_frontmatter(body)
    links = set(WIKI_LINK_RE.findall(body))
    return Document(
        path=path,
        rel=rel,
        body=body,
        frontmatter=frontmatter,
        links=links,
        kind=_classify(rel, frontmatter),
    )


def _parse_frontmatter(text: str) -> dict[str, object]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    result: dict[str, object] = {}
    current_key: str | None = None
    for raw_line in text[4:end].splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if line.startswith("  - ") and current_key:
            existing = result.setdefault(current_key, [])
            if isinstance(existing, list):
                existing.append(_strip_quotes(line[4:].strip()))
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        current_key = key
        if value == "":
            result[key] = []
        elif value.startswith("[") and value.endswith("]"):
            result[key] = [_strip_quotes(item.strip()) for item in value[1:-1].split(",") if item.strip()]
        else:
            result[key] = _strip_quotes(value)
    return result


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _classify(rel: str, frontmatter: dict[str, object]) -> str:
    explicit = frontmatter.get("kind")
    if isinstance(explicit, str) and explicit:
        return explicit if explicit in KNOWN_KINDS else "unknown"
    parts = rel.split("/")
    if parts[0] == "_raw":
        return "source"
    if parts[0] == "_inbox":
        return "inbox"
    if parts[0] == "_archive":
        return "archive"
    stem = Path(rel).stem
    if DATE_SUFFIX_RE.search(stem):
        return "daily-log"
    return "canonical"


def _frontmatter_issues(doc: Document) -> Iterable[dict[str, str]]:
    required = {
        "canonical": ("kind", "tags", "created"),
        "daily-log": ("kind", "tags", "created", "canonical"),
        "source": ("kind", "created"),
    }.get(doc.kind, ())
    for key in required:
        if key not in doc.frontmatter or _is_blank(doc.frontmatter[key]):
            yield _issue("missing-required-frontmatter", doc, f"missing {key}")


def _is_blank(value: object) -> bool:
    return value == "" or value == []


def _has_canonical_link(doc: Document) -> bool:
    canonical = doc.frontmatter.get("canonical")
    if isinstance(canonical, str) and canonical.startswith("[[") and canonical.endswith("]]"):
        return True
    return any("canonical" in link.lower() for link in doc.links) or bool(canonical)


def _has_related_section(doc: Document) -> bool:
    return any(
        heading in doc.body
        for heading in ("## Related Logs", "## 관련 로그", "## Related Documents", "## 관련 문서")
    )


def _raw_is_linked(doc: Document, all_text: str) -> bool:
    raw_stem = Path(doc.rel).with_suffix("").as_posix()
    return f"[[{raw_stem}" in all_text


def _issue(code: str, doc: Document, message: str | None = None) -> dict[str, str]:
    return {
        "code": code,
        "path": doc.rel,
        "message": message or code.replace("-", " "),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KB LLM wiki conventions.")
    parser.add_argument("--root", required=True, help="KB vault root to inspect.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()

    issues = validate_root(Path(args.root))
    if args.json:
        print(json.dumps({"issues": issues}, ensure_ascii=False, indent=2))
    else:
        if not issues:
            print("OK")
        for issue in issues:
            print(f"{issue['code']}: {issue['path']} - {issue['message']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
