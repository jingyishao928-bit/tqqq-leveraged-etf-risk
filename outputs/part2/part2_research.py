"""Additional Part 2 historical diagnostics and presentation figures.

Run with --output-dir to generate CSV/Stata pairs, PNGs and display inputs.
The analysis reads the same audited canonical returns as analyze_part2.py.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator, PercentFormatter, StrMethodFormatter
import numpy as np
import pandas as pd
from scipy import stats

from analyze_part2 import REGIMES, build_paths, compute_tables, export_table, load_sample

INK, MUTED, GRID = "#34383C", "#62676B", "#D6DADD"
TQQQ, NDX, QQQ, SQQQ = "#C64752", "#4B5563", "#4B8B70", "#7B5A98"
BLUE, GOLD, SOFT = "#496C83", "#9C7335", "#F2F3F4"
MAIN_BAND = 0.03


def disjoint_windows(holding: pd.DataFrame, days: int, band: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Classify consecutive complete QQQ blocks using realized inputs.

    One row per block includes decimal cumulative returns, the reset gap
    and annualized RMS of daily returns. The median split is ex post.
    """
    w = holding.loc[(holding["benchmark"] == "QQQ") & (holding["window_days"] == days)]
    w = w.iloc[::days].copy().reset_index(drop=True)
    midpoint = w["annualized_rms"].median()
    w["band"] = band
    w["vol_split"] = midpoint
    w["vol_group"] = np.where(w["annualized_rms"] >= midpoint, "Higher RMS", "Lower RMS")
    w["direction"] = np.select(
        [w["underlying_return"] < -band, w["underlying_return"] > band],
        ["Down", "Up"], default="Near flat",
    )
    group = (
        w.groupby(["direction", "vol_group"], sort=True)["reset_gap"]
        .agg(n="size", median="median", q25=lambda x: x.quantile(.25),
             q75=lambda x: x.quantile(.75)).reset_index()
    )
    group["window_days"], group["band"], group["vol_split"] = days, band, midpoint
    if (w["analysis_start"].iloc[1:].to_numpy() <= w["analysis_end"].iloc[:-1].to_numpy()).any():
        raise AssertionError("Consecutive blocks overlap")
    return w, group


def log_attribution(path: pd.DataFrame, fees: pd.DataFrame, leverage: float) -> pd.DataFrame:
    """Compute cumulative levels and increments in natural log units."""
    f = path.iloc[-1]
    rows = []
    for ticker in ("ndx", "qqq"):
        net = fees.loc[(fees["benchmark"] == ticker.upper()) & (fees["scenario"] == "Net")]
        levels = np.log([
            f[f"{ticker}_wealth"] ** leverage,
            f[f"daily_3x_{ticker}_wealth"],
            net["terminal_wealth"].item(),
            f["tqqq_wealth"],
        ])
        amounts = np.diff(levels, prepend=0)
        labels = ("Scaled index log growth", "Exact reset penalty",
                  "Net-fee scenario", "Actual minus fee scenario")
        np.testing.assert_allclose(amounts.sum(), np.log(f["tqqq_wealth"]), atol=1e-12)
        rows.extend(zip([ticker.upper()] * 4, labels, levels, amounts, strict=True))
    return pd.DataFrame(rows, columns=["benchmark", "step", "log_level", "log_increment"])


def make_axes(title: str, subtitle: str, ylabel: str, xlabel: str = ""):
    """Return a 16:9 figure with separate headings and an uncluttered axis."""
    fig, ax = plt.subplots(figsize=(12, 6.75))
    fig.subplots_adjust(left=.11, right=.965, bottom=.16, top=.73)
    fig.text(.11, .941, title, color=INK, size=24, weight="bold", va="top")
    fig.text(.11, .853, subtitle, color=MUTED, size=13, va="top")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.grid(axis="y", color=GRID, alpha=.6, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", labelsize=14, length=0, colors=MUTED)
    ax.set(ylabel=ylabel, xlabel=xlabel)
    ax.yaxis.label.set_size(15)
    ax.xaxis.label.set_size(15)
    ax.yaxis.label.set_color(INK)
    ax.xaxis.label.set_color(INK)
    return fig, ax


def save_figure(fig, path: Path) -> None:
    """Write an exact 3,600 × 2,025 PNG without cropping labels."""
    fig.savefig(path, dpi=300, bbox_inches="tight", bbox_extra_artists=[fig.patch], pad_inches=0)
    plt.close(fig)


def wealth_figure(cumulative: pd.DataFrame, sample, out: Path) -> None:
    """Display the three QQQ-basis comparisons on a common log axis."""
    span = f"{sample.base:%Y-%m-%d} to {sample.end:%Y-%m-%d}"
    fig, ax = make_axes("TQQQ finishes below both comparisons",
                        f"{span}  |  Daily closes, initial wealth $1  |  QQQ-based comparators",
                        "Wealth per initial $1 (log scale)")
    for name, a, b in REGIMES:
        ax.axvspan(pd.Timestamp(a), pd.Timestamp(b), color=GRID, alpha=.27, zorder=1)
    series = [
        ("tqqq_wealth", TQQQ, "-", "Actual TQQQ"),
        ("daily_3x_qqq_wealth", BLUE, "--", "Ideal daily 3× QQQ"),
        ("linear_3x_qqq_wealth", NDX, ":", "Linear 3× QQQ"),
    ]
    for key, color, dash, label in series:
        ax.plot(cumulative["date"], cumulative[key], c=color, ls=dash, lw=2.45, label=label)
    ax.set_yscale("log")
    ax.yaxis.set_major_locator(LogLocator(base=2))
    ax.yaxis.set_major_formatter(StrMethodFormatter("{x:g}"))
    ax.set_xlim(cumulative["date"].iloc[0], cumulative["date"].iloc[-1])
    ax.xaxis.set_major_locator(mdates.YearLocator(month=1, day=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(ncols=3, loc="lower left", bbox_to_anchor=(0, 1.02), frameon=False, fontsize=14)
    fig.text(.11, .047, "Shaded: COVID sell-off and rebound  ·  2022 rate hikes  ·  April 2025 volatility",
             color=MUTED, fontsize=12)
    save_figure(fig, out)


def block_figure(w: pd.DataFrame, out: Path) -> None:
    """Show conditional compounding outcomes across disjoint windows."""
    fig, ax = make_axes(
        "Reset gaps widen near flat QQQ returns",
        f"{len(w)} disjoint 21-day blocks  |  {w['analysis_start'].iloc[0]:%Y-%m-%d} to "
        f"{w['analysis_end'].iloc[-1]:%Y-%m-%d}  |  Median RMS split",
        "Daily reset minus linear (pp)", "QQQ return in the block (%)",
    )
    clip = 100 * w["band"].iloc[0]
    ax.axvspan(-clip, clip, color=SOFT, zorder=0)
    for group, color, marker in (("Lower RMS", QQQ, "o"), ("Higher RMS", TQQQ, "^")):
        q = w[w["vol_group"] == group]
        ax.scatter(100*q["underlying_return"], 100*q["reset_gap"],
                   c=color, marker=marker, alpha=.75, s=58, label=group, zorder=3)
    ax.axhline(0, color=MUTED, lw=1)
    ax.xaxis.set_major_formatter(PercentFormatter(100, decimals=0))
    ax.legend(ncols=2, loc="lower left", bbox_to_anchor=(0, 1.01),
              frameon=False, fontsize=14)
    save_figure(fig, out)


def qq_figure(frame: pd.DataFrame, out: Path) -> None:
    """Compare standardized QQQ log returns with normal quantiles."""
    g = frame["qqq_log_return"]
    observed = (g - g.mean()) / g.std(ddof=1)
    (x, y), _ = stats.probplot(observed, dist="norm")
    fig, ax = make_axes(
        "Both tails extend beyond a normal reference",
        f"Standardized QQQ daily log returns  |  {frame.index[0]:%Y-%m-%d} to {frame.index[-1]:%Y-%m-%d}",
        "Observed quantiles (SD)", "Standard-normal quantiles (SD)",
    )
    ax.plot([x[0], x[-1]], [x[0], x[-1]], "--", lw=2, color=NDX)
    ax.scatter(x, y, s=13, c=QQQ, alpha=.5, edgecolors="none")
    save_figure(fig, out)


RESEARCH_FIGURES = {
    "wealth": "part2_wealth_log.png",
    "windows": "part2_conditional_reset_gap.png",
    "normal_qq": "part2_qqq_normal_qq.png",
}


def run(destination: Path) -> None:
    """Generate the independently reproducible research supplement."""
    sample, frame = load_sample()
    existing = compute_tables(frame, sample)
    path = build_paths(frame, sample)
    grids = [disjoint_windows(existing["holding"], h, band)
             for h in (10, 21) for band in (MAIN_BAND, 0.05)]
    core = grids[2][0]
    summaries = pd.concat([g for _, g in grids], ignore_index=True)
    bridge = log_attribution(path, existing["fees"], sample.leverage)

    assert len(core) == len(frame) // 21
    assert len(core) * 21 + len(frame) % 21 == len(frame)
    np.testing.assert_allclose(
        core["ideal_daily_return"] - core["linear_return"], core["reset_gap"], atol=1e-13
    )
    assert (core["exact_log_drag"] <= 1e-12).all()

    chart_dir, table_dir = destination / "figures", destination / "tables"
    for folder in (chart_dir, table_dir):
        folder.mkdir(parents=True, exist_ok=True)
    results = {"disjoint_windows": core, "conditional_summary": summaries, "log_bridge": bridge}
    for name, df in results.items():
        export_table(df, table_dir / f"part2_research_{name}.csv")

    wealth_figure(existing["cumulative_path"], sample, chart_dir / RESEARCH_FIGURES["wealth"])
    block_figure(core, chart_dir / RESEARCH_FIGURES["windows"])
    qq_figure(frame, chart_dir / RESEARCH_FIGURES["normal_qq"])
    original = existing["metrics"].set_index("metric")["display"].to_dict()
    new_data = {
        "n": len(core),
        "median_rms": core["vol_split"].iloc[0],
        "unused_days": len(frame) % 21,
        "excess_kurtosis_qqq_log": float(stats.kurtosis(frame["qqq_log_return"], fisher=True, bias=False)),
        "groups": summaries.to_dict("records"),
        "bridge": bridge.to_dict("records"),
        "original": original,
    }
    (destination / "analysis_values.json").write_text(json.dumps(new_data, indent=2, allow_nan=False) + "\n")
    print(f"{sample.n} observations, {len(core)} complete 21-day blocks, {len(summaries)} grouped rows")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    run(parser.parse_args().output_dir)


if __name__ == "__main__":
    main()
