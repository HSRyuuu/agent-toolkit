#!/usr/bin/env python3
"""Build first-pass filtered Codex candidates from collection JSON."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def load_input(path: str | None) -> dict[str, Any]:
    if path:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    return json.load(sys.stdin)


def score_candidate(session: dict[str, Any]) -> int:
    score = 0
    if session.get("thread_source") == "user":
        score += 50
    if session.get("clean_user_requests"):
        score += 25
    score += min(int(session.get("tool_call_count") or 0), 20)
    score += min(int(session.get("assistant_message_count") or 0), 10)
    return score


def infer_title(session: dict[str, Any]) -> str:
    requests = session.get("clean_user_requests")
    if isinstance(requests, list) and requests:
        first = str(requests[0]).strip()
        return first[:80] + ("..." if len(first) > 80 else "")
    return f"Codex session {session.get('session_id') or 'unknown'}"


def filter_sessions(sessions: list[dict[str, Any]], include_supporting: bool) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for session in sessions:
        score = score_candidate(session)
        reason = []
        if session.get("thread_source") != "user":
            reason.append("not a primary user thread")
        if not session.get("clean_user_requests"):
            reason.append("no clean user request")

        candidate = {
            **session,
            "candidate_title": infer_title(session),
            "first_pass_score": score,
            "filter_reasons": reason,
        }

        if score >= 60 or (include_supporting and score >= 25):
            accepted.append(candidate)
        else:
            rejected.append(candidate)

    accepted.sort(key=lambda item: item.get("first_pass_score", 0), reverse=True)
    return accepted, rejected


def main() -> int:
    parser = argparse.ArgumentParser(description="Filter collected Codex candidates.")
    parser.add_argument("input", nargs="?", help="Collection JSON file; defaults to stdin")
    parser.add_argument("--include-supporting", action="store_true", help="Keep lower-confidence supporting sessions")
    args = parser.parse_args()

    data = load_input(args.input)
    sessions = data.get("sessions") if isinstance(data.get("sessions"), list) else []
    accepted, rejected = filter_sessions(sessions, args.include_supporting)
    result = {
        "date": data.get("date"),
        "source": "codex",
        "stage": "first-pass-filter",
        "candidates": accepted,
        "rejected": rejected,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
