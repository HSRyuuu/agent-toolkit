#!/usr/bin/env python3
"""Build a final-info.json skeleton from a second-pass digest."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from first_pass_candidate_utils import DEFAULT_STATE_ROOT, compact, now_iso, project_name


SCHEMA_VERSION = "daily-work-log.final-info.v1"

TECH_PATTERNS: list[tuple[str, str]] = [
    ("spring.config.import", "Spring Boot"),
    ("spring profile", "Spring profiles"),
    ("config server", "Spring Cloud Config"),
    ("config.tbz", "Spring Cloud Config"),
    ("aws-valkey", "AWS Valkey"),
    ("secrets manager", "AWS Secrets Manager"),
    ("parameter store", "AWS Systems Manager Parameter Store"),
    ("securestring", "AWS Systems Manager Parameter Store"),
    ("aws sso", "AWS SSO"),
    ("iam", "AWS IAM"),
    ("custom_remarks", "MySQL"),
    ("data truncation", "MySQL"),
    ("confirmcheckout", "checkout"),
    ("multiplerooms", "checkout"),
    ("roomguest", "checkout"),
]


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


def default_digest_path(target_date: str, state_root: Path) -> Path:
    return state_root / target_date[:4] / target_date / "second-pass-digest.json"


def default_final_info_path(target_date: str, state_root: Path) -> Path:
    return state_root / target_date[:4] / target_date / "final-info.json"


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


def slugify(text: str, fallback: str) -> str:
    value = text.lower()
    value = re.sub(r"[^a-z0-9가-힣]+", "-", value).strip("-")
    return value[:80] or fallback


def infer_category(detail: dict[str, Any]) -> str:
    title = str(detail.get("title") or "").lower()
    blob = json.dumps(detail, ensure_ascii=False).lower()
    if any(word in blob for word in ("data truncation", "error", "exception", "판매 기간", "트러블슈팅", "원인")):
        return "troubleshooting"
    if any(word in title for word in ("구조", "개념", "profile", "config server", "문서화", "learning")):
        return "learning"
    if any(word in blob for word in ("전환", "검토", "iam", "sso", "parameter store", "secrets manager", "결정", "decision")):
        return "decision"
    if any(word in blob for word in ("구조", "개념", "profile", "config server", "문서화", "learning")):
        return "learning"
    return "work-item"


def infer_tech_stack(text: str) -> list[str]:
    values: list[str] = []
    lowered = text.lower()
    for pattern, label in TECH_PATTERNS:
        if pattern in lowered and label not in values:
            values.append(label)
    return values


def infer_modules(paths: list[str], title: str) -> list[str]:
    modules: list[str] = []
    title_parts = re.split(r"\s+-\s+|\s+", title)
    if title_parts:
        first = title_parts[0].strip()
        if first and first not in modules:
            modules.append(first)
    lowered_title = title.lower()
    for keyword in ("config-server", "spring-profile", "secret-manager", "checkout", "custom_remarks"):
        if keyword.replace("-", " ") in lowered_title or keyword in lowered_title:
            modules.append(keyword)
    return modules


def selected_candidate_by_group(digest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item.get("group_id")): item for item in digest.get("selected_candidates") or []}


def build_item(detail: dict[str, Any], selected_candidate: dict[str, Any]) -> dict[str, Any]:
    group_id = str(detail.get("group_id"))
    title = str(detail.get("title") or selected_candidate.get("title") or f"선택 후보 {group_id}")
    work_units = [unit for unit in detail.get("work_units") or [] if isinstance(unit, dict)]
    evidence = detail.get("evidence_paths") or {}
    project_files = list(evidence.get("project_files") or [])
    source_projects = [path for path in detail.get("source_projects") or [] if isinstance(path, str)]
    repo_names = [project_name(path) for path in source_projects]

    text_blob = json.dumps({"title": title, "work_units": work_units, "detail": detail}, ensure_ascii=False)
    tech_stack = infer_tech_stack(text_blob)
    modules = infer_modules(project_files, title)
    include_keywords: list[str] = []
    add_unique(include_keywords, tech_stack + modules[:4], limit=12)
    what_i_did = []
    for unit in work_units[:5]:
        summary = unit.get("outcome") or unit.get("user_request") or unit.get("title")
        if summary:
            what_i_did.append(compact(str(summary), 220))
    if not what_i_did:
        what_i_did.append(compact(str(detail.get("digest_summary") or title), 220))

    return {
        "item_id": slugify(title, f"selected-{group_id}"),
        "selected_group_id": group_id,
        "title": title,
        "category": infer_category(detail),
        "summary": compact(str(detail.get("digest_summary") or title), 280),
        "memory_cue": compact(f"{title}: {detail.get('digest_summary') or ''}", 240),
        "what_i_did": what_i_did,
        "why_it_mattered": "",
        "technical_context": {
            "repo_names": repo_names,
            "codebase_paths": source_projects,
            "modules": modules,
            "systems": [],
            "tech_stack": tech_stack,
            "context_links": [],
        },
        "decisions": [],
        "learnings": [],
        "troubleshooting": [],
        "follow_ups": [],
        "uncertainties": [],
        "markdown_hints": {
            "detail_level": "normal",
            "include_keywords": include_keywords,
            "avoid_details": ["회사 소스코드 원문", "원시 로그 전문", "secret 또는 credential", "고객 식별자"],
        },
        "evidence_paths": {
            "session_files": evidence.get("session_files") or [],
            "kb_documents": evidence.get("kb_documents") or [],
            "project_files": project_files,
            "notes": evidence.get("notes") or [],
        },
        "safe_evidence_summary": [
            compact(str(unit.get("title") or unit.get("user_request") or ""), 180)
            for unit in work_units[:6]
            if unit.get("title") or unit.get("user_request")
        ],
        "confidence": detail.get("confidence") or selected_candidate.get("confidence") or "medium",
    }


def build_final_info(digest: dict[str, Any], digest_path: Path | None = None) -> dict[str, Any]:
    by_group = selected_candidate_by_group(digest)
    selected_items = [
        build_item(detail, by_group.get(str(detail.get("group_id")), {}))
        for detail in digest.get("selected_details") or []
        if isinstance(detail, dict)
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "date": digest.get("date"),
        "generated_at": now_iso(),
        "markdown_generation_policy": {
            "purpose": "사용자가 하루 뒤/몇 주 뒤에 읽어도 어떤 일을 했는지 기억할 수 있는 일일 업무 기록을 만든다.",
            "include": [
                "업무를 식별할 수 있는 프로젝트, repo, 모듈, 시스템, 기술 스택",
                "조사/판단/문서화/트러블슈팅의 높은 수준 요약",
                "다시 찾아볼 수 있는 근거 파일 경로와 링크",
            ],
            "exclude": [
                "구체적인 회사 소스코드",
                "긴 원문 로그",
                "고객 식별자",
                "인증 정보와 secret 원문",
                "운영 데이터 원문",
            ],
        },
        "source_files": {
            "second_pass_digest": str(digest_path) if digest_path else None,
            "numbered_candidates": digest.get("source_files", {}).get("numbered_candidates"),
            "first_pass": digest.get("source_files", {}).get("first_pass") or [],
        },
        "selected_candidates": digest.get("selected_candidates") or [],
        "selected_items": selected_items,
        "final_markdown_plan": {
            "target_path_pattern": "<journal-root>/daily-work-log/YYYY/MM/YYYY-MM-DD.md",
            "frontmatter_required": {
                "date": digest.get("date"),
                "type": "daily-work-log",
                "summary": "",
                "tags": [],
            },
            "write_guidance": [
                "구체적인 코드나 원시 로그 대신, 사용자가 기억을 되살릴 수 있는 업무 식별 정보와 높은 수준의 요약을 쓴다.",
                "관련 repo, 모듈, 기술 스택, KB/세션/문서 경로는 남긴다.",
                "최종 tags는 문서를 다 쓴 뒤 검색 키워드 관점으로 채운다.",
            ],
        },
    }


def write_result(result: dict[str, Any], output: str | None, stdout: bool, state_root: Path) -> None:
    if stdout:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    path = Path(output).expanduser() if output else default_final_info_path(str(result["date"]), state_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="second-pass-digest.json에서 final-info.json 초안을 만든다.")
    parser.add_argument("--date", required=True, help="대상 날짜 YYYY-MM-DD")
    parser.add_argument("--state-root", default=str(DEFAULT_STATE_ROOT), help="기본값: ~/.daily-work-log")
    parser.add_argument("--digest", help="기본값: ~/.daily-work-log/YYYY/YYYY-MM-DD/second-pass-digest.json")
    parser.add_argument("--output", help="기본값: ~/.daily-work-log/YYYY/YYYY-MM-DD/final-info.json")
    parser.add_argument("--stdout", action="store_true")
    args = parser.parse_args()

    state_root = Path(args.state_root).expanduser()
    digest_path = Path(args.digest).expanduser() if args.digest else default_digest_path(args.date, state_root)
    result = build_final_info(load_json(digest_path), digest_path)
    write_result(result, args.output, args.stdout, state_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
