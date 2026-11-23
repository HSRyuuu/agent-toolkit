from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from build_day_evidence import render_evidence


def unit(started_at: str, request: str, outcome: str, **extra: object) -> dict:
    return {"started_at": started_at, "user_request": request, "outcome": outcome, **extra}


class RenderEvidenceTests(unittest.TestCase):
    def render(self, units: list[dict]) -> str:
        digest = {
            "selected_details": [
                {"group_id": "1", "title": "API 수정", "source_projects": ["/work/alpha"], "work_units": units}
            ]
        }
        numbered = {"displayed_candidates": [{"number": 1, "list_section": "other"}], "hidden_candidate_count": 2}
        return render_evidence("2026-07-02", digest, numbered, [("TODO", "완결되지 않은 것")])

    def test_group_header_lists_evidence_and_skips_temp_files(self) -> None:
        text = self.render(
            [
                unit(
                    "2026-07-02T01:00:00Z",
                    "API 고쳐줘",
                    "고쳤습니다",
                    edited_files=["/work/alpha/src/api.py", "/private/tmp/x/body.md"],
                    delivery_commands=["git commit"],
                    links=["https://example.com/pull/1"],
                )
            ]
        )
        self.assertIn("## 후보 1 | other | API 수정", text)
        self.assertIn("- 1 | other | 단위 1개 | API 수정", text)
        self.assertIn("한도로 숨긴 후보 2개", text)
        self.assertIn("- TODO: 완결되지 않은 것", text)
        self.assertIn("고친 파일: src/api.py\n", text)
        self.assertIn("커밋·푸시·PR 명령: git commit", text)
        self.assertIn("응답에 나온 링크: https://example.com/pull/1", text)
        self.assertIn("  -> 고쳤습니다", text)

    def test_unit_without_response_prints_request_only(self) -> None:
        text = self.render([unit("2026-07-02T01:00:00Z", "그럼 A안으로 하자", "결과 힌트가 부족함.")])
        self.assertIn("| 그럼 A안으로 하자", text)
        self.assertNotIn("결과 힌트가 부족함", text)


if __name__ == "__main__":
    unittest.main()
