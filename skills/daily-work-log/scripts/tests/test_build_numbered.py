from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

import build_numbered_candidates
from build_numbered_candidates import collect_groups


def work_unit(unit_id: str, request: str) -> dict:
    return {
        "work_unit_id": unit_id,
        "title": request,
        "user_request": request,
        "outcome": f"{request} 처리",
        "mentioned_paths": [f"src/{unit_id}.py"],
        "classification_hints": ["work-item"],
    }


def session_candidate(session_id: str, *units: dict) -> dict:
    return {
        "source": "codex",
        "session_id": session_id,
        "file": f"/sessions/{session_id}.jsonl",
        "cwd": f"/work/{session_id}",
        "title_hint": f"{session_id} 작업",
        "importance_score": 60,
        "confidence": "medium",
        "work_units": list(units),
    }


class BuildNumberedCandidatesTests(unittest.TestCase):
    def test_collect_groups_uses_session_and_kb_document_groups(self) -> None:
        first_pass = [
            {
                "source": "codex",
                "candidates": [
                    session_candidate("session-a", work_unit("a1", "API 수정"), work_unit("a2", "테스트 보강")),
                    session_candidate("session-b", work_unit("b1", "문서 정리")),
                ],
                "supporting": [],
            },
            {
                "source": "kb",
                "candidates": [
                    {
                        "source": "kb",
                        "session_id": None,
                        "file": "/kb/notes/today.md",
                        "title_hint": "오늘 업무 메모",
                        "importance_score": 55,
                        "confidence": "medium",
                        "work_units": [work_unit("kb1", "KB 메모")],
                    }
                ],
                "supporting": [],
            },
        ]

        groups = collect_groups(first_pass, include_supporting=False)
        self.assertEqual(len(groups), 3)
        self.assertEqual({group["topic_key"] for group in groups}, {"codex:session-a", "codex:session-b", "kb:오늘 업무 메모"})
        for number, group in enumerate(groups, start=1):
            group["number"] = number
        self.assertEqual([group["number"] for group in groups], [1, 2, 3])

    def test_source_has_no_hardcoded_topic_rules(self) -> None:
        # 회사/업무 식별자 부재는 verify-secrets 스킬과 스윕 grep이 담당한다.
        # 여기서는 하드코딩 주제 규칙 구조 자체가 없는 것만 검증한다.
        source = inspect.getsource(build_numbered_candidates)
        self.assertNotIn("TOPIC_RULES", source)


if __name__ == "__main__":
    unittest.main()
