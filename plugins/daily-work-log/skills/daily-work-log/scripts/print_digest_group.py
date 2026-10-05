#!/usr/bin/env python3
"""second-pass-digest.json의 묶음 하나를 시간순 work unit 목록으로 출력한다."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from first_pass_candidate_utils import DEFAULT_STATE_ROOT


def main() -> int:
    parser = argparse.ArgumentParser(description="digest 묶음의 work unit을 시간순으로 출력한다.")
    parser.add_argument("--date", required=True, help="대상 날짜 YYYY-MM-DD")
    parser.add_argument("--group", help="출력할 group_id. 없으면 묶음 목록만 출력")
    parser.add_argument("--state-root", default=str(DEFAULT_STATE_ROOT), help="기본값: ~/.daily-work-log")
    args = parser.parse_args()

    path = Path(args.state_root).expanduser() / args.date[:4] / args.date / "second-pass-digest.json"
    digest = json.loads(path.read_text(encoding="utf-8"))
    details = digest.get("selected_details") or []

    if not args.group:
        for detail in details:
            print(f"{detail.get('group_id')}\t{len(detail.get('work_units') or [])} units\t{detail.get('title')}")
        return 0

    for detail in details:
        if str(detail.get("group_id")) != args.group:
            continue
        print(f"## group {detail.get('group_id')} {detail.get('title')}")
        for unit in detail.get("work_units") or []:
            print(f"\n- {unit.get('started_at')} | {unit.get('project')} | {unit.get('user_request')}")
            print(f"  -> {unit.get('outcome')}")
        return 0
    raise SystemExit(f"group not found: {args.group}")


if __name__ == "__main__":
    raise SystemExit(main())
