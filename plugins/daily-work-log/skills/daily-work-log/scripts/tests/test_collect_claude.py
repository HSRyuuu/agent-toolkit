from __future__ import annotations

import json
import sys
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from zoneinfo import ZoneInfo


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from collect_claude_first_pass_candidates import candidate_from_file, file_matches_date
from first_pass_candidate_utils import OUTCOME_LIMIT, OUTCOME_LONG_LIMIT


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def user_row(timestamp: str, text: str, session_id: str = "session-a") -> dict:
    return {
        "timestamp": timestamp,
        "session_id": session_id,
        "cwd": "/work/alpha",
        "message": {"role": "user", "content": [{"type": "text", "text": text}]},
    }


def assistant_row(timestamp: str, text: str = "처리했습니다", session_id: str = "session-a") -> dict:
    return {
        "timestamp": timestamp,
        "session_id": session_id,
        "cwd": "/work/alpha",
        "message": {"role": "assistant", "content": [{"type": "text", "text": text}]},
    }


class ClaudeCollectorDateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tz = ZoneInfo("Asia/Seoul")

    def test_file_matches_date_scans_beyond_250_rows(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.jsonl"
            rows = [assistant_row("2026-07-01T01:00:00Z", f"noise {index}") for index in range(260)]
            rows.append(user_row("2026-07-01T16:00:00Z", "대상 날짜 요청"))
            write_jsonl(path, rows)

            self.assertTrue(file_matches_date(path, date(2026, 7, 2), self.tz))

    def test_candidate_filters_work_units_by_local_date(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.jsonl"
            write_jsonl(
                path,
                [
                    user_row("2026-07-01T14:30:00Z", "전날 요청"),
                    assistant_row("2026-07-01T14:40:00Z"),
                    user_row("2026-07-01T16:00:00Z", "대상 날짜 요청"),
                    assistant_row("2026-07-01T16:10:00Z"),
                ],
            )

            candidate = candidate_from_file(path, date(2026, 7, 2), self.tz)
            self.assertEqual([unit["user_request"] for unit in candidate["work_units"]], ["대상 날짜 요청"])

    def test_block_only_user_message_does_not_create_empty_work_unit(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.jsonl"
            write_jsonl(
                path,
                [
                    user_row("2026-07-01T16:00:00Z", "<system-reminder>internal</system-reminder>"),
                    assistant_row("2026-07-01T16:01:00Z"),
                    user_row("2026-07-01T16:10:00Z", "대상 날짜 요청"),
                    assistant_row("2026-07-01T16:11:00Z"),
                ],
            )

            candidate = candidate_from_file(path, date(2026, 7, 2), self.tz)
            self.assertEqual([unit["user_request"] for unit in candidate["work_units"]], ["대상 날짜 요청"])

    def test_long_outcome_only_for_last_and_delivery_units(self) -> None:
        long_text = "가" * 2000
        commit_row = {
            "timestamp": "2026-07-01T16:21:00Z",
            "session_id": "session-a",
            "cwd": "/work/alpha",
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "tool_use", "name": "Edit", "input": {"file_path": "/work/alpha/a.py"}},
                    {"type": "tool_use", "name": "Bash", "input": {"command": "git commit -m x && git push"}},
                ],
            },
        }
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.jsonl"
            write_jsonl(
                path,
                [
                    user_row("2026-07-01T16:00:00Z", "조사해줘"),
                    assistant_row("2026-07-01T16:10:00Z", long_text),
                    user_row("2026-07-01T16:20:00Z", "커밋해줘"),
                    commit_row,
                    assistant_row("2026-07-01T16:22:00Z", long_text + " https://example.com/pull/7."),
                    user_row("2026-07-01T16:30:00Z", "마무리 정리해줘"),
                    assistant_row("2026-07-01T16:31:00Z", long_text),
                ],
            )

            units = candidate_from_file(path, date(2026, 7, 2), self.tz)["work_units"]

        self.assertEqual([len(unit["outcome"]) for unit in units], [OUTCOME_LIMIT + 2, OUTCOME_LONG_LIMIT + 2, OUTCOME_LONG_LIMIT + 2])
        self.assertEqual(units[1]["edited_files"], ["/work/alpha/a.py"])
        self.assertEqual(units[1]["delivery_commands"], ["git commit", "git push"])
        self.assertEqual(units[1]["links"], ["https://example.com/pull/7"])
        self.assertEqual(units[0]["delivery_commands"], [])


if __name__ == "__main__":
    unittest.main()
