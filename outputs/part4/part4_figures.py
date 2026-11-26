"""Draw four presentation figures from the exported Part 4 estimates."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator, PercentFormatter
import numpy as np
import pandas as pd

from leveraged_etf_risk.plotting import FIGURE_DPI, set_plot_style
from part4_analysis import (
    BASE_CASE, LONG_INVERSE, LONG_SQQQ, MAIN_MODEL, OBSERVED, SHORT_TQQQ, SIDES,
)


NAVY = "#173853"
CORAL = "#bd4d39"
TEAL = "#16766f"
INK = "#162b3b"
MUTED = "#405464"
GRID = "#d8e0e7"
ASSET_COLORS = {"TQQQ": CORAL, "QQQ": NAVY}
SIDE_COLORS = {"Long": NAVY, "Short": CORAL}
SIZE = (12, 6.75)
HEADLINE_LEVEL = 0.99


def canvas(title: str, subtitle: str, footnote: str) -> plt.Figure:
    """Create a white 16:9 figure with fixed title, subtitle and source space."""
    set_plot_style()
    fig = plt.figure(figsize=SIZE, facecolor="white")
    fig.text(0.067, 0.947, title, fontsize=22, weight="bold", color=INK, va="top")
    fig.text(0.067, 0.879, subtitle, fontsize=12, color=MUTED, va="top")
    fig.text(0.067, 0.031, footnote, fontsize=9.5, color=MUTED, va="bottom", linespacing=1.35)
    return fig


def style(ax: plt.Axes, grid_axis: str = "y") -> None:
    """Use the same restrained axes and readability settings throughout."""
    ax.spines[["left", "right", "top"]].set_visible(False)
    ax.spines["bottom"].set_color("#a6b3be")
    ax.grid(False)
    ax.grid(axis=grid_axis, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", labelsize=10, length=0, pad=5, colors=MUTED)
    ax.yaxis.set_label_position("left")


def save(fig: plt.Figure, target: Path) -> None:
    """Write a 300 dpi PNG with a white background and exact slide aspect ratio."""
    fig.savefig(target, dpi=FIGURE_DPI, facecolor="white")
    plt.close(fig)


def loss_pct(value: float) -> str:
    return f"{value:.1%}"


def frequency_pct(value: float) -> str:
    """Show rare counts at 10,000-path resolution."""
    return f"{value:.2%}"


def risk_overview(risk: pd.DataFrame, multipliers: pd.DataFrame, target: Path,
                  baseline_note: str) -> None:
    """Draw 99% losses and TQQQ/QQQ multiples for both sides and each horizon."""
    main = risk.loc[(risk.case == MAIN_MODEL) & np.isclose(risk.confidence, HEADLINE_LEVEL)]
    ratio = multipliers.loc[(multipliers.case == MAIN_MODEL)
                            & np.isclose(multipliers.confidence, HEADLINE_LEVEL)]
    horizons = sorted(main.horizon_days.unique())
    x = np.arange(len(horizons))
    n = int(main.observations.iloc[0])
    fig = canvas(
        "TQQQ risk multiples change with the holding period",
        f"99% VaR and sample ES  ·  {n:,} shared QQQ paths  ·  GARCH-t",
        "Losses are per initial dollar. Full 95% and 99% estimates and model comparisons are in the report tables.\n"
        f"{baseline_note}",
    )
    grid = fig.add_gridspec(2, 3, left=0.09, right=0.96, bottom=0.16, top=0.742,
                           hspace=0.48, wspace=0.32)
    for row, side in enumerate(SIDES):
        subset = main.loc[main.position.eq(side)]
        ratios = ratio.loc[ratio.position.eq(side)].set_index("horizon_days").loc[horizons]
        for col, (metric, title) in enumerate((("var_loss", "VaR"), ("es_loss", "Sample ES"))):
            ax = fig.add_subplot(grid[row, col])
            style(ax)
            ax.set_title(f"{side} positions  ·  {title}", fontsize=12, weight="bold", color=INK, pad=9)
            for asset, shift in (("TQQQ", -0.17), ("QQQ", 0.17)):
                values = subset.loc[subset.asset.eq(asset)].set_index("horizon_days").loc[horizons, metric]
                bars = ax.bar(x + shift, values, width=0.29, color=ASSET_COLORS[asset], label=asset)
                ax.bar_label(bars, labels=[f"{value:.0%}" for value in values], padding=3,
                             fontsize=9, color=INK)
            ax.set_ylim(0, main[metric].max() * 1.24)
            ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
            ax.yaxis.set_major_locator(MaxNLocator(4))
            ax.set_xticks(x, [f"{days}d" for days in horizons])
            if row == 0 and col == 0:
                handles, labels = ax.get_legend_handles_labels()
                fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(0.067, 0.842),
                           frameon=False, ncol=2, fontsize=10)
        ax = fig.add_subplot(grid[row, 2])
        style(ax)
        ax.set_title(f"{side} positions  ·  TQQQ / QQQ", fontsize=12, weight="bold", color=INK, pad=9)
        ax.axhline(3.0, lw=1.1, ls=":", color=MUTED)
        ax.plot(x, ratios.var_multiple, "o-", color=NAVY, lw=2, label="VaR")
        ax.plot(x, ratios.es_multiple, "s--", color=CORAL, lw=2, label="Sample ES")
        ax.set_xticks(x, [f"{days}d" for days in horizons])
        low = min(3.0, ratio[["var_multiple", "es_multiple"]].min().min())
        high = max(3.0, ratio[["var_multiple", "es_multiple"]].max().max())
        pad = max(0.15, (high - low) * 0.20)
        ax.set_xlim(-0.24, len(x) - 0.68)
        ax.set_ylim(low - pad, high + pad)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:.1f}×"))
        ax.set_yticks([2.4, 3.0, 3.6, 4.2])
        offset = (-13, -12) if side == "Long" else (-13, 8)
        ax.annotate(f"{ratios.es_multiple.iloc[-1]:.2f}×",
                    (x[-1], ratios.es_multiple.iloc[-1]), xytext=offset, textcoords="offset points",
                    fontsize=9, weight="bold", color=CORAL)
        if row == 0:
            handles, labels = ax.get_legend_handles_labels()
            fig.legend(handles, labels, loc="upper right", bbox_to_anchor=(0.96, 0.842),
                       frameon=False, ncol=2, fontsize=10)
    fig.text(0.5, 0.086, "Holding period in trading days", ha="center", color=MUTED, fontsize=11)
    save(fig, target)


def exceedance(ax: plt.Axes, losses: np.ndarray, color: str, label: str,
               left: float, right: float) -> None:
    """Plot the share of the sample with losses strictly greater than each x value."""
    interior = np.unique(losses[(losses >= left) & (losses <= right)])
    x = np.unique(np.r_[left, interior, right])
    y = (losses.size - np.searchsorted(np.sort(losses), x, side="right")) / losses.size
    ax.step(x, np.where(y > 0, y, np.nan), where="post", color=color, lw=2.25, label=label)


def tqqq_tails(losses: dict, risk: pd.DataFrame, days: int, target: Path,
               baseline_note: str) -> None:
    """Show the body and both right loss tails on the 21-day baseline sample."""
    n = len(losses["Long"])
    tail = risk.loc[(risk.case == MAIN_MODEL) & (risk.asset == "TQQQ")
                    & (risk.horizon_days == days) & np.isclose(risk.confidence, HEADLINE_LEVEL)]
    tail = tail.set_index("position")
    fig = canvas(
        f"{days}-day TQQQ losses from long and short positions",
        f"GARCH-t  ·  {n:,} paths  ·  Dashed lines mark the 99% VaR thresholds",
        "Shading marks losses included in sample ES within the displayed range. "
        "The right panel extends across the observed tail.\n"
        f"{baseline_note}",
    )
    grid = fig.add_gridspec(1, 2, width_ratios=[1.37, 1], left=0.08, right=0.951,
                           bottom=0.18, top=0.755, wspace=0.24)
    body, far_tail = (fig.add_subplot(grid[0, col]) for col in range(2))
    right = max(1.10, float(tail.es_loss.max()) * 1.13)
    left = -max(0.78, float(np.quantile(np.abs(losses["Long"]), 0.95)))
    bins = np.linspace(left, right, 55)
    full_right = max(1.05, max(sample.max() for sample in losses.values())) * 1.025
    for side, values in losses.items():
        color = SIDE_COLORS[side]
        threshold = tail.loc[side, "var_loss"]
        counts, _ = np.histogram(values, bins)
        tail_counts, _ = np.histogram(values[values >= threshold], bins)
        body.stairs(counts / n, bins, lw=2.1, color=color, label=f"{side} TQQQ")
        body.stairs(tail_counts / n, bins, fill=True, color=color, alpha=0.50, lw=0)
        body.axvline(threshold, color=color, ls="--", lw=1.45)
        exceedance(far_tail, values, color, side, 0.30, full_right)
        far_tail.axvline(threshold, color=color, ls="--", lw=1.15, alpha=0.8)
    style(body)
    body.set_title("Loss distributions", loc="left", weight="bold", color=INK, pad=10)
    body.set_xlim(left, right)
    body.set_xlabel("Loss per initial dollar", color=MUTED)
    body.set_ylabel("Share of paths per bin", color=MUTED)
    body.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    body.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    handles, labels = body.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(0.067, 0.836),
               frameon=False, ncol=2, fontsize=10)
    style(far_tail)
    far_tail.set_title("Upper loss tails", loc="left", weight="bold", color=INK, pad=10)
    far_tail.set_yscale("log")
    far_tail.set_ylim(0.8 / n, 0.35)
    far_tail.set_xlim(0.30, full_right)
    far_tail.set_xlabel("Loss threshold", color=MUTED)
    far_tail.set_ylabel("Share of paths exceeding threshold (log scale)", color=MUTED)
    far_tail.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    far_tail.xaxis.set_major_locator(MaxNLocator(6))
    far_tail.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=2))
    far_tail.annotate("1% tail (99% VaR)", (0.97, 1.0 - HEADLINE_LEVEL),
                      xycoords=far_tail.get_yaxis_transform(), xytext=(0, 4),
                      textcoords="offset points", ha="right", va="bottom",
                      color="#64798a", fontsize=9)
    for i, side in enumerate(SIDES):
        line = tail.loc[side]
        fig.text(0.085 + i * 0.43, 0.085,
                 f"{side}  |  VaR {loss_pct(line.var_loss)}  ·  Sample ES {loss_pct(line.es_loss)}",
                 fontsize=12, color=SIDE_COLORS[side], weight="bold")
    save(fig, target)


def volatility_regimes(phases: pd.DataFrame, conditional: pd.DataFrame, days: int, target: Path) -> None:
    """Compare historical drawdowns with conditional 99% ES across starting volatilities."""
    fig = canvas(
        "Losses across historical and simulated volatility scenarios",
        "Historical stress episodes and a controlled GARCH-t initial-volatility comparison",
        "Historical drawdowns start at each preceding close.\n"
        "Common shocks across the 15%, 25%, and 45% (high-volatility) scenarios.",
    )
    grid = fig.add_gridspec(1, 2, left=0.078, right=0.95, bottom=0.21, top=0.741,
                           wspace=0.27, width_ratios=[1.15, 1])
    observed = fig.add_subplot(grid[0, 0])
    stress = fig.add_subplot(grid[0, 1])
    display_names = {
        "2021 up market": "2021\nup market", "COVID sell-off": "COVID\nsell-off",
        "COVID rebound": "COVID\nrebound", "Rate-hike bear market": "2022\nrate hikes",
        "April tariff volatility": "Apr 2025\ntariffs",
    }
    data = phases.pivot(index="regime", columns="asset", values="max_drawdown_loss").loc[list(display_names)]
    x = np.arange(len(data))
    for asset, shift in (("TQQQ", -0.17), ("QQQ", 0.17)):
        bars = observed.bar(x + shift, data[asset], width=0.30, label=asset, color=ASSET_COLORS[asset])
        observed.bar_label(bars, labels=[f"{v:.0%}" for v in data[asset]], padding=3, fontsize=9, color=INK)
    style(observed)
    observed.set_title("Historical maximum drawdown", loc="left", weight="bold", color=INK, pad=9)
    observed.set_xticks(x, [display_names[label] for label in data.index])
    observed.set_ylim(0, 1.0)
    observed.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    handles, labels = observed.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(0.065, 0.837),
               frameon=False, ncol=2, fontsize=10)
    rows = conditional.loc[(conditional.asset == "TQQQ") & (conditional.horizon_days == days)
                           & np.isclose(conditional.confidence, HEADLINE_LEVEL)]
    for side in SIDES:
        data = rows.loc[rows.position.eq(side)].sort_values("initial_vol_annual")
        xs = data.initial_vol_annual.to_numpy()
        stress.plot(xs, data.es_loss, "o-", label=f"{side} TQQQ",
                    color=SIDE_COLORS[side], lw=2.5, ms=6)
        for case, value, es in zip(data.case, xs, data.es_loss, strict=True):
            offset = (0, 10) if side == "Short" else (0, -16)
            label = f"{es:.2%}" if case == "Normal" else loss_pct(es)
            alignment = "center"
            if case == "Normal" and side == "Short":
                offset, alignment = (-8, 12), "right"
            stress.annotate(label, (value, es), ha=alignment, textcoords="offset points",
                            xytext=offset, color=SIDE_COLORS[side], fontsize=10, weight="bold")
    style(stress)
    stress.set_title(f"{days}-day 99% sample ES", loc="left", weight="bold", color=INK, pad=9)
    labels = [f"{value:.0%}" for value in xs]
    labels[-1] += "\nHigh-volatility scenario"
    stress.set_xticks(xs, labels)
    stress.set_xlabel("Annualized initial QQQ volatility", color=MUTED)
    stress.xaxis.set_label_coords(0.5, -0.18)
    stress.set_xlim(xs[0] - 0.045, xs[-1] + 0.04)
    stress.set_ylim(0, rows.es_loss.max() * 1.19)
    stress.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    handles, labels = stress.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper right", bbox_to_anchor=(0.955, 0.837),
               frameon=False, ncol=2, fontsize=10)
    save(fig, target)


def inverse_positions(losses: dict, results: pd.DataFrame, days: int, target: Path,
                      baseline_note: str) -> None:
    """Show terminal loss exceedances and the three reverse-stress headline metrics."""
    n = len(losses[SHORT_TQQQ])
    main = results.loc[(results.model == MAIN_MODEL) & (results.cost_basis == BASE_CASE)
                       & (results.horizon_days == days) & np.isclose(results.confidence, HEADLINE_LEVEL)]
    main = main.set_index("position")
    history = results.loc[(results.model == OBSERVED) & (results.horizon_days == days)
                          & np.isclose(results.confidence, HEADLINE_LEVEL)].set_index("position")
    fig = canvas(
        "What loss can a bearish Nasdaq-100 position sustain?",
        f"{days}-day terminal losses  ·  GARCH-t  ·  {n:,} paths  ·  excluding borrow fees",
        "A fixed-share TQQQ short reaches a 100% notional loss when TQQQ doubles. The ideal inverse resets daily.\n"
        f"{baseline_note}",
    )
    grid = fig.add_gridspec(1, 2, left=0.075, right=0.964, bottom=0.17, top=0.773,
                           wspace=0.15, width_ratios=[1.04, 1])
    ax = fig.add_subplot(grid[0, 0])
    display_max = 2.0
    exceedance(ax, losses[SHORT_TQQQ], CORAL, "Short TQQQ", 0.0, display_max)
    exceedance(ax, losses[LONG_INVERSE], TEAL, "Long ideal −3×", 0.0, display_max)
    for cutoff in (0.50, 1.00):
        ax.axvline(cutoff, color=MUTED, ls=":", lw=1.4)
    style(ax)
    ax.set_yscale("log")
    ax.set_ylim(0.8 / n, 1)
    ax.set_xlim(0.0, display_max)
    ax.set_xticks(np.arange(0.0, display_max + 0.01, 0.5))
    ax.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:.2%}"))
    ax.set_xlabel("Terminal loss threshold (shown through 200%)", color=MUTED)
    ax.set_ylabel("Share of paths exceeding threshold (log scale)", color=MUTED)
    ax.legend(frameon=False, loc="upper right", fontsize=10)

    panel = fig.add_subplot(grid[0, 1])
    panel.set_axis_off()
    panel.text(0.01, 1.015, "Simulated terminal losses", fontsize=13, weight="bold", color=INK)
    positions = (SHORT_TQQQ, LONG_INVERSE)
    for x, label, color in zip((0.61, 0.89), ("Short TQQQ", "Long ideal −3×"), (CORAL, TEAL), strict=True):
        panel.text(x, 0.885, label, transform=panel.transAxes, ha="center", weight="bold",
                   color=color, fontsize=11)
    stats = [("Loss > 50%", "prob_loss_gt_50", frequency_pct),
             ("Loss > 100%", "prob_loss_gt_100", frequency_pct),
             ("Maximum sample loss", "max_sample_loss", loss_pct)]
    for y, (label, column, formatter) in zip((0.72, 0.54, 0.36), stats, strict=True):
        panel.axhline(y + 0.085, color=GRID, lw=0.85)
        panel.text(0.01, y, label, transform=panel.transAxes, va="center", color=INK, fontsize=11)
        for x, position, color in zip((0.61, 0.89), positions, (CORAL, TEAL), strict=True):
            panel.text(x, y, formatter(main.loc[position, column]), transform=panel.transAxes,
                       ha="center", va="center", fontsize=17, weight="bold", color=color)
    panel.axhline(0.265, color=GRID, lw=0.85)
    panel.text(0.01, 0.175, "Historical check on adjusted prices", color=INK, fontsize=11, weight="bold",
               transform=panel.transAxes)
    historical_short = history.loc[SHORT_TQQQ, "max_sample_loss"]
    historical_inverse = history.loc[LONG_SQQQ, "max_sample_loss"]
    panel.text(0.01, 0.045,
               f"Maximum {days}-day loss  ·  Short TQQQ {historical_short:.1%}\n"
               f"Long SQQQ {historical_inverse:.1%}  ·  {int(history.observations.iloc[0]):,} overlapping windows",
               color=MUTED, fontsize=10, linespacing=1.5, transform=panel.transAxes)
    save(fig, target)
