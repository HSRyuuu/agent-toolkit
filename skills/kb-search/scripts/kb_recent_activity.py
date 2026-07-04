#!/usr/bin/env python3
"""Summarize KB documents created or updated on a date."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

from kb_frontmatter import date_in_range, load_docs, metadata_row, normalize_date


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List KB Markdown files whose created or updated date matches a date."
    )
    parser.add_argument("root", nargs="?", default=".", help="KB root directory")
    parser.add_argument(
        "--date",
        default=None,
        help="target date YYYY-MM-DD; defaults to today",
    )
    parser.add_argument("--since", help="start date YYYY-MM-DD, inclusive")
    parser.add_argument("--until", help="end date YYYY-MM-DD, inclusive")
    parser.add_argument("--json", action="store_true", help="emit JSON object")
    args = parser.parse_args()
    if args.date and (args.since or args.until):
        parser.error("--date cannot be used with --since/--until")
    return args


def format_line(row: dict[str, Any]) -> str:
    title = row.get("title") or "-"
    return f"- {row['path']} — {title}"


def main() -> int:
    args = parse_args()
    root = Path(args.root).expanduser().resolve()
    rows = [metadata_row(doc) for doc in load_docs(root)]
    range_mode = bool(args.since or args.until)
    target_date = None if range_mode else (args.date or dt.date.today().isoformat())
    if range_mode:
        created = [row for row in rows if date_in_range(row.get("created"), args.since, args.until) is True]
        updated = [row for row in rows if date_in_range(row.get("updated"), args.since, args.until) is True]
    else:
        created = [row for row in rows if normalize_date(row.get("created")) == target_date]
        updated = [row for row in rows if normalize_date(row.get("updated")) == target_date]

    if args.json:
        payload = {"created": created, "updated": updated}
        if range_mode:
            payload.update({"since": args.since, "until": args.until})
        else:
            payload["date"] = target_date
        print(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if range_mode:
        print(f"Range: {args.since or '-'}..{args.until or '-'}")
    else:
        print(f"Date: {target_date}")
    print(f"Created: {len(created)}")
    for row in created:
        print(format_line(row))
    print(f"Updated: {len(updated)}")
    for row in updated:
        print(format_line(row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
