#!/usr/bin/env python3
"""Build numbered daily-work-log candidates from first-pass candidate JSON files."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from first_pass_candidate_utils import DEFAULT_STATE_ROOT, compact, default_output_path, now_iso, project_name


SCHEMA_VERSION = "daily-work-log.numbered-candidates.v1"

NOISE_RE = re.compile(
    r"(<turn_aborted>|<local-command|local-command-|continue from where you left off|please run /login|login successful)",
    re.I,
)
TOPIC_RULES: list[tuple[str, str, str]] = [
    (
        "secret-config-transition",
        "AWS secret/config 전환 검토",
        r"secret manager|secretsmanager|parameter store|parameterstore|securestring|aws sso|iam|credential|access key|spring cloud aws",
    ),
    (
        "config-server-profile",
        "Config Server / Spring profile 구조 조사",
        r"config(?:\s|-)server|config\.example|aws-valkey|spring\.config\.import|spring profile|resources-\{?profile\}?|classpath",
    ),
    (
        "checkout-custom-remarks",
        "checkout custom_remarks 오류 조사",
        r"custom_remarks|multiplerooms|roomguest|data truncation|confirmcheckout|checkout|판매 기간",
    ),
]


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def candidate_paths(target_date: str, state_root: Path) -> list[Path]:
    return [
        default_output_path("codex", target_date, state_root),
        default_output_path("claude", target_date, state_root),
        default_output_path("kb", target_date, state_root),
    ]


def text_blob(candidate: dict[str, Any], unit: dict[str, Any]) -> str:
    parts = [
        candidate.get("title_hint"),
        candidate.get("first_pass_summary"),
        unit.get("title"),
        unit.get("user_request"),
        unit.get("outcome"),
        " ".join(str(item) for item in unit.get("mentioned_paths") or []),
    ]
    return " ".join(str(part) for part in parts if part)


def topic_for(candidate: dict[str, Any], unit: dict[str, Any]) -> tuple[str, str]:
    blob = text_blob(candidate, unit)
    project = project_name(candidate.get("cwd"))
    for key, label, pattern in TOPIC_RULES:
        if re.search(pattern, blob, re.I):
            return f"{project}:{key}", f"{project} - {label}"
    if candidate.get("source") == "kb":
        title = unit.get("title") or candidate.get("title_hint") or "KB 후보"
        return f"kb:{title}", str(title)
    session_id = candidate.get("session_id") or candidate.get("file") or "unknown"
    return f"{project}:session:{session_id}", str(candidate.get("title_hint") or unit.get("title") or project)


def is_noise(unit: dict[str, Any]) -> bool:
    raw = " ".join(str(unit.get(key) or "") for key in ("title", "user_request", "outcome"))
    return bool(NOISE_RE.search(raw))


def add_unique(values: list[Any], new_values: list[Any], limit: int | None = None) -> None:
    seen = {json.dumps(value, ensure_ascii=False, sort_keys=True) for value in values}
    for value in new_values:
        marker = json.dumps(value, ensure_ascii=False, sort_keys=True)
        if marker in seen:
            continue
        seen.add(marker)
        values.append(value)
        if limit is not None and len(values) >= limit:
            return


def collect_groups(first_pass: list[dict[str, Any]], include_supporting: bool) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    sections = ["candidates", "supporting"] if include_supporting else ["candidates"]
    for source_doc in first_pass:
        source = source_doc.get("source")
        for section in sections:
            for candidate in source_doc.get(section) or []:
                if not isinstance(candidate, dict):
                    continue
                units = [unit for unit in candidate.get("work_units") or [] if isinstance(unit, dict) and not is_noise(unit)]
                for unit in units:
                    key, title = topic_for(candidate, unit)
                    group = groups.setdefault(
                        key,
                        {
                            "topic_key": key,
                            "title": title,
                            "source_projects": [],
                            "candidate_refs": [],
                            "kb_paths": [],
                            "work_unit_summaries": [],
                            "evidence_hints": [],
                            "importance_score": 0,
                            "confidence": "low",
                        },
                    )
                    score = int(candidate.get("importance_score") or 0)
                    group["importance_score"] += score
                    if score >= 80:
                        group["confidence"] = "high"
                    elif score >= 50 and group["confidence"] != "high":
                        group["confidence"] = "medium"
                    cwd = candidate.get("cwd")
                    if isinstance(cwd, str) and cwd:
                        add_unique(group["source_projects"], [cwd], limit=8)
                    ref = {
                        "source": source,
                        "session_id": candidate.get("session_id"),
                        "file": candidate.get("file"),
                        "work_unit_ids": [unit.get("work_unit_id")],
                    }
                    add_unique(group["candidate_refs"], [ref])
                    paths = unit.get("mentioned_paths") or []
                    if source == "kb":
                        add_unique(group["kb_paths"], paths, limit=12)
                    add_unique(group["evidence_hints"], paths, limit=20)
                    group["work_unit_summaries"].append(
                        {
                            "work_unit_id": unit.get("work_unit_id"),
                            "request": compact(str(unit.get("user_request") or ""), 180),
                            "outcome": compact(str(unit.get("outcome") or ""), 220),
                            "classification_hints": unit.get("classification_hints") or [],
                        }
                    )
    return sorted(groups.values(), key=lambda item: int(item.get("importance_score") or 0), reverse=True)


def build_result(target_date: str, state_root: Path, top_limit: int, other_limit: int, include_supporting: bool) -> dict[str, Any]:
    paths = candidate_paths(target_date, state_root)
    first_pass = [doc for path in paths if (doc := load_json(path))]
    groups = collect_groups(first_pass, include_supporting)
    displayed_limit = top_limit + other_limit
    numbered = []
    for index, group in enumerate(groups[:displayed_limit], start=1):
        group = dict(group)
        group["number"] = index
        group["list_section"] = "top" if index <= top_limit else "other"
        numbered.append(group)
    return {
        "schema_version": SCHEMA_VERSION,
        "date": target_date,
        "stage": "numbered-candidates",
        "generated_at": now_iso(),
        "source_files": [str(path) for path in paths if path.exists()],
        "top_limit": top_limit,
        "other_limit": other_limit,
        "displayed_candidates": numbered,
        "hidden_candidate_count": max(0, len(groups) - displayed_limit),
    }


def write_result(result: dict[str, Any], output: str | None, stdout: bool) -> None:
    if stdout:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if output:
        path = Path(output).expanduser()
    else:
        date = str(result["date"])
        path = DEFAULT_STATE_ROOT / date[:4] / date / "numbered-candidates.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="1차 후보 JSON에서 번호가 부여된 후보 목록을 만든다.")
    parser.add_argument("--date", required=True, help="대상 날짜 YYYY-MM-DD")
    parser.add_argument("--state-root", default=str(DEFAULT_STATE_ROOT), help="기본값: ~/.daily-work-log")
    parser.add_argument("--top-limit", type=int, default=10)
    parser.add_argument("--other-limit", type=int, default=3)
    parser.add_argument("--include-supporting", action="store_true")
    parser.add_argument("--output", help="기본값은 ~/.daily-work-log/YYYY/YYYY-MM-DD/numbered-candidates.json")
    parser.add_argument("--stdout", action="store_true")
    args = parser.parse_args()

    result = build_result(args.date, Path(args.state_root).expanduser(), args.top_limit, args.other_limit, args.include_supporting)
    write_result(result, args.output, args.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
