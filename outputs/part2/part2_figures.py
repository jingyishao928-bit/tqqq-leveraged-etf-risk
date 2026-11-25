"""Draw the widescreen figures for the Part 2 report and presentation."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import FuncFormatter, MaxNLocator, PercentFormatter, StrMethodFormatter
import pandas as pd

from analyze_part2 import REGIMES, Sample, build_paths
from leveraged_etf_risk.plotting import FIGURE_DPI, set_plot_style

FIGSIZE = (12, 6.75)
DPI = FIGURE_DPI
FIGURES = {
    "wealth": "fig_part2_cumulative_returns.png",
    "drawdown": "fig_part2_drawdown_and_pnl.png",
    "decay": "fig_part2_volatility_decay.png",
    "rolling": "fig_part2_rolling_volatility_and_leverage.png",
    "example": "fig_part2_two_day_example.png",
    "attribution": "fig_part2_return_decomposition.png",
}
NAVY, CORAL, BLUE, GOLD = "#173853", "#bd4d39", "#58738a", "#996d2a"
INK, MUTED, GRID = "#162b3b", "#405464", "#a6b3be"
SHADE = ("#f4d2cd", "#d3e6e7", "#f1dfbd", "#dcd9ee")
PATH_STYLES = {
    "qqq_wealth": (NAVY, "-", "QQQ (1×)"),
    "tqqq_wealth": (CORAL, "-", "Actual TQQQ"),
    "daily_3x_qqq_wealth": (BLUE, "--", "Ideal daily {leverage:g}× QQQ"),
    "linear_3x_qqq_wealth": (GOLD, ":", "Linear {leverage:g}× QQQ"),
}


def new_figure(sample: Sample, title: str):
    """Create a fixed-size canvas with a title and sample metadata."""
    set_plot_style()
    fig = plt.figure(figsize=FIGSIZE, facecolor="white")
    fig.text(0.09, 0.94, title, fontsize=19, fontweight="bold", color=INK, va="top")
    fig.text(
        0.09, 0.879,
        f"{sample.start:%Y-%m-%d} to {sample.end:%Y-%m-%d}  |  Frozen Part 1 daily data  |  "
        f"Wealth starts at 1.00 on {sample.base:%Y-%m-%d}",
        fontsize=11, color=MUTED, va="top",
    )
    return fig


def axes_format(ax, ylabel: str, *, percent=False):
    """Apply common tick, grid and label styling."""
    ax.set_ylabel(ylabel, fontsize=11, color=INK)
    ax.tick_params(axis="both", labelsize=11, colors=MUTED, length=0, pad=5)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.grid(False)
    ax.grid(axis="y", color=GRID, alpha=0.25, zorder=0)
    ax.set_axisbelow(True)
    if percent:
        ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))


def full_dates(ax, sample):
    """Format axes sharing the frozen historical calendar."""
    ax.set_xlim(sample.base, sample.end)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))


def shade_regimes(ax):
    """Mark retrospectively selected windows across full-history axes."""
    for (_, start, end), color in zip(REGIMES, SHADE, strict=True):
        ax.axvspan(pd.Timestamp(start), pd.Timestamp(end) + pd.Timedelta(days=1),
                   facecolor=color, edgecolor="none", alpha=0.73, zorder=0)


def legend(ax, *, y=1.03, columns=4):
    """Keep the series legend in reserved space above the plot."""
    ax.legend(loc="lower left", bbox_to_anchor=(0, y), ncol=columns, frameon=False,
              borderaxespad=0, handlelength=2.5, columnspacing=1.6,
              fontsize=11, labelcolor=INK)


def regime_key(fig, y=0.06):
    """Draw the historical-window legend in a separate figure margin."""
    patches = [Patch(facecolor=color, edgecolor="none", label=name)
               for (name, _, _), color in zip(REGIMES, SHADE, strict=True)]
    fig.legend(handles=patches, loc="center left", bbox_to_anchor=(0.09, y),
               ncol=4, frameon=False, borderaxespad=0, fontsize=11, labelcolor=MUTED)


def with_base(frame, columns, base, value):
    """Prepend a plotting anchor without adding a daily return observation."""
    anchor = pd.DataFrame(value, index=pd.DatetimeIndex([base]), columns=columns)
    return pd.concat([anchor, frame[columns]])


def wealth_lines(ax, frame, base, leverage):
    """Plot all four comparator paths on a linear normalized wealth axis."""
    values = with_base(frame, list(PATH_STYLES), base, 1.0)
    for key, (color, style, label) in PATH_STYLES.items():
        ax.plot(values.index, values[key], color=color, ls=style, lw=1.85,
                label=label.format(leverage=leverage), zorder=3)
    ax.axhline(1, color=GRID, lw=0.8, zorder=1)


def plot_wealth(sample, daily):
    """Compare the long-run daily-reset and linear-multiple paths."""
    fig = new_figure(sample, "Daily compounding lifted both ideal paths above their linear benchmarks")
    top = fig.add_axes((0.09, 0.52, 0.885, 0.24))
    bottom = fig.add_axes((0.09, 0.17, 0.885, 0.23), sharex=top)
    ymax = max(daily["daily_3x_qqq_wealth"].max(), daily["daily_3x_ndx_wealth"].max()) * 1.08
    for ax, code in ((top, "qqq"), (bottom, "ndx")):
        shade_regimes(ax)
        actual, ideal, linear = "tqqq_wealth", f"daily_3x_{code}_wealth", f"linear_3x_{code}_wealth"
        values = with_base(daily, [actual, ideal, linear], sample.base, 1.0)
        for key, color, style, name in (
            (actual, CORAL, "-", "Actual TQQQ"),
            (ideal, BLUE, "--", f"Ideal daily {sample.leverage:g}× {code.upper()}"),
            (linear, GOLD, ":", f"Linear {sample.leverage:g}× {code.upper()}"),
        ):
            ax.plot(values.index, values[key], color=color, ls=style, lw=1.65, label=name)
        full_dates(ax, sample)
        axes_format(ax, f"{code.upper()} basis · wealth / $1")
        ax.set_ylim(0, ymax)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=4, integer=True))
        legend(ax)
    top.tick_params(labelbottom=False)
    regime_key(fig)
    return fig


def plot_drawdown(sample, daily):
    """Show peak-relative drawdowns and fixed-share position P&L together."""
    fig = new_figure(sample, "TQQQ fell deeper from its peak and exposed shorts to large losses")
    ax = fig.add_axes((0.09, 0.51, 0.885, 0.26))
    pnl = fig.add_axes((0.09, 0.17, 0.885, 0.22), sharex=ax)
    for panel in (ax, pnl):
        full_dates(panel, sample)
        shade_regimes(panel)
        panel.axhline(0, color=GRID, lw=0.8, zorder=1)
    marks = with_base(daily, ["qqq_drawdown", "tqqq_drawdown", "long_tqqq_pnl",
                              "short_tqqq_pnl", "sqqq_cum_return"], sample.base, 0.0)
    ax.plot(marks.index, marks["qqq_drawdown"], color=NAVY, lw=1.55, label="QQQ")
    ax.plot(marks.index, marks["tqqq_drawdown"], color=CORAL, lw=1.55, label="TQQQ")
    axes_format(ax, "Drawdown (%)", percent=True)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
    ax.tick_params(labelbottom=False)
    legend(ax)
    for key, color, style, label in (
        ("long_tqqq_pnl", CORAL, "-", "Long TQQQ"),
        ("short_tqqq_pnl", NAVY, "-", "Short TQQQ"),
        ("sqqq_cum_return", GOLD, ":", "Long SQQQ"),
    ):
        pnl.plot(marks.index, marks[key], color=color, linestyle=style, lw=1.55, label=label)
    axes_format(pnl, "P&L per initial $1")
    pnl.yaxis.set_major_locator(MaxNLocator(nbins=4, symmetric=True))
    pnl.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{'-' if x < 0 else ''}${abs(x):,.0f}"))
    legend(pnl)
    regime_key(fig)
    return fig


def plot_decay(sample, daily, holding):
    """Contrast exact log drag with its approximation and show April wealth."""
    fig = new_figure(sample, "April volatility turned a small QQQ gain into a daily-reset loss")
    ax = fig.add_axes((0.09, 0.50, 0.885, 0.27))
    shade_regimes(ax)
    values = with_base(daily, ["exact_log_drag", "approx_log_drag"], sample.base, 0.0)
    ax.plot(values.index, 100 * values["exact_log_drag"], color=NAVY, lw=1.7, label="Exact log penalty")
    ax.plot(values.index, 100 * values["approx_log_drag"], color=CORAL, ls="--", lw=1.6,
            label="Second-order approximation")
    full_dates(ax, sample)
    axes_format(ax, "Log penalty (log pts)")
    ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
    legend(ax)

    inset = fig.add_axes((0.09, 0.16, 0.49, 0.20))
    _, start, end = REGIMES[-1]
    window = daily.loc[start:end]
    base = daily.index[daily.index.get_loc(window.index[0]) - 1]
    wealth_lines(inset, build_paths(window, sample), base, sample.leverage)
    inset.set_xlim(base, window.index[-1])
    inset.set_facecolor(SHADE[-1] + "46")
    inset.xaxis.set_major_locator(mdates.DayLocator(bymonthday=[1, 7, 14, 21, 28]))
    inset.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    axes_format(inset, "April wealth per $1")
    inset.yaxis.set_major_locator(MaxNLocator(nbins=4))
    inset.yaxis.set_major_formatter(StrMethodFormatter("{x:.2f}"))
    legend(inset, columns=2, y=1.00)

    scatter = fig.add_axes((0.66, 0.16, 0.315, 0.20))
    horizon = sample.horizons[-1]
    points = holding.loc[(holding["benchmark"] == "NDX") & (holding["window_days"] == horizon)]
    x = 100 * points["approx_log_drag"]
    y = 100 * points["exact_log_drag"]
    low = min(x.min(), y.min())
    scatter.scatter(x, y, s=9, color=NAVY, alpha=0.27, edgecolors="none", label=f"{horizon}d NDX windows")
    scatter.plot([low, 0], [low, 0], ls="--", lw=1.3, color=CORAL, label="Exact = estimate")
    axes_format(scatter, "Exact drag (log pts)")
    scatter.xaxis.set_major_locator(MaxNLocator(nbins=4))
    scatter.yaxis.set_major_locator(MaxNLocator(nbins=4))
    scatter.set_xlabel("Approximation (log pts)", fontsize=11, color=INK, labelpad=3)
    legend(scatter, columns=1, y=1.00)
    regime_key(fig, y=0.045)
    return fig


def plot_rolling(sample, rolling):
    """Show trailing volatility and the effective daily exposure separately."""
    fig = new_figure(sample, "Volatility surged while rolling leverage stayed near target")
    ax = fig.add_axes((0.09, 0.51, 0.885, 0.25))
    slope = fig.add_axes((0.09, 0.16, 0.885, 0.23), sharex=ax)
    for panel in (ax, slope):
        full_dates(panel, sample)
    for asset, color in (("qqq", NAVY), ("tqqq", CORAL)):
        for window, style in zip(sample.windows, ("-", "--"), strict=True):
            data = rolling.loc[rolling["window_days"] == window]
            ax.plot(data["date"], data[f"{asset}_ann_vol"], color=color, ls=style, lw=1.35,
                    label=f"{asset.upper()} · {window}d")
    axes_format(ax, "Annualized vol (%)", percent=True)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
    ax.tick_params(labelbottom=False)
    legend(ax)
    long_window = rolling.loc[rolling["window_days"] == sample.windows[-1]]
    for asset, color in (("qqq", NAVY), ("ndx", BLUE)):
        slope.plot(long_window["date"], long_window[f"beta_{asset}"], color=color,
                   lw=1.6, label=f"{sample.windows[-1]}d OLS vs. {asset.upper()}")
    slope.axhline(sample.leverage, color=CORAL, lw=1.25, ls="--",
                  label=f"{sample.leverage:g}× target")
    axes_format(slope, "Daily beta (×)")
    slope.yaxis.set_major_locator(MaxNLocator(nbins=4))
    slope.yaxis.set_major_formatter(StrMethodFormatter("{x:.2f}×"))
    legend(slope)
    fig.text(0.09, 0.065, "Trailing trading-day windows end at each plotted close.",
             color=MUTED, fontsize=11, va="center")
    return fig


def plot_two_days(sample, examples):
    """Show the exact hypothetical two-day results relative to zero."""
    fig = new_figure(sample, "A two-day round trip leaves ideal leveraged wealth lower")
    fig.text(0.09, 0.812, "Hypothetical returns over two trading days",
             fontsize=11, color=MUTED)
    ax = fig.add_axes((0.09, 0.18, 0.885, 0.54))
    positions = list(range(len(examples)))
    width = 0.22
    for index, (key, color, label) in enumerate((
        ("underlying_return", NAVY, "Underlying"),
        ("linear_return", GOLD, f"Linear {sample.leverage:g}×"),
        ("daily_reset_return", BLUE, f"Ideal daily {sample.leverage:g}×"),
    )):
        y = examples[key].where(examples[key].abs() > 1e-12, 0)
        ax.bar([p + (index - 1) * width for p in positions], y,
               width=width, color=color, label=label)
        if key == "daily_reset_return":
            ax.bar_label(ax.containers[-1], labels=[f"{value:.2%}" for value in y],
                         padding=4, fontsize=11, color=INK)
    labels = [f"{row.case}\n{row.day1:+.2%} then {row.day2:+.2%}"
              for row in examples.itertuples(index=False)]
    ax.set_xticks(positions, labels)
    ax.axhline(0, color=GRID, lw=0.9)
    ax.set_ylim(-0.65, 0.83)
    axes_format(ax, "Two-day return (%)", percent=True)
    legend(ax)
    return fig


def plot_attribution(sample, benchmarks):
    """Bridge linear to ideal and actual terminal returns on both bases."""
    fig = new_figure(sample, "The actual shortfall outweighed the daily compounding gain")
    for row, left in zip(benchmarks.itertuples(index=False), (0.09, 0.55), strict=True):
        ax = fig.add_axes((left, 0.18, 0.42, 0.56))
        bottoms = [0, row.linear_return, row.actual_return, 0]
        heights = [row.linear_return, row.reset_gap, -row.implementation_gap, row.actual_return]
        ax.bar(range(4), heights, bottom=bottoms, color=[GOLD, BLUE, CORAL, NAVY], width=0.63)
        for x, level in enumerate((row.linear_return, row.ideal_daily_return, row.actual_return)):
            ax.plot([x + 0.32, x + 0.68], [level, level], color=GRID, linestyle="--", lw=1)
        labels = [f"{row.linear_return:,.2%}", f"{100 * row.reset_gap:+,.2f} pp",
                  f"{100 * row.implementation_gap:+,.2f} pp", f"{row.actual_return:,.2%}"]
        for x, text in enumerate(labels):
            ax.text(x, bottoms[x] + heights[x] + 0.40, text, ha="center", va="bottom",
                    fontsize=11, color=INK)
        ax.set_ylim(0, 18)
        ax.set_title(f"{row.benchmark} benchmark", color=INK, fontsize=13, loc="left", pad=8)
        ax.set_xticks(range(4), ["Linear", "Daily-reset\ngain", "Actual vs.\nideal", "Actual"])
        axes_format(ax, "Cumulative return (%)" if left == 0.09 else "", percent=True)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
        if left > 0.09:
            ax.tick_params(labelleft=False)
    return fig


def render_figures(output: Path, sample: Sample, tables: dict[str, pd.DataFrame]):
    """Save the 300-DPI historical and teaching figures."""
    daily = tables["daily"].set_index("date")
    for key, routine, data in (
        ("wealth", plot_wealth, (daily,)),
        ("drawdown", plot_drawdown, (daily,)),
        ("decay", plot_decay, (daily, tables["holding"])),
        ("rolling", plot_rolling, (tables["rolling"],)),
        ("example", plot_two_days, (tables["examples"],)),
        ("attribution", plot_attribution, (tables["benchmarks"],)),
    ):
        fig = routine(sample, *data)
        try:
            # Include the full canvas in the tight bounds to preserve 16:9.
            fig.savefig(output / FIGURES[key], dpi=DPI, bbox_inches="tight",
                        bbox_extra_artists=[fig.patch], pad_inches=0)
        finally:
            plt.close(fig)
