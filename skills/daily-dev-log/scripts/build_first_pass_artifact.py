#!/usr/bin/env python3
"""Combine source availability, filtered sessions, and KB candidates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: str | None, default: Any) -> Any:
    if not path:
        return default
    with Path(path).expanduser().open("r", encoding="utf-8") as handle:
        return json.load(handle)


def candidates_from_filter(data: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = data.get("candidates")
    return candidates if isinstance(candidates, list) else []


def rejected_from_filter(data: dict[str, Any]) -> list[dict[str, Any]]:
    rejected = data.get("rejected")
    return rejected if isinstance(rejected, list) else []


def main() -> int:
    parser = argparse.ArgumentParser(description="Build daily-dev-log first-pass artifact.")
    parser.add_argument("--date", required=True)
    parser.add_argument("--sources", help="Output from detect_sources.py")
    parser.add_argument("--codex", help="Output from filter_codex_candidates.py")
    parser.add_argument("--claude", help="Output from filter_claude_candidates.py")
    parser.add_argument("--kb", help="JSON array or object containing kb_candidates")
    args = parser.parse_args()

    source_availability = load_json(args.sources, {})
    codex_filter = load_json(args.codex, {})
    claude_filter = load_json(args.claude, {})
    kb_data = load_json(args.kb, [])

    if isinstance(kb_data, dict):
        kb_candidates = kb_data.get("kb_candidates") or kb_data.get("candidates") or []
    elif isinstance(kb_data, list):
        kb_candidates = kb_data
    else:
        kb_candidates = []

    artifact = {
        "date": args.date,
        "stage": "first-pass-filter",
        "source_availability": source_availability,
        "codex_candidates": candidates_from_filter(codex_filter),
        "claude_candidates": candidates_from_filter(claude_filter),
        "kb_candidates": kb_candidates,
        "rejected_or_supporting": {
            "codex": rejected_from_filter(codex_filter),
            "claude": rejected_from_filter(claude_filter),
        },
        "notes": [],
    }
    print(json.dumps(artifact, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
