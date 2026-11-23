#!/usr/bin/env python3
"""하루치 수집을 한 번에 돌리고, 에이전트가 읽을 근거 파일 evidence.md를 만든다."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from build_numbered_candidates import DEFAULT_OTHER_LIMIT, DEFAULT_TOP_LIMIT
from first_pass_candidate_utils import DEFAULT_STATE_ROOT

SCRIPTS_DIR = Path(__file__).resolve().parent
EDITED_FILES_LIMIT = 30
LINKS_LIMIT = 15
# 임시 폴더에 쓴 파일은 다시 찾을 수 없으므로 고친 파일 목록에서 뺀다.
TEMP_PATH_PREFIXES = ("/tmp/", "/private/tmp/", "/var/folders/", "/private/var/folders/")
# 응답 없이 끝난 단위의 자리 채움 문구. 근거가 아니므로 출력하지 않는다.
PLACEHOLDER_OUTCOMES = ("결과 힌트가 부족함.", "신호가 있으나 최종 응답은 확인되지 않음.")


def load_config(state_root: Path) -> dict[str, Any]:
    try:
        data = json.loads((state_root / "config.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def impact_items(config: dict[str, Any]) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for item in config.get("impact-items") or []:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if isinstance(name, str) and name.strip():
            description = item.get("description")
            items.append((name.strip(), description.strip() if isinstance(description, str) else ""))
    return items


def run_script(name: str, *args: str) -> None:
    subprocess.run([sys.executable, str(SCRIPTS_DIR / name), *args], check=True, stdout=subprocess.DEVNULL)


def run_pipeline(target_date: str, state_root: Path, top_limit: int, other_limit: int, include_supporting: bool) -> int:
    """수집부터 digest까지 돌리고 표시 후보 수를 돌려준다."""
    common = ["--date", target_date, "--state-root", str(state_root)]
    supporting = ["--include-supporting"] if include_supporting else []
    run_script("collect_codex_first_pass_candidates.py", *common, *supporting)
    run_script("collect_claude_first_pass_candidates.py", *common, *supporting)
    run_script(
        "build_numbered_candidates.py",
        *common,
        "--top-limit",
        str(top_limit),
        "--other-limit",
        str(other_limit),
        *supporting,
    )
    day_dir = state_root / target_date[:4] / target_date
    numbered = json.loads((day_dir / "numbered-candidates.json").read_text(encoding="utf-8"))
    count = len(numbered.get("displayed_candidates") or [])
    if count:
        run_script("build_second_pass_digest.py", *common, "--selection", f"1-{count}")
    return count


def local_time(value: Any) -> str:
    if not isinstance(value, str) or not value:
        return "--:--"
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return "--:--"
    return parsed.astimezone().strftime("%H:%M")


def short_path(path: str, roots: list[str]) -> str:
    for root in roots:
        if root and path.startswith(root.rstrip("/") + "/"):
            return path[len(root.rstrip("/")) + 1 :]
    return path


def collect_unique(units: list[dict[str, Any]], key: str, limit: int, skip_prefixes: tuple[str, ...] = ()) -> tuple[list[str], int]:
    values: list[str] = []
    for unit in units:
        for value in unit.get(key) or []:
            if isinstance(value, str) and value not in values and not value.startswith(skip_prefixes):
                values.append(value)
    return values[:limit], max(0, len(values) - limit)


def is_placeholder(outcome: str) -> bool:
    return not outcome or outcome.endswith(PLACEHOLDER_OUTCOMES)


def render_group(detail: dict[str, Any], list_section: str) -> list[str]:
    units = [unit for unit in detail.get("work_units") or [] if isinstance(unit, dict)]
    projects = [path for path in detail.get("source_projects") or [] if isinstance(path, str)]
    lines = [f"## 후보 {detail.get('group_id')} | {list_section} | {detail.get('title')}", ""]
    if projects:
        lines.append(f"작업 폴더: {', '.join(projects)}")
    delivery, _ = collect_unique(units, "delivery_commands", 20)
    if delivery:
        lines.append(f"커밋·푸시·PR 명령: {', '.join(delivery)}")
    edited, more = collect_unique(units, "edited_files", EDITED_FILES_LIMIT, TEMP_PATH_PREFIXES)
    if edited:
        suffix = f" 외 {more}개" if more else ""
        lines.append(f"고친 파일: {', '.join(short_path(path, projects) for path in edited)}{suffix}")
    links, more = collect_unique(units, "links", LINKS_LIMIT)
    if links:
        suffix = f" 외 {more}개" if more else ""
        lines.append(f"응답에 나온 링크: {' '.join(links)}{suffix}")
    for unit in units:
        lines.append("")
        lines.append(f"- {local_time(unit.get('started_at'))} | {unit.get('user_request') or '(요청 없음)'}")
        outcome = str(unit.get("outcome") or "")
        if not is_placeholder(outcome):
            lines.append(f"  -> {outcome}")
    lines.append("")
    return lines


def render_evidence(target_date: str, digest: dict[str, Any], numbered: dict[str, Any], impacts: list[tuple[str, str]]) -> str:
    details = [detail for detail in digest.get("selected_details") or [] if isinstance(detail, dict)]
    sections = {str(item.get("number")): str(item.get("list_section") or "top") for item in numbered.get("displayed_candidates") or []}
    lines = [f"# {target_date} 근거", ""]
    hidden = int(numbered.get("hidden_candidate_count") or 0)
    lines.append(f"표시 후보 {len(details)}개" + (f", 한도로 숨긴 후보 {hidden}개" if hidden else ""))
    lines.append("각 단위는 `- 시작 시각 | 사용자 요청`과 `-> 마지막 응답` 두 줄이다. 응답 줄이 없으면 응답 없이 끝난 단위다.")
    lines.append("")
    if impacts:
        lines.append("## impact-items")
        lines.append("")
        lines.extend(f"- {name}: {description}" for name, description in impacts)
        lines.append("")
    lines.append("## 후보 목록")
    lines.append("")
    for detail in details:
        group_id = str(detail.get("group_id"))
        lines.append(f"- {group_id} | {sections.get(group_id, 'top')} | 단위 {len(detail.get('work_units') or [])}개 | {detail.get('title')}")
    lines.append("")
    for detail in details:
        lines.extend(render_group(detail, sections.get(str(detail.get("group_id")), "top")))
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="하루치 수집을 돌리고 evidence.md를 만든다.")
    parser.add_argument("--date", required=True, help="대상 날짜 YYYY-MM-DD")
    parser.add_argument("--state-root", default=str(DEFAULT_STATE_ROOT), help="기본값: ~/.daily-work-log")
    parser.add_argument("--top-limit", type=int, help=f"기본값: config.json의 top-limit, 없으면 {DEFAULT_TOP_LIMIT}")
    parser.add_argument("--other-limit", type=int, help=f"기본값: config.json의 other-limit, 없으면 {DEFAULT_OTHER_LIMIT}")
    parser.add_argument("--include-supporting", action="store_true", help="기본값: config.json의 include-supporting")
    parser.add_argument("--render-only", action="store_true", help="수집을 다시 돌리지 않고 저장된 digest로 evidence.md만 다시 만든다")
    args = parser.parse_args()

    state_root = Path(args.state_root).expanduser()
    config = load_config(state_root)
    day_dir = state_root / args.date[:4] / args.date
    if not args.render_only:
        count = run_pipeline(
            args.date,
            state_root,
            args.top_limit if args.top_limit is not None else int(config.get("top-limit") or DEFAULT_TOP_LIMIT),
            args.other_limit if args.other_limit is not None else int(config.get("other-limit") or DEFAULT_OTHER_LIMIT),
            args.include_supporting or config.get("include-supporting") is True,
        )
        if not count:
            (day_dir / "evidence.md").unlink(missing_ok=True)
            print("candidates: 0")
            return 0

    numbered = json.loads((day_dir / "numbered-candidates.json").read_text(encoding="utf-8"))
    digest = json.loads((day_dir / "second-pass-digest.json").read_text(encoding="utf-8"))
    text = render_evidence(args.date, digest, numbered, impact_items(config))
    path = day_dir / "evidence.md"
    path.write_text(text, encoding="utf-8")
    print(f"candidates: {len(digest.get('selected_details') or [])}")
    print(f"evidence: {path}")
    print(f"lines: {text.count(chr(10))}")
    print(f"chars: {len(text)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
