# Part 1 Deliverables: Product Mechanics, Data and Daily Compounding

> Updated 2026-11-24. This is an execution guide for the Part 1 presenter:
> English slide content and speaking notes, Chinese explanations, verified
> data results, code and Q&A preparation. Five slides and 3.5 minutes are a
> team planning suggestion, not an instructor requirement or grading promise.

## 1. Purpose, individual contribution and boundaries

**Main question: What are we studying, how does it work, and what data can
we use to study it?**

中文主线：认识产品 → 理解敞口与每日重置 → 理解每日复利 → 展示数据基础与清洗
→ 用一个日度实证检查，把产品机制和数据接起来。Part 1 保留**产品机制、数据基础、
每日复利逻辑**，不是只做开场介绍。

For individual assessment, make four contributions visible:

1. **Product research:** distinguish the fund, index, comparator and market
   participants; support product claims with primary sources.
2. **Mechanism analysis:** connect fund net assets, exposure, daily reset and
   compounded investor wealth with equations and a numerical example.
3. **Data ownership:** justify price fields, alignment, return definitions,
   extreme-observation treatment and reproducibility.
4. **Empirical judgment:** check the daily leverage relationship and explain
   what the evidence can and cannot establish.

Show actual work in the division-of-labor statement. More slides alone do
not demonstrate more contribution; keep detailed evidence in the appendix.

### Division of content

| Part | Main contribution | Boundary / handoff |
|---|---|---|
| **1: Product, data and basic daily compounding** | Product structure; daily reset; two-day example; clean data; descriptive statistics; one full-sample daily diagnostic | Establish definitions and the data foundation |
| **2: Return mechanics** | Actual-versus-ideal-versus-holding-period paths; volatility-drag derivation; rolling leverage; relation to volatility | Reuse the definitions; quantify the consequences without repeating S3 |
| **3: Model and simulation** | Model selection, calibration, diagnostics and daily path simulation | Explicitly choose NDX or QQQ and convert log returns to simple returns before leverage |
| **4: Risk results** | Long/short VaR and ES; confidence/horizon/regime/1x comparisons | State positions, units, signs and horizons |
| **5: Backtesting and risk management** | Chronological forecasts, exception tests and practical limits | Full-sample Part 1 statistics are descriptive, not parameters known in advance |

The current repository includes SQQQ and the canonical four-series dataset.
Mention SQQQ as an inverse-product comparison; keep TQQQ, NDX and QQQ at the
center of Part 1. Buying SQQQ is not equivalent to shorting TQQQ. [P2, P4]

## 2. Five-slide presentation blueprint

| Slide | Title | One job | Suggested time |
|---|---|---|---:|
| S1 | What exactly are we studying? | Define product and comparison design | 30 sec |
| S2 | How is daily 3x exposure maintained? | Explain exposure and daily rebalancing | 45 sec |
| S3 | Why is daily 3x not holding-period 3x? | Explain compounding through one example | 55 sec |
| S4 | From raw prices to a defensible dataset | Show cleaning decisions and evidence | 50 sec |
| S5 | Does the daily relationship resemble 3x? | Give a daily diagnostic and hand off | 30 sec |
| **Total** | | **Rehearse aloud; move detail to backup if needed** | **210 sec** |

### S1. What exactly are we studying? / 产品与研究设计

**Conclusion:** TQQQ has a daily leverage objective; NDX and QQQ answer
different benchmark questions.

**On the slide**

| Series | Product / reference | Research role |
|---|---|---|
| TQQQ | ProShares UltraPro QQQ; daily +3x objective before fees and expenses | Main leveraged ETF |
| NDX / `^NDX` | Nasdaq-100 price index | Underlying reference for the ideal daily mapping |
| QQQ | Invesco QQQ, tracking the Nasdaq-100 | Non-leveraged investable comparator |
| SQQQ, small footnote | ProShares UltraPro Short QQQ; daily -3x objective | Separate inverse-product comparison |

Issuer sources: [P1-P4]. The daily objective concerns fund performance; the
adjusted market-close returns used in our dataset are not official fund NAV
returns and cannot alone certify target compliance.

**中文讲解要点**

- NDX 是指数点位，QQQ 才是可交易的 1x ETF 对照。
- NDX 用来检查日度机制，QQQ 用来比较投资者承担的风险；不能悄悄互换。
- 底层相同并不意味着所有差异都来自杠杆，费用、分配和收益口径也有影响。
- ETF 份额在交易所买卖，基金内部仍可能使用 OTC 衍生品。

**English speaking notes — approximately 30 seconds**

> We study TQQQ, which targets three times the daily performance of the
> Nasdaq-100 before fees and expenses. NDX is our index reference, while QQQ
> is the investable, non-leveraged comparator. Keeping both helps us examine
> the daily mechanism and compare investor outcomes. Our key distinction is
> between a daily target and a holding-period return.

**Contribution evidence:** a source-linked comparison table and explicit
research design. Add dated source footers, not just fund logos.

### S2. How is daily 3x exposure maintained? / 敞口与每日重置

**Conclusion:** the target exposure changes when fund net assets change.

**Visual to build**

```text
Investors trade ETF shares on an exchange
                    |
             Fund net assets
                    |
          Portfolio + derivatives
                    |
          Target exposure ~= 3 x net assets
                    |
           Market move changes net assets
                    |
           Rebalance the exposure
```

The TQQQ holdings dated 2026-11-20 on the ProShares product page include index swaps,
Nasdaq-100 futures, equities and cash/Treasury holdings. This supports the
mechanism diagram, not a fixed allocation or a statement that each asset is
always held. Cite the displayed holdings date. [P1]

For a stylized return swap, the fund exchanges a financing leg for the agreed
reference return on a notional amount. For example, $200 of reference notional
with a +1% reference return produces +$2 before financing under that assumed
contract; a negative return reverses the return payment. Notional is exposure,
not the swap's market value or collateral balance. Futures likewise provide
exposure without purchasing the full underlying basket. Contract terms and
collateral/margin must be checked separately. [P2]

**Equations**

```text
Target exposure:          E*_t = ell x A_t
Rebalancing requirement:  Delta E_t = ell x A_t - E^-_t
TQQQ target multiple:     ell = 3
```

| Symbol | Meaning and unit |
|---|---|
| `A_t` | Whole-fund net assets after the move, in dollars; not a share price |
| `E*_t` | Target dollar-equivalent index exposure after rebalance |
| `E^-_t` | Exposure immediately before rebalance |
| `Delta E_t` | Additional exposure to acquire; negative means reduce exposure |
| `ell` | Daily leverage multiple, dimensionless |

Additional exposure is not necessarily an equal cash payment or margin deposit.

**Numerical mechanism, ignoring flows, costs and tracking**

Start with $100 of net assets, $300 of index exposure and $200 of financing
in a stylized financed portfolio. This is an illustration, not actual TQQQ
holdings or an operational forecast.

| Item | Index rises 10% | Index falls 10% |
|---|---:|---:|
| Exposure before rebalance | $330 | $270 |
| Net assets after move | $130 | $70 |
| Target exposure at 3x | $390 | $210 |
| Required rebalance | Add $60 of exposure | Reduce $60 of exposure |

中文：涨完后基金净资产也增加，原敞口不再是新净资产的三倍，需要加敞口；跌完
则要减敞口。实际交易还受申赎、衍生品结构、执行与成本影响。

**Market participants — understand these; keep the full table in backup**

| Participant | Role | Relevant issue |
|---|---|---|
| Investors | May seek short-horizon tactical exposure or hedging | Illustrative motivations, not verified ownership shares |
| Sponsor / manager | Designs and manages the fund | Management fee, execution and tracking risks |
| Authorized Participants | Participate in creation/redemption arrangements | Different from ordinary secondary-market investors |
| Market makers | Quote ETF shares and support market liquidity | Spreads and premiums/discounts to NAV |
| Swap counterparties | Supply contracted derivative exposure | Counterparty default and collateral arrangements |

Use [P2] for fund-specific derivative/counterparty disclosures and [P5] for
ETF trading and creation/redemption roles. Collateral mitigates rather than
eliminates counterparty risk. A fully paid ETF share purchase does not itself
make the investor post the fund's derivative margin; brokerage leverage and
short sales have separate margin considerations. Leave numerical rules to
Part 5 with the applicable account and regulatory context.

**English speaking notes — approximately 45 seconds**

> Three-times leverage is an exposure target. With one hundred dollars of
> net assets, the target exposure is three hundred dollars. In a simplified
> example, a ten-percent index rise increases net assets to one hundred and
> thirty dollars. Existing exposure becomes three hundred and thirty, but
> the new target is three hundred and ninety. The fund therefore adds
> exposure. The reverse happens after a fall. Derivatives help obtain this
> exposure, while financing, liquidity and counterparty arrangements create
> additional risks.

### S3. Why is daily 3x not holding-period 3x? / 每日复利

**Conclusion:** apply leverage each day, then compound the daily returns.

**Formulas**

```text
Index simple return:       r_t = I_t / I_(t-1) - 1
Actual ETF return:         R_t = P^adj_t / P^adj_(t-1) - 1
Ideal daily leverage:      R^ideal_t = ell x r_t
Actual wealth:            W_T = W_0 x PRODUCT(1 + R_t)
Ideal daily-reset wealth:  W^ideal_T = W_0 x PRODUCT(1 + ell x r_t)
Holding-period benchmark:  W^HP_T = W_0 x [1 + ell x (PRODUCT(1 + r_t) - 1)]
```

`I_t` is the index level; `P^adj_t` is the adjusted ETF closing price; `t`
is a trading day; `T` is the number of holding days; `W_0` is initial
investor wealth or a normalized wealth index. `PRODUCT` multiplies factors
from day 1 to day `T`. `W^HP` is a mathematical comparison, not the fund's
rule or an automatically feasible self-financing investment strategy.

For explanation, write `R_t = ell x r_t - c_t + u_t`, with specified cost
effects `c_t` and remaining differences `u_t`. Returns alone do not identify
them separately. Do not assume constant costs, infer fees from a regression
intercept, or subtract management fees again from observed ETF returns.

**Two-day example: no costs or tracking differences**

| Date | Index daily return | Index wealth | Ideal 3x daily return | Ideal 3x wealth |
|---|---:|---:|---:|---:|
| Start | - | 100 | - | 100 |
| Day 1 | +10% | 110 | +30% | 130 |
| Day 2 | -10% | 99 | -30% | 91 |

1. Index: `100 x 1.10 x 0.90 = 99`; cumulative return `99/100 - 1 = -1%`.
2. Ideal daily 3x: `100 x 1.30 x 0.70 = 91`; cumulative return `-9%`.
3. Three times the holding-period index return: `3 x (-1%) = -3%`;
   comparison wealth `100 x (1 - 0.03) = 97`.
4. Thus `91 != 97` even before costs. The difference is six percentage
   points of initial wealth, not an estimated management fee.

中文：第二天的 -30% 作用在 130 上，不是初始的 100 上。

**Important qualifications**

- Decay is not a guaranteed result in every market. With two +10% index
  days, the index returns 21% and the ideal 3x fund returns 69%, above
  `3 x 21% = 63%`.
- Path dependence here means the daily changes contain information beyond
  the index's terminal cumulative return. Merely permuting an identical set
  of daily returns does not change the terminal product in this ideal,
  constant-leverage, no-flow example: multiplication commutes.
- Require positive wealth factors in this illustration. Extreme-move,
  termination and NAV-floor treatment must be explicit in the simulation;
  do not silently carry a negative fund NAV forward.

**English speaking notes — approximately 55 seconds**

> Daily leverage must be compounded daily. Suppose an index starts at one
> hundred, rises ten percent and then falls ten percent. It finishes at
> ninety-nine, a one-percent loss. An ideal three-times fund instead moves
> from one hundred to one hundred and thirty, then to ninety-one. Its loss
> is nine percent, not three percent, even before costs. The second return
> applies to a different wealth base. This is not a claim that leverage
> always causes decay: persistent positive returns can produce the opposite
> comparison. Part 2 will quantify these effects in the historical paths.

### S4. From raw prices to a defensible dataset / 数据与清洗

**Conclusion:** use aligned adjusted-return data, preserve auditability and
retain plausible stress observations.

| Series | Historical source | Field and interpretation |
|---|---|---|
| TQQQ, QQQ, SQQQ | Yahoo Finance chart API | `Adj Close`; provider adjustment for splits/distributions, a total-return proxy |
| NDX (`^NDX`) | Yahoo Finance chart API | `Close`; price index excluding dividends |

These are secondary-provider market-price data, not official fund NAVs.
ETF adjusted returns and NDX price returns are not perfectly matched total
returns. Keep this limitation visible. Exact pages, timestamps and field
choices are in the [source manifest](../data/metadata/part1_source_manifest.csv).

**Current committed snapshot**

| Item | Value |
|---|---|
| Requested analysis window | 2019-01-01 to 2026-11-20 |
| Common prices | 2019-01-02 to 2026-11-20; 1,984 rows |
| Common returns | 2019-01-03 to 2026-11-20; 1,983 rows |
| Duplicate retained dates / missing retained prices | 0 / 0 |
| Flagged rows retained | 2 |
| Recorded retrieval time | 2026-11-23T16:23:25.950804+00:00 |

The 2019 start is a research-design choice that includes contrasting market
conditions but excludes earlier history. Do not call it the fund's lifetime
or an optimal selection. The first return is January 3 because the pipeline
computes returns after selecting the January 2 starting price, without
importing a prior-year price.

**Cleaning pipeline**

```text
Four frozen raw inputs
  -> parse dates, sort and deduplicate
  -> ETF adjusted close / NDX close
  -> inner-join common dates and restrict the sample
  -> require positive, non-missing prices
  -> calculate simple returns, then log returns
  -> flag extremes and retain plausible observations
  -> canonical CSV + DTA + audit metadata
```

**Explain why each choice matters**

1. No forward-filling: artificial flat prices can create zero returns and
   misleading catch-up returns. Check gaps against the trading calendar;
   a missing common trading day can make adjacent retained prices span more
   than one session.
2. Do not add dividends again to adjusted-price returns. Splits/reverse
   splits also make raw price-level comparisons misleading, especially SQQQ.
3. Simple return `r_t = P_t/P_(t-1) - 1`; log return `g_t = ln(1 + r_t)`;
   conversion `r_t = exp(g_t) - 1`. Store decimals: `0.01 = 1%`.
4. Apply daily leverage to simple returns, not directly to multi-day log
   returns. The model can use logs and convert them back before mapping.
5. Review flags: absolute TQQQ/SQQQ return over 30% or QQQ/NDX over 15%.
   These are workflow thresholds, not deletion rules or statistical tests.
6. Dates 2020-03-16 and 2025-04-09 remain flagged. Check source/event evidence
   before asserting a specific cause; internal consistency cannot certify
   a data vendor. Removing genuine stress days can understate tail risk.
7. Preserve frozen inputs. A live download may revise historical adjustments;
   review the raw files, metadata and outputs together when refreshing data.

**English speaking notes — approximately 50 seconds**

> Our matched sample contains nineteen hundred and eighty-four price dates
> and one fewer return, from January 2019 through November 2026. We use ETF
> adjusted closes and the NDX price index, while disclosing their return
> convention difference. We align common dates, avoid forward-filling and
> calculate both simple and log returns. Two extreme dates remain flagged
> rather than deleted. Removing genuine stress observations could understate
> risk. Sources, checksums and executable Python and Stata workflows make
> these choices traceable and reproducible.

### S5. Does the daily relationship resemble 3x? / 日度实证检查

**Conclusion:** strong co-movement and sensitivity close to 3x support the
broad mechanism; they do not prove exact tracking or a valid risk model.

**Chart specification — generated and ready for slide selection**

- Scatter: x = NDX daily simple return; y = TQQQ daily adjusted-price return.
- Include both `y = 3x` and the fitted OLS line with distinct styles.
- Show percent axes, `n = 1,983`, sample dates and the source/price-field caveat.
- Keep and label the two flagged dates; do not omit them to improve appearance.
- Output: `outputs/part1/figures/fig_part1_daily_leverage_check.png`.
  Regenerate with `python scripts/analyze_part1.py`; this is a separate
  analysis step after cleaning.

```text
Regression:        R_t = alpha + beta x r_t + epsilon_t
Fixed-target gap:  d_t = R_t - 3r_t
```

`alpha` is the fitted daily intercept, `beta` is the fitted slope, and
`epsilon_t` is the regression residual. It is not the same as `d_t`.

**Recomputed from the current canonical dataset**

| Statistic | Value | What to say |
|---|---:|---|
| Intercept `alpha` | -0.0002206204 | About -2.206 bp/day; not an identified fee |
| Slope `beta` | 2.9213226 | Estimated daily sensitivity, not the contractual target |
| `R^2` | 0.99784275 | High sample fit, not a forecast-validity test |
| Correlation | 0.99892079 | Strong co-movement, not exact 3x replication |
| Mean `d_t` | -0.0002842770 | About -2.843 bp/day; combines several effects |

The intercept/gap may reflect costs, tracking, market prices and differing
return conventions; this regression does not identify their contributions.
No hypothesis test of `beta = 3` is reported. An official tracking assessment
would need matched NAV and benchmark definitions. This is full-sample
descriptive evidence, not an out-of-sample backtest.

**English speaking notes — approximately 30 seconds**

> We finish with a daily diagnostic. The fitted TQQQ sensitivity to NDX is
> about two point nine two, with an R-squared of ninety-nine point eight
> percent. This supports the broad daily-leverage mechanism, but does not
> prove exact tracking. Costs, market-price effects and return conventions
> remain. Part 2 now examines how daily compounding and these differences
> accumulate over a holding period.

## 3. Descriptive statistics and existing evidence

Use as an S4/S5 inset or a backup table. All numbers are **daily simple
returns in percent**, not annualized returns or geometric growth rates.
Standard deviation uses `n - 1`. Each series has 1,983 observations over
2019-01-03 to 2026-11-20.

| Series | Daily mean | Daily standard deviation | Minimum | Maximum |
|---|---:|---:|---:|---:|
| TQQQ | 0.2143% | 4.4896% | -34.4652% | 35.2442% |
| QQQ | 0.0830% | 1.5178% | -11.9788% | 12.0031% |
| NDX | 0.0809% | 1.5352% | -12.1932% | 12.0223% |
| SQQQ | -0.2154% | 4.5035% | -35.2841% | 32.7422% |

中文：简单收益均值不等于几何增长率；波动率不是 VaR；历史最大损失不是未来
损失上限。不能仅凭上表宣布某个产品的长期风险收益比更好。

| Deliverable | File / location | Status |
|---|---|---|
| Frozen raw prices | `data/raw/{TQQQ,SQQQ,QQQ,NDX}_raw.csv` and `.dta` | Available |
| Canonical return panel | `data/processed/clean_returns.csv` / `.dta` | Available; use for new group work |
| Compatibility prices/returns | `data/processed/part1_clean_prices.*`, `part1_clean_returns.*` | Available; established replication-script inputs |
| Data explanation and audit | `docs/data_guide.md`, `data/metadata/part1_*.csv` | Available; source, dictionary, quality and checksums |
| Cleaning workflows | Python/Stata paths in section 5 | Available |
| Idealized replication diagnostic | `outputs/part1/figures/fig_part1_replication.png`; `outputs/part1/tables/table_part1_replication.csv` | Available; detailed interpretation handed to Part 2 |
| Descriptive/OLS results | Tables in this document; runnable script in section 5 | Computed from current data; refresh after snapshot changes |
| Daily scatter and standalone table exports | `fig_part1_daily_leverage_check.png`; `table_part1_descriptive_statistics.*`; `table_part1_daily_leverage_check.*` under `outputs/part1/` | Available; two CSV/DTA pairs and a 300-dpi PNG |
| Five slides and rehearsal | Section 2 blueprint | To prepare |
| Dated product evidence | Section 7 sources and exact holdings/factsheet captures | Sources checked; save evidence used in final slides |

**Distinguish two gaps:** actual TQQQ versus ideal daily 3x NDX is not a pure
volatility-decay estimate: both paths already compound daily leverage. Its
gap combines costs, tracking and return-definition differences. Ideal daily
3x versus three times the index holding-period return is the separate
compounding comparison. Part 2 must label these benchmarks explicitly.

## 4. Formula backup and interpretation

### Exact two-day identity

```text
Index cumulative return = (1 + r_1)(1 + r_2) - 1
                        = r_1 + r_2 + r_1 r_2
Ideal leveraged return  = (1 + ell r_1)(1 + ell r_2) - 1
                        = ell(r_1 + r_2) + ell^2 r_1 r_2
Difference from ell x index cumulative return
                        = ell(ell - 1)r_1 r_2
```

At `ell = 3`, the difference is `6r_1r_2`. Opposite signs give a negative
difference; same signs give a positive difference when the assumed wealth
factors remain valid. This exact result needs no volatility estimate. Leave
the log-growth/variance-drag approximation and its assumptions to Part 2.

### Rebalancing identity under the S2 assumptions

```text
A_t       = A_(t-1)(1 + ell r_t)
E^-_t     = ell A_(t-1)(1 + r_t)
Delta E_t = ell A_t - E^-_t
          = ell(ell - 1)A_(t-1)r_t
```

With `ell = 3`, initial net assets `100` and index return `0.10`, acquire
`3 x 2 x 100 x 0.10 = 60` of additional exposure. This is a stylized
mechanism; flows, derivatives and execution alter the actual implementation.

### Daily regression and units

```text
beta_hat  = SUM[(r_t - mean(r))(R_t - mean(R))]
            / SUM[(r_t - mean(r))^2]
alpha_hat = mean(R) - beta_hat x mean(r)
R^2       = 1 - SUM(epsilon_hat_t^2) / SUM[(R_t - mean(R))^2]
```

The slope is dimensionless. Intercepts/gaps are daily decimal returns:
multiply by 100 for percent, or 10,000 for basis points. High correlation
does not guarantee the correct scale, zero mean gap or matching wealth paths.

## 5. Reproduction and slide-preparation code

Run from the repository root. Use frozen inputs when preparing slides;
a live refresh is a separate reviewed data update.

All Part 1 generated figures and tables belong to `outputs/part1/`, with
`figures/` and `tables/` subdirectories. The analysis and replication scripts read this
root from `part1.output_dir` in `config/project.yaml`. Parts 2-5 have separate
reserved folders; see [output layout](../outputs/README.md).

### Existing Python / Stata workflows

```bash
# Offline cleaning from frozen raw CSVs.
python scripts/01_download_part1_data.py --clean-existing-raw

# Existing idealized replication diagnostic, mainly used by Part 2.
python scripts/02_part1_replication.py

# Descriptive table, daily OLS table and daily-leverage scatter.
python scripts/analyze_part1.py

# Rebuild corresponding Stata copies after an intentional output refresh.
python scripts/export_part1_stata.py

# Verify the reviewed snapshot and export conventions.
python -m unittest discover -s tests -v
python scripts/export_part1_stata.py --check-only
```

```stata
// Native Stata cleaning and established replication workflow.
do "stata/run_part1_pipeline.do" "`c(pwd)'"
```

### Runnable Python analysis: three outputs in one command

The former inline recipe is now
[`scripts/analyze_part1.py`](../scripts/analyze_part1.py). Install the existing
dependencies once, then run it from the repository root:

```bash
python -m pip install -r requirements.txt
python scripts/analyze_part1.py
```

It reads `data.processed_file` and the Part 1 date window, leverage and
output root from `config/project.yaml`. It performs no live download and
does not change the raw or processed inputs. Rerunning replaces only its
five named result files:

```text
outputs/part1/
  tables/
    table_part1_descriptive_statistics.csv
    table_part1_descriptive_statistics.dta
    table_part1_daily_leverage_check.csv
    table_part1_daily_leverage_check.dta
  figures/
    fig_part1_daily_leverage_check.png
```

**Step 1 — Check and select the input / 检查及选样**

The script requires unique ascending ISO dates, all four finite daily
simple-return columns and valid review flags. Positive-price returns must
exceed -100%. It rejects invalid input instead of dropping/filling rows.
The configured start/end dates are inclusive and the selected sample needs
at least three observations. Flagged stress observations remain in the
sample and are labelled on the plot. The two endpoints in the tables are
the actual selected dates, not merely the requested calendar dates.

**Step 2 — Describe daily returns / 描述统计**

The first table has one row each for TQQQ, QQQ, NDX and SQQQ. Columns are
`asset`, `observations`, `mean_daily_pct`, `daily_sd_pct`, `min_daily_pct`,
`max_daily_pct`, `analysis_start` and `analysis_end`. Percent columns use
`1 = 1%`; SD is the sample SD with `ddof=1`. These are daily arithmetic
statistics, not annualized statistics or compounded growth rates.

**Step 3 — Fit the daily relation / 日度回归**

Use decimal simple returns to fit `R_TQQQ = alpha + beta*r_NDX + residual`
with an intercept. The second table has `metric`, numeric `value`, `unit`
and actual analysis-date columns. It reports count, target leverage,
intercept, slope, R-squared, correlation, and the mean/sample SD of
`R_TQQQ - leverage*r_NDX`. Multiply decimal return metrics by `100` for
percent or `10,000` for basis points. Keep the fitted residual separate
from the fixed-target gap. No hypothesis-test p-values are reported.

**Step 4 — Export and plot / 导出与画图**

Both CSVs preserve numerical precision and receive same-folder DTA copies
using the shared Stata exporter, which verifies names, values and dates on
read-back. The 300-dpi scatter plots all selected observations, the ideal
daily target and fitted line, with percent axes, flagged dates, source and
price-field limitations. The console also prints both tables.

中文：先看描述表的均值、波动及极端值，了解数据尺度；再看回归斜率是否接近 3，
结合截距、固定目标偏差和散点图解释实际差异。高 R-squared 代表样本内拟合好，
不能推出精确跟踪、截距就是管理费，或者模型可以通过样本外回测。

For a disposable trial, add `--output-dir /path/to/trial-results`. A custom
YAML may be supplied with `--config /path/to/project.yaml`; relative
data/output paths inside that YAML still resolve from the repository root.

### Stata inspection and daily OLS

```stata
use "data/processed/clean_returns.dta", clear
format date %tdCCYY-NN-DD
isid date, sort
summarize tqqq_simple_return qqq_simple_return ndx_simple_return sqqq_simple_return
regress tqqq_simple_return ndx_simple_return
correlate tqqq_simple_return ndx_simple_return
generate double fixed_3x_gap = tqqq_simple_return - 3*ndx_simple_return
summarize fixed_3x_gap
list date tqqq_simple_return sqqq_simple_return qqq_simple_return ndx_simple_return ///
    if manual_review_flag == 1, noobs
```

These Stata results use decimal returns; section 3 displays percentages.
Convert units before comparing workflows. See [Stata exports](stata_exports.md)
for formats and [Data Guide](data_guide.md) for loading data in R or Excel.

## 6. Q&A and completion checklist

| Likely question | Answer to understand and adapt |
|---|---|
| Why both QQQ and NDX? | NDX anchors the index mapping; QQQ is an investable 1x comparator with different cost/distribution conventions. |
| Is daily 3x guaranteed? | No. It is a daily objective before fees/expenses; market prices and fund NAVs can also differ. [P1, P2] |
| Why adjusted prices? | They account for splits/distributions according to the provider. Historical adjusted prices are not executable historical quotes. |
| Why add exposure after an up day? | Net assets rise faster than existing exposure in the stylized example, reducing the leverage ratio unless exposure is increased. |
| Does compounding always hurt? | No; show the two-day identity and distinguish trending from alternating returns. |
| Does reordering identical daily returns change ideal terminal wealth? | No in this constant-leverage, no-flow product formula. Different daily paths with the same index terminal return can still produce different leveraged outcomes. |
| Why retain extreme dates? | A flag requests review. Genuine stress returns belong in a risk dataset; arbitrary deletion understates tails. Source verification remains important. |
| Why is beta 2.92 rather than 3? | It is an estimated market-return slope, affected by several possible differences, not a direct measurement of contractual leverage. |
| Is the intercept the management fee? | No. It is conditional on the estimated slope and does not causally identify an isolated cost. |
| Is high correlation enough? | No. Check scale, intercept, daily gaps and compounded paths separately. |
| Can this full-sample regression enter the backtest? | Not as information known in advance. Part 5 must estimate using only data available at each forecast date. |
| Is buying SQQQ the same as shorting TQQQ? | No. They have different daily exposure and multi-day P&L, plus different costs and margin/borrow arrangements. |

**Completion checklist**

- [ ] Five readable slides and a timed rehearsal at approximately 3.5 minutes.
- [ ] Presenter's own full-name introduction using the team's agreed format.
- [ ] Dated issuer/holdings evidence and source footers.
- [x] Generated daily scatter and descriptive/OLS tables with readable units;
  choose the final slide placement during rehearsal.
- [ ] Canonical CSV/DTA, variable dictionary and source/quality metadata.
- [ ] Code entry points and a record of successful snapshot checks.
- [ ] Visible limitations: market price versus NAV; ETF adjusted versus index price return.
- [ ] Part 2 agreement on actual, ideal daily-reset and holding-period benchmarks.
- [ ] Part 3 agreement on NDX versus QQQ and return conversion.
- [ ] Part 5 agreement on calibration/evaluation dates and look-ahead prevention.

For the report, contribute one product/mechanism subsection and one
source/data-methodology subsection. Keep detail proportional to the team's
page limit and record the work actually completed in the contribution log.

## 7. Sources and product-fact freshness

Primary pages checked for this update on 2026-11-24. A page's holdings/data
date can differ from its access date. Historical sample results above come
from the committed data, not these live pages.

| ID | Source | Purpose |
|---|---|---|
| P1 | [ProShares TQQQ](https://www.proshares.com/our-etfs/leveraged-and-inverse/tqqq) | Objective, benchmark, inception and dated holdings |
| P2 | [TQQQ summary prospectus, September 28, 2026](https://www.proshares.com/globalassets/proshares/prospectuses/tqqq_summary_prospectus.pdf) | Daily objective, fees, investment techniques and counterparty disclosures |
| P3 | [Invesco QQQ](https://www.invesco.com/qqq-etf/en/home.html) | Investable Nasdaq-100 exposure; use current documents for terms |
| P4 | [ProShares SQQQ](https://www.proshares.com/our-etfs/leveraged-and-inverse/sqqq) | Separate daily -3x objective |
| P5 | [SEC: Investor Bulletin — Exchange-Traded Funds](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-12) | ETF trading, APs, creation/redemption and premiums/discounts |
| P6 | [SEC: Leveraged and Inverse ETFs — Investor Bulletin](https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-alerts/sec) | Daily reset and multi-day performance context |
| P7 | [ProShares geared-investing FAQs](https://www.proshares.com/resources/faqs/geared-investing) | General daily-gearing, holding-period and cost explanations |
| D1 | [Repository source manifest](../data/metadata/part1_source_manifest.csv) | Historical Yahoo pages, retrieval timestamp, sample and fields |
| D2 | [Repository Data Guide](data_guide.md) | Data lineage, canonical variables, quality checks and limitations |

**Fee freshness:** the September 28, 2026 summary prospectus reports a 0.94%
gross expense ratio and 0.78% after the stated waiver/reimbursement, with
that arrangement through September 30, 2027. The fee table excludes
transaction and financing costs. These are dated disclosures, not an all-in
constant cost of leverage. [P2] Older product-fact metadata does not yet store
this newer waiver-expiry detail; cite the prospectus when using it. This
documentation-only update does not refresh that metadata.

If adding AUM, spreads, volume or holdings weights, record the exact date
and source. Label current figures separately from the frozen return sample
ending 2026-11-20. These dynamic facts are optional supporting context, not
necessary for the five-slide analytical story.
