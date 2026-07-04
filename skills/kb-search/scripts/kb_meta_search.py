#!/usr/bin/env python3
"""Search Markdown KB documents by YAML frontmatter fields."""

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
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search KB Markdown files by python-frontmatter metadata."
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
    parser.add_argument("--json", action="store_true", help="emit JSON array")
    return parser.parse_args()


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
        print(f"{row['path']}\tcreated={created}\tupdated={updated}\t{title}")


def main() -> int:
    args = parse_args()
    root = Path(args.root).expanduser().resolve()
    invalid_date_paths: set[str] = set()
    docs = [doc for doc in load_docs(root) if matches(doc, args, invalid_date_paths)]
    rows = [metadata_row(doc) for doc in docs]
    if invalid_date_paths:
        print(f"invalid date skipped: {len(invalid_date_paths)} files", file=sys.stderr)
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print_table(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
