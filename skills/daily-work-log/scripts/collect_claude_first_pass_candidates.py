#!/usr/bin/env python3
"""Claude 세션 JSONL에서 daily-work-log 1차 후보 카드를 만든다."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from first_pass_candidate_utils import (
    clean_user_text,
    build_work_unit,
    classification_hints,
    compact,
    confidence,
    extract_paths,
    first_pass_summary_with_units,
    infer_title,
    load_jsonl,
    now_iso,
    SCHEMA_VERSION,
    score_candidate,
    signal_flags,
    split_candidates,
    write_or_print,
)


DEFAULT_ROOT = Path.home() / ".claude"


def parse_date_value(value: Any) -> date | None:
    if not isinstance(value, str) or not value:
        return None
    raw = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(raw).date()
    except ValueError:
        return None


def row_date(row: dict[str, Any]) -> date | None:
    for key in ("timestamp", "created_at", "createdAt"):
        parsed = parse_date_value(row.get(key))
        if parsed:
            return parsed
    message = row.get("message")
    if isinstance(message, dict):
        for key in ("timestamp", "created_at", "createdAt"):
            parsed = parse_date_value(message.get(key))
            if parsed:
                return parsed
    return None


def row_timestamp(row: dict[str, Any]) -> str | None:
    for key in ("timestamp", "created_at", "createdAt"):
        value = row.get(key)
        if isinstance(value, str):
            return value
    message = row.get("message")
    if isinstance(message, dict):
        for key in ("timestamp", "created_at", "createdAt"):
            value = message.get(key)
            if isinstance(value, str):
                return value
    return None


def iter_jsonl(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    projects = root / "projects"
    paths = sorted(projects.rglob("*.jsonl")) if projects.is_dir() else []
    if paths:
        return paths
    return sorted(root.rglob("*.jsonl"))


def file_matches_date(path: Path, target_date: date) -> bool:
    rows = load_jsonl(path, limit=250)
    for row in rows:
        parsed = row_date(row)
        if parsed == target_date:
            return True
        if parsed and parsed > target_date:
            return False
    try:
        return date.fromtimestamp(path.stat().st_mtime) == target_date
    except OSError:
        return False


def content_texts(content: Any) -> list[str]:
    if isinstance(content, str):
        return [content]
    if not isinstance(content, list):
        return []
    texts: list[str] = []
    for item in content:
        if isinstance(item, str):
            texts.append(item)
        elif isinstance(item, dict):
            text = item.get("text") or item.get("content")
            if isinstance(text, str):
                texts.append(text)
    return texts


def collect_tool_names(content: Any) -> list[str]:
    if not isinstance(content, list):
        return []
    names: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "tool_use":
            name = item.get("name")
            if isinstance(name, str):
                names.append(name)
        elif item.get("type") in {"tool_result", "server_tool_use"}:
            name = item.get("name")
            if isinstance(name, str):
                names.append(name)
    return names


def has_tool_result(content: Any) -> bool:
    if not isinstance(content, list):
        return False
    return any(isinstance(item, dict) and item.get("type") == "tool_result" for item in content)


def message_role(row: dict[str, Any]) -> str | None:
    message = row.get("message")
    if isinstance(message, dict) and isinstance(message.get("role"), str):
        return message["role"]
    row_type = row.get("type")
    if row_type in {"user", "assistant"}:
        return str(row_type)
    return None


def message_content(row: dict[str, Any]) -> Any:
    message = row.get("message")
    if isinstance(message, dict) and "content" in message:
        return message.get("content")
    return row.get("content")


def candidate_from_file(path: Path) -> dict[str, Any]:
    rows = load_jsonl(path)
    user_snippets: list[str] = []
    result_snippets: list[str] = []
    tool_names: list[str] = []
    signal_chunks: list[str] = []
    timestamps: list[str] = []
    work_units: list[dict[str, Any]] = []
    current_unit: dict[str, Any] | None = None
    cwd: str | None = None
    session_id: str | None = None
    title_hint: str | None = None
    is_sidechain = False
    interrupted = False

    def ensure_unit() -> dict[str, Any]:
        nonlocal current_unit
        if current_unit is None:
            current_unit = {
                "user_request": "",
                "result_snippets": [],
                "tool_names": [],
                "signal_chunks": [],
            }
        return current_unit

    def flush_unit() -> None:
        nonlocal current_unit
        if current_unit is None:
            return
        user_request = str(current_unit.get("user_request") or "")
        results = list(current_unit.get("result_snippets") or [])
        unit_tools = list(current_unit.get("tool_names") or [])
        unit_signal = "\n".join(str(chunk) for chunk in current_unit.get("signal_chunks") or [])
        if user_request or results or unit_tools:
            work_units.append(
                build_work_unit(
                    source="claude",
                    session_id=session_id or path.stem,
                    cwd=cwd,
                    index=len(work_units) + 1,
                    user_request=user_request,
                    result_snippets=results,
                    tool_names=unit_tools,
                    signal_text=unit_signal,
                )
            )
        current_unit = None

    for row in rows:
        timestamp = row_timestamp(row)
        if timestamp:
            timestamps.append(timestamp)
        if isinstance(row.get("cwd"), str):
            cwd = row.get("cwd")
        if isinstance(row.get("session_id"), str):
            session_id = row.get("session_id")
        if isinstance(row.get("uuid"), str) and not session_id:
            session_id = row.get("uuid")
        if row.get("isSidechain") is True or "/subagents/" in str(path):
            is_sidechain = True

        row_type = row.get("type")
        if row_type == "ai-title":
            text = row.get("content") or row.get("title")
            if isinstance(text, str):
                title_hint = text
        if row_type == "queue-operation":
            content = row.get("content")
            if isinstance(content, str):
                cleaned = clean_user_text(content)
                if cleaned:
                    user_snippets.append(cleaned)
                    if current_unit and current_unit.get("user_request") == cleaned:
                        current_unit["signal_chunks"].append(cleaned)
                        continue
                    flush_unit()
                    current_unit = {
                        "user_request": cleaned,
                        "result_snippets": [],
                        "tool_names": [],
                        "signal_chunks": [cleaned],
                    }
        if row_type in {"last-prompt", "attachment", "mode"}:
            signal_chunks.append(json.dumps(row, ensure_ascii=False)[:1000])
            continue
        if "interrupted" in json.dumps(row, ensure_ascii=False).lower():
            interrupted = True

        role = message_role(row)
        content = message_content(row)
        texts = [text for text in content_texts(content) if text.strip()]
        content_has_tool_result = has_tool_result(content)
        if role == "user" and not content_has_tool_result:
            for text in texts:
                cleaned = clean_user_text(text)
                if cleaned:
                    user_snippets.append(cleaned)
                    if current_unit and current_unit.get("user_request") == cleaned:
                        current_unit["signal_chunks"].append(cleaned)
                        continue
                    flush_unit()
                    current_unit = {
                        "user_request": cleaned,
                        "result_snippets": [],
                        "tool_names": [],
                        "signal_chunks": [cleaned],
                    }
        elif role == "assistant":
            snippets = [compact(text, 260) for text in texts]
            result_snippets.extend(snippets)
            unit = ensure_unit()
            unit["result_snippets"].extend(snippets)
            unit["signal_chunks"].extend(texts)
        elif content_has_tool_result:
            signal_chunks.append(json.dumps(row, ensure_ascii=False)[:4000])
            ensure_unit()["signal_chunks"].append(json.dumps(row, ensure_ascii=False)[:4000])

        names = collect_tool_names(content)
        tool_names.extend(names)
        if names or texts:
            row_text = json.dumps(row, ensure_ascii=False)[:4000]
            signal_chunks.append(row_text)
            unit = ensure_unit()
            unit["tool_names"].extend(names)
            unit["signal_chunks"].append(row_text)

    flush_unit()

    clean_requests = user_snippets[:5]
    assistant_results = result_snippets[-3:]
    unique_tools = sorted(set(tool_names))
    signal_text = "\n".join(signal_chunks)
    flags = signal_flags(unique_tools, signal_text)
    is_skill_only = bool(unique_tools and set(unique_tools).issubset({"Skill", "Agent"}))
    score = score_candidate(
        clean_user_requests=clean_requests,
        tool_call_count=len(tool_names),
        result_snippets=assistant_results,
        flags=flags,
        is_supporting=is_sidechain,
        is_skill_only=is_skill_only,
        interrupted_without_result=interrupted and not assistant_results,
    )
    title = infer_title(clean_requests, title_hint, f"Claude session {path.stem}")

    return {
        "session_id": session_id or path.stem,
        "source": "claude",
        "file": str(path),
        "started_at": timestamps[0] if timestamps else None,
        "last_seen_at": timestamps[-1] if timestamps else None,
        "cwd": cwd,
        "is_sidechain": is_sidechain,
        "title_hint": title,
        "user_intent_snippets": clean_requests,
        "result_snippets": assistant_results,
        "tool_names": unique_tools,
        "tool_call_count": len(tool_names),
        "mentioned_paths": extract_paths(signal_text),
        "work_units": work_units,
        **flags,
        "classification_hints": classification_hints(flags),
        "importance_score": score,
        "first_pass_summary": first_pass_summary_with_units(cwd, clean_requests, unique_tools, flags, work_units),
        "confidence": confidence(score),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Claude 1차 후보 카드를 수집한다.")
    parser.add_argument("--date", required=True, help="대상 날짜 YYYY-MM-DD")
    parser.add_argument("--sessions-root", default=str(DEFAULT_ROOT))
    parser.add_argument("--include-supporting", action="store_true", help="sidechain/subagent 후보도 primary 판단에 포함")
    parser.add_argument("--output", help="출력 JSON 경로. 기본값은 ~/.daily-work-log/YYYY/YYYY-MM-DD/claude-candidates.json")
    parser.add_argument("--stdout", action="store_true", help="파일에 쓰지 않고 stdout으로 출력")
    args = parser.parse_args()

    target_date = date.fromisoformat(args.date)
    root = Path(args.sessions_root).expanduser()
    collected = [candidate_from_file(path) for path in iter_jsonl(root) if file_matches_date(path, target_date)]
    if not args.include_supporting:
        collected = [item for item in collected if not item.get("is_sidechain")]

    candidates, supporting, rejected = split_candidates(collected)
    result = {
        "schema_version": SCHEMA_VERSION,
        "date": args.date,
        "source": "claude",
        "stage": "first-pass-collection",
        "generated_at": now_iso(),
        "candidates": candidates,
        "supporting": supporting,
        "rejected": rejected,
    }
    write_or_print(result, args.output, args.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
