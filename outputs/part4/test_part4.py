"""Regression tests for the Part 4 financial conventions and upstream handoff."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np

from part4_risk_results import (
    PART3_TABLES, ROOT, Settings, baseline_quantiles, calibrate, load_baseline,
    published_parameters, read_returns, verify_frozen_input,
)
from part4_analysis import (
    MAIN_MODEL, daily_reset, garch_paths, position_loss, position_records, quantile_audit,
    replay_part3_paths, rolling_terminal, student_shocks, tail_records,
)


class Part4Conventions(unittest.TestCase):
    """Exercise the financial cases that could silently change a tail estimate."""

    @classmethod
    def setUpClass(cls):
        cls.settings = Settings.from_repo(ROOT)
        cls.frame = read_returns(cls.settings)
        cls.fit = calibrate(cls.frame, cls.settings)

    def test_fixed_share_short_and_daily_inverse_after_a_round_trip(self):
        log_returns = np.log([1.10, 1 / 1.10])
        bull = daily_reset(log_returns, 3.0, 0.0)[-1]
        inverse = daily_reset(log_returns, -3.0, 0.0)[-1]
        self.assertAlmostEqual(position_loss(bull, "Short"), -position_loss(bull, "Long"))
        self.assertGreater(1 - bull, 0.0)
        self.assertGreater(position_loss(inverse, "Long"), 0.0)
        self.assertAlmostEqual(daily_reset(np.log([0.5, 1.5]), 3.0, 0.0)[-1], 0.0)
        self.assertAlmostEqual(position_loss(np.array([2.0]), "Short")[0], 1.0)

    def test_inclusive_es_and_strict_reverse_stress_thresholds(self):
        loss = np.array([0.0, 0.50, 0.80, 1.0, 1.0, 1.01])
        row = tail_records(loss, (0.8,))[0]
        self.assertEqual(row["var_loss"], 1.0)
        self.assertEqual(row["tail_observations"], 3)
        self.assertAlmostEqual(row["es_loss"], (2 + 1.01) / 3)
        rows = position_records({"Short TQQQ": loss}, self.settings, horizon_days=21)
        self.assertEqual(rows[0]["count_loss_gt_50"], 4)
        self.assertEqual(rows[0]["count_loss_gt_100"], 1)
        self.assertEqual(rows[0]["max_sample_loss"], 1.01)

    def test_historical_rolling_windows_use_only_their_own_returns(self):
        log_returns = np.log([1.10, 0.95, 1.25, 0.85])
        initial = rolling_terminal(log_returns, 2)
        log_returns[-1] = 0.0
        changed = rolling_terminal(log_returns, 2)
        np.testing.assert_allclose(initial[:2], changed[:2])
        self.assertNotEqual(initial[2], changed[2])

    def test_conditional_paths_share_shocks_reproducibly(self):
        rng_a = np.random.default_rng(self.settings.seed)
        rng_b = np.random.default_rng(self.settings.seed)
        a = student_shocks(rng_a, self.settings, self.fit.nu)
        b = student_shocks(rng_b, self.settings, self.fit.nu)
        np.testing.assert_array_equal(a, b)
        calm = garch_paths(a, 1.0, self.fit)
        stress = garch_paths(b, 2.0, self.fit)
        np.testing.assert_allclose(
            100.0 * stress[:, 0] - self.fit.mean_pct,
            2.0 * (100.0 * calm[:, 0] - self.fit.mean_pct),
        )

    def test_seeded_fallback_for_missing_part3_files(self):
        with TemporaryDirectory() as folder:
            paths, sources = load_baseline(Path(folder), self.frame, self.settings, self.fit)
        replay = replay_part3_paths(self.frame, self.settings, self.fit)
        self.assertEqual(set(sources.values()), {"Part 3 Notebook replay"})
        for case in paths:
            np.testing.assert_array_equal(paths[case], replay[case])
        baseline_quantiles(paths, self.settings, published_parameters(self.fit, self.settings), sources)

    def test_published_baseline_matches_notebook_quantiles(self):
        self.assertEqual(len(verify_frozen_input(self.settings, ROOT)), 64)
        drag = published_parameters(self.fit, self.settings)
        paths, sources = load_baseline(PART3_TABLES, self.frame, self.settings, self.fit)
        self.assertEqual(set(sources.values()), {"Published Part 3 CSV"})
        published = baseline_quantiles(paths, self.settings, drag, sources)
        loss = 1.0 - daily_reset(paths[MAIN_MODEL], 3.0, drag)[:, -1]
        audit = quantile_audit(loss, published[MAIN_MODEL]).iloc[0]
        self.assertAlmostEqual(audit.notebook_recomputed_loss, audit.notebook_published_loss, 12)
        self.assertNotEqual(audit.shared_var_loss, audit.notebook_recomputed_loss)


if __name__ == "__main__":
    unittest.main()
