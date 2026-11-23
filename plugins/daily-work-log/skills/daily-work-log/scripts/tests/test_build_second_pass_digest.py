from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from build_second_pass_digest import build_digest


DATE = "2026-07-02"


def unit(index: int, started_at: str, request: str) -> dict:
    return {
        "work_unit_id": f"claude:s1:{index}",
        "started_at": started_at,
        "title": request,
        "user_request": request,
        "outcome": f"{request} 완료",
    }


class BuildSecondPassDigestTests(unittest.TestCase):
    def test_dedupes_fork_copies_by_content_and_sorts_by_time(self) -> None:
        # 원래 세션, 포크 복사본, 이어 쓴 세션이 같은 session_id를 공유한다.
        original = {"source": "claude", "file": "/a.jsonl", "session_id": "s1", "work_units": [unit(1, "2026-07-02T01:00:00Z", "A"), unit(2, "2026-07-02T02:00:00Z", "B")]}
        fork_copy = {"source": "claude", "file": "/b.jsonl", "session_id": "s1", "work_units": [unit(1, "2026-07-02T01:00:00Z", "A"), unit(2, "2026-07-02T02:00:00Z", "B")]}
        resumed = {"source": "claude", "file": "/c.jsonl", "session_id": "s1", "work_units": [unit(1, "2026-07-02T00:30:00Z", "C")]}
        candidates = [original, fork_copy, resumed]
        refs = [
            {"source": "claude", "session_id": "s1", "file": c["file"], "work_unit_ids": [u["work_unit_id"] for u in c["work_units"]]}
            for c in candidates
        ]
        with TemporaryDirectory() as tmp:
            state_root = Path(tmp)
            day = state_root / DATE[:4] / DATE
            day.mkdir(parents=True)
            (day / "claude-candidates.json").write_text(json.dumps({"source": "claude", "candidates": candidates}), encoding="utf-8")
            numbered_path = day / "numbered-candidates.json"
            numbered_path.write_text(
                json.dumps({"displayed_candidates": [{"number": 1, "title": "t", "list_section": "top", "candidate_refs": refs}]}),
                encoding="utf-8",
            )
            digest = build_digest(DATE, state_root, numbered_path, "1")

        requests = [u["user_request"] for u in digest["selected_details"][0]["work_units"]]
        self.assertEqual(requests, ["C", "A", "B"])

    def test_fork_copy_keeps_longer_outcome(self) -> None:
        # 같은 단위가 원래 세션에서는 마지막 단위라 길고, 포크에서는 중간 단위라 짧다.
        prefix = "가" * 250
        short = {**unit(1, "2026-07-02T01:00:00Z", "A"), "outcome": prefix + "..."}
        long = {**unit(1, "2026-07-02T01:00:00Z", "A"), "outcome": prefix + "나" * 500}
        candidates = [
            {"source": "claude", "file": "/fork.jsonl", "session_id": "s1", "work_units": [short]},
            {"source": "claude", "file": "/orig.jsonl", "session_id": "s1", "work_units": [long]},
        ]
        refs = [{"source": "claude", "session_id": "s1", "file": c["file"], "work_unit_ids": ["claude:s1:1"]} for c in candidates]
        with TemporaryDirectory() as tmp:
            state_root = Path(tmp)
            day = state_root / DATE[:4] / DATE
            day.mkdir(parents=True)
            (day / "claude-candidates.json").write_text(json.dumps({"source": "claude", "candidates": candidates}), encoding="utf-8")
            numbered_path = day / "numbered-candidates.json"
            numbered_path.write_text(
                json.dumps({"displayed_candidates": [{"number": 1, "title": "t", "list_section": "top", "candidate_refs": refs}]}),
                encoding="utf-8",
            )
            digest = build_digest(DATE, state_root, numbered_path, "1")

        units = digest["selected_details"][0]["work_units"]
        self.assertEqual(len(units), 1)
        self.assertEqual(units[0]["outcome"], long["outcome"])


if __name__ == "__main__":
    unittest.main()
