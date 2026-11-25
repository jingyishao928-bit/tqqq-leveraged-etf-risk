"""Build the Part 2 historical analysis from the frozen canonical dataset."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from export_part1_stata import prepare_frame, verify_round_trip  # noqa: E402

REGIMES = (
    ("COVID sell-off", "2020-02-20", "2020-03-23"),
    ("COVID rebound", "2020-03-24", "2020-09-02"),
    ("Rate-hike bear market", "2022-01-04", "2022-12-30"),
    ("April tariff volatility", "2025-04-01", "2025-04-30"),
)
ASSETS = ("QQQ", "TQQQ", "SQQQ")
TABLES = {
    "daily": "part2_daily_paths",
    "rolling": "part2_rolling_metrics",
    "performance": "table_part2_performance",
    "regimes": "table_part2_regime_attribution",
    "tracking": "table_part2_tracking",
    "positions": "table_part2_positions",
    "metrics": "table_part2_key_metrics",
    "cumulative_path": "part2_cumulative_path",
    "examples": "table_part2_two_day_example",
    "holding": "table_part2_holding_period",
    "holding_summary": "table_part2_holding_period_summary",
    "fees": "table_part2_fee_sensitivity",
    "benchmarks": "table_part2_benchmark_sensitivity",
}


@dataclass(frozen=True)
class Sample:
    """Frozen Part 1 settings and dates, with rates in decimal units."""

    base: pd.Timestamp
    start: pd.Timestamp
    end: pd.Timestamp
    n: int
    annual_days: int
    leverage: float
    fee: float
    gross_fee: float
    windows: tuple[int, ...]
    horizons: tuple[int, ...]
    output_dir: Path
    fee_accessed: str
    fee_source: str
    checked_rows: int


def load_sample(root: Path = ROOT) -> tuple[Sample, pd.DataFrame]:
    """Validate the reviewed CSV snapshot and return sorted decimal returns.

    The first common price date is read from the audit metadata. Each
    canonical return, including the first, remains in the analysis.
    """
    cfg = yaml.safe_load((root / "config/project.yaml").read_text())
    data = cfg["data"]
    part1 = cfg["part1"]
    part2 = cfg["part2"]
    meta = root / "data/metadata"
    audit = pd.read_csv(meta / "part1_checksums.csv").set_index("path")
    for name in (data["processed_file"], "data/metadata/part1_data_quality.csv",
                 "data/metadata/part1_product_facts.csv"):
        content = (root / name).read_bytes()
        if len(content) != audit.at[name, "bytes"] or sha256(content).hexdigest() != audit.at[name, "sha256"]:
            raise ValueError(f"Frozen input does not match the Part 1 checksum: {name}")

    quality = pd.read_csv(meta / "part1_data_quality.csv").set_index("check")["value"]
    fact = pd.read_csv(meta / "part1_product_facts.csv").set_index(["ticker", "fact"])
    fee = fact.loc[("TQQQ", "net_expense_ratio")]
    base, end = pd.Timestamp(quality["price_start"]), pd.Timestamp(quality["price_end"])
    requested_start = pd.Timestamp(data["start_date"])
    requested_end = pd.Timestamp(part1["analysis_end_date"])
    frame = pd.read_csv(root / data["processed_file"], float_precision="round_trip")
    if not frame["date"].str.fullmatch(r"\d{4}-\d{2}-\d{2}").all():
        raise ValueError("Canonical dates must use YYYY-MM-DD")
    frame["date"] = pd.to_datetime(frame["date"], format="%Y-%m-%d")
    frame = frame.set_index("date", verify_integrity=True)
    if (
        not frame.index.is_monotonic_increasing
        or requested_start != pd.Timestamp(part1["analysis_start_date"])
        or not requested_start <= base < frame.index[0]
        or frame.index[-1] != end or end != requested_end
        or len(frame) != int(quality["return_rows"])
        or len(frame) + 1 != int(quality["price_rows"])
        or data["price_field"] != "adjusted_close"
        or not pd.api.types.is_bool_dtype(frame["manual_review_flag"])
        or frame["manual_review_flag"].sum() != int(quality["manual_review_rows"])
    ):
        raise ValueError("Canonical data does not match the reviewed Part 1 contract")

    cols = [f"{name.lower()}_simple_return" for name in (*ASSETS, "NDX")]
    price_cols = ["qqq_adj_close", "tqqq_adj_close", "sqqq_adj_close", "ndx_close"]
    returns = frame[cols]
    prices = frame[price_cols]
    if (not np.isfinite(returns).all().all() or (returns <= -1).any().any()
            or not np.isfinite(prices).all().all() or (prices <= 0).any().any()):
        raise ValueError("Canonical price or simple return is out of range")
    np.testing.assert_allclose(returns.iloc[1:], prices.pct_change().iloc[1:],
                               rtol=0, atol=2e-12)
    log_returns = frame[[name.replace("_simple_", "_log_") for name in cols]]
    np.testing.assert_allclose(log_returns, np.log1p(returns), rtol=0, atol=2e-12)

    leverage = float(cfg["products"]["bull_beta"])
    annual_days = int(cfg["project"]["trading_days_per_year"])
    fee_rate = float(fee["value"].removesuffix("%")) / 100
    gross_fee = float(fact.at[("TQQQ", "gross_expense_ratio"), "value"].removesuffix("%")) / 100
    windows = tuple(part2["rolling_volatility_windows"])
    horizons = tuple(cfg["risk"]["horizon_days"])
    if (not np.isfinite(leverage) or leverage <= 1 or leverage != part1["leverage"]
            or annual_days <= 0 or not 0 <= fee_rate <= gross_fee < 1
            or len(windows) != 2 or not 2 <= windows[0] < windows[1] <= len(frame)
            or not horizons or horizons[0] != 1
            or tuple(sorted(set(horizons))) != horizons or horizons[-1] > len(frame)
            or cfg["simulation"]["nav_floor"] != 0):
        raise ValueError("Part 1 project settings or expense ratio are invalid")
    return Sample(base, frame.index[0], end, len(frame), annual_days, leverage,
                  fee_rate, gross_fee, windows, horizons, root / part2["output_dir"],
                  fee["accessed_on"], fee["source"], int(quality["manual_review_rows"])), frame


def build_paths(frame: pd.DataFrame, sample: Sample) -> pd.DataFrame:
    """Build chronological wealth, drawdowns and TQQQ P&L per initial dollar.

    Inputs are aligned daily simple decimal returns. All wealth paths start
    at 1 immediately before the first return. No synthetic return is added.
    """
    q = frame["qqq_simple_return"]
    t = frame["tqqq_simple_return"]
    ndx = frame["ndx_simple_return"]
    ideal = sample.leverage * q
    fee_ideal = ideal - sample.fee / sample.annual_days
    ndx_ideal = sample.leverage * ndx
    if (pd.concat([ideal, fee_ideal, ndx_ideal], axis=1) <= -1).any().any():
        raise ValueError("An ideal daily multiplier is nonpositive, so log attribution is undefined")

    path = frame[["qqq_simple_return", "tqqq_simple_return", "sqqq_simple_return",
                  "ndx_simple_return", "manual_review_flag"]].copy()
    for asset in ASSETS:
        prefix = asset.lower()
        wealth = (1 + path[f"{prefix}_simple_return"]).cumprod()
        path[f"{prefix}_wealth"] = wealth
        path[f"{prefix}_cum_return"] = wealth - 1
        path[f"{prefix}_drawdown"] = wealth / wealth.cummax().clip(lower=1) - 1

    path["daily_3x_qqq_wealth"] = (1 + ideal).cumprod()
    path["linear_3x_qqq_wealth"] = 1 + sample.leverage * path["qqq_cum_return"]
    path["fee_3x_qqq_wealth"] = (1 + fee_ideal).cumprod()
    path["ndx_wealth"] = (1 + ndx).cumprod()
    path["daily_3x_ndx_wealth"] = (1 + ndx_ideal).cumprod()
    path["linear_3x_ndx_wealth"] = 1 + sample.leverage * (path["ndx_wealth"] - 1)
    path["ndx_exact_log_drag"] = (np.log1p(ndx_ideal) - sample.leverage * np.log1p(ndx)).cumsum()
    path["ndx_approx_log_drag"] = (-0.5 * sample.leverage * (sample.leverage - 1) * ndx**2).cumsum()
    path["qqq_target_gap"] = t - ideal
    path["ndx_target_gap"] = t - ndx_ideal
    path["trend_wealth_gap"] = path["qqq_wealth"] ** sample.leverage - path["linear_3x_qqq_wealth"]
    path["variance_wealth_gap"] = path["daily_3x_qqq_wealth"] - path["qqq_wealth"] ** sample.leverage
    path["reset_wealth_gap"] = path["daily_3x_qqq_wealth"] - path["linear_3x_qqq_wealth"]
    path["fee_wealth_gap"] = path["fee_3x_qqq_wealth"] - path["daily_3x_qqq_wealth"]
    path["residual_wealth_gap"] = path["tqqq_wealth"] - path["fee_3x_qqq_wealth"]
    path["exact_log_drag"] = (np.log1p(ideal) - sample.leverage * np.log1p(q)).cumsum()
    path["approx_log_drag"] = (-0.5 * sample.leverage * (sample.leverage - 1) * q**2).cumsum()
    path["long_tqqq_pnl"] = path["tqqq_cum_return"]
    path["short_tqqq_pnl"] = -path["long_tqqq_pnl"]
    return path


def rolling_metrics(frame: pd.DataFrame, sample: Sample) -> pd.DataFrame:
    """Compute trailing sample volatilities, OLS slopes and realized log drag.

    Return complete windows only, keyed by close date and trading-day window.
    Returns and annualized volatility are decimal fractions, slopes are
    dimensionless. The end-of-day observations are descriptive.
    """
    q, t, n = (frame[f"{asset}_simple_return"] for asset in ("qqq", "tqqq", "ndx"))
    result = []
    for window in sample.windows:
        if len(frame) < window:
            raise ValueError(f"Sample needs {window} trading-day returns")
        qr, tr, nr = (series.rolling(window, min_periods=window) for series in (q, t, n))
        rows = pd.DataFrame({
            "window_days": window,
            "qqq_ann_vol": qr.std() * np.sqrt(sample.annual_days),
            "tqqq_ann_vol": tr.std() * np.sqrt(sample.annual_days),
            "sqqq_ann_vol": frame["sqqq_simple_return"].rolling(window).std() * np.sqrt(sample.annual_days),
            "beta_qqq": tr.cov(q) / qr.var(),
            "beta_ndx": tr.cov(n) / nr.var(),
            "qqq_window_return": (1 + q).rolling(window).apply(np.prod, raw=True) - 1,
            "window_exact_log_drag": (
                np.log1p(sample.leverage * q) - sample.leverage * np.log1p(q)
            ).rolling(window).sum(),
        })
        result.append(rows.iloc[window - 1:].reset_index())
    return pd.concat(result, ignore_index=True)


def performance_table(path: pd.DataFrame, sample: Sample) -> pd.DataFrame:
    """Summarize daily returns, geometric annual returns and worst drawdowns."""
    rows = []
    for asset in ASSETS:
        name = asset.lower()
        ret = path[f"{name}_simple_return"]
        wealth = path[f"{name}_wealth"]
        trough = path[f"{name}_drawdown"].idxmin()
        wealth_to_trough = pd.concat([pd.Series({sample.base: 1.0}), wealth.loc[:trough]])
        rows.append({
            "asset": asset,
            "observations": sample.n,
            "analysis_start": sample.start,
            "analysis_end": sample.end,
            "daily_mean": ret.mean(),
            "daily_sd": ret.std(),
            "daily_min": ret.min(),
            "daily_max": ret.max(),
            "cumulative_return": wealth.iloc[-1] - 1,
            "annual_return": wealth.iloc[-1] ** (sample.annual_days / sample.n) - 1,
            "annual_volatility": ret.std() * np.sqrt(sample.annual_days),
            "max_drawdown": path.at[trough, f"{name}_drawdown"],
            "peak_date": wealth_to_trough.idxmax().date().isoformat(),
            "trough_date": trough.date().isoformat(),
        })
    return pd.DataFrame(rows)


def regime_table(frame: pd.DataFrame, sample: Sample) -> pd.DataFrame:
    """Rebase each selected historical interval to the prior close."""
    rows = []
    periods = (("Full sample", sample.start, sample.end), *REGIMES)
    for label, start, end in periods:
        window = frame.loc[start:end]
        q = window["qqq_simple_return"]
        terminal = build_paths(window, sample).iloc[-1]
        rows.append({
            "regime": label,
            "analysis_start": window.index[0],
            "analysis_end": window.index[-1],
            "observations": len(window),
            "qqq_annual_vol": q.std() * np.sqrt(sample.annual_days),
            "qqq_return": terminal["qqq_cum_return"],
            "tqqq_return": terminal["tqqq_cum_return"],
            "daily_3x_qqq_return": terminal["daily_3x_qqq_wealth"] - 1,
            "linear_3x_qqq_return": terminal["linear_3x_qqq_wealth"] - 1,
            "daily_3x_ndx_return": terminal["daily_3x_ndx_wealth"] - 1,
            "fee_3x_qqq_return": terminal["fee_3x_qqq_wealth"] - 1,
            "valuation_gap": terminal["tqqq_wealth"] - terminal["daily_3x_qqq_wealth"],
            "ndx_valuation_gap": terminal["tqqq_wealth"] - terminal["daily_3x_ndx_wealth"],
            "benchmark_basis_gap": terminal["daily_3x_ndx_wealth"] - terminal["daily_3x_qqq_wealth"],
            "relative_gap": terminal["tqqq_wealth"] / terminal["daily_3x_qqq_wealth"] - 1,
            "trend_gap": terminal["trend_wealth_gap"],
            "variance_gap": terminal["variance_wealth_gap"],
            "reset_gap": terminal["reset_wealth_gap"],
            "fee_gap": terminal["fee_wealth_gap"],
            "relative_fee_gap": terminal["fee_3x_qqq_wealth"] / terminal["daily_3x_qqq_wealth"] - 1,
            "residual_gap": terminal["residual_wealth_gap"],
            "actual_linear_gap": terminal["tqqq_wealth"] - terminal["linear_3x_qqq_wealth"],
            "exact_log_drag": terminal["exact_log_drag"],
            "approx_log_drag": terminal["approx_log_drag"],
        })
    return pd.DataFrame(rows)


def tracking_table(path: pd.DataFrame, sample: Sample) -> pd.DataFrame:
    """Summarize historical fixed-target daily errors with two comparators."""
    rows = []
    for asset in ("qqq", "ndx"):
        gap = path[f"{asset}_target_gap"]
        ideal = sample.leverage * path[f"{asset}_simple_return"]
        ratio = path["tqqq_wealth"].iloc[-1] / path[f"daily_3x_{asset}_wealth"].iloc[-1]
        rows.append({
            "benchmark": asset.upper(),
            "analysis_start": sample.start,
            "analysis_end": sample.end,
            "observations": sample.n,
            "mean_daily_error": gap.mean(),
            "daily_error_sd": gap.std(),
            "daily_error_rmse": np.sqrt((gap**2).mean()),
            "annual_tracking_error": gap.std() * np.sqrt(sample.annual_days),
            "daily_correlation": ideal.corr(path["tqqq_simple_return"]),
            "terminal_relative_gap": ratio - 1,
        })
    return pd.DataFrame(rows)


def position_table(path: pd.DataFrame) -> pd.DataFrame:
    """Report fixed-share P&L normalized by initial dollar exposure."""
    rows = []
    for position, pnl in (
        ("Long TQQQ", path["long_tqqq_pnl"]),
        ("Short TQQQ", path["short_tqqq_pnl"]),
        ("Long SQQQ", path["sqqq_cum_return"]),
    ):
        daily_pnl = np.diff(pnl.to_numpy(), prepend=0.0)
        rows.append({
            "position": position,
            "terminal_pnl_per_dollar": pnl.iloc[-1],
            "worst_mark_per_dollar": min(0.0, pnl.min()),
            "best_mark_per_dollar": max(0.0, pnl.max()),
            "worst_daily_move_per_dollar": daily_pnl.min(),
            "best_daily_move_per_dollar": daily_pnl.max(),
        })
    return pd.DataFrame(rows)


def metric_table(tables: dict[str, pd.DataFrame], sample: Sample) -> pd.DataFrame:
    """Centralize display precision for all numbers cited across deliverables."""
    rows = []

    def record(metric, value, unit, display):
        rows.append((metric, value, unit, display))

    def pct(metric, value, unit="%"):
        record(metric, 100 * value, unit, f"{100 * value:,.2f}{unit if unit == '%' else ' ' + unit}")

    record("base_date", sample.base.date().isoformat(), "date", sample.base.date().isoformat())
    record("analysis_start", sample.start.date().isoformat(), "date", sample.start.date().isoformat())
    record("analysis_end", sample.end.date().isoformat(), "date", sample.end.date().isoformat())
    record("fee_accessed", sample.fee_accessed, "date", sample.fee_accessed)
    for name, value in (("returns", sample.n), ("priced_dates", sample.n + 1),
                        ("annual_days", sample.annual_days), ("review_flags", sample.checked_rows),
                        ("short_window", sample.windows[0]), ("long_window", sample.windows[1])):
        record(name, value, "count", f"{value:,}")
    record("leverage", sample.leverage, "multiple", f"{sample.leverage:g}×")
    record("leverage_number", sample.leverage, "multiple", f"{sample.leverage:g}")
    record("fee_source", sample.fee_source, "source URL", sample.fee_source)
    record("base_wealth", 1, "wealth per initial dollar", "1.00")
    pct("annual_fee_scenario", sample.fee)
    pct("annual_fee_gross", sample.gross_fee)
    for horizon in sample.horizons:
        record(f"holding_days_{horizon}", horizon, "count", str(horizon))
    for key, row in zip(("round_trip", "two_gains", "two_losses"),
                        tables["examples"].itertuples(index=False), strict=True):
        for metric in ("day1", "day2", "underlying_return", "daily_reset_return", "linear_return"):
            value = getattr(row, metric)
            pct(f"{key}_{metric}", 0.0 if abs(value) < 1e-12 else value)
        pct(f"{key}_reset_gap", row.reset_gap, "pp")
    for row in tables["benchmarks"].itertuples(index=False):
        key = row.benchmark.lower()
        for metric in ("ideal_daily_return", "linear_return"):
            pct(f"bench_{key}_{metric}", getattr(row, metric))
        for metric in ("reset_gap", "implementation_gap", "actual_linear_gap"):
            pct(f"bench_{key}_{metric}", getattr(row, metric), "pp")
        for metric in ("exact_log_drag", "approx_log_drag", "approximation_error"):
            pct(f"bench_{key}_{metric}", getattr(row, metric), "log pts")
    for row in tables["fees"].itertuples(index=False):
        key = f"fee_{row.benchmark.lower()}_{row.scenario.lower().replace(' ', '_')}"
        pct(f"{key}_annual_fee", row.annual_fee)
        pct(f"{key}_fee_gap", row.fee_gap, "pp")
        pct(f"{key}_remaining_gap", row.remaining_gap, "pp")
        record(f"{key}_terminal_wealth", row.terminal_wealth, "wealth per initial dollar",
               f"{row.terminal_wealth:.4f}")
    for row in tables["holding_summary"].itertuples(index=False):
        key = f"holding_{row.benchmark.lower()}_{row.window_days}"
        value = 0.0 if abs(row.mean_abs_reset_gap) < 1e-12 else row.mean_abs_reset_gap
        pct(f"{key}_mean_abs_reset_gap", value, "pp")
        pct(f"{key}_mean_exact_log_drag", row.mean_exact_log_drag, "log pts")

    for row in tables["performance"].itertuples(index=False):
        for metric in ("daily_mean", "daily_sd", "daily_min", "daily_max", "cumulative_return",
                       "annual_return", "annual_volatility", "max_drawdown"):
            pct(f"{row.asset}_{metric}", getattr(row, metric))
        for metric in ("peak_date", "trough_date"):
            value = getattr(row, metric)
            record(f"{row.asset}_{metric}", value, "date", value)
    for key, row in zip(("full", "crash", "rebound", "bear", "choppy"),
                        tables["regimes"].itertuples(index=False), strict=True):
        for metric in ("analysis_start", "analysis_end"):
            value = getattr(row, metric).date().isoformat()
            record(f"{key}_{metric}", value, "date", value)
        record(f"{key}_observations", row.observations, "count", f"{row.observations:,}")
        for metric in ("qqq_annual_vol", "qqq_return", "tqqq_return", "daily_3x_qqq_return",
                       "linear_3x_qqq_return", "daily_3x_ndx_return", "relative_gap", "relative_fee_gap"):
            pct(f"{key}_{metric}", getattr(row, metric))
        for metric in ("valuation_gap", "ndx_valuation_gap", "benchmark_basis_gap",
                       "trend_gap", "variance_gap", "reset_gap", "fee_gap",
                       "residual_gap", "actual_linear_gap"):
            pct(f"{key}_{metric}", getattr(row, metric), "pp")
        pct(f"{key}_reset_gap_abs", abs(row.reset_gap), "pp")
        pct(f"{key}_benchmark_basis_gap_abs", abs(row.benchmark_basis_gap), "pp")
        pct(f"{key}_relative_fee_gap_abs", abs(row.relative_fee_gap))
        for metric in ("exact_log_drag", "approx_log_drag"):
            pct(f"{key}_{metric}", getattr(row, metric), "log pts")
    for row in tables["tracking"].itertuples(index=False):
        name = row.benchmark
        pct(f"{name}_annual_tracking_error", row.annual_tracking_error)
        pct(f"{name}_terminal_relative_gap", row.terminal_relative_gap)
        record(f"{name}_mean_daily_error", 1e4 * row.mean_daily_error, "bp",
               f"{1e4 * row.mean_daily_error:.2f} bp")
        record(f"{name}_daily_correlation", row.daily_correlation, "correlation", f"{row.daily_correlation:.4f}")
    for row in tables["positions"].itertuples(index=False):
        key = row.position.lower().replace(" ", "_")
        for metric in ("terminal_pnl_per_dollar", "worst_mark_per_dollar", "best_mark_per_dollar",
                       "worst_daily_move_per_dollar", "best_daily_move_per_dollar"):
            value = getattr(row, metric)
            precision = 4 if key == "long_sqqq" else 2
            record(f"{key}_{metric}", value, "USD per initial USD",
                   f"{'-' if value < 0 else ''}${abs(value):.{precision}f}")
            if metric == "worst_mark_per_dollar":
                record(f"{key}_{metric}_abs", abs(value), "USD per initial USD",
                       f"${abs(value):.{precision}f}")
    rolling = tables["rolling"]
    long_window = rolling.loc[rolling["window_days"] == sample.windows[-1]]
    for benchmark in ("qqq", "ndx"):
        slope = long_window[f"beta_{benchmark}"]
        for stat, value in (("min", slope.min()), ("max", slope.max())):
            record(f"beta_{benchmark}_{stat}", value, "multiple", f"{value:.3f}×")
    for asset in ("qqq", "tqqq"):
        for window in sample.windows:
            max_vol = rolling.loc[rolling["window_days"] == window, f"{asset}_ann_vol"].max()
            pct(f"{asset}_peak_vol_{window}", max_vol)
    corr = long_window["qqq_ann_vol"].corr(-long_window["window_exact_log_drag"])
    record("vol_drag_correlation", corr, "correlation", f"{corr:.3f}")
    return pd.DataFrame(rows, columns=["metric", "value", "unit", "display"])


def compute_tables(frame: pd.DataFrame, sample: Sample) -> dict[str, pd.DataFrame]:
    """Return the proposed Part 2 table payloads without writing files."""
    from part2_sensitivity import (
        benchmark_sensitivity, cumulative_path, fee_sensitivity, holding_periods,
        summarize_holding_periods, two_day_examples,
    )

    path = build_paths(frame, sample)
    windows = holding_periods(frame, sample)
    tables = {
        "daily": path.reset_index(),
        "rolling": rolling_metrics(frame, sample),
        "performance": performance_table(path, sample),
        "regimes": regime_table(frame, sample),
        "tracking": tracking_table(path, sample),
        "positions": position_table(path),
        "cumulative_path": cumulative_path(path, sample),
        "examples": two_day_examples(sample),
        "holding": windows,
        "holding_summary": summarize_holding_periods(windows),
        "fees": fee_sensitivity(frame, sample),
        "benchmarks": benchmark_sensitivity(path, sample),
    }
    tables["metrics"] = metric_table(tables, sample)
    return tables


def export_table(frame: pd.DataFrame, path: Path) -> None:
    """Use the repository's Stata schema and verify each CSV/DTA pair."""
    if frame.isna().any().any() or not np.isfinite(frame.select_dtypes("number")).all().all():
        raise ValueError(f"Missing or non-finite values in {path.name}")
    frame.to_csv(path, index=False, date_format="%Y-%m-%d")
    prepared, labels, dates = prepare_frame(path)
    prepared.to_stata(
        path.with_suffix(".dta"), version=118, write_index=False, variable_labels=labels,
        convert_dates=dates, data_label=f"Exported from {path.name}",
        time_stamp=datetime(2000, 1, 1),  # Fixed file metadata for reproducible bytes.
    )
    verify_round_trip(prepared, path.with_suffix(".dta"))


def run(output: Path | None) -> None:
    """Write all verified Part 2 artifacts under the requested output root."""
    from part2_documents import render_documents
    from part2_figures import render_figures

    sample, frame = load_sample()
    output = output if output is not None else sample.output_dir
    tables = compute_tables(frame, sample)
    for folder in ("tables", "figures"):
        (output / folder).mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        export_table(table, output / "tables" / f"{TABLES[name]}.csv")
    render_figures(output / "figures", sample, tables)
    for name, document in render_documents(tables["metrics"]).items():
        (output / name).write_text(document, encoding="utf-8")
    print(tables["metrics"][["metric", "display"]].to_csv(index=False), end="")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path)
    run(parser.parse_args().output_dir)


if __name__ == "__main__":
    main()
