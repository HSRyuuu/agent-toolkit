#!/usr/bin/env python3
"""Extract a tolerant Claude JSONL session digest."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any


PATH_RE = re.compile(r"(?<![A-Za-z0-9_])(?:/Users/|/private/|/tmp/|~\/)[^\s'\"`<>)]*")
ERROR_RE = re.compile(r"\b(error|failed|failure|exception|traceback|denied|timeout)\b", re.IGNORECASE)


def compact(text: str, limit: int = 2000) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def parse_timestamp_value(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    raw = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def parse_date(row: dict[str, Any]) -> date | None:
    for key in ("timestamp", "created_at", "createdAt", "date"):
        parsed = parse_timestamp_value(row.get(key))
        if parsed:
            return parsed.date()
    message = row.get("message")
    if isinstance(message, dict):
        for key in ("timestamp", "created_at", "createdAt"):
            parsed = parse_timestamp_value(message.get(key))
            if parsed:
                return parsed.date()
    return None


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def text_from_content(content: Any) -> tuple[list[str], list[dict[str, Any]]]:
    texts: list[str] = []
    tool_calls: list[dict[str, Any]] = []
    if isinstance(content, str):
        return [content], tool_calls
    if not isinstance(content, list):
        return texts, tool_calls

    for item in content:
        if isinstance(item, str):
            texts.append(item)
            continue
        if not isinstance(item, dict):
            continue
        item_type = item.get("type")
        if item_type in {"text", "input_text", "output_text"} and isinstance(item.get("text"), str):
            texts.append(item["text"])
        elif item_type in {"tool_use", "tool_result"}:
            tool_calls.append(
                {
                    "name": item.get("name") or item_type,
                    "call_id": item.get("id") or item.get("tool_use_id") or "",
                    "arguments": compact(json.dumps(item.get("input") or item.get("content") or {}, ensure_ascii=False), 1000),
                }
            )
    return texts, tool_calls


def extract_role_and_content(row: dict[str, Any]) -> tuple[str | None, Any]:
    message = row.get("message")
    if isinstance(message, dict):
        role = message.get("role")
        content = message.get("content")
        if role in {"user", "assistant"}:
            return role, content

    row_type = row.get("type")
    if row_type in {"user", "assistant"}:
        return row_type, row.get("content") or row.get("text") or row.get("message")
    return None, None


def extract_digest(path: Path) -> dict[str, Any]:
    rows = load_jsonl(path)
    messages: list[dict[str, str]] = []
    tool_calls: list[dict[str, Any]] = []
    mentioned_paths: set[str] = set()
    errors: list[str] = []
    started_at: str | None = None
    cwd: str | None = None
    session_id: str | None = None

    for row in rows:
        if started_at is None:
            for key in ("timestamp", "created_at", "createdAt"):
                if isinstance(row.get(key), str):
                    started_at = row[key]
                    break
        if cwd is None and isinstance(row.get("cwd"), str):
            cwd = row["cwd"]
        if session_id is None:
            for key in ("session_id", "sessionId", "uuid", "id"):
                if isinstance(row.get(key), str):
                    session_id = row[key]
                    break

        role, content = extract_role_and_content(row)
        texts, nested_tools = text_from_content(content)
        tool_calls.extend(nested_tools)
        for tool in nested_tools:
            mentioned_paths.update(PATH_RE.findall(str(tool)))

        if role in {"user", "assistant"}:
            for text in texts:
                cleaned = compact(text)
                if cleaned:
                    messages.append({"role": role, "text": cleaned})
                    mentioned_paths.update(PATH_RE.findall(cleaned))
                    if ERROR_RE.search(cleaned):
                        errors.append(compact(cleaned, 300))

    return {
        "source": "claude",
        "session_id": session_id or path.stem,
        "file": str(path),
        "started_at": started_at,
        "cwd": cwd,
        "event_count": len(rows),
        "messages": messages,
        "tool_calls": tool_calls,
        "mentioned_paths": sorted(mentioned_paths),
        "errors": errors[:20],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract a Claude session digest.")
    parser.add_argument("session_file")
    args = parser.parse_args()

    digest = extract_digest(Path(args.session_file).expanduser())
    print(json.dumps(digest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
