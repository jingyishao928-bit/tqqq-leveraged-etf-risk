# Part 2. Widescreen slides and speaker notes

Target delivery time is four minutes.

## Slide 1 — Daily leverage did not fix the holding-period multiple

- Use the same adjusted-price sample and initial close for each path.
- Compounding carried the ideal daily-reset path above the linear comparator.
- Actual TQQQ finished below both hypothetical comparisons.

| KPI card | Cumulative return |
|---|---:|
| Actual TQQQ | **823.07%** |
| Ideal daily 3× QQQ | **1,626.69%** |
| Linear 3× QQQ | **935.65%** |

**Figure.** [fig_part2_cumulative_returns.png](figures/fig_part2_cumulative_returns.png). Show the QQQ triplet first, then the NDX triplet on the same scale. Use [fig_part2_two_day_example.png](figures/fig_part2_two_day_example.png) as the opening build.

**Speaker notes (about 65 seconds).** “Recall the simple round trip from Part 1. With a gain of 10.00% followed by the exact return that takes the index back to its starting value, the ideal leveraged position earns -5.45%. We start all historical paths at 1.00 at the 2019-01-02 close. On the same 1,983 trading returns through 2026-11-20, QQQ gained 311.88%. Applying 3× to each daily return and reinvesting generated a much higher hypothetical final return than applying the multiple once to QQQ's cumulative gain. Actual TQQQ ended below both comparisons. The same ordering holds against the formal Nasdaq-100 price index in the lower panel. The two plots answer different benchmark questions, while the actual TQQQ curve is identical in both.”

## Slide 2 — TQQQ’s deeper drawdown did not cap short losses

- TQQQ fell much farther from its prior peak than QQQ.
- Fixed-share short P&L moves opposite to fixed-share long P&L.
- Long SQQQ compounds its own daily inverse returns.

| KPI card | Historical observation |
|---|---:|
| TQQQ maximum drawdown | **-81.66%** |
| QQQ maximum drawdown | **-35.12%** |
| Worst TQQQ short mark per initial USD | **-$18.46** |

**Figure.** [fig_part2_drawdown_and_pnl.png](figures/fig_part2_drawdown_and_pnl.png). Compare the drawdowns in the upper panel and the short TQQQ and long SQQQ curves below.

**Speaker notes (about 50 seconds).** “The upper panel measures loss from each ETF's prior high. TQQQ reached a trough drawdown of -81.66%, with the trough on 2022-12-28. The bottom panel holds share count fixed from the start of the sample. The short lost $18.46 per initial dollar at its worst mark before borrow and margin effects. SQQQ's line follows a different path because its inverse exposure resets daily. The drawdown and the short loss measure different exposures and different reference points. The drawdown is relative to the latest peak and the short mark starts at the original dollar of exposure.”

## Slide 3 — April reversals pushed the ideal daily-reset return below zero

- A sustained rebound can make the daily-reset path outperform the linear multiple.
- April's small net QQQ gain left little trend contribution to offset the variance penalty.
- The constant-fee scenario quantifies expense sensitivity on the ideal path.

| KPI card | Historical observation |
|---|---:|
| April QQQ return | **1.40%** |
| April ideal daily minus linear | **-7.57 pp** |
| Rebound ideal daily minus linear | **164.86 pp** |

**Figure.** [fig_part2_volatility_decay.png](figures/fig_part2_volatility_decay.png). Use the upper panel for the log penalty and the April lines for the choppy-period gap. Use [fig_part2_return_decomposition.png](figures/fig_part2_return_decomposition.png) as a second build for full-sample attribution.

**Speaker notes (about 75 seconds).** “The top panel compares the exact log penalty with the squared-return approximation. In April, QQQ recovered to a 1.40% gain, but the ideal daily-reset path ended at -3.38%. In the COVID rebound, reinvested gains pushed daily reset 164.86 pp ahead of the linear multiple despite a continuing variance penalty. Against the NDX linear benchmark, the full-sample compounding contribution was 478.49 pp and the actual-versus-ideal difference was -535.87 pp. Applying the 0.78% expense snapshot to the QQQ ideal throughout the sample lowers its final wealth by 5.95%. The remaining gap reflects multiple effects that these data cannot separate.”

## Slide 4 — Near-target leverage still left volatility highly variable

- Trailing volatility rose sharply during stressed markets.
- The rolling regression slope stayed close to the daily target.
- Part 3 models underlying volatility to inform multi-day loss distributions.

| KPI card | Historical observation |
|---|---:|
| Peak 21-day QQQ annualized volatility | **91.73%** |
| Peak 21-day TQQQ annualized volatility | **265.95%** |
| 63-day TQQQ slope versus QQQ | **2.848×–3.002×** |

**Figure.** [fig_part2_rolling_volatility_and_leverage.png](figures/fig_part2_rolling_volatility_and_leverage.png). Point first to the volatility peaks, then to the slope around the target line.

**Speaker notes (about 50 seconds).** “The top panel shows 21- and 63-day annualized volatilities. The lower panel estimates the daily slope against QQQ and NDX. The exposure stayed close to 3×, even when volatility changed sharply. On the NDX basis, the average absolute reset gap increased from 0.53 pp across 10 trading days to 1.16 pp across 21 trading days. That contrast motivates Part 3. We need a model of the underlying volatility and plausible sequences of returns, so subsequent VaR and ES estimates reflect how daily compounding changes multi-day losses.”

## 中文串讲摘要

按四页顺序呈现。先用全样本净值图说明每日重置和持有期线性倍数的分歧，再用最大回撤及固定股数损益展示多空风险。第三页对照疫情反弹与四月震荡，最后用滚动波动率与斜率说明为何下一阶段需要对标的波动率建模。投影时保留图表的宽屏比例，讲解词放入演讲者备注。
