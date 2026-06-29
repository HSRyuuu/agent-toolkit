import tempfile
import unittest
from pathlib import Path

from validate_llm_wiki import validate_root


class ValidateLlmWikiTest(unittest.TestCase):
    def test_reports_daily_log_without_canonical_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Tripbtoz").mkdir()
            (root / "Tripbtoz" / "tripbtoz-onboarding-2026-06-29.md").write_text(
                """---
kind: daily-log
tags: [tripbtoz]
created: 2026-06-29
---

# Tripbtoz onboarding - 2026-06-29
""",
                encoding="utf-8",
            )

            issues = validate_root(root)

        self.assert_issue(issues, "daily-log-without-canonical-link")

    def test_reports_unlinked_raw_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "_raw").mkdir()
            (root / "_raw" / "onboarding.md").write_text(
                "# Raw onboarding notes\n", encoding="utf-8"
            )
            (root / "Tripbtoz").mkdir()
            (root / "Tripbtoz" / "tripbtoz-onboarding.md").write_text(
                """---
kind: canonical
tags: [tripbtoz]
created: 2026-06-29
---

# Tripbtoz onboarding
""",
                encoding="utf-8",
            )

            issues = validate_root(root)

        self.assert_issue(issues, "raw-source-unlinked")

    def test_reports_unknown_explicit_kind(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Tripbtoz").mkdir()
            (root / "Tripbtoz" / "tripbtoz-note.md").write_text(
                """---
kind: meeting-note
tags: [tripbtoz]
created: 2026-06-29
---

# Tripbtoz note
""",
                encoding="utf-8",
            )

            issues = validate_root(root)

        self.assert_issue(issues, "unknown-kind")

    def test_accepts_linked_canonical_daily_log_and_raw_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "_raw").mkdir()
            (root / "_raw" / "onboarding.md").write_text(
                "# Raw onboarding notes\n", encoding="utf-8"
            )
            (root / "Tripbtoz").mkdir()
            (root / "Tripbtoz" / "tripbtoz-onboarding.md").write_text(
                """---
kind: canonical
tags: [tripbtoz]
created: 2026-06-29
source:
  - "[[_raw/onboarding]]"
---

# Tripbtoz onboarding

## Related Logs

- [[Tripbtoz/tripbtoz-onboarding-2026-06-29]]

## Source Links

- [[_raw/onboarding]]
""",
                encoding="utf-8",
            )
            (root / "Tripbtoz" / "tripbtoz-onboarding-2026-06-29.md").write_text(
                """---
kind: daily-log
tags: [tripbtoz]
created: 2026-06-29
canonical: "[[Tripbtoz/tripbtoz-onboarding]]"
source:
  - "[[_raw/onboarding]]"
---

# Tripbtoz onboarding - 2026-06-29

Related: [[Tripbtoz/tripbtoz-onboarding]]
""",
                encoding="utf-8",
            )

            issues = validate_root(root)

        codes = {issue["code"] for issue in issues}
        self.assertNotIn("daily-log-without-canonical-link", codes)
        self.assertNotIn("raw-source-unlinked", codes)

    def assert_issue(self, issues, code):
        self.assertIn(code, {issue["code"] for issue in issues})


if __name__ == "__main__":
    unittest.main()
