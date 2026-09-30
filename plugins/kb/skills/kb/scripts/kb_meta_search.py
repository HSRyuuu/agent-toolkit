#!/usr/bin/env python3
"""Search Markdown KB documents by YAML frontmatter fields or ranked text."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from kb_frontmatter import (
    KbDoc,
    coerce_list,
    date_in_range,
    load_docs,
    matches_all_needles,
    metadata_row,
    normalize_date,
    scalar_contains,
    document_status,
    is_knowledge_doc,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search KB Markdown files by metadata fields or ranked text."
    )
    parser.add_argument("root", nargs="?", default=".", help="KB root directory")
    parser.add_argument("--created", action="append", default=[], help="created date YYYY-MM-DD")
    parser.add_argument("--updated", action="append", default=[], help="updated date YYYY-MM-DD")
    parser.add_argument("--created-since", help="created start date YYYY-MM-DD, inclusive")
    parser.add_argument("--created-until", help="created end date YYYY-MM-DD, inclusive")
    parser.add_argument("--updated-since", help="updated start date YYYY-MM-DD, inclusive")
    parser.add_argument("--updated-until", help="updated end date YYYY-MM-DD, inclusive")
    parser.add_argument("--tag", action="append", default=[], help="tag substring; repeatable")
    parser.add_argument("--alias", action="append", default=[], help="alias substring; repeatable")
    parser.add_argument("--title", help="title substring")
    parser.add_argument("--summary", help="summary substring")
    parser.add_argument("--source", help="source substring")
    parser.add_argument("--path", help="path substring")
    parser.add_argument("--agent-edit-mode", help="agent_edit_mode exact value")
    parser.add_argument("--query", help="free-text query across path and searchable metadata")
    parser.add_argument("--content", action="store_true", help="also search headings and body (AND terms)")
    parser.add_argument("--scope", choices=("active", "all"), default="active",
                        help="active: maintained/unspecified; all: also draft/historical")
    parser.add_argument("--include-guidance", action="store_true", help="include README/index/agent rules")
    parser.add_argument("--limit", type=int, help="maximum number of ranked results")
    parser.add_argument("--json", action="store_true", help="emit JSON array")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be at least 1")
    return args


def query_score(doc: KbDoc, query: str | None, content: bool = False) -> int | None:
    if not query:
        return 0
    meta = doc.metadata
    title = str(meta.get("title") or "").casefold()
    aliases = [value.casefold() for value in coerce_list(meta.get("aliases"))]
    tags = [value.casefold() for value in coerce_list(meta.get("tags"))]
    summary = str(meta.get("summary") or "").casefold()
    path = doc.relpath.casefold()
    folded = query.casefold().strip()
    tokens = folded.split()
    values = [title, *aliases, *tags, summary, path]
    body = doc.content.casefold() if content else ""
    headings = "\n".join(line for line in body.splitlines() if line.startswith("#"))
    if content:
        values += [body]
    if not tokens or not all(any(token in value for value in values) for token in tokens):
        return None

    score = 0
    if folded == title:
        score += 1000
    if folded in aliases:
        score += 800
    for token in tokens:
        if token in title:
            score += 100
        if any(token in alias for alias in aliases):
            score += 80
        if token in tags:
            score += 60
        if token in summary:
            score += 20
        if token in path:
            score += 10
        if token in headings:
            score += 8
        if token in body:
            score += 2
    return score


def match_details(doc: KbDoc, query: str | None, content: bool) -> dict[str, Any]:
    """Explain selected hits only; a snippet locates evidence, not a full answer."""
    tokens = (query or "").casefold().split()
    fields = {name: " ".join(coerce_list(doc.metadata.get(name))).casefold()
              for name in ("title", "aliases", "tags", "summary")}
    fields["path"] = doc.relpath.casefold()
    matched = [name for name, value in fields.items() if any(t in value for t in tokens)]
    details: dict[str, Any] = {"matched_fields": matched}
    if content:
        for lineno, line in enumerate(doc.content.splitlines(), 1):
            folded = line.casefold()
            positions = [folded.find(t) for t in tokens if t in folded]
            if not positions:
                continue
            matched.append("heading" if line.startswith("#") else "body")
            start = max(0, min(positions) - 40)
            from kb_lint import scan_secrets_in_text
            snippet = "[sensitive candidate omitted]" if scan_secrets_in_text(doc.relpath, line) else line[start:start + 180]
            details.update(line=doc.content_line_offset + lineno, snippet=snippet)
            break
    return details


def matches(doc: KbDoc, args: argparse.Namespace, invalid_date_paths: set[str]) -> bool:
    meta = doc.metadata
    created = normalize_date(meta.get("created"))
    updated = normalize_date(meta.get("updated"))

    if args.created and created not in args.created:
        return False
    if args.updated and updated not in args.updated:
        return False
    if args.created_since or args.created_until:
        created_in_range = date_in_range(meta.get("created"), args.created_since, args.created_until)
        if created_in_range is None:
            invalid_date_paths.add(doc.relpath)
            return False
        if not created_in_range:
            return False
    if args.updated_since or args.updated_until:
        updated_in_range = date_in_range(meta.get("updated"), args.updated_since, args.updated_until)
        if updated_in_range is None:
            invalid_date_paths.add(doc.relpath)
            return False
        if not updated_in_range:
            return False
    if args.tag and not matches_all_needles(coerce_list(meta.get("tags")), args.tag):
        return False
    if args.alias and not matches_all_needles(coerce_list(meta.get("aliases")), args.alias):
        return False
    if not scalar_contains(meta.get("title"), args.title):
        return False
    if not scalar_contains(meta.get("summary"), args.summary):
        return False
    if not scalar_contains(meta.get("source"), args.source):
        return False
    if args.path and args.path.casefold() not in doc.relpath.casefold():
        return False
    if args.agent_edit_mode and meta.get("agent_edit_mode") != args.agent_edit_mode:
        return False
    return True


def print_table(rows: list[dict[str, Any]]) -> None:
    if not rows:
        print("No matching documents.")
        return
    for row in rows:
        updated = row.get("updated") or "-"
        created = row.get("created") or "-"
        title = row.get("title") or "-"
        print(f"{row['path']}\tstatus={row['status']}\tcreated={created}\tupdated={updated}\t{title}")
        if row.get("matched_fields"):
            print(f"  matched={','.join(row['matched_fields'])} score={row['score']}")
        if row.get("line"):
            print(f"  L{row['line']}: {row['snippet']}")


def main() -> int:
    args = parse_args()
    root = Path(args.root).expanduser().resolve()
    invalid_date_paths: set[str] = set()
    errors: list[str] = []
    ranked = []
    for doc in load_docs(root, errors=errors):
        if not args.include_guidance and not is_knowledge_doc(doc):
            continue
        if args.scope == "active" and document_status(doc) in {"draft", "historical"}:
            continue
        if not matches(doc, args, invalid_date_paths):
            continue
        score = query_score(doc, args.query, args.content)
        if score is not None:
            ranked.append((score, doc))
    ranked.sort(key=lambda pair: (-pair[0], pair[1].relpath))
    if args.limit is not None:
        ranked = ranked[: args.limit]
    rows = [dict(metadata_row(doc), score=score, **match_details(doc, args.query, args.content))
            for score, doc in ranked]
    if invalid_date_paths:
        print(f"invalid date skipped: {len(invalid_date_paths)} files", file=sys.stderr)
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print_table(rows)
    for path in errors:
        print(f"Partial search: cannot read/parse {path}", file=sys.stderr)
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
