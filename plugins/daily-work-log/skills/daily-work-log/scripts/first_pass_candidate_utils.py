#!/usr/bin/env python3
"""Utilities for daily-work-log first-pass candidate collection."""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone, tzinfo
from pathlib import Path
from typing import Any


DEFAULT_STATE_ROOT = Path.home() / ".daily-work-log"
SCHEMA_VERSION = "daily-work-log.first-pass.v1"

PATH_RE = re.compile(
    r"(?:(?:/|~\/|\.\.?/)[A-Za-z0-9._@%+=:,~/-]+|[A-Za-z0-9_.-]+/[A-Za-z0-9._@%+=:,~/-]+)"
)
EDIT_TOOLS = {
    "apply_patch",
    "Edit",
    "MultiEdit",
    "Write",
    "NotebookEdit",
    "str_replace_editor",
}
GIT_RE = re.compile(r"\b(git\s+(?:status|diff|add|commit|push|pull|merge|rebase|checkout|switch)|gh\s+pr)\b", re.I)
TEST_RE = re.compile(r"\b(pytest|npm\s+(?:test|run\s+test)|pnpm\s+(?:test|run\s+test)|yarn\s+test|mvn\s+test|gradle\s+test|cargo\s+test|go\s+test)\b", re.I)
ERROR_RE = re.compile(r"\b(error|exception|traceback|failed|failure|timeout|timed out|permission denied|not permitted|fatal|panic)\b", re.I)
COMMAND_RE = re.compile(
    r"\b("
    r"git\s+(?:status|diff|add|commit|push|pull|merge|rebase|checkout|switch|show|log)"
    r"|gh\s+pr\s+\w+"
    r"|(?:npm|pnpm|yarn)\s+(?:test|run\s+\S+|install|build|lint)"
    r"|pytest(?:\s+\S+)*"
    r"|python3?\s+\S+"
    r"|mvn\s+test"
    r"|gradle\s+test"
    r"|cargo\s+test"
    r"|go\s+test(?:\s+\S+)*"
    r")\b",
    re.I,
)
COMMIT_RE = re.compile(r"\b[0-9a-f]{7,40}\b")
SYSTEM_REMINDER_OPEN = "<system-reminder>"
SYSTEM_REMINDER_CLOSE = "</system-reminder>"


def load_jsonl(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for index, line in enumerate(handle):
                if limit is not None and index >= limit:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(row, dict):
                    rows.append(row)
    except OSError:
        return []
    return rows


def compact(text: str, limit: int = 240) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def strip_injected_blocks(text: str) -> str:
    while SYSTEM_REMINDER_OPEN in text:
        start = text.find(SYSTEM_REMINDER_OPEN)
        end = text.find(SYSTEM_REMINDER_CLOSE, start + len(SYSTEM_REMINDER_OPEN))
        if end == -1:
            return text[:start]
        text = text[:start] + text[end + len(SYSTEM_REMINDER_CLOSE) :]
    return text


def to_local_date(value: Any, tz: tzinfo | None = None) -> date | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(tz).date()


def clean_user_text(text: str, limit: int = 260) -> str:
    text = strip_injected_blocks(text)
    text = re.sub(r"^\[[^\]]+\]\([^)]*SKILL\.md\)\s*", "", text.strip())
    leading = text.lstrip()
    if leading.startswith(
        (
            "# AGENTS.md instructions",
            "<INSTRUCTIONS>",
            "<environment_context>",
            "<permissions instructions>",
            "<developer_context>",
            "<skill>",
            "<command-message>",
            "<command-name>",
            "<command-args>",
            "Base directory for this skill:",
        )
    ):
        return ""

    noise_markers = (
        "# AGENTS.md instructions",
        "<INSTRUCTIONS>",
        "<environment_context>",
        "<permissions instructions>",
        ">>> TRANSCRIPT",
    )
    earliest = len(text)
    for marker in noise_markers:
        index = text.find(marker)
        if index > 0:
            earliest = min(earliest, index)
    if earliest != len(text):
        text = text[:earliest]

    kept = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# Files mentioned by the user:"):
            continue
        kept.append(line)
    return compact("\n".join(kept), limit)


def extract_paths(text: str, limit: int = 30) -> list[str]:
    paths: list[str] = []
    seen: set[str] = set()
    for match in PATH_RE.findall(text):
        value = match.rstrip(".,:;)]}\"'")
        if re.match(r"^[nrt]/", value):
            value = value[1:]
        if len(value) < 3 or value in seen:
            continue
        if value.startswith(("http://", "https://")):
            continue
        seen.add(value)
        paths.append(value)
        if len(paths) >= limit:
            break
    return paths


def extract_commands(text: str, limit: int = 20) -> list[str]:
    commands: list[str] = []
    seen: set[str] = set()
    for match in COMMAND_RE.findall(text):
        value = compact(match, 160)
        if value in seen:
            continue
        seen.add(value)
        commands.append(value)
        if len(commands) >= limit:
            break
    return commands


def extract_commits(text: str, limit: int = 12) -> list[str]:
    commits: list[str] = []
    seen: set[str] = set()
    for match in COMMIT_RE.findall(text):
        if match in seen:
            continue
        seen.add(match)
        commits.append(match)
        if len(commits) >= limit:
            break
    return commits


def has_edit_signal(tool_names: list[str], signal_text: str) -> bool:
    if any(name in EDIT_TOOLS for name in tool_names):
        return True
    return bool(
        re.search(
            r"\b(apply_patch|write file|created file|edited file|modified file|updated file)\b|파일을?\s*(?:수정|생성|작성)|수정했습니다|반영했습니다",
            signal_text,
            re.I,
        )
    )


def signal_flags(tool_names: list[str], signal_text: str) -> dict[str, bool]:
    return {
        "has_edit_signal": has_edit_signal(tool_names, signal_text),
        "has_git_signal": bool(GIT_RE.search(signal_text)),
        "has_test_signal": bool(TEST_RE.search(signal_text)),
        "has_error_signal": bool(ERROR_RE.search(signal_text)),
    }


def classification_hints(flags: dict[str, bool]) -> list[str]:
    hints = ["work-item"]
    if flags.get("has_error_signal"):
        hints.append("troubleshooting")
    if flags.get("has_test_signal"):
        hints.append("verification")
    if flags.get("has_git_signal"):
        hints.append("git-work")
    return hints


def confidence(score: int) -> str:
    if score >= 80:
        return "high"
    if score >= 50:
        return "medium"
    return "low"


def project_name(cwd: Any) -> str:
    if isinstance(cwd, str) and cwd.strip():
        return Path(cwd).name or cwd
    return "알 수 없는 작업공간"


def infer_title(user_snippets: list[str], title_hint: str | None, fallback: str) -> str:
    if title_hint:
        return compact(title_hint, 90)
    if user_snippets:
        return compact(user_snippets[0], 90)
    return fallback


def first_pass_summary(cwd: Any, user_snippets: list[str], tool_names: list[str], flags: dict[str, bool]) -> str:
    intent = compact(user_snippets[0], 80) if user_snippets else "사용자 요청"
    tools = ", ".join(tool_names[:6]) if tool_names else "도구 사용 없음"
    active_signals = []
    if flags.get("has_edit_signal"):
        active_signals.append("수정")
    if flags.get("has_git_signal"):
        active_signals.append("git")
    if flags.get("has_test_signal"):
        active_signals.append("테스트")
    if flags.get("has_error_signal"):
        active_signals.append("에러/트러블슈팅")
    signal_text = ", ".join(active_signals) if active_signals else "강한 작업 신호 없음"
    return f"{project_name(cwd)}에서 '{intent}' 관련 작업으로 보임. 도구: {tools}. 신호: {signal_text}."


def work_unit_title(cwd: Any, user_request: str) -> str:
    request = compact(user_request, 70) if user_request else "사용자 요청"
    return f"{project_name(cwd)} - {request}"


def work_unit_outcome(result_snippets: list[str], flags: dict[str, bool]) -> str:
    if result_snippets:
        return compact(result_snippets[-1], 320)
    signals = []
    if flags.get("has_edit_signal"):
        signals.append("수정")
    if flags.get("has_git_signal"):
        signals.append("git")
    if flags.get("has_test_signal"):
        signals.append("테스트")
    if flags.get("has_error_signal"):
        signals.append("트러블슈팅")
    if signals:
        return f"{', '.join(signals)} 신호가 있으나 최종 응답은 확인되지 않음."
    return "결과 힌트가 부족함."


def build_work_unit(
    *,
    source: str,
    session_id: Any,
    cwd: Any,
    index: int,
    user_request: str,
    result_snippets: list[str],
    tool_names: list[str],
    signal_text: str,
) -> dict[str, Any]:
    unique_tools = sorted(set(tool_names))
    flags = signal_flags(unique_tools, signal_text)
    commands = extract_commands(signal_text)
    paths = extract_paths(signal_text, limit=20)
    commits = extract_commits(signal_text)
    tests = [command for command in commands if TEST_RE.search(command)]
    git_evidence = [command for command in commands if GIT_RE.search(command)]
    if commits and (flags.get("has_git_signal") or re.search(r"\bcommit\b|커밋", signal_text, re.I)):
        git_evidence.extend(f"commit:{commit}" for commit in commits)

    return {
        "work_unit_id": f"{source}:{session_id}:{index}",
        "title": work_unit_title(cwd, user_request),
        "user_request": user_request,
        "outcome": work_unit_outcome(result_snippets, flags),
        "changed_paths": paths if flags.get("has_edit_signal") else [],
        "mentioned_paths": paths,
        "commands": commands,
        "git_evidence": git_evidence[:12],
        "test_evidence": tests[:12],
        "tool_names": unique_tools,
        "result_snippets": result_snippets[-3:],
        "final_answer": result_snippets[-1] if result_snippets else None,
        "classification_hints": classification_hints(flags),
        **flags,
        "confidence": confidence(
            score_candidate(
                clean_user_requests=[user_request] if user_request else [],
                tool_call_count=len(tool_names),
                result_snippets=result_snippets,
                flags=flags,
                is_supporting=False,
                is_skill_only=False,
                interrupted_without_result=False,
            )
        ),
    }


def first_pass_summary_with_units(
    cwd: Any,
    user_snippets: list[str],
    tool_names: list[str],
    flags: dict[str, bool],
    work_units: list[dict[str, Any]],
) -> str:
    if work_units:
        titles = "; ".join(compact(str(unit.get("title") or ""), 60) for unit in work_units[:3])
        suffix = " 등" if len(work_units) > 3 else ""
        return f"{project_name(cwd)}에서 {len(work_units)}개 업무 단위 후보: {titles}{suffix}"
    return first_pass_summary(cwd, user_snippets, tool_names, flags)


def score_candidate(
    *,
    clean_user_requests: list[str],
    tool_call_count: int,
    result_snippets: list[str],
    flags: dict[str, bool],
    is_supporting: bool,
    is_skill_only: bool,
    interrupted_without_result: bool,
) -> int:
    score = 0
    if clean_user_requests:
        score += 30
    if tool_call_count:
        score += 15
    if flags.get("has_edit_signal"):
        score += 20
    if flags.get("has_git_signal"):
        score += 15
    if flags.get("has_test_signal"):
        score += 10
    if flags.get("has_error_signal"):
        score += 20
    if result_snippets:
        score += 15
    if is_supporting:
        score -= 25
    if is_skill_only:
        score -= 20
    if interrupted_without_result:
        score -= 15
    return max(0, score)


def split_candidates(candidates: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    primary: list[dict[str, Any]] = []
    supporting: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for candidate in candidates:
        score = int(candidate.get("importance_score") or 0)
        if score >= 50:
            primary.append(candidate)
        elif score >= 25:
            supporting.append(candidate)
        else:
            rejected.append(candidate)
    key = lambda item: int(item.get("importance_score") or 0)
    primary.sort(key=key, reverse=True)
    supporting.sort(key=key, reverse=True)
    rejected.sort(key=key, reverse=True)
    return primary, supporting, rejected


def default_output_path(source: str, target_date: str, state_root: Path = DEFAULT_STATE_ROOT) -> Path:
    year = target_date[:4]
    return state_root / year / target_date / f"{source}-candidates.json"


def write_or_print(
    result: dict[str, Any],
    output: str | None,
    stdout: bool,
    state_root: Path = DEFAULT_STATE_ROOT,
) -> Path | None:
    if stdout:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return None
    if output:
        path = Path(output).expanduser()
    else:
        path = default_output_path(str(result["source"]), str(result["date"]), state_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(path)
    return path


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
