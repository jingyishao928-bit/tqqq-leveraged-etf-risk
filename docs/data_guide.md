# Data Guide: TQQQ, SQQQ, QQQ and Nasdaq-100

This is the main data reference for the group. Read this page before using the
data in a model, chart, slide or report. It explains what each file contains,
where the observations came from, how the raw data were changed, what every
analysis variable means and which limitations must be disclosed.

## 中文快速说明

- 新分析优先使用 `data/processed/clean_returns.csv`；Stata 使用同名 `.dta`。
- 数据包括 TQQQ（每日 +3 倍 ETF）、SQQQ（每日 -3 倍反向 ETF）、QQQ（1 倍
  ETF 基准）和 NDX（Nasdaq-100 指数）。
- TQQQ、SQQQ、QQQ 使用 Yahoo Finance 的 `Adj Close`，NDX 使用 `Close`。
- 四组数据只保留共同交易日，不补周末、假期或缺失价格。
- 收益率是小数：`0.01` 代表 `1%`，不是 `0.01%`。
- SQQQ 是每日反向重置 ETF，不等同于做空 TQQQ。两者多日损益路径不同。
- SQQQ 历史调整价格很高是反向 ETF 多次反向拆股经过回溯调整的结果。分析应
  关注收益率和标准化净值，不应把历史调整价格当作当时可观察的实际报价。
- 两个极端日期被保留并标记，不应直接删除，否则会低估 VaR、ES 和压力期风险。

## 1. Which file should I use?

| Task | Recommended file | Reason |
|---|---|---|
| New modeling, VaR/ES, regimes or backtesting | `data/processed/clean_returns.csv` | Canonical lower-case schema with all four series |
| The same work in Stata | `data/processed/clean_returns.dta` | Same observations and variables in Stata 118 format |
| Part 1 TQQQ replication script | `data/processed/part1_clean_returns.csv` | Retains the established upper-case compatibility names |
| Price-level chart before computing returns | `data/processed/part1_clean_prices.csv` | Includes the first common price date and has no return-related row loss |
| Audit the downloaded observations | `data/raw/*_raw.csv` | Frozen source extracts; do not edit these files |
| Check sources and retrieval time | `data/metadata/part1_source_manifest.csv` | Provider, URL, timestamps, windows and selected price field |
| Check exact variable definitions | `data/metadata/part1_data_dictionary.csv` | Machine-readable field dictionary |
| Check data integrity | `data/metadata/part1_data_quality.csv` and `part1_checksums.csv` | Counts, dates, flags and SHA-256 fingerprints |

The CSV files are the reviewed source of truth. Every tracked CSV has a
same-folder `.dta` copy for Stata. Do not combine the raw and processed files
in one analysis: choose the processed table unless the task is specifically a
source audit or a cleaning-method demonstration.

## 2. What the four series represent

| Stored label | Yahoo ticker | Project role | Price field used |
|---|---|---|---|
| TQQQ | `TQQQ` | ProShares UltraPro QQQ; daily +3x leveraged product being studied | `Adj Close` |
| SQQQ | `SQQQ` | ProShares UltraPro Short QQQ; daily -3x inverse product for comparison | `Adj Close` |
| QQQ | `QQQ` | Invesco QQQ; non-leveraged ETF benchmark | `Adj Close` |
| NDX | `^NDX` | Nasdaq-100 price index; underlying mechanism benchmark | `Close` |

The leverage targets are daily objectives. A +3x or -3x daily target is not a
promise that the fund's multi-day cumulative return will equal three times the
index's multi-day cumulative return. Daily rebalancing and compounding make
the result path-dependent.

SQQQ and a short TQQQ position are different exposures. SQQQ resets its
inverse leverage every day and embeds its own fees, financing and tracking.
A short TQQQ position instead has the negative P&L of TQQQ shares and may
involve borrow costs, margin and losses greater than the initial capital.

## 3. Source, retrieval and sample dates

### Historical market observations

The committed raw observations were downloaded through Yahoo Finance's chart
endpoint and preserved as frozen extracts. Human-readable source pages are:

| Series | Historical-data page |
|---|---|
| TQQQ | <https://finance.yahoo.com/quote/TQQQ/history/> |
| SQQQ | <https://finance.yahoo.com/quote/SQQQ/history/> |
| QQQ | <https://finance.yahoo.com/quote/QQQ/history/> |
| Nasdaq-100 | <https://finance.yahoo.com/quote/%5ENDX/history/> |

The current source manifest records retrieval at
`2026-11-23T16:23:25.950804+00:00`. Yahoo Finance is a convenient secondary
data source, not the issuer, exchange or official Nasdaq index vendor. A live
redownload may include later provider revisions, so the committed raw files
are used for reproducibility.

### Product facts

Price history and product terms are separate sources. Current product facts for
QQQ, TQQQ and SQQQ were verified from Invesco and ProShares issuer materials
on 2026-11-24 and stored in
`data/metadata/part1_product_facts.csv`. The record covers formal names,
sponsors or advisers, benchmarks, objectives, inception dates, expense ratios
and the current TQQQ waiver expiry.

Official issuer references are:

- QQQ product detail: <https://www.invesco.com/us/en/financial-products/etfs/invesco-qqq-trust-series-1.html>
- QQQ overview: <https://www.invesco.com/qqq-etf/en/home.html>
- TQQQ product page: <https://www.proshares.com/our-etfs/leveraged-and-inverse/tqqq>
- TQQQ summary prospectus: <https://www.proshares.com/globalassets/proshares/prospectuses/tqqq_summary_prospectus.pdf>
- SQQQ product page: <https://www.proshares.com/our-etfs/leveraged-and-inverse/sqqq>
- SQQQ summary prospectus: <https://www.proshares.com/globalassets/proshares/prospectuses/sqqq_summary_prospectus.pdf>

The TQQQ prospectus dated 2026-09-28 reports 0.94% before waivers, a
0.16% contractual reduction, 0.78% after waivers and a 2027-09-30 expiry for
the applicable arrangements. SQQQ currently reports 0.94% gross and net. QQQ
reports a 0.18% total expense ratio. These expense ratios are not complete
all-in trading or financing costs.

These issuer pages support product descriptions and current terms. They are
not the source of the committed historical OHLCV observations.

### Date ranges and row counts

| Stage | Dates | Rows | Interpretation |
|---|---:|---:|---|
| Each raw file | 2010-02-11 to 2026-11-20 | 4,221 | Frozen daily source observations |
| Configured analysis window | 2019-01-01 to 2026-11-20 | N/A | Requested project period |
| Clean common prices | 2019-01-02 to 2026-11-20 | 1,984 | Dates observed for all four series |
| Clean common returns | 2019-01-03 to 2026-11-20 | 1,983 | One fewer row because a return needs the previous price |

There is no 2019-01-01 price because it was not a trading day. The first
common price is therefore 2019-01-02, and its first daily return is dated
2019-01-03.

## 4. Data lineage: raw to clean

```text
Yahoo Finance chart endpoint
        |
        v
four frozen raw files (TQQQ, SQQQ, QQQ, NDX)
        |
        | parse dates, sort, remove duplicate dates
        | choose ETF Adj Close and NDX Close
        | inner-join the four common trading calendars
        | restrict to the configured 2019-2026 window
        | validate positive and non-missing prices
        v
part1_clean_prices
        |
        | compute simple and log returns from adjacent trading rows
        | retain and flag extreme observations
        v
part1_clean_returns + canonical clean_returns
        |
        v
models, simulation, VaR/ES, regimes and backtesting
```

The exact cleaning steps are:

1. Parse dates, sort ascending and remove duplicate dates inside each source.
2. Use adjusted close for TQQQ, SQQQ and QQQ; use close for NDX.
3. Inner-join the four series on date. A date survives only when all four have
   an observation.
4. Restrict dates to the configured project window.
5. Do not forward-fill, interpolate or manufacture weekend/holiday prices.
6. Require every retained analysis price to be present and strictly positive.
7. Calculate simple returns first and log returns second.
8. Retain plausible extreme observations and mark them for review.

This means the clean data are not a random subsample. They are a matched
trading-date panel designed for valid same-day comparison across the four
series.

## 5. Raw-file variables

Each `data/raw/*_raw.csv` file has the following fields:

| Field | Meaning | Unit/use |
|---|---|---|
| `Ticker` | Stored Yahoo symbol | Text audit field |
| `Date` | Source trading date | `YYYY-MM-DD`; join key |
| `Open` | Opening price or index level | Raw audit only |
| `High` | Highest reported value during the session | Raw audit only |
| `Low` | Lowest reported value during the session | Raw audit only |
| `Close` | Unadjusted closing price or index level | Used for NDX |
| `Adj Close` | Provider-adjusted close | Used for TQQQ, SQQQ and QQQ |
| `Volume` | Provider-reported daily volume | Context only; ETF and index volumes are not directly comparable |
| `Dividends` | Cash-distribution event reported by the provider | Audit only; already reflected in ETF adjusted close when applicable |
| `Stock Splits` | Split event reported by the provider | Audit only; adjusted close reflects split history |

ETF price fields are in USD-per-share terms, subject to Yahoo's historical
adjustments. NDX is measured in index points. These levels must not be added,
averaged or directly compared across products.

SQQQ has experienced reverse splits. A historical adjusted close can therefore
look extremely large even though that was not the contemporaneous quoted share
price. This is expected in a back-adjusted series and does not by itself imply
a data error. The raw file records eight non-unit split factors: `0.25` on
2012-05-11, 2014-01-24, 2017-01-12 and 2019-05-24, and `0.20` on 2020-08-18,
2022-01-13, 2024-11-07 and 2025-11-20.

## 6. Canonical analysis variables

The canonical file is `data/processed/clean_returns.csv`.

### Prices and volumes

| Variable | Meaning | Unit |
|---|---|---|
| `date` | Common trading date | `YYYY-MM-DD` |
| `qqq_adj_close` | QQQ adjusted close | Back-adjusted USD per share |
| `tqqq_adj_close` | TQQQ adjusted close | Back-adjusted USD per share |
| `sqqq_adj_close` | SQQQ adjusted close | Back-adjusted USD per share |
| `ndx_close` | Nasdaq-100 unadjusted close | Index points |
| `qqq_volume` | QQQ source-reported daily volume | Shares |
| `tqqq_volume` | TQQQ source-reported daily volume | Shares |
| `sqqq_volume` | SQQQ source-reported daily volume | Shares |
| `ndx_volume` | Source-reported NDX volume field | Provider units; context only |

### Returns and review flag

| Variable | Meaning | Unit/formula |
|---|---|---|
| `qqq_simple_return` | QQQ one-day simple return | Decimal, `P_t / P_(t-1) - 1` |
| `tqqq_simple_return` | TQQQ one-day simple return | Decimal, `P_t / P_(t-1) - 1` |
| `sqqq_simple_return` | SQQQ one-day simple return | Decimal, `P_t / P_(t-1) - 1` |
| `ndx_simple_return` | NDX one-day simple return | Decimal, `P_t / P_(t-1) - 1` |
| `qqq_log_return` | QQQ one-day log return | `ln(1 + qqq_simple_return)` |
| `tqqq_log_return` | TQQQ one-day log return | `ln(1 + tqqq_simple_return)` |
| `sqqq_log_return` | SQQQ one-day log return | `ln(1 + sqqq_simple_return)` |
| `ndx_log_return` | NDX one-day log return | `ln(1 + ndx_simple_return)` |
| `manual_review_flag` | Large daily move requiring source review | Boolean: `True` or `False` |

A return of `0.025` means `+2.5%`; a return of `-0.025` means `-2.5%`.
The two return definitions are related by

```text
simple return: r_t = P_t / P_(t-1) - 1
log return:    g_t = ln(P_t / P_(t-1)) = ln(1 + r_t)
conversion:    r_t = exp(g_t) - 1
```

The idealized daily leveraged return is based on a simple return, for example
`3 * ndx_simple_return`. Do not multiply a log return by three and then treat
the result as a simple return without first applying `exp(g) - 1`.

## 7. Compatibility-file names

`part1_clean_prices.csv` and `part1_clean_returns.csv` contain the same
economic series but preserve the original Part 1 naming style, such as
`TQQQ_price`, `SQQQ_simple_ret` and `NDX_log_ret`. They exist so the established
replication script continues to run. New work should use the canonical
lower-case table to avoid different teams creating incompatible schemas.

## 8. Extreme observations and review thresholds

The cleaning code sets `manual_review_flag = True` when any condition holds:

```text
abs(TQQQ return) > 30%
abs(SQQQ return) > 30%
abs(QQQ return)  > 15%
abs(NDX return)  > 15%
```

Two rows are currently flagged:

| Date | TQQQ | SQQQ | QQQ | NDX | Decision |
|---|---:|---:|---:|---:|---|
| 2020-03-16 | -34.47% | +32.74% | -11.98% | -12.19% | Retained and flagged |
| 2025-04-09 | +35.24% | -35.28% | +12.00% | +12.02% | Retained and flagged |

The flag is a review aid, not a deletion instruction. Removing genuine stress
days would bias volatility, VaR and ES downward. Any decision to winsorize or
exclude observations must be a separate documented modeling choice and must
not overwrite the canonical dataset.

## 9. Quality controls already completed

- Dates are unique and sorted in ascending order.
- The clean tables contain only common dates for all four series.
- No retained analysis price is missing or non-positive.
- The return table contains 1,983 finite return observations for every series.
- Exactly two rows are flagged for manual review.
- SQQQ daily returns have a correlation of approximately `0.99856` with the
  idealized `-3 * NDX` daily simple return.
- Each tracked CSV has a readable same-folder Stata `.dta` file with matching
  dimensions and values.
- SHA-256 file fingerprints are recorded in
  `data/metadata/part1_checksums.csv`.

Run the current automated checks with:

```bash
python -m unittest discover -s tests -v
python scripts/export_part1_stata.py --check-only
```

Passing tests confirm consistency with the reviewed snapshot. They do not
prove that Yahoo Finance has no provider errors or that current product terms
have not changed.

## 10. How to load the canonical data

### Python

```python
import pandas as pd

data = pd.read_csv(
    "data/processed/clean_returns.csv",
    parse_dates=["date"],
)
print(data.shape)
print(data[["date", "tqqq_simple_return", "sqqq_simple_return"]].head())
```

### R

```r
data <- read.csv("data/processed/clean_returns.csv")
data$date <- as.Date(data$date)
str(data)
head(data[c("date", "tqqq_simple_return", "sqqq_simple_return")])
```

### Stata

```stata
use "data/processed/clean_returns.dta", clear
describe
summarize tqqq_simple_return sqqq_simple_return qqq_simple_return ndx_simple_return
format date %tdCCYY-NN-DD
```

### Excel

Open `data/processed/clean_returns.csv` directly. Confirm that the `date`
column is interpreted as a date and leave return columns as decimals. Format a
return column as Percentage only for display; do not multiply it by 100 and
then feed that displayed percentage into a model. Do not save manual changes
over the canonical file.

## 11. Rebuilding the data

Rebuild the processed CSV files from the committed raw files without making a
live network request:

```bash
python scripts/01_download_part1_data.py --clean-existing-raw
```

Rebuild or verify the Stata exports:

```bash
python scripts/export_part1_stata.py
python scripts/export_part1_stata.py --check-only
```

Run the native Stata cleaning and replication route from the repository root:

```stata
do "stata/run_part1_pipeline.do" "`c(pwd)'"
```

A live data refresh must update the raw files, processed files, source
manifest, quality summary, checksums, documentation and tests together in one
reviewed pull request.

## 12. Limitations to state in the project

1. Yahoo Finance is a secondary data provider, not the official Nasdaq index
   vendor or the ETF issuer.
2. ETF adjusted returns and NDX price-index returns are not a perfectly matched
   total-return comparison.
3. Adjusted close incorporates distributions and split adjustments but does
   not separately identify financing costs, transaction costs or tracking
   mechanics.
4. The matched-date rule can remove a date that exists in only some inputs.
5. The sample ends on 2026-11-20 and contains no later observations.
6. QQQ, TQQQ and SQQQ product facts are issuer-verified snapshots accessed on
   2026-11-24; fees and contractual waivers can change after that date.
7. SQQQ is not a proxy for the P&L of shorting TQQQ.
8. The difference between actual TQQQ and an idealized `3 * NDX` path cannot be
   attributed entirely to volatility decay. Fees, financing, tracking and the
   return-convention mismatch also contribute.

## 13. Related references

- `docs/data_dictionary.md`: concise canonical schema.
- `docs/part1_data_notes.md`: shorter methodological narrative.
- `docs/stata_exports.md`: CSV-to-Stata conversion conventions.
- `tests/README.md`: automated-test coverage and snapshot change record.
- `data/metadata/part1_source_manifest.csv`: exact source record.
- `data/metadata/part1_data_dictionary.csv`: machine-readable field definitions.
- `data/metadata/part1_data_quality.csv`: current row-count and quality summary.
- `data/metadata/part1_checksums.csv`: file-integrity fingerprints.
