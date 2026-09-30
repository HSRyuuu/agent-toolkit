from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from first_pass_candidate_utils import to_local_date


class ToLocalDateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.seoul = ZoneInfo("Asia/Seoul")

    def test_utc_z_timestamp_converts_to_local_date(self) -> None:
        self.assertEqual(to_local_date("2026-07-01T16:00:00Z", self.seoul), date(2026, 7, 2))

    def test_offset_timestamp_keeps_its_local_calendar_day(self) -> None:
        self.assertEqual(to_local_date("2026-07-01T16:00:00+09:00", self.seoul), date(2026, 7, 1))

    def test_naive_timestamp_is_treated_as_utc(self) -> None:
        self.assertEqual(to_local_date("2026-07-01T16:00:00", self.seoul), date(2026, 7, 2))

    def test_invalid_values_return_none(self) -> None:
        for value in ("not-a-date", None, 12345):
            with self.subTest(value=value):
                self.assertIsNone(to_local_date(value, self.seoul))


if __name__ == "__main__":
    unittest.main()
