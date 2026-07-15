from __future__ import annotations

import inspect
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

import build_final_info_skeleton
from build_final_info_skeleton import build_final_info, load_impact_items


class BuildFinalInfoSkeletonTests(unittest.TestCase):
    def test_build_final_info_uses_neutral_slots(self) -> None:
        digest = {
            "date": "2026-07-02",
            "selected_candidates": [{"group_id": 1, "title": "API 오류 조사", "confidence": "high"}],
            "selected_details": [
                {
                    "group_id": 1,
                    "title": "API 오류 조사",
                    "digest_summary": "error handling 관련 작업을 정리함",
                    "source_projects": ["/work/order-api"],
                    "work_units": [{"title": "에러 처리 확인", "outcome": "예외 흐름을 점검함"}],
                    "evidence_paths": {"project_files": ["src/api.py"]},
                    "confidence": "high",
                }
            ],
        }

        result = build_final_info(digest)
        item = result["selected_items"][0]
        self.assertEqual(item["category"], "work-item")
        self.assertEqual(item["technical_context"]["tech_stack"], [])
        self.assertEqual(item["technical_context"]["modules"], [])
        self.assertEqual(item["technical_context"]["repo_names"], ["order-api"])
        self.assertEqual(item["markdown_hints"]["include_keywords"], [])
        self.assertNotIn("impact", result)

    def test_build_final_info_adds_impact_skeleton_when_configured(self) -> None:
        digest = {
            "date": "2026-07-02",
            "selected_candidates": [{"group_id": 1, "title": "API 오류 조사", "confidence": "high"}],
            "selected_details": [
                {
                    "group_id": 1,
                    "title": "API 오류 조사",
                    "digest_summary": "error handling 관련 작업을 정리함",
                    "source_projects": ["/work/order-api"],
                    "work_units": [{"title": "에러 처리 확인", "outcome": "예외 흐름을 점검함"}],
                    "evidence_paths": {"project_files": ["src/api.py"]},
                    "confidence": "high",
                }
            ],
        }

        result = build_final_info(digest, impact_items=["Jira Ticket", "PR/MR 기록"])
        self.assertEqual(
            result["impact"],
            {
                "impact_items": ["Jira Ticket", "PR/MR 기록"],
                "findings": {"Jira Ticket": [], "PR/MR 기록": []},
            },
        )

    def test_load_impact_items_missing_config_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(load_impact_items(Path(tmp) / "missing-config.json"), [])

    def test_load_impact_items_reads_hyphenated_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.json"
            config_path.write_text(
                json.dumps({"log_root": "/x", "impact-items": ["Jira Ticket", "", 42, "PR/MR 기록"]}),
                encoding="utf-8",
            )
            self.assertEqual(load_impact_items(config_path), ["Jira Ticket", "PR/MR 기록"])

    def test_load_impact_items_without_field_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.json"
            config_path.write_text(json.dumps({"log_root": "/x"}), encoding="utf-8")
            self.assertEqual(load_impact_items(config_path), [])

    def test_source_has_no_inference_patterns(self) -> None:
        # 회사/업무 식별자 부재는 verify-secrets 스킬과 스윕 grep이 담당한다.
        # 여기서는 추론 로직 심볼이 없는 것만 검증한다.
        source = inspect.getsource(build_final_info_skeleton)
        for forbidden in (
            "TECH_PATTERNS",
            "infer_category",
            "infer_tech_stack",
            "infer_modules",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
