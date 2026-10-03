from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from first_pass_candidate_utils import clean_user_text, strip_injected_blocks


class CleanUserTextTests(unittest.TestCase):
    def test_strip_injected_block_keeps_real_request(self) -> None:
        text = "<system-reminder>ignore this</system-reminder>\n오늘 한 일 정리해줘"
        self.assertEqual(strip_injected_blocks(text).strip(), "오늘 한 일 정리해줘")

    def test_clean_user_text_drops_block_only_message(self) -> None:
        text = "<system-reminder>internal notice</system-reminder>"
        self.assertEqual(clean_user_text(text), "")

    def test_strip_injected_block_handles_missing_close_tag(self) -> None:
        text = "실제 요청\n<system-reminder>truncated"
        self.assertEqual(strip_injected_blocks(text).strip(), "실제 요청")

    def test_strip_injected_block_removes_multiple_blocks(self) -> None:
        text = "A <system-reminder>one</system-reminder> B <system-reminder>two</system-reminder> C"
        self.assertEqual(strip_injected_blocks(text), "A  B  C")

    def test_existing_noise_rules_still_apply_after_block_removal(self) -> None:
        self.assertEqual(clean_user_text("# AGENTS.md instructions\nnoise"), "")
        self.assertEqual(
            clean_user_text("실제 요청\n# Files mentioned by the user:\n/path/to/file.py"),
            "실제 요청 /path/to/file.py",
        )
        self.assertEqual(clean_user_text("실제 요청\n<environment_context>noise</environment_context>"), "실제 요청")

    def test_harness_blocks_are_removed(self) -> None:
        for tag in ("local-command-caveat", "recommended_plugins", "task-notification", "fork-source"):
            self.assertEqual(clean_user_text(f"<{tag}>harness</{tag}>"), "", tag)
        self.assertEqual(clean_user_text("<task-notification>done</task-notification> 실제 요청"), "실제 요청")
        self.assertEqual(clean_user_text("[Image: source: /tmp/a.png] 이거 고쳐줘"), "이거 고쳐줘")

    def test_harness_messages_are_dropped(self) -> None:
        self.assertEqual(clean_user_text("The fork runs as its own separate session — nothing it does arrives"), "")
        self.assertEqual(clean_user_text('<pasted_content id="1"> You are working inside Orca, a multi-agent IDE.'), "")
        self.assertEqual(clean_user_text('<pasted_content id="2"> TEC-922 작업 지시'), '<pasted_content id="2"> TEC-922 작업 지시')


if __name__ == "__main__":
    unittest.main()
