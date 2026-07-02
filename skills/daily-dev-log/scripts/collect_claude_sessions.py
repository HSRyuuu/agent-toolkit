#!/usr/bin/env python3
"""Collect lightweight Claude session candidates for a date."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

from extract_claude_session import extract_digest, parse_date


DEFAULT_ROOT = Path.home() / ".claude"


def iter_jsonl(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    projects = root / "projects"
    paths = sorted(projects.rglob("*.jsonl")) if projects.is_dir() else []
    if paths:
        return paths
    return sorted(root.rglob("*.jsonl"))


def file_matches_date(path: Path, target_date: date) -> bool:
    try:
        with path.open("r", encoding="utf-8") as handle:
            for _, line in zip(range(200), handle):
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                parsed = parse_date(row)
                if parsed == target_date:
                    return True
                if parsed and parsed > target_date:
                    return False
    except OSError:
        return False
    try:
        return date.fromtimestamp(path.stat().st_mtime) == target_date
    except OSError:
        return False


def candidate_from_digest(digest: dict[str, Any]) -> dict[str, Any]:
    messages = digest.get("messages") if isinstance(digest.get("messages"), list) else []
    user_messages = [m for m in messages if isinstance(m, dict) and m.get("role") == "user"]
    assistant_messages = [m for m in messages if isinstance(m, dict) and m.get("role") == "assistant"]
    tool_calls = digest.get("tool_calls") if isinstance(digest.get("tool_calls"), list) else []
    first_user = [str(m.get("text", ""))[:220] for m in user_messages[:5]]

    return {
        "source": "claude",
        "session_id": digest.get("session_id"),
        "file": digest.get("file"),
        "started_at": digest.get("started_at"),
        "cwd": digest.get("cwd"),
        "event_count": digest.get("event_count"),
        "user_message_count": len(user_messages),
        "assistant_message_count": len(assistant_messages),
        "tool_call_count": len(tool_calls),
        "tool_names": sorted({call.get("name") for call in tool_calls if isinstance(call, dict) and call.get("name")}),
        "clean_user_requests": first_user,
        "confidence": "medium" if first_user else "low",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect Claude session candidates for a date.")
    parser.add_argument("--date", required=True, help="Target date in YYYY-MM-DD")
    parser.add_argument("--sessions-root", default=str(DEFAULT_ROOT))
    args = parser.parse_args()

    target_date = date.fromisoformat(args.date)
    root = Path(args.sessions_root).expanduser()
    candidates = []
    for path in iter_jsonl(root):
        if file_matches_date(path, target_date):
            candidates.append(candidate_from_digest(extract_digest(path)))

    print(json.dumps({"date": args.date, "source": "claude", "sessions": candidates}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
