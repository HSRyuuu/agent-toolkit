#!/usr/bin/env python3
"""Markdown KB에서 daily-work-log 1차 후보 카드를 조용히 만든다."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime
from hashlib import sha1
from pathlib import Path
from typing import Any

from first_pass_candidate_utils import (
    SCHEMA_VERSION,
    classification_hints,
    compact,
    confidence,
    default_output_path,
    extract_paths,
    now_iso,
    split_candidates,
)


KB_CONFIG_JSON = Path.home() / ".config" / "kb" / "kb-config.json"
KB_CONFIG_PATH = Path.home() / ".config" / "kb" / "path"
IGNORED_DIRS = {".git", ".obsidian", ".venv", "node_modules"}


def normalize_date(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip().strip('"').strip("'")
    if not text:
        return None
    return text[:10]


def first_non_empty_line(path: Path) -> str | None:
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped:
                return stripped
    except OSError:
        return None
    return None


def valid_dir(raw: Any) -> Path | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    candidate = Path(raw).expanduser()
    if candidate.is_absolute() and candidate.is_dir():
        return candidate.resolve()
    return None


def resolve_kb_root(explicit_root: str | None = None) -> Path | None:
    explicit = valid_dir(explicit_root)
    if explicit:
        return explicit

    try:
        data = json.loads(KB_CONFIG_JSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data = None
    if isinstance(data, dict):
        for key in ("path", "root", "kb_root"):
            configured = valid_dir(data.get(key))
            if configured:
                return configured

    configured = valid_dir(first_non_empty_line(KB_CONFIG_PATH))
    if configured:
        return configured
    return None


def iter_markdown_files(root: Path) -> list[Path]:
    paths: list[Path] = []
    for path in sorted(root.rglob("*")):
        if path.suffix.lower() not in {".md", ".markdown"}:
            continue
        try:
            rel_parts = path.relative_to(root).parts
        except ValueError:
            continue
        if any(part in IGNORED_DIRS for part in rel_parts):
            continue
        paths.append(path)
    return paths


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text

    raw = text[4:end]
    body = text[end + 4 :]
    metadata: dict[str, Any] = {}
    current_key: str | None = None
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t")) and current_key:
            stripped = line.strip()
            if stripped.startswith("- "):
                metadata.setdefault(current_key, []).append(stripped[2:].strip().strip('"').strip("'"))
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        current_key = key.strip()
        value = value.strip()
        if not value:
            metadata[current_key] = []
        elif value.startswith("[") and value.endswith("]"):
            metadata[current_key] = [
                item.strip().strip('"').strip("'") for item in value[1:-1].split(",") if item.strip()
            ]
        else:
            metadata[current_key] = value.strip('"').strip("'")
    return metadata, body


def first_heading(body: str) -> str | None:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or None
    return None


def read_doc_item(root: Path, path: Path, target_date: str) -> dict[str, Any] | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    metadata, body = parse_frontmatter(text)
    created = normalize_date(metadata.get("created") or metadata.get("date"))
    updated = normalize_date(metadata.get("updated"))
    if target_date not in {created, updated}:
        return None

    relpath = path.relative_to(root).as_posix()
    title = metadata.get("title") or first_heading(body) or Path(relpath).stem.replace("-", " ")
    summary = metadata.get("summary") or f"KB 문서가 {target_date}에 생성 또는 수정됨."
    action = "created" if created == target_date and updated != target_date else "updated"
    evidence = []
    if created == target_date:
        evidence.append(f"created={target_date}")
    if updated == target_date:
        evidence.append(f"updated={target_date}")

    return {
        "id": stable_id(f"doc:{relpath}"),
        "kind": "doc",
        "file": str(path),
        "path": relpath,
        "title": compact(str(title), 100),
        "summary": compact(str(summary), 360),
        "action": action,
        "evidence": evidence,
        "text": text[:4000],
    }


def row_date(row: dict[str, Any]) -> str | None:
    for key in ("timestamp", "created_at", "createdAt", "updated_at", "updatedAt", "date"):
        parsed = normalize_date(row.get(key))
        if parsed:
            return parsed
    return None


def collect_path_values(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            if isinstance(nested, str) and ("path" in key.casefold() or nested.endswith((".md", ".markdown"))):
                found.append(nested)
            found.extend(collect_path_values(nested))
    elif isinstance(value, list):
        for nested in value:
            found.extend(collect_path_values(nested))
    elif isinstance(value, str):
        found.extend(path for path in extract_paths(value) if path.endswith((".md", ".markdown")))
    return dedupe(found)


def row_summary(row: dict[str, Any]) -> str:
    for key in ("summary", "message", "title", "description", "action", "content"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return compact(value, 360)
    return compact(json.dumps(row, ensure_ascii=False), 360)


def read_log_items(root: Path, target_date: str) -> list[dict[str, Any]]:
    log_path = root / "log.jsonl"
    try:
        lines = log_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []

    items: list[dict[str, Any]] = []
    for index, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict) or row_date(row) != target_date:
            continue
        summary = row_summary(row)
        paths = collect_path_values(row)
        title = row.get("title") if isinstance(row.get("title"), str) else summary
        items.append(
            {
                "id": stable_id(f"log:{index}:{summary}"),
                "kind": "log",
                "file": str(log_path),
                "path": paths[0] if paths else "log.jsonl",
                "paths": paths,
                "title": compact(str(title), 100),
                "summary": summary,
                "action": str(row.get("action") or "logged"),
                "evidence": [f"log.jsonl:{index}"],
                "text": json.dumps(row, ensure_ascii=False)[:4000],
            }
        )
    return items


def stable_id(value: str) -> str:
    return sha1(value.encode("utf-8")).hexdigest()[:12]


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def classify(summary: str, paths: list[str]) -> tuple[dict[str, bool], list[str]]:
    text = "\n".join([summary, *paths])
    has_error = bool(
        re.search(
            r"\b(error|exception|failed|failure|timeout|troubleshooting)\b|장애|오류|실패|트러블슈팅",
            text,
            re.I,
        )
    )
    flags = {
        "has_edit_signal": True,
        "has_git_signal": False,
        "has_test_signal": False,
        "has_error_signal": has_error,
    }
    hints = ["knowledge-base", *classification_hints(flags)]
    if any("troubleshooting" in path.casefold() or "trouble-shooting" in path.casefold() for path in paths):
        if "troubleshooting" not in hints:
            hints.append("troubleshooting")
    return flags, dedupe(hints)


def score_item(item: dict[str, Any], flags: dict[str, bool]) -> int:
    score = 55
    if item.get("kind") == "log":
        score += 5
    if any(str(value).startswith("created=") for value in item.get("evidence", [])):
        score += 5
    if flags.get("has_error_signal"):
        score += 20
    paths = item.get("paths") or [item.get("path")]
    if paths and paths != ["log.jsonl"]:
        score += 5
    return score


def candidate_from_item(item: dict[str, Any], target_date: str) -> dict[str, Any]:
    paths = dedupe([str(path) for path in (item.get("paths") or [item.get("path")]) if path])
    summary = str(item.get("summary") or "")
    flags, hints = classify(summary, paths)
    score = score_item(item, flags)
    title = compact(str(item.get("title") or item.get("path") or "KB 활동"), 100)
    result_snippets = [summary] if summary else []
    mentioned_paths = paths
    work_unit = {
        "work_unit_id": f"kb:{target_date}:{item['id']}:1",
        "title": f"KB - {title}",
        "user_request": None,
        "outcome": summary or "KB 활동 기록이 있으나 요약이 부족함.",
        "changed_paths": mentioned_paths,
        "mentioned_paths": mentioned_paths,
        "commands": [],
        "git_evidence": [],
        "test_evidence": [],
        "tool_names": [],
        "result_snippets": result_snippets,
        "final_answer": None,
        "classification_hints": hints,
        **flags,
        "confidence": confidence(score),
    }
    return {
        "session_id": None,
        "source": "kb",
        "file": item.get("file"),
        "started_at": target_date,
        "last_seen_at": target_date,
        "cwd": None,
        "title_hint": title,
        "user_intent_snippets": [],
        "result_snippets": result_snippets,
        "tool_names": [],
        "tool_call_count": 0,
        "mentioned_paths": mentioned_paths,
        "work_units": [work_unit],
        **flags,
        "classification_hints": hints,
        "importance_score": score,
        "first_pass_summary": f"KB에 '{title}' 관련 기록이 있음.",
        "confidence": confidence(score),
    }


def collect_items(root: Path, target_date: str) -> list[dict[str, Any]]:
    by_path: dict[str, dict[str, Any]] = {}
    loose_items: list[dict[str, Any]] = []

    for path in iter_markdown_files(root):
        item = read_doc_item(root, path, target_date)
        if item:
            by_path[str(item["path"])] = item

    for item in read_log_items(root, target_date):
        paths = [path for path in item.get("paths", []) if path in by_path]
        if paths:
            for path in paths:
                existing = by_path[path]
                existing["summary"] = compact(f"{existing['summary']} / {item['summary']}", 360)
                existing["evidence"] = dedupe([*existing.get("evidence", []), *item.get("evidence", [])])
        else:
            loose_items.append(item)

    return [*by_path.values(), *loose_items]


def empty_result(target_date: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "date": target_date,
        "source": "kb",
        "stage": "first-pass-collection",
        "generated_at": now_iso(),
        "candidates": [],
        "supporting": [],
        "rejected": [],
    }


def emit(result: dict[str, Any], output: str | None, stdout: bool, emit_empty: bool) -> None:
    has_any = any(result.get(key) for key in ("candidates", "supporting", "rejected"))
    if not has_any and not emit_empty:
        return
    if stdout:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    path = Path(output).expanduser() if output else default_output_path("kb", str(result["date"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="KB 1차 후보 카드를 선택적으로 수집한다.")
    parser.add_argument("--date", required=True, help="대상 날짜 YYYY-MM-DD")
    parser.add_argument("--kb-root", help="KB root 절대 경로. 없으면 ~/.config/kb 설정을 사용")
    parser.add_argument("--output", help="출력 JSON 경로. 기본값은 ~/.daily-work-log/YYYY/YYYY-MM-DD/kb-candidates.json")
    parser.add_argument("--stdout", action="store_true", help="파일에 쓰지 않고 stdout으로 출력")
    parser.add_argument("--emit-empty", action="store_true", help="KB가 없거나 후보가 없어도 빈 JSON을 출력")
    args = parser.parse_args()

    date.fromisoformat(args.date)
    root = resolve_kb_root(args.kb_root)
    if not root:
        emit(empty_result(args.date), args.output, args.stdout, args.emit_empty)
        return 0

    candidates, supporting, rejected = split_candidates(
        [candidate_from_item(item, args.date) for item in collect_items(root, args.date)]
    )
    result = {
        "schema_version": SCHEMA_VERSION,
        "date": args.date,
        "source": "kb",
        "stage": "first-pass-collection",
        "generated_at": now_iso(),
        "candidates": candidates,
        "supporting": supporting,
        "rejected": rejected,
    }
    emit(result, args.output, args.stdout, args.emit_empty)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
