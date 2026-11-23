"""Generate the Part 1 descriptive table, daily OLS table and leverage scatter.

Run ``python outputs/part1/analyze_part1.py`` from the repository root after
installing requirements.txt. The script reads frozen canonical simple
returns, never downloads or modifies input data, and exports both CSV and
verified Stata 14+ DTA tables. Paths, dates and leverage come from project.yaml.

The regression is a full-sample market-return diagnostic, not a NAV tracking
assessment or an out-of-sample backtest. No coefficient hypothesis tests
are reported. ETF adjusted returns and the NDX price return differ in their
distribution treatment.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # Run without a graphical desktop, including in CI.
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from leveraged_etf_risk.plotting import set_plot_style  # noqa: E402
from export_part1_stata import export_one  # noqa: E402

ASSETS = ("tqqq", "qqq", "ndx", "sqqq")
RETURN_COLUMNS = tuple(f"{asset}_simple_return" for asset in ASSETS)
TABLE_NAMES = (
    "table_part1_descriptive_statistics",
    "table_part1_daily_leverage_check",
)
FIGURE_NAME = "fig_part1_daily_leverage_check.png"


def load_returns(
    path: Path, start_date: str, end_date: str | None
) -> pd.DataFrame:
    """Read a canonical CSV and select an inclusive date window.

    Required return columns contain daily simple returns in decimals
    (0.01 = 1%). Validate the entire input before selecting dates. Reject
    missing/invalid values rather than silently dropping or filling rows.
    Review flags are retained as booleans, not used as exclusion criteria.
    Return an independent, date-ordered frame with at least 3 observations.
    """
    frame = pd.read_csv(path)
    required = {"date", "manual_review_flag", *RETURN_COLUMNS}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Missing canonical columns: {', '.join(missing)}")

    if not frame["date"].astype(str).str.fullmatch(r"\d{4}-\d{2}-\d{2}").all():
        raise ValueError("date must contain non-missing YYYY-MM-DD values")
    frame["date"] = pd.to_datetime(frame["date"], format="%Y-%m-%d", errors="raise")
    if not frame["date"].is_unique or not frame["date"].is_monotonic_increasing:
        raise ValueError("Dates must be unique and ascending; rerun cleaning first")

    for column in RETURN_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    values = frame[list(RETURN_COLUMNS)].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("All required daily returns must be non-missing and finite")
    if (values <= -1.0).any():
        raise ValueError("Positive-price simple returns must be greater than -1")

    flags = frame["manual_review_flag"].astype(str).str.lower()
    if not flags.isin(("true", "false", "1", "0")).all():
        raise ValueError("manual_review_flag must contain only True/False or 1/0")
    frame["manual_review_flag"] = flags.isin(("true", "1"))

    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date) if end_date is not None else frame["date"].max()
    if pd.isna(start) or pd.isna(end) or start > end:
        raise ValueError("Analysis dates must be valid, with start <= end")
    sample = frame.loc[frame["date"].between(start, end)].copy().reset_index(drop=True)
    if len(sample) < 3:
        raise ValueError("The configured analysis window needs at least 3 observations")
    return sample


def descriptive_statistics(frame: pd.DataFrame) -> pd.DataFrame:
    """Summarize each asset's daily decimal simple returns as percentages.

    Output has one row per asset: count, arithmetic mean, sample standard
    deviation (ddof=1), minimum and maximum. Percent columns store 1 for 1%.
    Actual sample endpoints are included in both table formats.
    """
    rows = []
    for asset, column in zip(ASSETS, RETURN_COLUMNS, strict=True):
        returns = frame[column]
        rows.append(
            {
                "asset": asset.upper(),
                "observations": len(returns),
                "mean_daily_pct": 100.0 * returns.mean(),
                "daily_sd_pct": 100.0 * returns.std(ddof=1),
                "min_daily_pct": 100.0 * returns.min(),
                "max_daily_pct": 100.0 * returns.max(),
            }
        )
    table = pd.DataFrame(rows)
    table["analysis_start"] = frame["date"].min()
    table["analysis_end"] = frame["date"].max()
    return table


def daily_leverage_check(frame: pd.DataFrame, leverage: float) -> pd.DataFrame:
    """Fit R_TQQQ = intercept + slope * r_NDX + residual by OLS.

    Inputs are aligned daily simple decimal returns. Include an intercept.
    Output is a numeric metric/value table with explicit units and actual
    dates. The fixed-target gap R_TQQQ - leverage*r_NDX is NOT the fitted
    OLS residual. Its SD is a sample SD (ddof=1).
    """
    if not np.isfinite(leverage) or leverage <= 0:
        raise ValueError("Part 1 target leverage must be finite and positive")
    x = frame["ndx_simple_return"].to_numpy(dtype=float)
    y = frame["tqqq_simple_return"].to_numpy(dtype=float)
    if len(x) < 3 or np.ptp(x) == 0.0 or np.ptp(y) == 0.0:
        raise ValueError("OLS needs at least 3 rows and nonconstant NDX/TQQQ returns")
    design = np.column_stack((np.ones(len(x)), x))
    (intercept, slope), _, rank, _ = np.linalg.lstsq(design, y, rcond=None)
    if rank != 2:
        raise ValueError("OLS design is rank deficient")
    residual = y - (intercept + slope * x)
    r_squared = 1.0 - np.sum(residual**2) / np.sum((y - y.mean()) ** 2)
    gap = y - leverage * x
    table = pd.DataFrame(
        [
            ("observations", len(x), "count"),
            ("target_leverage", leverage, "multiple"),
            ("intercept_daily_decimal", intercept, "daily decimal return"),
            ("slope", slope, "dimensionless"),
            ("r_squared", r_squared, "fraction"),
            ("correlation", np.corrcoef(x, y)[0, 1], "dimensionless"),
            ("mean_fixed_target_gap_decimal", gap.mean(), "daily decimal return"),
            ("sd_fixed_target_gap_decimal", gap.std(ddof=1), "daily decimal return"),
        ],
        columns=["metric", "value", "unit"],
    )
    if not np.isfinite(table["value"]).all():
        raise ValueError("OLS produced non-finite metrics")
    table["analysis_start"] = frame["date"].min()
    table["analysis_end"] = frame["date"].max()
    return table


def plot_daily_leverage(
    frame: pd.DataFrame, checks: pd.DataFrame, path: Path
) -> None:
    """Save a 300-dpi PNG with daily percent axes, both lines and review dates.

    The plotted points use the same complete sample as both output tables.
    Returns remain decimal internally; PercentFormatter only changes labels.
    """
    metrics = checks.set_index("metric")["value"]
    x = frame["ndx_simple_return"]
    y = frame["tqqq_simple_return"]
    grid = np.linspace(x.min(), x.max(), 200)
    set_plot_style()
    fig, ax = plt.subplots(figsize=(9, 6.3))
    try:
        ax.scatter(x, y, s=13, alpha=0.30, color="#416788", edgecolors="none",
                   label="Daily observations", zorder=2)
        leverage = metrics["target_leverage"]
        ax.plot(grid, leverage * grid, "--", color="#a85e2d", linewidth=1.8,
                label=f"Ideal daily target: y = {leverage:g}x", zorder=3)
        ax.plot(grid, metrics["intercept_daily_decimal"] + metrics["slope"] * grid,
                color="#173b57", linewidth=1.5, label="Fitted OLS with intercept", zorder=4)
        flagged = frame.loc[frame["manual_review_flag"]]
        if not flagged.empty:
            ax.scatter(flagged["ndx_simple_return"], flagged["tqqq_simple_return"],
                       s=42, marker="D", color="#c48423", edgecolors="white",
                       linewidths=0.6, label="Flagged for review (retained)", zorder=5)
            for row in flagged.itertuples(index=False):
                positive = row.ndx_simple_return >= 0
                ax.annotate(
                    f"{row.date:%Y-%m-%d}",
                    (row.ndx_simple_return, row.tqqq_simple_return),
                    xytext=(-20, 16) if positive else (20, -20),
                    textcoords="offset points", ha="right" if positive else "left",
                    fontsize=9, color="#68470e",
                    arrowprops={"arrowstyle": "-", "color": "#a58a5b", "lw": 0.7},
                )
        ax.axhline(0, color="#a0a0a0", linewidth=0.6, zorder=1)
        ax.axvline(0, color="#a0a0a0", linewidth=0.6, zorder=1)
        ax.set(
            xlabel="NDX daily simple return (%)",
            ylabel="TQQQ daily adjusted-price return (%)",
            title="Daily leverage diagnostic: TQQQ versus Nasdaq-100",
        )
        ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
        ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
        ax.grid(alpha=0.22)
        ax.margins(0.08)
        ax.text(
            0.03, 0.96,
            f"Slope = {metrics['slope']:.4f}\n"
            f"Daily intercept = {1e4 * metrics['intercept_daily_decimal']:.3f} bp\n"
            f"R-squared = {metrics['r_squared']:.6f}",
            transform=ax.transAxes, va="top", fontsize=10,
            bbox={"facecolor": "white", "edgecolor": "#dddddd", "alpha": 0.94},
        )
        ax.legend(loc="lower right", frameon=True)
        fig.text(
            0.11, 0.045,
            f"{frame.date.min():%Y-%m-%d} to {frame.date.max():%Y-%m-%d}; "
            f"n = {len(frame):,}; source: frozen Yahoo Finance extract.\n"
            "ETF adjusted market prices versus NDX price index. Full-sample diagnostic; not fund NAV tracking.",
            fontsize=8, color="#444444",
        )
        fig.tight_layout(rect=(0, 0.10, 1, 1))
        fig.savefig(path, bbox_inches="tight")
    finally:
        plt.close(fig)


def run_analysis(
    input_path: Path,
    output_dir: Path,
    leverage: float,
    start_date: str,
    end_date: str | None,
) -> tuple[pd.DataFrame, pd.DataFrame, list[Path]]:
    """Read frozen data and write two CSV/DTA pairs plus one PNG.

    input_path is a canonical CSV, output_dir is the Part 1 output root,
    leverage is a positive multiple, and dates are inclusive ISO dates.
    Return both tables and the five generated paths. Never mutate inputs.
    Existing generated files with these exact names are regenerated.
    """
    frame = load_returns(input_path, start_date, end_date)
    stats = descriptive_statistics(frame)
    checks = daily_leverage_check(frame, leverage)
    table_dir, figure_dir = output_dir / "tables", output_dir / "figures"
    table_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for name, table in zip(TABLE_NAMES, (stats, checks), strict=True):
        csv_path = table_dir / f"{name}.csv"
        table.to_csv(csv_path, index=False, date_format="%Y-%m-%d")
        dta_path, _, _ = export_one(csv_path)
        outputs.extend((csv_path, dta_path))
    figure_path = figure_dir / FIGURE_NAME
    plot_daily_leverage(frame, checks, figure_path)
    outputs.append(figure_path)
    print(f"Sample: {frame.date.min():%Y-%m-%d} to {frame.date.max():%Y-%m-%d}; "
          f"n={len(frame):,}; retained review flags={int(frame.manual_review_flag.sum())}")
    return stats, checks, outputs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config/project.yaml",
                        help="YAML settings; relative data/output paths resolve from the repo root")
    parser.add_argument("--output-dir", type=Path,
                        help="optional alternative output root for a disposable run")
    args = parser.parse_args()
    with args.config.open() as handle:
        config = yaml.safe_load(handle)
    part1 = config["part1"]
    output_dir = args.output_dir if args.output_dir is not None else ROOT / part1["output_dir"]
    stats, checks, outputs = run_analysis(
        input_path=ROOT / config["data"]["processed_file"],
        output_dir=output_dir,
        leverage=float(part1["leverage"]),
        start_date=part1["analysis_start_date"],
        end_date=part1["analysis_end_date"],
    )
    print("\nDescriptive statistics (daily percent; sample SD):")
    print(stats.to_string(index=False, float_format=lambda value: f"{value:.6f}"))
    print("\nDaily OLS: TQQQ = intercept + slope * NDX + residual")
    print(checks.to_string(index=False, float_format=lambda value: f"{value:.10g}"))
    print("\nGenerated files (CSV/DTA round trips verified):")
    for path in outputs:
        print(path.resolve())


if __name__ == "__main__":
    main()
