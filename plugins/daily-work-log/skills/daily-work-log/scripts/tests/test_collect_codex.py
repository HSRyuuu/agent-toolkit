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

from collect_codex_first_pass_candidates import candidate_from_file, session_files_for_date


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def meta(cwd: str = "/work/alpha") -> dict:
    return {"type": "session_meta", "payload": {"id": "session-a", "cwd": cwd, "thread_source": "user"}}


def user_row(timestamp: str, text: str) -> dict:
    return {
        "timestamp": timestamp,
        "type": "response_item",
        "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": text}]},
    }


def assistant_row(timestamp: str, text: str = "반영했습니다") -> dict:
    return {
        "timestamp": timestamp,
        "type": "response_item",
        "payload": {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": text}]},
    }


class CodexCollectorDateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tz = ZoneInfo("Asia/Seoul")

    def test_session_files_include_adjacent_utc_directories(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            previous_day = root / "2026" / "07" / "01" / "a.jsonl"
            target_day = root / "2026" / "07" / "02" / "b.jsonl"
            next_day = root / "2026" / "07" / "03" / "c.jsonl"
            for path in (previous_day, target_day, next_day):
                write_jsonl(path, [meta()])

            files = session_files_for_date(root, date(2026, 7, 2))
            self.assertEqual(files, [previous_day, target_day, next_day])

    def test_candidate_filters_work_units_by_local_date(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "2026" / "07" / "01" / "a.jsonl"
            write_jsonl(
                path,
                [
                    meta(),
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
            path = Path(tmp) / "2026" / "07" / "01" / "a.jsonl"
            write_jsonl(
                path,
                [
                    meta(),
                    user_row("2026-07-01T16:00:00Z", "<system-reminder>internal</system-reminder>"),
                    assistant_row("2026-07-01T16:01:00Z"),
                    user_row("2026-07-01T16:10:00Z", "대상 날짜 요청"),
                    assistant_row("2026-07-01T16:11:00Z"),
                ],
            )

            candidate = candidate_from_file(path, date(2026, 7, 2), self.tz)
            self.assertEqual([unit["user_request"] for unit in candidate["work_units"]], ["대상 날짜 요청"])


if __name__ == "__main__":
    unittest.main()
