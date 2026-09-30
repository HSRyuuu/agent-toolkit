#!/usr/bin/env python3
"""Build a compact second-pass digest for selected daily-work-log candidates."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from first_pass_candidate_utils import DEFAULT_STATE_ROOT, compact, default_output_path, now_iso, project_name


SCHEMA_VERSION = "daily-work-log.second-pass-digest.v1"


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SystemExit(f"cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def default_numbered_path(target_date: str, state_root: Path) -> Path:
    return state_root / target_date[:4] / target_date / "numbered-candidates.json"


def default_digest_path(target_date: str, state_root: Path) -> Path:
    return state_root / target_date[:4] / target_date / "second-pass-digest.json"


def parse_selection(value: str) -> list[int]:
    numbers: list[int] = []
    seen: set[int] = set()
    for raw_part in re.split(r"[,\s]+", value.strip()):
        if not raw_part:
            continue
        range_match = re.fullmatch(r"(\d+)-(\d+)", raw_part)
        if range_match:
            start, end = (int(range_match.group(1)), int(range_match.group(2)))
            step = 1 if start <= end else -1
            expanded = range(start, end + step, step)
        elif raw_part.isdigit():
            expanded = [int(raw_part)]
        else:
            raise SystemExit(f"invalid selection token: {raw_part}")
        for number in expanded:
            if number not in seen:
                seen.add(number)
                numbers.append(number)
    if not numbers:
        raise SystemExit("empty selection")
    return numbers


def candidate_paths(target_date: str, state_root: Path, source_files: list[Any]) -> list[Path]:
    paths = [Path(str(path)).expanduser() for path in source_files if isinstance(path, str)]
    if paths:
        return paths
    return [
        default_output_path("codex", target_date, state_root),
        default_output_path("claude", target_date, state_root),
        default_output_path("kb", target_date, state_root),
    ]


def first_pass_docs(target_date: str, state_root: Path, numbered: dict[str, Any]) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for path in candidate_paths(target_date, state_root, numbered.get("source_files") or []):
        if path.exists():
            docs.append(load_json(path))
    return docs


def normalize_ref(candidate: dict[str, Any], unit: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": candidate.get("source"),
        "session_id": candidate.get("session_id"),
        "file": candidate.get("file"),
        "work_unit_id": unit.get("work_unit_id"),
    }


def ref_key(ref: dict[str, Any]) -> tuple[Any, Any, Any, Any]:
    return (ref.get("source"), ref.get("session_id"), ref.get("file"), ref.get("work_unit_id"))


def build_unit_index(first_pass: list[dict[str, Any]]) -> dict[tuple[Any, Any, Any, Any], dict[str, Any]]:
    index: dict[tuple[Any, Any, Any, Any], dict[str, Any]] = {}
    for doc in first_pass:
        for section in ("candidates", "supporting", "rejected"):
            for candidate in doc.get(section) or []:
                if not isinstance(candidate, dict):
                    continue
                for unit in candidate.get("work_units") or []:
                    if not isinstance(unit, dict):
                        continue
                    ref = normalize_ref(candidate, unit)
                    key = ref_key(ref)
                    index[key] = {
                        "candidate": candidate,
                        "work_unit": unit,
                        "section": section,
                        "source": candidate.get("source") or doc.get("source"),
                    }
    return index


def add_unique(values: list[Any], new_values: list[Any], limit: int | None = None) -> None:
    seen = {json.dumps(value, ensure_ascii=False, sort_keys=True) for value in values}
    for value in new_values:
        if value in (None, "", []):
            continue
        marker = json.dumps(value, ensure_ascii=False, sort_keys=True)
        if marker in seen:
            continue
        seen.add(marker)
        values.append(value)
        if limit is not None and len(values) >= limit:
            return


def selected_groups(numbered: dict[str, Any], selection: list[int]) -> list[dict[str, Any]]:
    by_number = {int(item.get("number")): item for item in numbered.get("displayed_candidates") or [] if item.get("number") is not None}
    missing = [number for number in selection if number not in by_number]
    if missing:
        raise SystemExit(f"selection not found in numbered candidates: {missing}")
    groups: list[dict[str, Any]] = []
    for number in selection:
        group = dict(by_number[number])
        group["selected_number"] = number
        groups.append(group)
    return groups


def compact_unit(unit: dict[str, Any], candidate: dict[str, Any], source: str | None, section: str) -> dict[str, Any]:
    return {
        "source": source,
        "section": section,
        "session_id": candidate.get("session_id"),
        "session_file": candidate.get("file"),
        "cwd": candidate.get("cwd"),
        "project": project_name(candidate.get("cwd")),
        "work_unit_id": unit.get("work_unit_id"),
        "title": compact(str(unit.get("title") or ""), 140),
        "user_request": compact(str(unit.get("user_request") or ""), 500),
        "outcome": compact(str(unit.get("outcome") or ""), 700),
        "classification_hints": unit.get("classification_hints") or [],
        "mentioned_paths": (unit.get("mentioned_paths") or [])[:30],
        "changed_paths": (unit.get("changed_paths") or [])[:30],
        "commands": (unit.get("commands") or [])[:20],
        "git_evidence": (unit.get("git_evidence") or [])[:12],
        "test_evidence": (unit.get("test_evidence") or [])[:12],
        "confidence": unit.get("confidence") or candidate.get("confidence"),
    }


def compact_group(group: dict[str, Any]) -> dict[str, Any]:
    return {
        "group_id": str(group.get("number")),
        "title": group.get("title"),
        "list_section": group.get("list_section"),
        "topic_key": group.get("topic_key"),
        "selection_note": "사용자가 오늘 일지에 포함하도록 선택함",
        "candidate_refs": group.get("candidate_refs") or [],
        "kb_paths": group.get("kb_paths") or [],
        "source_projects": group.get("source_projects") or [],
        "confidence": group.get("confidence"),
    }


def build_digest(target_date: str, state_root: Path, numbered_path: Path, selection_text: str) -> dict[str, Any]:
    numbered = load_json(numbered_path)
    selection = parse_selection(selection_text)
    groups = selected_groups(numbered, selection)
    first_pass = first_pass_docs(target_date, state_root, numbered)
    unit_index = build_unit_index(first_pass)

    selected_candidates = [compact_group(group) for group in groups]
    selected_details: list[dict[str, Any]] = []
    unresolved_refs: list[dict[str, Any]] = []

    for group in groups:
        work_units: list[dict[str, Any]] = []
        session_files: list[str] = []
        kb_documents: list[str] = []
        project_files: list[str] = []
        source_projects: list[str] = []
        commands: list[str] = []
        tests: list[str] = []
        git_evidence: list[str] = []

        for ref in group.get("candidate_refs") or []:
            work_unit_ids = ref.get("work_unit_ids") or []
            for work_unit_id in work_unit_ids:
                lookup = {
                    "source": ref.get("source"),
                    "session_id": ref.get("session_id"),
                    "file": ref.get("file"),
                    "work_unit_id": work_unit_id,
                }
                item = unit_index.get(ref_key(lookup))
                if item is None:
                    unresolved_refs.append(lookup)
                    continue
                candidate = item["candidate"]
                unit = item["work_unit"]
                compacted = compact_unit(unit, candidate, item.get("source"), str(item.get("section") or ""))
                work_units.append(compacted)
                add_unique(session_files, [candidate.get("file")], limit=12)
                add_unique(source_projects, [candidate.get("cwd")], limit=12)
                add_unique(project_files, compacted["mentioned_paths"], limit=50)
                add_unique(project_files, compacted["changed_paths"], limit=50)
                add_unique(commands, compacted["commands"], limit=30)
                add_unique(tests, compacted["test_evidence"], limit=20)
                add_unique(git_evidence, compacted["git_evidence"], limit=20)

        add_unique(kb_documents, group.get("kb_paths") or [], limit=30)
        selected_details.append(
            {
                "group_id": str(group.get("number")),
                "title": group.get("title"),
                "topic_key": group.get("topic_key"),
                "source_projects": source_projects or group.get("source_projects") or [],
                "work_units": work_units,
                "evidence_paths": {
                    "session_files": session_files,
                    "kb_documents": kb_documents,
                    "project_files": project_files,
                    "notes": [],
                },
                "execution_evidence": {
                    "commands": commands,
                    "test_evidence": tests,
                    "git_evidence": git_evidence,
                },
                "digest_summary": summarize_work_units(group, work_units),
                "confidence": group.get("confidence"),
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "date": target_date,
        "stage": "second-pass-digest",
        "generated_at": now_iso(),
        "source_files": {
            "numbered_candidates": str(numbered_path),
            "first_pass": [str(path) for path in candidate_paths(target_date, state_root, numbered.get("source_files") or []) if path.exists()],
        },
        "selection": selection,
        "selected_candidates": selected_candidates,
        "selected_details": selected_details,
        "unresolved_refs": unresolved_refs,
    }


def summarize_work_units(group: dict[str, Any], work_units: list[dict[str, Any]]) -> str:
    if not work_units:
        return compact(str(group.get("title") or ""), 220)
    outcomes = [str(unit.get("outcome") or "") for unit in work_units if unit.get("outcome")]
    if outcomes:
        return compact(" / ".join(outcomes[:3]), 420)
    requests = [str(unit.get("user_request") or "") for unit in work_units if unit.get("user_request")]
    return compact(" / ".join(requests[:3]), 420)


def write_result(result: dict[str, Any], output: str | None, stdout: bool, state_root: Path) -> None:
    if stdout:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    path = Path(output).expanduser() if output else default_digest_path(str(result["date"]), state_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="선택한 번호의 2차 상세 탐색용 digest JSON을 만든다.")
    parser.add_argument("--date", required=True, help="대상 날짜 YYYY-MM-DD")
    parser.add_argument("--selection", required=True, help="선택 번호. 예: 4,5,6 또는 4-6")
    parser.add_argument("--state-root", default=str(DEFAULT_STATE_ROOT), help="기본값: ~/.daily-work-log")
    parser.add_argument("--numbered", help="기본값: ~/.daily-work-log/YYYY/YYYY-MM-DD/numbered-candidates.json")
    parser.add_argument("--output", help="기본값: ~/.daily-work-log/YYYY/YYYY-MM-DD/second-pass-digest.json")
    parser.add_argument("--stdout", action="store_true")
    args = parser.parse_args()

    state_root = Path(args.state_root).expanduser()
    numbered_path = Path(args.numbered).expanduser() if args.numbered else default_numbered_path(args.date, state_root)
    result = build_digest(args.date, state_root, numbered_path, args.selection)
    write_result(result, args.output, args.stdout, state_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
