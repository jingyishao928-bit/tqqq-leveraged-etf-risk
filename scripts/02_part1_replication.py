"""Create the Part 1 idealized daily-reset replication check.

The check is deliberately diagnostic: it compares a TQQQ adjusted-price
wealth index with an idealized wealth index that compounds 3 times the daily
NDX price return. The gap is not treated as a model error because the TQQQ
adjusted-price series also reflects fees, financing, trading, tracking
differences and distributions, while NDX here is a price index.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import yaml


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from leveraged_etf_risk.plotting import set_plot_style  # noqa: E402


with (ROOT / "config" / "project.yaml").open() as handle:
    PROJECT_CONFIG = yaml.safe_load(handle)

PART1_CONFIG = PROJECT_CONFIG["part1"]
LEVERAGE = float(PART1_CONFIG["leverage"])
PRICES_FILE = ROOT / PART1_CONFIG["prices_file"]
RETURNS_FILE = ROOT / PART1_CONFIG["returns_file"]
OUTPUT_DIR = ROOT / PART1_CONFIG["output_dir"]
TABLE_DIR = OUTPUT_DIR / "tables"
FIGURE_DIR = OUTPUT_DIR / "figures"


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    prices = pd.read_csv(PRICES_FILE, parse_dates=["Date"])
    returns = pd.read_csv(RETURNS_FILE, parse_dates=["Date"])
    frame = prices.merge(
        returns[["Date", "NDX_simple_ret", "TQQQ_simple_ret"]],
        on="Date",
        how="left",
        validate="one_to_one",
    )

    frame["TQQQ_adjusted_price_wealth_index"] = (
        frame["TQQQ_price"] / frame["TQQQ_price"].iloc[0]
    )
    frame["TQQQ_idealized_3x_wealth_index"] = (
        1.0 + LEVERAGE * frame["NDX_simple_ret"].fillna(0.0)
    ).cumprod()
    frame["tracking_gap_pct"] = (
        frame["TQQQ_adjusted_price_wealth_index"]
        / frame["TQQQ_idealized_3x_wealth_index"]
        - 1.0
    )

    output_columns = [
        "Date",
        "TQQQ_adjusted_price_wealth_index",
        "TQQQ_idealized_3x_wealth_index",
        "tracking_gap_pct",
        "NDX_simple_ret",
    ]
    frame[output_columns].to_csv(
        TABLE_DIR / "part1_replication_path.csv", index=False, date_format="%Y-%m-%d", float_format="%.8f"
    )

    first = frame.iloc[0]
    last = frame.iloc[-1]
    actual_daily = frame["TQQQ_simple_ret"]
    target_daily = LEVERAGE * frame["NDX_simple_ret"]
    summary = pd.DataFrame(
        [
            ["analysis_start", first["Date"].date().isoformat()],
            ["analysis_end", last["Date"].date().isoformat()],
            ["leverage_target", LEVERAGE],
            ["common_price_rows", len(frame)],
            ["return_observations", int(frame["NDX_simple_ret"].notna().sum())],
            [
                "adjusted_price_final_wealth_index",
                last["TQQQ_adjusted_price_wealth_index"],
            ],
            [
                "idealized_3x_final_wealth_index",
                last["TQQQ_idealized_3x_wealth_index"],
            ],
            ["final_tracking_gap_pct", last["tracking_gap_pct"]],
            [
                "daily_return_correlation_actual_vs_3x_ndx",
                actual_daily.corr(target_daily),
            ],
            ["mean_daily_actual_minus_ideal_return", (actual_daily - target_daily).mean()],
            ["median_daily_actual_minus_ideal_return", (actual_daily - target_daily).median()],
        ],
        columns=["metric", "value"],
    )
    summary.to_csv(TABLE_DIR / "table_part1_replication.csv", index=False, float_format="%.8f")

    set_plot_style()
    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True, constrained_layout=True)
    axes[0].plot(
        frame["Date"],
        frame["TQQQ_adjusted_price_wealth_index"],
        label="TQQQ adjusted-price wealth index",
        linewidth=1.3,
    )
    axes[0].plot(
        frame["Date"],
        frame["TQQQ_idealized_3x_wealth_index"],
        label="Idealized daily 3x NDX wealth index",
        linewidth=1.1,
    )
    axes[0].set_title("TQQQ adjusted-price wealth versus an idealized daily 3x path")
    axes[0].set_ylabel("Wealth index (start = 1.00)")
    axes[0].legend(loc="upper left")
    axes[1].plot(frame["Date"], 100.0 * frame["tracking_gap_pct"], color="#b23a48", linewidth=1.1)
    axes[1].axhline(0.0, color="black", linewidth=0.8)
    axes[1].set_title("TQQQ adjusted-price wealth relative to the idealized path")
    axes[1].set_ylabel("Gap (%)")
    axes[1].set_xlabel("Date")
    fig.savefig(FIGURE_DIR / "fig_part1_replication.png", bbox_inches="tight")
    plt.close(fig)

    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
