# Part 1 Deliverables

## The four-slide job

Part 1 should establish the product, the daily-reset claim, the data design,
and a transparent replication check. It should not jump ahead to VaR or ES
results that depend on later model work.

### Slide 1 Product and research question

Show TQQQ, the Nasdaq-100 benchmark, the 3x daily objective, and the project
question: what happens when a daily leveraged product is held for more than
one day?

Suggested sentence:

> We study whether a fund that targets three times the Nasdaq-100 each day
> also delivers three times the index over a long holding period.

中文意思：我们研究的是“每日三倍”是否等于“持有期三倍”；答案不是简单的
是，因为每天都会重新设定基数。

### Slide 2 Daily leverage and compounding

Use the mechanism equations:

`R_TQQQ,t ≈ 3 r_NDX,t` for one day, before fees and expenses.

`V_t = V_(t-1) (1 + R_TQQQ,t)` for multi-day wealth compounding.

Do not write `R_TQQQ = 3 * cumulative NDX return` as the fund's rule. A short
two-day example is enough to show that the order and size of daily returns
matter.

### Slide 3 Data and cleaning

State the common window (2019-01-01 to 2026-11-20), the three series, the
source pages, the price-field choices and the common-date join. Mention that
the cleaned table contains 1,984 price dates and 1,983 return observations.

Suggested sentence:

> We use adjusted close for TQQQ and QQQ, close for the Nasdaq-100 index, and
> retain only dates observed in all three series.

Point the audience to `data/metadata/part1_data_dictionary.csv` and
`data/metadata/part1_source_manifest.csv` for auditability.

### Slide 4 Replication check

Show `fig_part1_replication.png` and explain the diagnostic formula:

`V_ideal,t = V_ideal,t-1 (1 + 3 r_NDX,t)`.

The idealized path is initialized at the first cleaned TQQQ price and compared
with adjusted TQQQ. The two daily series move closely, but their cumulative
paths diverge. This supports the explanation that daily leverage compounds
path-dependently and that fees, financing, trading costs, distributions and
tracking differences matter.

Use the exact summary numbers from `table_part1_replication.csv`. Do not
describe the idealized path as the actual fund NAV or interpret its gap as a
single fee estimate.

## Handoff to later parts

Part 2 can use the NDX and QQQ fields in `part1_clean_returns.csv` for initial
model exploration, but the group should use the canonical
`clean_returns.csv` once its QQQ, TQQQ and SQQQ contract is implemented. Part
3 can use the same date window and the same sign convention for risk. Part 4
can use the actual/idealized gap and volatility measures for scenario
analysis. Part 5 can backtest only after the estimation window and evaluation
window are explicitly separated.
