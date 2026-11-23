import csv
import math
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRICES_FILE = ROOT / "data" / "processed" / "part1_clean_prices.csv"
RETURNS_FILE = ROOT / "data" / "processed" / "part1_clean_returns.csv"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


class Part1DataTests(unittest.TestCase):
    def test_price_dates_are_unique_and_ascending(self):
        rows = read_rows(PRICES_FILE)
        dates = [date.fromisoformat(row["Date"]) for row in rows]
        self.assertEqual(len(rows), 1984)
        self.assertEqual(dates, sorted(set(dates)))
        self.assertEqual(dates[0].isoformat(), "2019-01-02")
        self.assertEqual(dates[-1].isoformat(), "2026-11-20")

    def test_prices_are_positive(self):
        rows = read_rows(PRICES_FILE)
        for row in rows:
            for column in ("TQQQ_price", "QQQ_price", "NDX_price"):
                self.assertGreater(float(row[column]), 0.0)

    def test_returns_are_complete_and_finite(self):
        rows = read_rows(RETURNS_FILE)
        columns = ("TQQQ_simple_ret", "QQQ_simple_ret", "NDX_simple_ret")
        self.assertEqual(len(rows), 1983)
        for row in rows:
            for column in columns:
                self.assertTrue(math.isfinite(float(row[column])))

    def test_exactly_two_rows_are_flagged_for_review(self):
        rows = read_rows(RETURNS_FILE)
        flagged = [row for row in rows if row["manual_review_flag"] == "True"]
        self.assertEqual([row["Date"] for row in flagged], ["2020-03-16", "2025-04-09"])


if __name__ == "__main__":
    unittest.main()
