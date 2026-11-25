"""Targeted tests for Part 2 financial signs, dates and causality."""

from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "outputs/part2"))

from analyze_part2 import build_paths, load_sample, rolling_metrics  # noqa: E402
from part2_sensitivity import benchmark_sensitivity, holding_periods, two_day_examples  # noqa: E402


class Part2AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sample, cls.frame = load_sample()

    def test_flat_baseline_can_have_negative_daily_reset_return(self):
        block = self.frame.iloc[:2].copy()
        block["qqq_simple_return"] = [0.10, 1 / 1.10 - 1]
        path = build_paths(block, self.sample)
        self.assertAlmostEqual(path["linear_3x_qqq_wealth"].iloc[-1], 1)
        self.assertLess(path["daily_3x_qqq_wealth"].iloc[-1], 1)
        last = path.iloc[-1]
        self.assertAlmostEqual(last["reset_wealth_gap"],
                               last["trend_wealth_gap"] + last["variance_wealth_gap"])
        self.assertLess(last["fee_wealth_gap"], 0)

    def test_daily_reset_and_short_marks_respect_initial_close(self):
        block = self.frame.iloc[:2].copy()
        block["tqqq_simple_return"] = [-0.20, 2]
        path = build_paths(block, self.sample)
        np.testing.assert_allclose(path["tqqq_drawdown"], [-0.20, 0], atol=1e-12)
        np.testing.assert_allclose(path["short_tqqq_pnl"], [0.20, -1.40], atol=1e-12)
        self.assertNotEqual(path["sqqq_cum_return"].iloc[-1], path["short_tqqq_pnl"].iloc[-1])

    def test_rolling_has_complete_causal_windows_only(self):
        cutoff = self.sample.windows[-1] + 4
        prefix = self.frame.iloc[:cutoff]
        known = rolling_metrics(prefix, self.sample)
        revised = self.frame.iloc[:cutoff + 2].copy()
        revised.iloc[cutoff:, revised.columns.get_loc("qqq_simple_return")] = [0.05, -0.08]
        complete = rolling_metrics(revised, self.sample)
        past = complete.loc[complete["date"] <= prefix.index[-1]].reset_index(drop=True)
        pd.testing.assert_frame_equal(known, past)
        for window in self.sample.windows:
            subset = known.loc[known["window_days"] == window]
            self.assertEqual(len(subset), cutoff - window + 1)
            self.assertEqual(subset["date"].iloc[0], prefix.index[window - 1])

    def test_wealth_paths_reproducible_as_expanding_prefix(self):
        complete = build_paths(self.frame.iloc[:100], self.sample)
        prefix = build_paths(self.frame.iloc[:70], self.sample)
        pd.testing.assert_frame_equal(complete.iloc[:70], prefix)


    def test_same_sample_reproduces_part1_index_path(self):
        paths = build_paths(self.frame, self.sample)
        part1 = pd.read_csv(ROOT / "outputs/part1/tables/part1_replication_path.csv")
        self.assertAlmostEqual(paths["tqqq_wealth"].iloc[-1],
                               part1["TQQQ_adjusted_price_wealth_index"].iloc[-1], places=7)
        self.assertAlmostEqual(paths["daily_3x_ndx_wealth"].iloc[-1],
                               part1["TQQQ_idealized_3x_wealth_index"].iloc[-1], places=7)
        compared = benchmark_sensitivity(paths, self.sample)
        np.testing.assert_allclose(compared["reset_gap"] + compared["implementation_gap"],
                                   compared["actual_linear_gap"], atol=1e-12)

    def test_two_day_examples_and_one_day_holding_identity(self):
        cases = two_day_examples(self.sample)
        beta = self.sample.leverage
        np.testing.assert_allclose(cases["reset_gap"],
                                   beta * (beta - 1) * cases["day1"] * cases["day2"], atol=1e-12)
        result = holding_periods(self.frame, self.sample)
        one_day = result.loc[result["window_days"] == 1]
        self.assertEqual(len(one_day), 2 * len(self.frame))
        np.testing.assert_allclose(one_day["reset_gap"], 0, atol=1e-12)
        self.assertTrue(one_day["analysis_start"].eq(one_day["analysis_end"]).all())


if __name__ == "__main__":
    unittest.main()
