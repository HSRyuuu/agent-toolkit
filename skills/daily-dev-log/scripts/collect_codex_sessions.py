#!/usr/bin/env python3
"""Collect lightweight Codex session candidates for a date."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any


DEFAULT_SESSIONS_ROOT = Path.home() / ".codex" / "sessions"
NOISE_MARKERS = (
    "# AGENTS.md instructions",
    "<INSTRUCTIONS>",
    "<environment_context>",
    "<permissions instructions>",
    ">>> TRANSCRIPT",
)


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


def text_blocks(content: Any) -> list[str]:
    if isinstance(content, str):
        return [content]
    if not isinstance(content, list):
        return []
    texts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        if item.get("type") in {"input_text", "output_text", "text"}:
            text = item.get("text")
            if isinstance(text, str):
                texts.append(text)
    return texts


def compact(text: str, limit: int = 220) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def clean_user_text(text: str) -> str:
    leading = text.lstrip()
    if leading.startswith(
        (
            "# AGENTS.md instructions",
            "<environment_context>",
            "<permissions instructions>",
            "<developer_context>",
        )
    ):
        return ""

    earliest = len(text)
    for marker in NOISE_MARKERS:
        index = text.find(marker)
        if index > 0:
            earliest = min(earliest, index)
    if earliest != len(text):
        text = text[:earliest]

    lines = []
    skip_prefixes = ("# Files mentioned by the user:",)
    for line in text.splitlines():
        stripped = line.strip()
        if any(stripped.startswith(prefix) for prefix in skip_prefixes):
            continue
        lines.append(line)
    return compact("\n".join(lines))


def first_session_meta(rows: list[dict[str, Any]]) -> dict[str, Any]:
    for row in rows:
        if row.get("type") == "session_meta":
            payload = row.get("payload")
            if isinstance(payload, dict):
                return payload
    return {}


def summarize_session(path: Path) -> dict[str, Any]:
    rows = load_jsonl(path)
    meta = first_session_meta(rows)
    user_texts: list[str] = []
    assistant_texts: list[str] = []
    tool_names: list[str] = []

    for row in rows:
        if row.get("type") != "response_item":
            continue
        payload = row.get("payload")
        if not isinstance(payload, dict):
            continue
        payload_type = payload.get("type")
        if payload_type == "message":
            role = payload.get("role")
            texts = text_blocks(payload.get("content"))
            if role == "user":
                user_texts.extend(clean_user_text(text) for text in texts if text.strip())
            elif role == "assistant":
                assistant_texts.extend(compact(text) for text in texts if text.strip())
        elif payload_type == "function_call":
            name = payload.get("name")
            if isinstance(name, str):
                tool_names.append(name)

    clean_requests = [text for text in user_texts if text][:5]
    thread_source = meta.get("thread_source") or ""
    confidence = "high" if thread_source == "user" and clean_requests else "medium"
    if thread_source and thread_source != "user":
        confidence = "low"

    return {
        "source": "codex",
        "session_id": meta.get("id") or meta.get("session_id") or path.stem,
        "parent_session_id": meta.get("session_id"),
        "file": str(path),
        "started_at": meta.get("timestamp"),
        "cwd": meta.get("cwd"),
        "thread_source": thread_source,
        "event_count": len(rows),
        "user_message_count": len(user_texts),
        "assistant_message_count": len(assistant_texts),
        "tool_call_count": len(tool_names),
        "tool_names": sorted(set(tool_names)),
        "clean_user_requests": clean_requests,
        "assistant_snippets": assistant_texts[-3:],
        "confidence": confidence,
    }


def session_files_for_date(root: Path, target_date: date) -> list[Path]:
    day_dir = root / f"{target_date:%Y}" / f"{target_date:%m}" / f"{target_date:%d}"
    if day_dir.is_dir():
        return sorted(day_dir.glob("*.jsonl"))
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect Codex session candidates for a date.")
    parser.add_argument("--date", required=True, help="Target date in YYYY-MM-DD")
    parser.add_argument("--sessions-root", default=str(DEFAULT_SESSIONS_ROOT))
    parser.add_argument("--include-subagents", action="store_true")
    args = parser.parse_args()

    target_date = date.fromisoformat(args.date)
    root = Path(args.sessions_root).expanduser()
    candidates = []
    for path in session_files_for_date(root, target_date):
        summary = summarize_session(path)
        if args.include_subagents or summary.get("thread_source") == "user":
            candidates.append(summary)

    print(json.dumps({"date": args.date, "source": "codex", "sessions": candidates}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
