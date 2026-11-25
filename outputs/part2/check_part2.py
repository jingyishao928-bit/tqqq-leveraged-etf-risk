"""Audit the five Part 2 review criteria without editing the frozen inputs."""

from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path
import subprocess

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
import pandas as pd
from PIL import Image, ImageChops

from analyze_part2 import ROOT, TABLES, compute_tables, load_sample
from export_part1_stata import export_one
from part2_documents import METRIC, REPORT, SLIDES, render_documents
from part2_figures import DPI, FIGSIZE, FIGURES
from part2_research import RESEARCH_FIGURES


def check_inputs(sample, frame):
    """Verify all frozen checksums and the initial close against Part 1."""
    audit = pd.read_csv(ROOT / "data/metadata/part1_checksums.csv")
    for row in audit.itertuples(index=False):
        content = (ROOT / row.path).read_bytes()
        if len(content) != row.bytes or sha256(content).hexdigest() != row.sha256:
            raise AssertionError(f"Part 1 input diverged: {row.path}")

    # Read the price-only Part 1 compatibility table as an independent audit.
    prices = pd.read_csv(ROOT / "data/processed/part1_clean_prices.csv",
                         index_col="Date", parse_dates=["Date"], float_precision="round_trip")
    if not prices.index.equals(frame.index.insert(0, sample.base)):
        raise AssertionError("Canonical return dates differ from the Part 1 aligned price dates")
    for ticker in ("QQQ", "TQQQ", "SQQQ", "NDX"):
        np.testing.assert_allclose(prices[f"{ticker}_price"].pct_change().iloc[1:],
                                   frame[f"{ticker.lower()}_simple_return"], rtol=0, atol=2e-12)
    if (sample.leverage, sample.annual_days, sample.windows, sample.horizons) != (3, 252, (21, 63), (1, 10, 21)):
        raise AssertionError("Unexpected leverage or annualization relative to the project specification")


def check_numbers(output, console, expected):
    """Compare all CSV/DTA payloads and the exact display strings in both documents."""
    for key, name in TABLES.items():
        path = output / "tables" / f"{name}.csv"
        actual = pd.read_csv(path, dtype=str, keep_default_na=False)
        from_memory = expected[key].to_csv(index=False, date_format="%Y-%m-%d")
        if path.read_text() != from_memory or actual.eq("").any().any():
            raise AssertionError(f"Incomplete or changed CSV: {path.name}")
        numeric = expected[key].select_dtypes("number")
        if not np.isfinite(numeric).all().all():
            raise AssertionError(f"Non-finite data: {path.name}")
        export_one(path, check_only=True)

    metric_csv = pd.read_csv(output / "tables" / f"{TABLES['metrics']}.csv",
                             dtype=str, keep_default_na=False)
    console_csv = pd.read_csv(console, dtype=str, keep_default_na=False)
    pd.testing.assert_frame_equal(metric_csv[["metric", "display"]], console_csv)
    documents = render_documents(metric_csv)
    for name, doc in documents.items():
        if (output / name).read_text(encoding="utf-8") != doc:
            raise AssertionError(f"Document and numerical ledger differ: {name}")
    referenced = set(METRIC.findall(REPORT)) | set(METRIC.findall(SLIDES))
    return len(referenced)


def check_causality(sample, frame, tables):
    """Recalculate every path and rolling window with explicit past-only slices."""
    daily = tables["daily"].set_index("date")
    q, t, s, n = (frame[f"{asset}_simple_return"].to_numpy()
                  for asset in ("qqq", "tqqq", "sqqq", "ndx"))
    beta, annual, fee = sample.leverage, sample.annual_days, sample.fee
    if not daily.index.equals(frame.index):
        raise AssertionError("A daily observation was omitted or added")
    for label, returns in (("qqq", q), ("tqqq", t), ("sqqq", s)):
        prices = frame[f"{label}_adj_close"]
        initial = prices.iloc[0] / (1 + returns[0])
        wealth = prices.to_numpy() / initial
        future_free_peak = np.maximum.accumulate(np.r_[1, wealth])[1:]
        np.testing.assert_allclose(daily[f"{label}_wealth"], wealth, rtol=2e-11, atol=1e-12)
        np.testing.assert_allclose(daily[f"{label}_drawdown"], wealth / future_free_peak - 1,
                                   rtol=2e-11, atol=1e-12)
        history = np.r_[1, daily[f"{label}_wealth"]]
        np.testing.assert_allclose(np.diff(history) / history[:-1], returns, rtol=2e-11, atol=1e-12)
    for key, changes in (
        ("daily_3x_qqq_wealth", beta * q),
        ("fee_3x_qqq_wealth", beta * q - fee / annual),
        ("daily_3x_ndx_wealth", beta * n),
    ):
        np.testing.assert_allclose(daily[key], np.exp(np.log1p(changes).cumsum()), rtol=2e-11)
    np.testing.assert_allclose(daily["linear_3x_qqq_wealth"], 1 + beta * (daily["qqq_wealth"] - 1),
                               rtol=2e-11)
    np.testing.assert_allclose(daily["long_tqqq_pnl"] + daily["short_tqqq_pnl"], 0, atol=1e-12)

    drag = np.log1p(beta * q) - beta * np.log1p(q)
    exact = np.log(daily["daily_3x_qqq_wealth"] / daily["qqq_wealth"]**beta)
    np.testing.assert_allclose(daily["exact_log_drag"], exact, rtol=2e-11, atol=1e-12)
    rolling = tables["rolling"]
    for window in sample.windows:
        observed = rolling.loc[rolling["window_days"] == window].set_index("date")
        if not observed.index.equals(frame.index[window - 1:]):
            raise AssertionError(f"Rolling window dates are misaligned for {window} days")
        qw, tw, sw, nw = (sliding_window_view(x, window) for x in (q, t, s, n))
        for key, values in (("qqq", qw), ("tqqq", tw), ("sqqq", sw)):
            np.testing.assert_allclose(observed[f"{key}_ann_vol"],
                                       values.std(axis=1, ddof=1) * np.sqrt(annual), rtol=2e-11)
        tc = tw - tw.mean(axis=1, keepdims=True)
        for key, values in (("qqq", qw), ("ndx", nw)):
            centered = values - values.mean(axis=1, keepdims=True)
            np.testing.assert_allclose(observed[f"beta_{key}"],
                                       (tc * centered).sum(axis=1) / (centered**2).sum(axis=1),
                                       rtol=2e-11)
        np.testing.assert_allclose(observed["window_exact_log_drag"],
                                   sliding_window_view(drag, window).sum(axis=1), rtol=2e-11)
        np.testing.assert_allclose(observed["qqq_window_return"],
                                   (1 + qw).prod(axis=1) - 1, rtol=2e-11, atol=1e-12)

    compare_holding_periods(sample, frame, tables)

    cumulative = tables["cumulative_path"].set_index("date")
    part1 = pd.read_csv(ROOT / "outputs/part1/tables/part1_replication_path.csv",
                        index_col="Date", parse_dates=["Date"])
    if not cumulative.index.equals(part1.index) or not cumulative.iloc[0].eq(1).all():
        raise AssertionError("Part 1 and Part 2 wealth anchors differ")
    np.testing.assert_allclose(
        cumulative[["tqqq_wealth", "daily_3x_ndx_wealth"]],
        part1[["TQQQ_adjusted_price_wealth_index", "TQQQ_idealized_3x_wealth_index"]],
        rtol=0, atol=5.1e-9,
    )
    regimes = tables["regimes"].set_index("regime")
    for total, components in (
        ("reset_gap", ("trend_gap", "variance_gap")),
        ("valuation_gap", ("residual_gap", "fee_gap")),
        ("valuation_gap", ("ndx_valuation_gap", "benchmark_basis_gap")),
        ("actual_linear_gap", ("reset_gap", "valuation_gap")),
    ):
        np.testing.assert_allclose(regimes[total], regimes[list(components)].sum(axis=1), atol=1e-12)
    for row in regimes.itertuples():
        phase = frame.loc[row.analysis_start:row.analysis_end]
        r = phase["qqq_simple_return"].to_numpy()
        np.testing.assert_allclose(
            [row.qqq_return, row.daily_3x_qqq_return, row.linear_3x_qqq_return, row.tqqq_return],
            [np.prod(1 + r) - 1, np.prod(1 + beta * r) - 1, beta * (np.prod(1 + r) - 1),
             np.prod(1 + phase["tqqq_simple_return"]) - 1],
            rtol=2e-11,
        )
    if (
        not (regimes["exact_log_drag"] < 0).all()
        or not (regimes["fee_gap"] < 0).all()
        or regimes.at["COVID rebound", "reset_gap"] <= 0
        or not regimes.at["April tariff volatility", "daily_3x_qqq_return"] < 0
        < regimes.at["April tariff volatility", "qqq_return"]
    ):
        raise AssertionError("Historical figure and narrative conclusions need review")



def compare_holding_periods(sample, frame, tables):
    """Independently verify timing, return identities and fee monotonicity."""
    holding = tables["holding"]
    beta = sample.leverage
    for (benchmark, days), group in holding.groupby(["benchmark", "window_days"]):
        history = frame[f"{benchmark.lower()}_simple_return"]
        starts = history.index[:len(history) - days + 1]
        ends = history.index[days - 1:]
        if not pd.Index(group["analysis_start"]).equals(starts) or not pd.Index(group["analysis_end"]).equals(ends):
            raise AssertionError(f"Misaligned {benchmark} holding periods at {days} days")
        q = history.rolling(days)
        t = frame["tqqq_simple_return"].rolling(days)
        ideal = (1 + beta * history).rolling(days).apply(np.prod, raw=True).iloc[days - 1:] - 1
        underlying = q.apply(lambda r: (1 + r).prod(), raw=True).iloc[days - 1:] - 1
        actual = t.apply(lambda r: (1 + r).prod(), raw=True).iloc[days - 1:] - 1
        variance = history.pow(2).rolling(days).sum().iloc[days - 1:]
        np.testing.assert_allclose(group["ideal_daily_return"], ideal, atol=2e-12)
        np.testing.assert_allclose(group["linear_return"], beta * underlying, atol=2e-12)
        np.testing.assert_allclose(group["reset_gap"], ideal - beta * underlying, atol=2e-12)
        np.testing.assert_allclose(group["implementation_gap"], actual - ideal, atol=2e-12)
        np.testing.assert_allclose(group["realized_variance"], variance, atol=2e-12)
        np.testing.assert_allclose(group["approximation_error"],
                                   group["exact_log_drag"] - group["approx_log_drag"], atol=2e-12)
        np.testing.assert_allclose(group["exact_log_drag"],
                                   np.log1p(ideal) - beta * np.log1p(underlying), atol=2e-12)
    one_day = holding.loc[holding["window_days"] == 1]
    np.testing.assert_allclose(one_day["reset_gap"], 0, atol=2e-12)
    for benchmark, group in tables["fees"].groupby("benchmark"):
        if not group.sort_values("annual_fee")["terminal_wealth"].is_monotonic_decreasing:
            raise AssertionError(f"Fee sensitivity is not decreasing for {benchmark}")
        observed = tables["benchmarks"].set_index("benchmark").at[benchmark, "implementation_gap"]
        np.testing.assert_allclose(group["fee_gap"] + group["remaining_gap"], observed, atol=2e-12)
    examples = tables["examples"]
    np.testing.assert_allclose(examples["reset_gap"],
                               beta * (beta - 1) * examples["day1"] * examples["day2"], atol=2e-12)

def check_figures(output) -> int:
    """Verify exact widescreen pixel dimensions, PNG density and rendered content."""
    expected = set(FIGURES.values())
    existing = {path.name for path in (output / "figures").glob("*.png")}
    supplement = set(RESEARCH_FIGURES.values())
    if existing & supplement:
        expected.update(supplement)
    if existing != expected:
        raise AssertionError(f"Figure set mismatch: expected {expected}, found {existing}")
    for name in sorted(expected):
        with Image.open(output / "figures" / name) as png:
            if (png.size != tuple(round(inches * DPI) for inches in FIGSIZE)
                    or png.format != "PNG"
                    or any(abs(dpi - DPI) > 0.01 for dpi in png.info.get("dpi", (0, 0)))):
                raise AssertionError(f"Invalid 16:9 PNG dimensions or DPI: {name}")
            background = Image.new("RGB", png.size, "white")
            ink = ImageChops.difference(png.convert("RGB"), background).getbbox()
            if not ink or ink[0] <= 0 or ink[1] <= 0 or ink[2] >= png.width or ink[3] >= png.height:
                raise AssertionError(f"Blank or clipped figure: {name}")
    return len(expected)


def check_git(base):
    """Confirm that the review includes only Part 2 paths and tests."""
    subprocess.run(["git", "diff", "--check", base], cwd=ROOT, check=True)
    changed = subprocess.check_output(["git", "diff", "--name-only", "-z", base], cwd=ROOT,
                                      text=True).strip("\0").split("\0")
    shared = {".gitignore", "config/project.yaml", "README.md", "outputs/README.md",
              "tests/README.md", "tests/test_part2_analysis.py"}
    other = {path for path in changed if path not in shared and not path.startswith("outputs/part2/")}
    if other:
        raise AssertionError(f"Unexpected review paths: {other}")
    status = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=all", "--ignored=matching"],
        cwd=ROOT, text=True
    )
    leftovers = [line for line in status.splitlines()
                 if line.startswith(("?? ", "!! ")) and not line.startswith("!! .venv/")
                 and "__pycache__" not in line[3:].split("/")]
    if leftovers:
        raise AssertionError(f"Temporary or unreviewed files: {leftovers}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--console", type=Path, required=True)
    parser.add_argument("--git-base", help="Verify the review diff against this Git ref or commit")
    args = parser.parse_args()

    sample, frame = load_sample()
    output = args.output_dir if args.output_dir is not None else sample.output_dir
    check_inputs(sample, frame)
    print("1. PASS — frozen data, dates, row counts and project settings")
    tables = compute_tables(frame, sample)
    metrics = check_numbers(output, args.console, tables)
    print(f"2. PASS — console, CSV/DTA, report and slides ({metrics} cited values)")
    check_causality(sample, frame, tables)
    print("3. PASS — trailing windows, chronological paths and attribution identities")
    count = check_figures(output)
    print(f"4. PASS — {count} full-canvas 16:9 PNGs at {DPI} DPI")
    if args.git_base:
        check_git(args.git_base)
        print("5. PASS — Git diff contains only Part 2 source, outputs and workflow documentation")
    else:
        print("5. SKIP — pass --git-base for pre-submission Git scope verification")


if __name__ == "__main__":
    main()
