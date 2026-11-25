"""Render report and presentation copy from the same values as the console."""

import re

import pandas as pd

REPORT = r"""# Part 2. Historical performance and daily-reset attribution

## Sample and measurement

The frozen Part 1 master dataset contains {{returns}} common daily returns from **{{analysis_start}} to {{analysis_end}}** and {{priced_dates}} common price dates. Wealth is indexed to {{base_wealth}} at the **{{base_date}} close**, immediately before the first return. QQQ, TQQQ and SQQQ use adjusted market closes. The Nasdaq-100 (NDX) comparison uses its price index. Both flagged observations remain in the analysis. Returns use the canonical simple-return columns and annualization uses {{annual_days}} trading days. [Data dictionary](../../docs/data_dictionary.md) · [Data guide](../../docs/data_guide.md)

For each ETF with daily simple returns $r_t$, let $W_t=\prod_{s=1}^t(1+r_s)$. Cumulative return is $W_t-1$. Geometric annual return is $W_T^{A/n}-1$ for $n$ observed returns and annualization factor $A$. Annualized volatility is the sample standard deviation of daily returns times $\sqrt A$. Drawdown is $W_t/\max_{0\le s\le t}W_s-1$, and maximum drawdown is its most negative value. Rolling volatility uses trailing {{short_window}}- and {{long_window}}-trading-day windows with the same annualization and sample standard deviation. Each rolling estimate is dated at the close of its last input observation.

| Metric | QQQ | TQQQ | SQQQ |
|---|---:|---:|---:|
| Mean daily return | {{QQQ_daily_mean}} | {{TQQQ_daily_mean}} | {{SQQQ_daily_mean}} |
| Daily volatility | {{QQQ_daily_sd}} | {{TQQQ_daily_sd}} | {{SQQQ_daily_sd}} |
| Worst day | {{QQQ_daily_min}} | {{TQQQ_daily_min}} | {{SQQQ_daily_min}} |
| Best day | {{QQQ_daily_max}} | {{TQQQ_daily_max}} | {{SQQQ_daily_max}} |
| Cumulative return | {{QQQ_cumulative_return}} | {{TQQQ_cumulative_return}} | {{SQQQ_cumulative_return}} |
| Annualized return | {{QQQ_annual_return}} | {{TQQQ_annual_return}} | {{SQQQ_annual_return}} |
| Annualized volatility | {{QQQ_annual_volatility}} | {{TQQQ_annual_volatility}} | {{SQQQ_annual_volatility}} |
| Maximum drawdown | {{QQQ_max_drawdown}} | {{TQQQ_max_drawdown}} | {{SQQQ_max_drawdown}} |
| Peak → trough | {{QQQ_peak_date}} → {{QQQ_trough_date}} | {{TQQQ_peak_date}} → {{TQQQ_trough_date}} | {{SQQQ_peak_date}} → {{SQQQ_trough_date}} |

TQQQ earned a higher annualized return and sustained a much deeper peak-to-trough loss than QQQ. For a position initiated at one dollar of exposure and held at fixed share count, long TQQQ P&L is $W_A-1$ and short P&L is its negative. These are adjusted-price dollar equivalents per initial dollar, before any additional short-borrow cost, margin, collateral remuneration or implementation expenses. A price rise can generate an uncapped loss on the fixed-share short. Long SQQQ compounds its own inverse returns and can lose at most its invested capital. The minimum fixed-share P&L mark is measured from the initial entry and can differ substantially from maximum drawdown, which is measured from a subsequent peak. [Drawdown and fixed-share P&L](figures/fig_part2_drawdown_and_pnl.png)

| Position | Terminal P&L per initial USD | Worst P&L mark per initial USD |
|---|---:|---:|
| Long TQQQ | {{long_tqqq_terminal_pnl_per_dollar}} | {{long_tqqq_worst_mark_per_dollar}} |
| Short TQQQ | {{short_tqqq_terminal_pnl_per_dollar}} | {{short_tqqq_worst_mark_per_dollar}} |
| Long SQQQ | {{long_sqqq_terminal_pnl_per_dollar}} | {{long_sqqq_worst_mark_per_dollar}} |

## Daily reset, trend and volatility

For QQQ daily simple returns $r_t$ and TQQQ adjusted-price returns $a_t$, define QQQ wealth $W_Q=\prod_t(1+r_t)$, and compare the three paths below from the same close.

$$
W_A=\prod_t(1+a_t),\qquad
W_D=\prod_t(1+Lr_t),\qquad
W_H=1+L(W_Q-1),\qquad L={{leverage_number}}.
$$

$W_D$ reinvests gains and losses at target daily exposure before incremental costs. $W_H$ is an arithmetic holding-period comparator. Its value can cross zero and represents neither a funded ETF wealth process nor a margin rule. The full-sample cumulative returns were **{{TQQQ_cumulative_return}}** for actual TQQQ, **{{full_daily_3x_qqq_return}}** for the ideal daily-reset path and **{{full_linear_3x_qqq_return}}** for the linear QQQ multiple. [Wealth paths](figures/fig_part2_cumulative_returns.png)

A two-day expansion gives $W_D-W_H=L(L-1)r_1r_2$. The cross term is positive when both returns have the same sign and negative when they have opposite signs. In the cost-free fixed-leverage model, permuting the same set of returns preserves terminal wealth because the daily multipliers commute. The underlying's terminal return alone does not determine those multipliers. [Two-day illustration](figures/fig_part2_two_day_example.png)

| Hypothetical path | Day one | Day two | Underlying | Ideal daily reset | Linear multiple |
|---|---:|---:|---:|---:|---:|
| Round trip | {{round_trip_day1}} | {{round_trip_day2}} | {{round_trip_underlying_return}} | {{round_trip_daily_reset_return}} | {{round_trip_linear_return}} |
| Two gains | {{two_gains_day1}} | {{two_gains_day2}} | {{two_gains_underlying_return}} | {{two_gains_daily_reset_return}} | {{two_gains_linear_return}} |
| Two losses | {{two_losses_day1}} | {{two_losses_day2}} | {{two_losses_underlying_return}} | {{two_losses_daily_reset_return}} | {{two_losses_linear_return}} |

The round trip uses the exact second return $1/(1+r_1)-1$ before rounding.

To isolate the log penalty of the daily reset, compare $W_D$ to the power of underlying wealth:

$$
\begin{aligned}
\Delta_{\log}&=\log W_D-L\log W_Q
=\sum_t[\log(1+Lr_t)-L\log(1+r_t)]\\
&\approx-\tfrac12L(L-1)\sum_t r_t^2.
\end{aligned}
$$

The approximation retains the quadratic term in $\log(1+x)$ about zero. Linear terms cancel. Higher-order terms matter on extreme days, and the approximation is most accurate when $|r_t|$ and $|Lr_t|$ are small. For positive daily multipliers and $L>1$, convexity gives $(1+r_t)^L\ge 1+Lr_t$, so the exact log penalty is nonpositive. Squared simple returns satisfy $\sum r_t^2=(n-1)s_r^2+n\bar r^2$, where $s_r^2$ is sample variance. The approximation therefore includes squared drift as well as variance. Full-sample exact and approximate drag were {{full_exact_log_drag}} and {{full_approx_log_drag}}. Each log point denotes one hundredth of a log unit. Neither log value is an arithmetic return gap.

An exact wealth-point decomposition links this penalty to the linear comparator:

$$
W_D-W_H=\underbrace{(W_Q^L-W_H)}_{\text{convex trend term}}+
         \underbrace{(W_D-W_Q^L)}_{\text{daily-reset variance penalty}}.
$$

The first term is nonnegative and grows as the underlying moves away from unit wealth in either direction. For the full period, it was {{full_trend_gap}} and the second term was {{full_variance_gap}}, leaving a positive {{full_reset_gap}} daily-reset gap. Thus a large directional move can outweigh the penalty, while a choppy path with a small net move has little trend contribution. Percentage-point gaps equal one hundred times a wealth-index difference. [Exact penalty and April paths](figures/fig_part2_volatility_decay.png)

The actual-versus-linear gap is $(W_D-W_H)+(W_A-W_D)$. Running both benchmarks on identical dates gives the following reconciliation. The NDX ideal path reproduces the Part 1 index calculation, and the QQQ panel shows the sensitivity to using the investable proxy. [Return-gap waterfall](figures/fig_part2_return_decomposition.png) · [Part 1 replication](../part1/tables/table_part1_replication.csv)

| Full-sample benchmark | Ideal daily return | Linear return | Reset minus linear | Actual minus ideal | Actual minus linear |
|---|---:|---:|---:|---:|---:|
| NDX | {{bench_ndx_ideal_daily_return}} | {{bench_ndx_linear_return}} | {{bench_ndx_reset_gap}} | {{bench_ndx_implementation_gap}} | {{bench_ndx_actual_linear_gap}} |
| QQQ | {{bench_qqq_ideal_daily_return}} | {{bench_qqq_linear_return}} | {{bench_qqq_reset_gap}} | {{bench_qqq_implementation_gap}} | {{bench_qqq_actual_linear_gap}} |

On the NDX basis, exact log drag is {{bench_ndx_exact_log_drag}}, versus {{bench_ndx_approx_log_drag}} from the second-order estimate. The exact-minus-approximate gap is {{bench_ndx_approximation_error}}. This log penalty coexists with the positive arithmetic reset gap.

## Historical attribution

The windows below were chosen after observing the historical episodes and do not classify future regimes. Each window starts from the preceding trading close with unit wealth. Values shown are cumulative within the indicated **return dates**.

| Window | Return dates | QQQ annualized volatility | QQQ | TQQQ | Ideal daily reset | Linear QQQ multiple | Daily reset minus linear |
|---|---|---:|---:|---:|---:|---:|---:|
| COVID sell-off | {{crash_analysis_start}} to {{crash_analysis_end}} | {{crash_qqq_annual_vol}} | {{crash_qqq_return}} | {{crash_tqqq_return}} | {{crash_daily_3x_qqq_return}} | {{crash_linear_3x_qqq_return}} | {{crash_reset_gap}} |
| COVID rebound | {{rebound_analysis_start}} to {{rebound_analysis_end}} | {{rebound_qqq_annual_vol}} | {{rebound_qqq_return}} | {{rebound_tqqq_return}} | {{rebound_daily_3x_qqq_return}} | {{rebound_linear_3x_qqq_return}} | {{rebound_reset_gap}} |
| Rate-hike bear market | {{bear_analysis_start}} to {{bear_analysis_end}} | {{bear_qqq_annual_vol}} | {{bear_qqq_return}} | {{bear_tqqq_return}} | {{bear_daily_3x_qqq_return}} | {{bear_linear_3x_qqq_return}} | {{bear_reset_gap}} |
| April tariff volatility | {{choppy_analysis_start}} to {{choppy_analysis_end}} | {{choppy_qqq_annual_vol}} | {{choppy_qqq_return}} | {{choppy_tqqq_return}} | {{choppy_daily_3x_qqq_return}} | {{choppy_linear_3x_qqq_return}} | {{choppy_reset_gap}} |

- **COVID sell-off and rebound.** As losses contracted the dollar exposure of the daily-reset position, ideal wealth fell less than the linear comparator during the sell-off despite {{crash_exact_log_drag}} of log drag. Reinvested gains during the subsequent rebound generated a {{rebound_reset_gap}} advantage over the linear comparator. The variance penalty was still present during the rebound ({{rebound_variance_gap}}).
- **Rate-hike bear market.** Repeated losses reduced the dollar base of the ideal position. The linear comparator approached zero and the daily-reset gap was positive, even as actual TQQQ returned {{bear_tqqq_return}} and its full-history drawdown trough fell within this period.
- **April tariff volatility.** QQQ finished up {{choppy_qqq_return}} after large reversals. The convex term was only {{choppy_trend_gap}}, against a {{choppy_variance_gap}} wealth penalty. The actual-minus-linear cumulative-return gap reached {{choppy_actual_linear_gap}}.

## Tracking and expense sensitivity

TQQQ targets daily Nasdaq-100 performance before fees and expenses. QQQ is the investable comparison, while NDX gives a separate price-index diagnostic. Define fixed-target daily error $e_t=a_t-Lr_t$ for each comparator and annualized tracking error as its sample standard deviation times $\sqrt A$. The mean daily error measures bias separately. A small spread in daily errors can coexist with a large long-run relative wealth gap. These calculations use adjusted market-price returns, and the NDX series is a price index. [ProShares summary prospectus]({{fee_source}})

| Benchmark for ideal daily reset | Mean daily error | Annualized tracking error | Daily correlation | Actual relative to final ideal wealth |
|---|---:|---:|---:|---:|
| QQQ | {{QQQ_mean_daily_error}} | {{QQQ_annual_tracking_error}} | {{QQQ_daily_correlation}} | {{QQQ_terminal_relative_gap}} |
| NDX | {{NDX_mean_daily_error}} | {{NDX_annual_tracking_error}} | {{NDX_daily_correlation}} | {{NDX_terminal_relative_gap}} |

Switching the ideal reference from QQQ to NDX lowers its terminal wealth by {{full_benchmark_basis_gap_abs}}. Actual TQQQ minus the NDX ideal is {{full_ndx_valuation_gap}}. These two benchmark components sum to the QQQ-based actual-minus-ideal gap before rounding. This decomposition is separate from the expense scenario below.

## Fee and holding-period sensitivity

Estimate fee sensitivity by deducting $f/A$ from every ideal daily QQQ-based return and compounding $W_F=\prod_t(1+Lr_t-f/A)$. The Part 1 issuer snapshot records a {{annual_fee_scenario}} net operating expense ratio on {{fee_accessed}}. Using it throughout the history is a constant-rate sensitivity, while the true historical rates and QQQ's embedded expenses are not separately observable from these returns. Holding financing, trading and tracking assumptions fixed, the scenario changes terminal wealth by {{full_fee_gap}} ({{full_relative_fee_gap}} relative to $W_D$). The actual-minus-ideal gap is {{full_valuation_gap}} and equals the expense scenario plus the {{full_residual_gap}} residual. The residual can reflect financing, transaction costs, distribution and benchmark-basis differences, premiums or discounts, and other tracking effects. The dataset does not identify the separate cost contributions. [Part 1 issuer facts](../../data/metadata/part1_product_facts.csv)

| NDX daily-reset scenario | Annual rate | Terminal wealth | Fee impact vs. zero fee | Actual minus scenario |
|---|---:|---:|---:|---:|
| No fee | {{fee_ndx_no_fee_annual_fee}} | {{fee_ndx_no_fee_terminal_wealth}} | {{fee_ndx_no_fee_fee_gap}} | {{fee_ndx_no_fee_remaining_gap}} |
| Net expense snapshot | {{fee_ndx_net_annual_fee}} | {{fee_ndx_net_terminal_wealth}} | {{fee_ndx_net_fee_gap}} | {{fee_ndx_net_remaining_gap}} |
| Gross expense snapshot | {{fee_ndx_gross_annual_fee}} | {{fee_ndx_gross_terminal_wealth}} | {{fee_ndx_gross_fee_gap}} | {{fee_ndx_gross_remaining_gap}} |

The fee table supplies the same scenarios on the QQQ basis. All differences were calculated before rounding.

| Trailing holding days | Mean absolute daily-reset gap, NDX | Mean absolute daily-reset gap, QQQ | Mean exact NDX log drag |
|---|---:|---:|---:|
| {{holding_days_1}} | {{holding_ndx_1_mean_abs_reset_gap}} | {{holding_qqq_1_mean_abs_reset_gap}} | {{holding_ndx_1_mean_exact_log_drag}} |
| {{holding_days_10}} | {{holding_ndx_10_mean_abs_reset_gap}} | {{holding_qqq_10_mean_abs_reset_gap}} | {{holding_ndx_10_mean_exact_log_drag}} |
| {{holding_days_21}} | {{holding_ndx_21_mean_abs_reset_gap}} | {{holding_qqq_21_mean_abs_reset_gap}} | {{holding_ndx_21_mean_exact_log_drag}} |

The ideal holding-period comparisons coincide at one day and diverge in multi-day windows. The average absolute gap grew with horizon in both series over this sample. The holding-period file reports realized variance as the sum of squared daily simple returns and annualized RMS as the square root of that sum times the annualization factor divided by the window length. Unlike centered sample volatility, RMS is defined for a single return. Overlapping windows describe historical outcomes and have shared observations. [Holding-period diagnostics](tables/table_part2_holding_period_summary.csv)

The trailing OLS slope with an intercept is $\mathrm{Cov}(a_t,r_t)/\mathrm{Var}(r_t)$, with both moments estimated over the same window. The {{long_window}}-day TQQQ slope ranged from {{beta_qqq_min}} to {{beta_qqq_max}} against QQQ and {{beta_ndx_min}} to {{beta_ndx_max}} against NDX. The contemporaneous correlation between QQQ volatility and the magnitude of exact log drag was {{vol_drag_correlation}} across {{long_window}}-day windows. Both calculations use the same realized returns, and overlapping windows make this a descriptive relationship. [Rolling volatility and effective leverage](figures/fig_part2_rolling_volatility_and_leverage.png)

## Implication for Part 3

Similar daily leverage can produce different multi-day loss profiles when the underlying variance and return sequence change. Part 3 should estimate the underlying return process and its conditional volatility, using the canonical QQQ log returns adopted in the current Part 3 notebook. QQQ is a tradable proxy for the Nasdaq-100, and the benchmark comparison above gives the magnitude of the historical basis difference. Any simulated log return must be converted to a simple return before daily leverage and compounding. Simulated paths can then support position-specific VaR and ES in Part 4, followed by chronological validation in Part 5. The historical paths and rolling tables above provide diagnostics for this handoff. [Model specification](../../docs/model_specification.md) · [Part 3 notebook](../../part3.ipynb)

## 中文摘要

沿用 Part 1 的复权收盘价和共同交易日。TQQQ 的年化收益为 {{TQQQ_annual_return}}，QQQ 为 {{QQQ_annual_return}}，但两者的最大回撤分别为 {{TQQQ_max_drawdown}} 和 {{QQQ_max_drawdown}}。样本内固定股数做空 TQQQ 的期末损益为每初始 1 美元 {{short_tqqq_terminal_pnl_per_dollar}}，与持有每日反向重置的 SQQQ 有显著差别。

反弹期每日重置比线性倍数高 {{rebound_reset_gap}}。{{choppy_analysis_start}} 至 {{choppy_analysis_end}} 的震荡期，QQQ 上涨 {{choppy_qqq_return}}，理想每日重置路径的收益为 {{choppy_daily_3x_qqq_return}}，落后线性倍数 {{choppy_reset_gap_abs}}。按披露费率估算的敏感性为理想终值下降 {{full_relative_fee_gap_abs}}，历史实际费用及融资等组成无法单独识别。下一阶段将基于标的收益动态估计波动率，再用于多日 VaR/ES。
"""

SLIDES = """# Part 2. Widescreen slides and speaker notes

Target delivery time is four minutes.

## Slide 1 — Daily leverage did not fix the holding-period multiple

- Use the same adjusted-price sample and initial close for each path.
- Compounding carried the ideal daily-reset path above the linear comparator.
- Actual TQQQ finished below both hypothetical comparisons.

| KPI card | Cumulative return |
|---|---:|
| Actual TQQQ | **{{TQQQ_cumulative_return}}** |
| Ideal daily {{leverage}} QQQ | **{{full_daily_3x_qqq_return}}** |
| Linear {{leverage}} QQQ | **{{full_linear_3x_qqq_return}}** |

**Figure.** [fig_part2_cumulative_returns.png](figures/fig_part2_cumulative_returns.png). Show the QQQ triplet first, then the NDX triplet on the same scale. Use [fig_part2_two_day_example.png](figures/fig_part2_two_day_example.png) as the opening build.

**Speaker notes (about 65 seconds).** “Recall the simple round trip from Part 1. With a gain of {{round_trip_day1}} followed by the exact return that takes the index back to its starting value, the ideal leveraged position earns {{round_trip_daily_reset_return}}. We start all historical paths at {{base_wealth}} at the {{base_date}} close. On the same {{returns}} trading returns through {{analysis_end}}, QQQ gained {{QQQ_cumulative_return}}. Applying {{leverage}} to each daily return and reinvesting generated a much higher hypothetical final return than applying the multiple once to QQQ's cumulative gain. Actual TQQQ ended below both comparisons. The same ordering holds against the formal Nasdaq-100 price index in the lower panel. The two plots answer different benchmark questions, while the actual TQQQ curve is identical in both.”

## Slide 2 — TQQQ’s deeper drawdown did not cap short losses

- TQQQ fell much farther from its prior peak than QQQ.
- Fixed-share short P&L moves opposite to fixed-share long P&L.
- Long SQQQ compounds its own daily inverse returns.

| KPI card | Historical observation |
|---|---:|
| TQQQ maximum drawdown | **{{TQQQ_max_drawdown}}** |
| QQQ maximum drawdown | **{{QQQ_max_drawdown}}** |
| Worst TQQQ short mark per initial USD | **{{short_tqqq_worst_mark_per_dollar}}** |

**Figure.** [fig_part2_drawdown_and_pnl.png](figures/fig_part2_drawdown_and_pnl.png). Compare the drawdowns in the upper panel and the short TQQQ and long SQQQ curves below.

**Speaker notes (about 50 seconds).** “The upper panel measures loss from each ETF's prior high. TQQQ reached a trough drawdown of {{TQQQ_max_drawdown}}, with the trough on {{TQQQ_trough_date}}. The bottom panel holds share count fixed from the start of the sample. The short lost {{short_tqqq_worst_mark_per_dollar_abs}} per initial dollar at its worst mark before borrow and margin effects. SQQQ's line follows a different path because its inverse exposure resets daily. The drawdown and the short loss measure different exposures and different reference points. The drawdown is relative to the latest peak and the short mark starts at the original dollar of exposure.”

## Slide 3 — April reversals pushed the ideal daily-reset return below zero

- A sustained rebound can make the daily-reset path outperform the linear multiple.
- April's small net QQQ gain left little trend contribution to offset the variance penalty.
- The constant-fee scenario quantifies expense sensitivity on the ideal path.

| KPI card | Historical observation |
|---|---:|
| April QQQ return | **{{choppy_qqq_return}}** |
| April ideal daily minus linear | **{{choppy_reset_gap}}** |
| Rebound ideal daily minus linear | **{{rebound_reset_gap}}** |

**Figure.** [fig_part2_volatility_decay.png](figures/fig_part2_volatility_decay.png). Use the upper panel for the log penalty and the April lines for the choppy-period gap. Use [fig_part2_return_decomposition.png](figures/fig_part2_return_decomposition.png) as a second build for full-sample attribution.

**Speaker notes (about 75 seconds).** “The top panel compares the exact log penalty with the squared-return approximation. In April, QQQ recovered to a {{choppy_qqq_return}} gain, but the ideal daily-reset path ended at {{choppy_daily_3x_qqq_return}}. In the COVID rebound, reinvested gains pushed daily reset {{rebound_reset_gap}} ahead of the linear multiple despite a continuing variance penalty. Against the NDX linear benchmark, the full-sample compounding contribution was {{bench_ndx_reset_gap}} and the actual-versus-ideal difference was {{bench_ndx_implementation_gap}}. Applying the {{annual_fee_scenario}} expense snapshot to the QQQ ideal throughout the sample lowers its final wealth by {{full_relative_fee_gap_abs}}. The remaining gap reflects multiple effects that these data cannot separate.”

## Slide 4 — Near-target leverage still left volatility highly variable

- Trailing volatility rose sharply during stressed markets.
- The rolling regression slope stayed close to the daily target.
- Part 3 models underlying volatility to inform multi-day loss distributions.

| KPI card | Historical observation |
|---|---:|
| Peak {{short_window}}-day QQQ annualized volatility | **{{qqq_peak_vol_21}}** |
| Peak {{short_window}}-day TQQQ annualized volatility | **{{tqqq_peak_vol_21}}** |
| {{long_window}}-day TQQQ slope versus QQQ | **{{beta_qqq_min}}–{{beta_qqq_max}}** |

**Figure.** [fig_part2_rolling_volatility_and_leverage.png](figures/fig_part2_rolling_volatility_and_leverage.png). Point first to the volatility peaks, then to the slope around the target line.

**Speaker notes (about 50 seconds).** “The top panel shows {{short_window}}- and {{long_window}}-day annualized volatilities. The lower panel estimates the daily slope against QQQ and NDX. The exposure stayed close to {{leverage}}, even when volatility changed sharply. On the NDX basis, the average absolute reset gap increased from {{holding_ndx_10_mean_abs_reset_gap}} across {{holding_days_10}} trading days to {{holding_ndx_21_mean_abs_reset_gap}} across {{holding_days_21}} trading days. That contrast motivates Part 3. We need a model of the underlying volatility and plausible sequences of returns, so subsequent VaR and ES estimates reflect how daily compounding changes multi-day losses.”

## 中文串讲摘要

按四页顺序呈现。先用全样本净值图说明每日重置和持有期线性倍数的分歧，再用最大回撤及固定股数损益展示多空风险。第三页对照疫情反弹与四月震荡，最后用滚动波动率与斜率说明为何下一阶段需要对标的波动率建模。投影时保留图表的宽屏比例，讲解词放入演讲者备注。
"""

METRIC = re.compile(r"{{([a-zA-Z0-9_]+)}}")


def render_documents(metrics: pd.DataFrame) -> dict[str, str]:
    """Substitute the render-ready values exported to CSV and the console."""
    values = metrics.set_index("metric")["display"].to_dict()
    return {
        name: METRIC.sub(lambda match: str(values[match[1]]), template)
        for name, template in (
            ("part2_report_section.md", REPORT),
            ("part2_ppt_slides.md", SLIDES),
        )
    }
