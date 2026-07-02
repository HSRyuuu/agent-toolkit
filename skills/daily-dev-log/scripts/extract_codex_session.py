#!/usr/bin/env python3
"""Extract a detailed but safe Codex session digest."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from collect_codex_sessions import clean_user_text, compact, first_session_meta, load_jsonl, text_blocks


PATH_RE = re.compile(r"(?<![A-Za-z0-9_])(?:/Users/|/private/|/tmp/|~\/)[^\s'\"`<>)]*")
ERROR_RE = re.compile(r"\b(error|failed|failure|exception|traceback|denied|timeout)\b", re.IGNORECASE)


def maybe_json_excerpt(value: Any, limit: int = 1200) -> str:
    if isinstance(value, str):
        return compact(value, limit)
    return compact(json.dumps(value, ensure_ascii=False, sort_keys=True), limit)


def extract_digest(path: Path) -> dict[str, Any]:
    rows = load_jsonl(path)
    meta = first_session_meta(rows)
    safe_meta = {
        key: meta.get(key)
        for key in (
            "id",
            "session_id",
            "parent_thread_id",
            "timestamp",
            "cwd",
            "originator",
            "cli_version",
            "source",
            "thread_source",
            "model_provider",
        )
        if key in meta
    }
    messages: list[dict[str, str]] = []
    tool_calls: list[dict[str, Any]] = []
    tool_outputs: list[dict[str, str]] = []
    mentioned_paths: set[str] = set()
    errors: list[str] = []

    for row in rows:
        if row.get("type") != "response_item":
            continue
        payload = row.get("payload")
        if not isinstance(payload, dict):
            continue
        payload_type = payload.get("type")
        if payload_type == "message":
            role = payload.get("role")
            if role not in {"user", "assistant"}:
                continue
            for text in text_blocks(payload.get("content")):
                cleaned = clean_user_text(text) if role == "user" else compact(text, 2000)
                if cleaned:
                    messages.append({"role": role, "text": cleaned})
                    mentioned_paths.update(PATH_RE.findall(cleaned))
                    if ERROR_RE.search(cleaned):
                        errors.append(compact(cleaned, 300))
        elif payload_type == "function_call":
            arguments = payload.get("arguments")
            call = {
                "name": payload.get("name"),
                "call_id": payload.get("call_id"),
                "arguments": maybe_json_excerpt(arguments, 1000),
            }
            tool_calls.append(call)
            mentioned_paths.update(PATH_RE.findall(call["arguments"]))
        elif payload_type == "function_call_output":
            output = maybe_json_excerpt(payload.get("output"), 1200)
            tool_outputs.append({"call_id": payload.get("call_id") or "", "output_excerpt": output})
            mentioned_paths.update(PATH_RE.findall(output))
            if ERROR_RE.search(output):
                errors.append(compact(output, 300))

    return {
        "source": "codex",
        "session_id": meta.get("id") or meta.get("session_id") or path.stem,
        "file": str(path),
        "metadata": safe_meta,
        "messages": messages,
        "tool_calls": tool_calls,
        "tool_outputs": tool_outputs,
        "mentioned_paths": sorted(mentioned_paths),
        "errors": errors[:20],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract a Codex session digest.")
    parser.add_argument("session_file")
    args = parser.parse_args()

    digest = extract_digest(Path(args.session_file).expanduser())
    print(json.dumps(digest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
