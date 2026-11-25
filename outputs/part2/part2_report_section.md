# Part 2. Historical performance and daily-reset attribution

## Sample and measurement

The frozen Part 1 master dataset contains 1,983 common daily returns from **2019-01-03 to 2026-11-20** and 1,984 common price dates. Wealth is indexed to 1.00 at the **2019-01-02 close**, immediately before the first return. QQQ, TQQQ and SQQQ use adjusted market closes. The Nasdaq-100 (NDX) comparison uses its price index. Both flagged observations remain in the analysis. Returns use the canonical simple-return columns and annualization uses 252 trading days. [Data dictionary](../../docs/data_dictionary.md) · [Data guide](../../docs/data_guide.md)

For each ETF with daily simple returns $r_t$, let $W_t=\prod_{s=1}^t(1+r_s)$. Cumulative return is $W_t-1$. Geometric annual return is $W_T^{A/n}-1$ for $n$ observed returns and annualization factor $A$. Annualized volatility is the sample standard deviation of daily returns times $\sqrt A$. Drawdown is $W_t/\max_{0\le s\le t}W_s-1$, and maximum drawdown is its most negative value. Rolling volatility uses trailing 21- and 63-trading-day windows with the same annualization and sample standard deviation. Each rolling estimate is dated at the close of its last input observation.

| Metric | QQQ | TQQQ | SQQQ |
|---|---:|---:|---:|
| Mean daily return | 0.08% | 0.21% | -0.22% |
| Daily volatility | 1.52% | 4.49% | 4.50% |
| Worst day | -11.98% | -34.47% | -35.28% |
| Best day | 12.00% | 35.24% | 32.74% |
| Cumulative return | 311.88% | 823.07% | -99.82% |
| Annualized return | 19.71% | 32.64% | -55.13% |
| Annualized volatility | 24.09% | 71.27% | 71.49% |
| Maximum drawdown | -35.12% | -81.66% | -99.91% |
| Peak → trough | 2021-12-27 → 2022-11-03 | 2021-11-19 → 2022-12-28 | 2019-01-03 → 2026-10-06 |

TQQQ earned a higher annualized return and sustained a much deeper peak-to-trough loss than QQQ. For a position initiated at one dollar of exposure and held at fixed share count, long TQQQ P&L is $W_A-1$ and short P&L is its negative. These are adjusted-price dollar equivalents per initial dollar, before any additional short-borrow cost, margin, collateral remuneration or implementation expenses. A price rise can generate an uncapped loss on the fixed-share short. Long SQQQ compounds its own inverse returns and can lose at most its invested capital. The minimum fixed-share P&L mark is measured from the initial entry and can differ substantially from maximum drawdown, which is measured from a subsequent peak. [Drawdown and fixed-share P&L](figures/fig_part2_drawdown_and_pnl.png)

| Position | Terminal P&L per initial USD | Worst P&L mark per initial USD |
|---|---:|---:|
| Long TQQQ | $8.23 | -$0.10 |
| Short TQQQ | -$8.23 | -$18.46 |
| Long SQQQ | -$0.9982 | -$0.9990 |

## Daily reset, trend and volatility

For QQQ daily simple returns $r_t$ and TQQQ adjusted-price returns $a_t$, define QQQ wealth $W_Q=\prod_t(1+r_t)$, and compare the three paths below from the same close.

$$
W_A=\prod_t(1+a_t),\qquad
W_D=\prod_t(1+Lr_t),\qquad
W_H=1+L(W_Q-1),\qquad L=3.
$$

$W_D$ reinvests gains and losses at target daily exposure before incremental costs. $W_H$ is an arithmetic holding-period comparator. Its value can cross zero and represents neither a funded ETF wealth process nor a margin rule. The full-sample cumulative returns were **823.07%** for actual TQQQ, **1,626.69%** for the ideal daily-reset path and **935.65%** for the linear QQQ multiple. [Wealth paths](figures/fig_part2_cumulative_returns.png)

A two-day expansion gives $W_D-W_H=L(L-1)r_1r_2$. The cross term is positive when both returns have the same sign and negative when they have opposite signs. In the cost-free fixed-leverage model, permuting the same set of returns preserves terminal wealth because the daily multipliers commute. The underlying's terminal return alone does not determine those multipliers. [Two-day illustration](figures/fig_part2_two_day_example.png)

| Hypothetical path | Day one | Day two | Underlying | Ideal daily reset | Linear multiple |
|---|---:|---:|---:|---:|---:|
| Round trip | 10.00% | -9.09% | 0.00% | -5.45% | 0.00% |
| Two gains | 10.00% | 10.00% | 21.00% | 69.00% | 63.00% |
| Two losses | -10.00% | -10.00% | -19.00% | -51.00% | -57.00% |

The round trip uses the exact second return $1/(1+r_1)-1$ before rounding.

To isolate the log penalty of the daily reset, compare $W_D$ to the power of underlying wealth:

$$
\begin{aligned}
\Delta_{\log}&=\log W_D-L\log W_Q
=\sum_t[\log(1+Lr_t)-L\log(1+r_t)]\\
&\approx-\tfrac12L(L-1)\sum_t r_t^2.
\end{aligned}
$$

The approximation retains the quadratic term in $\log(1+x)$ about zero. Linear terms cancel. Higher-order terms matter on extreme days, and the approximation is most accurate when $|r_t|$ and $|Lr_t|$ are small. For positive daily multipliers and $L>1$, convexity gives $(1+r_t)^L\ge 1+Lr_t$, so the exact log penalty is nonpositive. Squared simple returns satisfy $\sum r_t^2=(n-1)s_r^2+n\bar r^2$, where $s_r^2$ is sample variance. The approximation therefore includes squared drift as well as variance. Full-sample exact and approximate drag were -139.79 log pts and -137.40 log pts. Each log point denotes one hundredth of a log unit. Neither log value is an arithmetic return gap.

An exact wealth-point decomposition links this penalty to the linear comparator:

$$
W_D-W_H=\underbrace{(W_Q^L-W_H)}_{\text{convex trend term}}+
         \underbrace{(W_D-W_Q^L)}_{\text{daily-reset variance penalty}}.
$$

The first term is nonnegative and grows as the underlying moves away from unit wealth in either direction. For the full period, it was 5,951.79 pp and the second term was -5,260.75 pp, leaving a positive 691.04 pp daily-reset gap. Thus a large directional move can outweigh the penalty, while a choppy path with a small net move has little trend contribution. Percentage-point gaps equal one hundred times a wealth-index difference. [Exact penalty and April paths](figures/fig_part2_volatility_decay.png)

The actual-versus-linear gap is $(W_D-W_H)+(W_A-W_D)$. Running both benchmarks on identical dates gives the following reconciliation. The NDX ideal path reproduces the Part 1 index calculation, and the QQQ panel shows the sensitivity to using the investable proxy. [Return-gap waterfall](figures/fig_part2_return_decomposition.png) · [Part 1 replication](../part1/tables/table_part1_replication.csv)

| Full-sample benchmark | Ideal daily return | Linear return | Reset minus linear | Actual minus ideal | Actual minus linear |
|---|---:|---:|---:|---:|---:|
| NDX | 1,358.94% | 880.45% | 478.49 pp | -535.87 pp | -57.38 pp |
| QQQ | 1,626.69% | 935.65% | 691.04 pp | -803.62 pp | -112.58 pp |

On the NDX basis, exact log drag is -142.93 log pts, versus -140.52 log pts from the second-order estimate. The exact-minus-approximate gap is -2.41 log pts. This log penalty coexists with the positive arithmetic reset gap.

## Historical attribution

The windows below were chosen after observing the historical episodes and do not classify future regimes. Each window starts from the preceding trading close with unit wealth. Values shown are cumulative within the indicated **return dates**.

| Window | Return dates | QQQ annualized volatility | QQQ | TQQQ | Ideal daily reset | Linear QQQ multiple | Daily reset minus linear |
|---|---|---:|---:|---:|---:|---:|---:|
| COVID sell-off | 2020-02-20 to 2020-03-23 | 80.02% | -27.92% | -69.83% | -69.46% | -83.75% | 14.29 pp |
| COVID rebound | 2020-03-24 to 2020-09-02 | 29.68% | 77.92% | 389.98% | 398.63% | 233.77% | 164.86 pp |
| Rate-hike bear market | 2022-01-04 to 2022-12-30 | 32.20% | -33.22% | -79.68% | -78.22% | -99.66% | 21.44 pp |
| April tariff volatility | 2025-04-01 to 2025-04-30 | 58.78% | 1.40% | -4.22% | -3.38% | 4.19% | -7.57 pp |

- **COVID sell-off and rebound.** As losses contracted the dollar exposure of the daily-reset position, ideal wealth fell less than the linear comparator during the sell-off despite -20.42 log pts of log drag. Reinvested gains during the subsequent rebound generated a 164.86 pp advantage over the linear comparator. The variance penalty was still present during the rebound (-64.61 pp).
- **Rate-hike bear market.** Repeated losses reduced the dollar base of the ideal position. The linear comparator approached zero and the daily-reset gap was positive, even as actual TQQQ returned -79.68% and its full-history drawdown trough fell within this period.
- **April tariff volatility.** QQQ finished up 1.40% after large reversals. The convex term was only 0.06 pp, against a -7.63 pp wealth penalty. The actual-minus-linear cumulative-return gap reached -8.41 pp.

## Tracking and expense sensitivity

TQQQ targets daily Nasdaq-100 performance before fees and expenses. QQQ is the investable comparison, while NDX gives a separate price-index diagnostic. Define fixed-target daily error $e_t=a_t-Lr_t$ for each comparator and annualized tracking error as its sample standard deviation times $\sqrt A$. The mean daily error measures bias separately. A small spread in daily errors can coexist with a large long-run relative wealth gap. These calculations use adjusted market-price returns, and the NDX series is a price index. [ProShares summary prospectus](https://www.proshares.com/globalassets/proshares/prospectuses/tqqq_summary_prospectus.pdf)

| Benchmark for ideal daily reset | Mean daily error | Annualized tracking error | Daily correlation | Actual relative to final ideal wealth |
|---|---:|---:|---:|---:|
| QQQ | -3.46 bp | 3.21% | 0.9991 | -46.54% |
| NDX | -2.84 bp | 3.83% | 0.9989 | -36.73% |

Switching the ideal reference from QQQ to NDX lowers its terminal wealth by 267.75 pp. Actual TQQQ minus the NDX ideal is -535.87 pp. These two benchmark components sum to the QQQ-based actual-minus-ideal gap before rounding. This decomposition is separate from the expense scenario below.

## Fee and holding-period sensitivity

Estimate fee sensitivity by deducting $f/A$ from every ideal daily QQQ-based return and compounding $W_F=\prod_t(1+Lr_t-f/A)$. The Part 1 issuer snapshot records a 0.78% net operating expense ratio on 2026-11-24. Using it throughout the history is a constant-rate sensitivity, while the true historical rates and QQQ's embedded expenses are not separately observable from these returns. Holding financing, trading and tracking assumptions fixed, the scenario changes terminal wealth by -102.76 pp (-5.95% relative to $W_D$). The actual-minus-ideal gap is -803.62 pp and equals the expense scenario plus the -700.86 pp residual. The residual can reflect financing, transaction costs, distribution and benchmark-basis differences, premiums or discounts, and other tracking effects. The dataset does not identify the separate cost contributions. [Part 1 issuer facts](../../data/metadata/part1_product_facts.csv)

| NDX daily-reset scenario | Annual rate | Terminal wealth | Fee impact vs. zero fee | Actual minus scenario |
|---|---:|---:|---:|---:|
| No fee | 0.00% | 14.5894 | 0.00 pp | -535.87 pp |
| Net expense snapshot | 0.78% | 13.7210 | -86.83 pp | -449.03 pp |
| Gross expense snapshot | 0.94% | 13.5494 | -104.00 pp | -431.87 pp |

The fee table supplies the same scenarios on the QQQ basis. All differences were calculated before rounding.

| Trailing holding days | Mean absolute daily-reset gap, NDX | Mean absolute daily-reset gap, QQQ | Mean exact NDX log drag |
|---|---:|---:|---:|
| 1 | 0.00 pp | 0.00 pp | -0.07 log pts |
| 10 | 0.53 pp | 0.52 pp | -0.71 log pts |
| 21 | 1.16 pp | 1.16 pp | -1.49 log pts |

The ideal holding-period comparisons coincide at one day and diverge in multi-day windows. The average absolute gap grew with horizon in both series over this sample. The holding-period file reports realized variance as the sum of squared daily simple returns and annualized RMS as the square root of that sum times the annualization factor divided by the window length. Unlike centered sample volatility, RMS is defined for a single return. Overlapping windows describe historical outcomes and have shared observations. [Holding-period diagnostics](tables/table_part2_holding_period_summary.csv)

The trailing OLS slope with an intercept is $\mathrm{Cov}(a_t,r_t)/\mathrm{Var}(r_t)$, with both moments estimated over the same window. The 63-day TQQQ slope ranged from 2.848× to 3.002× against QQQ and 2.790× to 3.016× against NDX. The contemporaneous correlation between QQQ volatility and the magnitude of exact log drag was 0.959 across 63-day windows. Both calculations use the same realized returns, and overlapping windows make this a descriptive relationship. [Rolling volatility and effective leverage](figures/fig_part2_rolling_volatility_and_leverage.png)

## Implication for Part 3

Similar daily leverage can produce different multi-day loss profiles when the underlying variance and return sequence change. Part 3 should estimate the underlying return process and its conditional volatility, using the canonical QQQ log returns adopted in the current Part 3 notebook. QQQ is a tradable proxy for the Nasdaq-100, and the benchmark comparison above gives the magnitude of the historical basis difference. Any simulated log return must be converted to a simple return before daily leverage and compounding. Simulated paths can then support position-specific VaR and ES in Part 4, followed by chronological validation in Part 5. The historical paths and rolling tables above provide diagnostics for this handoff. [Model specification](../../docs/model_specification.md) · [Part 3 notebook](../../part3.ipynb)

## 中文摘要

沿用 Part 1 的复权收盘价和共同交易日。TQQQ 的年化收益为 32.64%，QQQ 为 19.71%，但两者的最大回撤分别为 -81.66% 和 -35.12%。样本内固定股数做空 TQQQ 的期末损益为每初始 1 美元 -$8.23，与持有每日反向重置的 SQQQ 有显著差别。

反弹期每日重置比线性倍数高 164.86 pp。2025-04-01 至 2025-04-30 的震荡期，QQQ 上涨 1.40%，理想每日重置路径的收益为 -3.38%，落后线性倍数 7.57 pp。按披露费率估算的敏感性为理想终值下降 5.95%，历史实际费用及融资等组成无法单独识别。下一阶段将基于标的收益动态估计波动率，再用于多日 VaR/ES。
