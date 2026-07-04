#!/usr/bin/env python3
"""Codex 세션 JSONL에서 daily-work-log 1차 후보 카드를 만든다."""

from __future__ import annotations

import argparse
import json
from datetime import date
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


DEFAULT_SESSIONS_ROOT = Path.home() / ".codex" / "sessions"


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


def session_files_for_date(root: Path, target_date: date) -> list[Path]:
    day_dir = root / f"{target_date:%Y}" / f"{target_date:%m}" / f"{target_date:%d}"
    if not day_dir.is_dir():
        return []
    return sorted(day_dir.glob("*.jsonl"))


def first_session_meta(rows: list[dict[str, Any]]) -> dict[str, Any]:
    for row in rows:
        if row.get("type") == "session_meta":
            payload = row.get("payload")
            if isinstance(payload, dict):
                return payload
    return {}


def candidate_from_file(path: Path) -> dict[str, Any]:
    rows = load_jsonl(path)
    meta = first_session_meta(rows)
    user_snippets: list[str] = []
    result_snippets: list[str] = []
    tool_names: list[str] = []
    signal_chunks: list[str] = []
    timestamps: list[str] = []
    work_units: list[dict[str, Any]] = []
    current_unit: dict[str, Any] | None = None
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
                    source="codex",
                    session_id=meta.get("id") or meta.get("session_id") or path.stem,
                    cwd=meta.get("cwd"),
                    index=len(work_units) + 1,
                    user_request=user_request,
                    result_snippets=results,
                    tool_names=unit_tools,
                    signal_text=unit_signal,
                )
            )
        current_unit = None

    for row in rows:
        timestamp = row.get("timestamp")
        if isinstance(timestamp, str):
            timestamps.append(timestamp)

        row_type = row.get("type")
        if row_type == "event_msg":
            message = json.dumps(row, ensure_ascii=False)
            signal_chunks.append(message[:1000])
            if "interrupted" in message.lower():
                interrupted = True
            continue

        if row_type != "response_item":
            continue
        payload = row.get("payload")
        if not isinstance(payload, dict):
            continue
        payload_type = payload.get("type")

        if payload_type == "message":
            role = payload.get("role")
            texts = [text for text in text_blocks(payload.get("content")) if text.strip()]
            if role == "user":
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
                signal_chunks.extend(texts)
                unit = ensure_unit()
                unit["result_snippets"].extend(snippets)
                unit["signal_chunks"].extend(texts)
        elif payload_type == "function_call":
            name = payload.get("name")
            if isinstance(name, str):
                tool_names.append(name)
                unit = ensure_unit()
                unit["tool_names"].append(name)
            payload_text = json.dumps(payload, ensure_ascii=False)[:4000]
            signal_chunks.append(payload_text)
            ensure_unit()["signal_chunks"].append(payload_text)
        elif payload_type == "function_call_output":
            payload_text = json.dumps(payload, ensure_ascii=False)[:4000]
            signal_chunks.append(payload_text)
            ensure_unit()["signal_chunks"].append(payload_text)

    flush_unit()

    clean_requests = user_snippets[:5]
    assistant_results = result_snippets[-3:]
    unique_tools = sorted(set(tool_names))
    signal_text = "\n".join(signal_chunks)
    flags = signal_flags(unique_tools, signal_text)
    thread_source = str(meta.get("thread_source") or "")
    is_supporting = bool(thread_source and thread_source != "user")
    is_skill_only = bool(unique_tools and set(unique_tools).issubset({"read_mcp_resource", "list_mcp_resources"}))
    score = score_candidate(
        clean_user_requests=clean_requests,
        tool_call_count=len(tool_names),
        result_snippets=assistant_results,
        flags=flags,
        is_supporting=is_supporting,
        is_skill_only=is_skill_only,
        interrupted_without_result=interrupted and not assistant_results,
    )
    title_hint = infer_title(clean_requests, None, f"Codex session {path.stem}")

    return {
        "session_id": meta.get("id") or meta.get("session_id") or path.stem,
        "source": "codex",
        "file": str(path),
        "started_at": meta.get("timestamp") or (timestamps[0] if timestamps else None),
        "last_seen_at": timestamps[-1] if timestamps else meta.get("timestamp"),
        "cwd": meta.get("cwd"),
        "thread_source": thread_source,
        "title_hint": title_hint,
        "user_intent_snippets": clean_requests,
        "result_snippets": assistant_results,
        "tool_names": unique_tools,
        "tool_call_count": len(tool_names),
        "mentioned_paths": extract_paths(signal_text),
        "work_units": work_units,
        **flags,
        "classification_hints": classification_hints(flags),
        "importance_score": score,
        "first_pass_summary": first_pass_summary_with_units(meta.get("cwd"), clean_requests, unique_tools, flags, work_units),
        "confidence": confidence(score),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Codex 1차 후보 카드를 수집한다.")
    parser.add_argument("--date", required=True, help="대상 날짜 YYYY-MM-DD")
    parser.add_argument("--sessions-root", default=str(DEFAULT_SESSIONS_ROOT))
    parser.add_argument("--include-supporting", action="store_true", help="subagent/supporting 후보도 primary 판단에 포함")
    parser.add_argument("--output", help="출력 JSON 경로. 기본값은 ~/.daily-work-log/YYYY/YYYY-MM-DD/codex-candidates.json")
    parser.add_argument("--stdout", action="store_true", help="파일에 쓰지 않고 stdout으로 출력")
    args = parser.parse_args()

    target_date = date.fromisoformat(args.date)
    root = Path(args.sessions_root).expanduser()
    collected = [candidate_from_file(path) for path in session_files_for_date(root, target_date)]
    if not args.include_supporting:
        collected = [item for item in collected if item.get("thread_source") in {"", "user"}]

    candidates, supporting, rejected = split_candidates(collected)
    result = {
        "schema_version": SCHEMA_VERSION,
        "date": args.date,
        "source": "codex",
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
