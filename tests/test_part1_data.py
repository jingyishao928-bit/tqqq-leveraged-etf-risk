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
PRODUCT_FACTS_FILE = ROOT / "data" / "metadata" / "part1_product_facts.csv"
REPLICATION_PATH_FILE = ROOT / "outputs" / "part1" / "tables" / "part1_replication_path.csv"
REPLICATION_SUMMARY_FILE = (
    ROOT / "outputs" / "part1" / "tables" / "table_part1_replication.csv"
)


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

    def test_product_facts_cover_qqq_tqqq_and_sqqq(self):
        rows = read_rows(PRODUCT_FACTS_FILE)
        self.assertEqual(
            len(rows),
            len({(row["ticker"], row["fact"]) for row in rows}),
            "Each ticker/fact pair must be unique",
        )
        self.assertEqual({row["ticker"] for row in rows}, {"QQQ", "TQQQ", "SQQQ"})
        self.assertTrue(all(row["accessed_on"] == "2026-11-24" for row in rows))
        self.assertTrue(all(row["source"].startswith("https://") for row in rows))

        facts = {
            ticker: {
                row["fact"]: row["value"]
                for row in rows
                if row["ticker"] == ticker
            }
            for ticker in ("QQQ", "TQQQ", "SQQQ")
        }
        expected = {
            "QQQ": {
                "formal_name": "Invesco QQQ Trust, Series 1",
                "investment_objective": "Passively managed and tracks the Nasdaq-100 Index",
                "inception_date": "1999-03-10",
                "total_expense_ratio": "0.18%",
            },
            "TQQQ": {
                "formal_name": "ProShares UltraPro QQQ",
                "investment_objective": "3x the daily performance of the Nasdaq-100 Index",
                "inception_date": "2010-02-09",
                "gross_expense_ratio": "0.94%",
                "net_expense_ratio": "0.78%",
                "waiver_expiry": "2027-09-30",
            },
            "SQQQ": {
                "formal_name": "ProShares UltraPro Short QQQ",
                "investment_objective": (
                    "3x the inverse (-3x) of the daily performance of the "
                    "Nasdaq-100 Index"
                ),
                "inception_date": "2010-02-09",
                "gross_expense_ratio": "0.94%",
                "net_expense_ratio": "0.94%",
            },
        }
        for ticker, expected_facts in expected.items():
            with self.subTest(ticker=ticker):
                for fact, value in expected_facts.items():
                    self.assertEqual(facts[ticker].get(fact), value)

    def test_replication_outputs_use_wealth_index_not_nav(self):
        path_rows = read_rows(REPLICATION_PATH_FILE)
        self.assertTrue(path_rows)
        self.assertEqual(
            set(path_rows[0]),
            {
                "Date",
                "TQQQ_adjusted_price_wealth_index",
                "TQQQ_idealized_3x_wealth_index",
                "tracking_gap_pct",
                "NDX_simple_ret",
            },
        )
        self.assertFalse(any("nav" in column.lower() for column in path_rows[0]))

        summary = {row["metric"]: row["value"] for row in read_rows(REPLICATION_SUMMARY_FILE)}
        self.assertNotIn("actual_final_nav_index", summary)
        self.assertNotIn("ideal_final_nav_index", summary)
        self.assertAlmostEqual(
            float(summary["adjusted_price_final_wealth_index"]),
            9.230664304230752,
        )
        self.assertAlmostEqual(
            float(summary["idealized_3x_final_wealth_index"]),
            14.589359383419465,
        )


if __name__ == "__main__":
    unittest.main()
