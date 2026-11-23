import csv
import math
import statistics
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRICES_FILE = ROOT / "data" / "processed" / "part1_clean_prices.csv"
RETURNS_FILE = ROOT / "data" / "processed" / "part1_clean_returns.csv"
CANONICAL_RETURNS_FILE = ROOT / "data" / "processed" / "clean_returns.csv"
SQQQ_RAW_FILE = ROOT / "data" / "raw" / "SQQQ_raw.csv"


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
            for column in ("TQQQ_price", "SQQQ_price", "QQQ_price", "NDX_price"):
                self.assertGreater(float(row[column]), 0.0)

    def test_returns_are_complete_and_finite(self):
        rows = read_rows(RETURNS_FILE)
        columns = (
            "TQQQ_simple_ret",
            "SQQQ_simple_ret",
            "QQQ_simple_ret",
            "NDX_simple_ret",
        )
        self.assertEqual(len(rows), 1983)
        for row in rows:
            for column in columns:
                self.assertTrue(math.isfinite(float(row[column])))

    def test_exactly_two_rows_are_flagged_for_review(self):
        rows = read_rows(RETURNS_FILE)
        flagged = [row for row in rows if row["manual_review_flag"] == "True"]
        self.assertEqual([row["Date"] for row in flagged], ["2020-03-16", "2025-04-09"])

    def test_sqqq_raw_data_matches_the_frozen_source_window(self):
        rows = read_rows(SQQQ_RAW_FILE)
        dates = [date.fromisoformat(row["Date"]) for row in rows]
        self.assertEqual(len(rows), 4221)
        self.assertEqual(dates, sorted(set(dates)))
        self.assertEqual(dates[0].isoformat(), "2010-02-11")
        self.assertEqual(dates[-1].isoformat(), "2026-11-20")
        self.assertTrue(all(row["Ticker"] == "SQQQ" for row in rows))

    def test_canonical_returns_include_all_four_series(self):
        rows = read_rows(CANONICAL_RETURNS_FILE)
        required_columns = (
            "qqq_adj_close",
            "tqqq_adj_close",
            "sqqq_adj_close",
            "ndx_close",
            "qqq_simple_return",
            "qqq_log_return",
            "tqqq_simple_return",
            "tqqq_log_return",
            "sqqq_simple_return",
            "sqqq_log_return",
            "ndx_simple_return",
            "ndx_log_return",
        )
        self.assertEqual(len(rows), 1983)
        self.assertEqual(rows[0]["date"], "2019-01-03")
        self.assertEqual(rows[-1]["date"], "2026-11-20")
        for row in rows:
            for column in required_columns:
                self.assertTrue(math.isfinite(float(row[column])))

    def test_sqqq_daily_returns_track_the_inverse_ndx_direction(self):
        rows = read_rows(RETURNS_FILE)
        actual = [float(row["SQQQ_simple_ret"]) for row in rows]
        target = [-3.0 * float(row["NDX_simple_ret"]) for row in rows]
        actual_mean = statistics.fmean(actual)
        target_mean = statistics.fmean(target)
        covariance = sum(
            (x - actual_mean) * (y - target_mean)
            for x, y in zip(actual, target, strict=True)
        )
        actual_ss = sum((x - actual_mean) ** 2 for x in actual)
        target_ss = sum((y - target_mean) ** 2 for y in target)
        correlation = covariance / math.sqrt(actual_ss * target_ss)
        self.assertGreater(correlation, 0.99)


if __name__ == "__main__":
    unittest.main()
