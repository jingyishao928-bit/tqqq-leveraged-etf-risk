"""Reproducible teaching examples, holding-period and benchmark sensitivities."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
import pandas as pd

from leveraged_etf_risk.mechanics import compound_wealth, leveraged_simple_return

if TYPE_CHECKING:
    from analyze_part2 import Sample


def two_day_examples(sample: Sample) -> pd.DataFrame:
    """Compare normalized wealth after two decimal returns in three cases."""
    rows = []
    for label, day1, day2 in (
        ("Round trip", 0.10, 1 / 1.10 - 1),
        ("Two gains", 0.10, 0.10),
        ("Two losses", -0.10, -0.10),
    ):
        returns = (day1, day2)
        underlying = compound_wealth(returns) - 1
        daily = compound_wealth(leveraged_simple_return(r, sample.leverage) for r in returns) - 1
        linear = sample.leverage * underlying
        rows.append((label, day1, day2, underlying, daily, linear, daily - linear))
    return pd.DataFrame(rows, columns=["case", "day1", "day2", "underlying_return",
                                      "daily_reset_return", "linear_return", "reset_gap"])


def holding_periods(frame: pd.DataFrame, sample: Sample) -> pd.DataFrame:
    """Compute historical overlapping trailing windows for NDX and QQQ.

    Dates are the first and last return dates. Realized variance is the sum
    of squared simple returns. Annualized RMS is defined even for one day.
    """
    actual = frame["tqqq_simple_return"].to_numpy()
    leverage = sample.leverage
    tables = []
    for asset in ("NDX", "QQQ"):
        returns = frame[f"{asset.lower()}_simple_return"].to_numpy()
        for horizon in sample.horizons:
            underlying = sliding_window_view(returns, horizon)
            fund = sliding_window_view(actual, horizon)
            underlying_return = (1 + underlying).prod(axis=1) - 1
            actual_return = (1 + fund).prod(axis=1) - 1
            daily_reset = (1 + leverage * underlying).prod(axis=1) - 1
            linear = leverage * underlying_return
            realized_variance = (underlying**2).sum(axis=1)
            exact = (np.log1p(leverage * underlying) - leverage * np.log1p(underlying)).sum(axis=1)
            approx = -0.5 * leverage * (leverage - 1) * realized_variance
            length = len(underlying)
            tables.append(pd.DataFrame({
                "benchmark": asset,
                "window_days": horizon,
                "analysis_start": frame.index[:length],
                "analysis_end": frame.index[horizon - 1:],
                "underlying_return": underlying_return,
                "actual_return": actual_return,
                "ideal_daily_return": daily_reset,
                "linear_return": linear,
                "reset_gap": daily_reset - linear,
                "implementation_gap": actual_return - daily_reset,
                "realized_variance": realized_variance,
                "annualized_rms": np.sqrt(realized_variance * sample.annual_days / horizon),
                "exact_log_drag": exact,
                "approx_log_drag": approx,
                "approximation_error": exact - approx,
            }))
    return pd.concat(tables, ignore_index=True)


def summarize_holding_periods(windows: pd.DataFrame) -> pd.DataFrame:
    """Summarize overlapping-window magnitudes and dispersion by horizon."""
    summaries = []
    for (benchmark, days), rows in windows.groupby(["benchmark", "window_days"], sort=False):
        summaries.append({
            "benchmark": benchmark,
            "window_days": days,
            "observations": len(rows),
            "mean_abs_reset_gap": rows["reset_gap"].abs().mean(),
            "mean_exact_log_drag": rows["exact_log_drag"].mean(),
            "mean_approximation_error": rows["approximation_error"].mean(),
            "mean_implementation_gap": rows["implementation_gap"].mean(),
            "share_ideal_below_linear": (rows["reset_gap"] < -1e-12).mean(),
        })
    return pd.DataFrame(summaries)


def fee_sensitivity(frame: pd.DataFrame, sample: Sample) -> pd.DataFrame:
    """Apply fixed fee scenarios to the two hypothetical daily-reset paths."""
    actual = compound_wealth(frame["tqqq_simple_return"])
    rows = []
    for asset in ("NDX", "QQQ"):
        returns = frame[f"{asset.lower()}_simple_return"]
        ideal = compound_wealth(leveraged_simple_return(r, sample.leverage) for r in returns)
        for scenario, annual_fee in (("No fee", 0.0), ("Net", sample.fee), ("Gross", sample.gross_fee)):
            fee_wealth = compound_wealth(
                leveraged_simple_return(r, sample.leverage, daily_fee=annual_fee / sample.annual_days)
                for r in returns
            )
            rows.append({
                "benchmark": asset,
                "scenario": scenario,
                "annual_fee": annual_fee,
                "terminal_wealth": fee_wealth,
                "cumulative_return": fee_wealth - 1,
                "fee_gap": fee_wealth - ideal,
                "relative_fee_gap": fee_wealth / ideal - 1,
                "remaining_gap": actual - fee_wealth,
            })
    return pd.DataFrame(rows)


def benchmark_sensitivity(path: pd.DataFrame, sample: Sample) -> pd.DataFrame:
    """Compare full-sample attribution against the formal index and ETF proxy."""
    last = path.iloc[-1]
    actual = last["tqqq_wealth"]
    rows = []
    for asset in ("ndx", "qqq"):
        ideal = last[f"daily_3x_{asset}_wealth"]
        linear = last[f"linear_3x_{asset}_wealth"]
        exact_log = last["exact_log_drag" if asset == "qqq" else "ndx_exact_log_drag"]
        approx_log = last["approx_log_drag" if asset == "qqq" else "ndx_approx_log_drag"]
        rows.append({
            "benchmark": asset.upper(),
            "underlying_return": last[f"{asset}_wealth"] - 1,
            "actual_return": actual - 1,
            "ideal_daily_return": ideal - 1,
            "linear_return": linear - 1,
            "reset_gap": ideal - linear,
            "implementation_gap": actual - ideal,
            "actual_linear_gap": actual - linear,
            "exact_log_drag": exact_log,
            "approx_log_drag": approx_log,
            "approximation_error": exact_log - approx_log,
        })
    return pd.DataFrame(rows)


def cumulative_path(path: pd.DataFrame, sample: Sample) -> pd.DataFrame:
    """Export all wealth dates, including the true prior-close anchor."""
    columns = [name for name in path.columns if name.endswith("_wealth")]
    anchor = pd.DataFrame(1.0, index=pd.Index([sample.base], name="date"), columns=columns)
    return pd.concat([anchor, path[columns]]).reset_index()
