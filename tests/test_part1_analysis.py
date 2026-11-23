"""Check analysis units, fitted versus target gaps and frozen-input safety."""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "outputs" / "part1"))

from analyze_part1 import (  # noqa: E402
    FIGURE_NAME,
    RETURN_COLUMNS,
    daily_leverage_check,
    descriptive_statistics,
    load_returns,
    run_analysis,
)


def sample_frame():
    x = np.array([-0.02, -0.01, 0.0, 0.01, 0.02])
    # Residual is orthogonal to both the constant and x. Known OLS coefficients.
    residual = np.array([0.001, -0.002, 0.002, -0.002, 0.001])
    return pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=5),
        "ndx_simple_return": x,
        "qqq_simple_return": x,
        "tqqq_simple_return": 0.001 + 2.5 * x + residual,
        "sqqq_simple_return": -3.0 * x,
        "manual_review_flag": [True, False, False, False, True],
    })


class Part1AnalysisTests(unittest.TestCase):
    def test_descriptive_units_and_sample_sd(self):
        frame = sample_frame()
        table = descriptive_statistics(frame).set_index("asset")
        self.assertEqual(table.loc["NDX", "observations"], 5)
        self.assertAlmostEqual(table.loc["NDX", "mean_daily_pct"], 0.0)
        self.assertAlmostEqual(table.loc["NDX", "daily_sd_pct"], np.sqrt(2.5))
        self.assertAlmostEqual(table.loc["NDX", "min_daily_pct"], -2.0)
        self.assertAlmostEqual(table.loc["NDX", "max_daily_pct"], 2.0)

    def test_known_ols_and_target_gap_are_distinct(self):
        frame = sample_frame()
        metrics = daily_leverage_check(frame, 3.0).set_index("metric")["value"]
        self.assertAlmostEqual(metrics["intercept_daily_decimal"], 0.001)
        self.assertAlmostEqual(metrics["slope"], 2.5)
        self.assertAlmostEqual(metrics["r_squared"], 1.0 - 0.000014 / 0.006264)
        self.assertAlmostEqual(metrics["mean_fixed_target_gap_decimal"], 0.001)
        gap = frame.tqqq_simple_return - 3 * frame.ndx_simple_return
        self.assertAlmostEqual(metrics["sd_fixed_target_gap_decimal"], gap.std(ddof=1))
        # Fitted residuals have mean zero; a fixed-target gap need not.
        self.assertNotAlmostEqual(metrics["mean_fixed_target_gap_decimal"], 0.0)

    def test_reject_degenerate_regression_and_invalid_leverage(self):
        for column in ("ndx_simple_return", "tqqq_simple_return"):
            frame = sample_frame()
            frame[column] = 0.01
            with self.subTest(column=column), self.assertRaises(ValueError):
                daily_leverage_check(frame, 3.0)
        for leverage in (0, -3, float("nan"), float("inf")):
            with self.subTest(leverage=leverage), self.assertRaises(ValueError):
                daily_leverage_check(sample_frame(), leverage)

    def test_validate_dates_returns_and_flags_without_silent_dropping(self):
        invalid = {}
        frame = sample_frame()
        invalid["duplicate_date"] = pd.concat([frame.iloc[:1], frame])
        invalid["descending_dates"] = frame.iloc[::-1]
        invalid["missing_column"] = frame.drop(columns=[RETURN_COLUMNS[0]])
        invalid["missing_date"] = frame.assign(date=pd.NaT)
        invalid["missing_return"] = frame.assign(qqq_simple_return=np.nan)
        invalid["infinite_return"] = frame.assign(qqq_simple_return=np.inf)
        invalid["invalid_price_return"] = frame.assign(qqq_simple_return=-1.0)
        invalid["invalid_flag"] = frame.assign(manual_review_flag="unknown")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "input.csv"
            for reason, bad_frame in invalid.items():
                with self.subTest(reason=reason):
                    bad_frame.to_csv(path, index=False, date_format="%Y-%m-%d")
                    with self.assertRaises(ValueError):
                        load_returns(path, "2024-01-01", "2024-01-05")

    def test_configured_window_and_review_observations_are_retained(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "input.csv"
            sample_frame().to_csv(path, index=False, date_format="%Y-%m-%d")
            frame = load_returns(path, "2024-01-02", "2024-01-05")
            self.assertEqual(len(frame), 4)
            self.assertTrue(frame.iloc[-1].manual_review_flag)
            with self.assertRaises(ValueError):
                load_returns(path, "2024-01-04", "2024-01-05")
            with self.assertRaises(ValueError):
                load_returns(path, "2024-01-05", "2024-01-01")

    def test_pipeline_exports_matching_dates_and_preserves_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "input.csv"
            sample_frame().to_csv(path, index=False, date_format="%Y-%m-%d")
            original = path.read_bytes()
            with contextlib.redirect_stdout(io.StringIO()):
                stats, checks, outputs = run_analysis(
                    path, root / "outputs", 3.0, "2024-01-01", "2024-01-05"
                )
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(len(outputs), 5)
            for output in outputs:
                self.assertTrue(output.is_file())
                if output.suffix == ".csv":
                    csv = pd.read_csv(output)
                    dta = pd.read_stata(output.with_suffix(".dta"))
                    self.assertEqual(dta.shape, csv.shape)
                    pd.testing.assert_series_equal(
                        dta["analysis_start"], pd.to_datetime(csv["analysis_start"]),
                        check_dtype=False,
                    )
                    np.testing.assert_allclose(
                        dta.select_dtypes("number"), csv.select_dtypes("number"),
                        rtol=1e-12, atol=1e-12,
                    )
            self.assertTrue((root / "outputs/figures" / FIGURE_NAME).read_bytes().startswith(b"\x89PNG"))
            self.assertTrue(stats.observations.eq(5).all())
            self.assertEqual(checks.set_index("metric").loc["observations", "value"], 5)


if __name__ == "__main__":
    unittest.main()
