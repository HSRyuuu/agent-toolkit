from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
TARGET_DATE = "2026-07-02"


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def run_script(name: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / name), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class StateRootTests(unittest.TestCase):
    def assert_json_file(self, path: Path, source: str) -> dict:
        self.assertTrue(path.exists(), f"missing {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["source"], source)
        return data

    def test_codex_collector_writes_to_state_root(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            sessions = base / "sessions"
            state_root = base / "state"
            write_jsonl(
                sessions / "2026" / "07" / "01" / "a.jsonl",
                [
                    {"type": "session_meta", "payload": {"id": "codex-a", "cwd": "/work/alpha", "thread_source": "user"}},
                    {
                        "timestamp": "2026-07-01T16:00:00Z",
                        "type": "response_item",
                        "payload": {
                            "type": "message",
                            "role": "user",
                            "content": [{"type": "input_text", "text": "오늘 한 일 정리"}],
                        },
                    },
                ],
            )

            result = run_script(
                "collect_codex_first_pass_candidates.py",
                "--date",
                TARGET_DATE,
                "--sessions-root",
                str(sessions),
                "--state-root",
                str(state_root),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assert_json_file(state_root / "2026" / TARGET_DATE / "codex-candidates.json", "codex")

    def test_claude_collector_writes_to_state_root(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            sessions = base / "sessions"
            state_root = base / "state"
            write_jsonl(
                sessions / "session.jsonl",
                [
                    {
                        "timestamp": "2026-07-01T16:00:00Z",
                        "session_id": "claude-a",
                        "cwd": "/work/alpha",
                        "message": {"role": "user", "content": [{"type": "text", "text": "오늘 한 일 정리"}]},
                    }
                ],
            )

            result = run_script(
                "collect_claude_first_pass_candidates.py",
                "--date",
                TARGET_DATE,
                "--sessions-root",
                str(sessions),
                "--state-root",
                str(state_root),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assert_json_file(state_root / "2026" / TARGET_DATE / "claude-candidates.json", "claude")

    def test_kb_collector_writes_to_state_root_and_converts_log_timestamp(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            kb = base / "kb"
            kb.mkdir()
            state_root = base / "state"
            write_jsonl(
                kb / "log.jsonl",
                [
                    {
                        "timestamp": "2026-07-01T16:00:00Z",
                        "summary": "KB에 오늘 업무 메모를 정리함",
                        "paths": ["notes/today.md"],
                    }
                ],
            )

            result = run_script(
                "collect_kb_first_pass_candidates.py",
                "--date",
                TARGET_DATE,
                "--kb-root",
                str(kb),
                "--state-root",
                str(state_root),
                "--emit-empty",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            data = self.assert_json_file(state_root / "2026" / TARGET_DATE / "kb-candidates.json", "kb")
            self.assertEqual(len(data["candidates"]), 1)


if __name__ == "__main__":
    unittest.main()
