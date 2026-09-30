from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


SCRIPTS_DIR = Path(__file__).resolve().parents[1]


def write_log(root: Path, date: str, *, doc_type: str = "daily-work-log", summary: str = "", tags: list[str] | None = None, body: str = "") -> Path:
    tags_yaml = "[" + ", ".join(tags or []) + "]"
    path = root / date[:4] / date[5:7] / f"{date}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        f"date: {date}\n"
        f"type: {doc_type}\n"
        f'summary: "{summary}"\n'
        f"tags: {tags_yaml}\n"
        "---\n\n"
        f"# {date} 업무 기록\n\n{body}\n",
        encoding="utf-8",
    )
    return path


def run_search(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "search_work_logs.py"), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class SearchWorkLogsTests(unittest.TestCase):
    def search_json(self, *args: str) -> dict:
        result = run_search(*args, "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_filters_by_tag_and_query(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_log(root, "2026-07-01", summary="kafka consumer 점검", tags=["kafka", "troubleshooting"], body="consumer lag 원인을 조사했다.")
            write_log(root, "2026-07-02", summary="배포 준비", tags=["deploy"], body="릴리즈 체크리스트 정리.")

            data = self.search_json("--log-root", str(root), "--tag", "kafka")
            self.assertEqual(data["total"], 1)
            self.assertEqual(data["results"][0]["date"], "2026-07-01")

            data = self.search_json("--log-root", str(root), "--query", "lag")
            self.assertEqual(data["total"], 1)
            self.assertTrue(data["results"][0]["matched_lines"])
            self.assertIn("lag", data["results"][0]["matched_lines"][0]["text"])

    def test_query_matches_summary_and_requires_all_terms(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_log(root, "2026-07-01", summary="kafka consumer 점검", tags=["kafka"], body="본문에는 다른 얘기.")

            data = self.search_json("--log-root", str(root), "--query", "consumer")
            self.assertEqual(data["total"], 1)

            data = self.search_json("--log-root", str(root), "--query", "consumer", "--query", "없는말")
            self.assertEqual(data["total"], 0)

    def test_date_range_and_sort_desc(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            for date in ("2026-06-30", "2026-07-01", "2026-07-02"):
                write_log(root, date, summary=f"{date} 작업")

            data = self.search_json("--log-root", str(root), "--since", "2026-07-01")
            self.assertEqual([row["date"] for row in data["results"]], ["2026-07-02", "2026-07-01"])

            data = self.search_json("--log-root", str(root), "--until", "2026-06-30")
            self.assertEqual(data["total"], 1)

    def test_type_filter_and_block_list_tags(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_log(root, "2026-07-01", doc_type="learning-note", summary="학습 메모")
            path = root / "2026" / "07" / "2026-07-02.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "---\ndate: 2026-07-02\ntype: daily-work-log\nsummary: 블록 리스트 태그\ntags:\n  - kafka\n  - retry\n---\n\n본문\n",
                encoding="utf-8",
            )

            data = self.search_json("--log-root", str(root), "--type", "daily-work-log")
            self.assertEqual(data["total"], 1)
            self.assertEqual(data["results"][0]["tags"], ["kafka", "retry"])

            data = self.search_json("--log-root", str(root), "--tag", "retry")
            self.assertEqual(data["total"], 1)

    def test_log_root_from_config(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "work-log"
            write_log(root, "2026-07-01", summary="config 경유")
            config = base / "config.json"
            config.write_text(json.dumps({"log_root": str(root)}), encoding="utf-8")

            data = self.search_json("--config", str(config), "--date", "2026-07-01")
            self.assertEqual(data["total"], 1)

    def test_missing_log_root_fails_clearly(self) -> None:
        with TemporaryDirectory() as tmp:
            result = run_search("--config", str(Path(tmp) / "missing.json"))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("log root", result.stderr)


if __name__ == "__main__":
    unittest.main()
