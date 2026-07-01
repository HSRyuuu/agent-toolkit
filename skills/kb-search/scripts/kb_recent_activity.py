#!/usr/bin/env python3
"""Summarize KB documents created or updated on a date."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

from kb_frontmatter import load_docs, metadata_row, normalize_date


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List KB Markdown files whose created or updated date matches a date."
    )
    parser.add_argument("root", nargs="?", default=".", help="KB root directory")
    parser.add_argument(
        "--date",
        default=dt.date.today().isoformat(),
        help="target date YYYY-MM-DD; defaults to today",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON object")
    return parser.parse_args()


def format_line(row: dict[str, Any]) -> str:
    title = row.get("title") or "-"
    return f"- {row['path']} — {title}"


def main() -> int:
    args = parse_args()
    root = Path(args.root).expanduser().resolve()
    rows = [metadata_row(doc) for doc in load_docs(root)]
    created = [row for row in rows if normalize_date(row.get("created")) == args.date]
    updated = [row for row in rows if normalize_date(row.get("updated")) == args.date]

    if args.json:
        print(
            json.dumps(
                {"date": args.date, "created": created, "updated": updated},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    print(f"Date: {args.date}")
    print(f"Created: {len(created)}")
    for row in created:
        print(format_line(row))
    print(f"Updated: {len(updated)}")
    for row in updated:
        print(format_line(row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
