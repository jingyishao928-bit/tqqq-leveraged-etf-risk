# Part 1 Data Description and Test Coverage

This document is the detailed reference for the data currently covered by the
automated tests in this directory. It explains where the Part 1 data came
from, how the raw extracts were transformed, what changed between data stages,
which observations require manual review, and what the tests do and do not
guarantee.

## 1. Scope and current status

The reviewed dataset covers four daily market series:

| Series | Role in the project | Raw ticker |
|---|---|---|
| TQQQ | Leveraged ETF being studied | `TQQQ` |
| SQQQ | Daily inverse leveraged ETF used for product comparison | `SQQQ` |
| QQQ | Unleveraged ETF benchmark | `QQQ` |
| Nasdaq-100 Index | Underlying index used for the idealized 3x mechanism check | `^NDX` (stored as `NDX`) |

These files support the product-mechanics, inverse-product and replication
analysis. `data/processed/clean_returns.csv` is the canonical group-wide
table. The `part1_` files retain the established column names used by the
existing replication script.

## 2. Date ranges and observation counts

| Data stage | Date range | Observations | Explanation |
|---|---:|---:|---|
| Raw TQQQ | 2010-02-11 to 2026-11-20 | 4,221 daily rows | Frozen Yahoo Finance extract |
| Raw SQQQ | 2010-02-11 to 2026-11-20 | 4,221 daily rows | Frozen Yahoo Finance extract |
| Raw QQQ | 2010-02-11 to 2026-11-20 | 4,221 daily rows | Frozen Yahoo Finance extract |
| Raw NDX | 2010-02-11 to 2026-11-20 | 4,221 daily rows | Frozen Yahoo Finance extract |
| Requested analysis window | 2019-01-01 to 2026-11-20 | Not applicable | Common project window configured for Part 1 |
| Clean common-price table | 2019-01-02 to 2026-11-20 | 1,984 common trading days | First available common trading day after the requested start |
| Clean return table | 2019-01-03 to 2026-11-20 | 1,983 daily returns | One fewer row because the first return requires the previous price |

The four raw files each contain 4,222 physical CSV lines: one header plus
4,221 observations. Weekends and market holidays are not inserted. The
processed tables contain only dates observed in all four source series.

The current files were retrieved on 2026-11-23 at approximately 16:23 UTC.
The exact timestamp for each series is stored in
`data/metadata/part1_source_manifest.csv`.

## 3. Sources and source separation

### Historical market data

Daily OHLCV observations, adjusted close values, dividends, and split events
were downloaded from Yahoo Finance historical data:

| Series | Source URL | Field used in the analysis |
|---|---|---|
| TQQQ | <https://finance.yahoo.com/quote/TQQQ/history/> | `Adj Close` |
| SQQQ | <https://finance.yahoo.com/quote/SQQQ/history/> | `Adj Close` |
| QQQ | <https://finance.yahoo.com/quote/QQQ/history/> | `Adj Close` |
| Nasdaq-100 | <https://finance.yahoo.com/quote/%5ENDX/history/> | `Close` |

The download script uses Yahoo Finance's chart endpoint in shorter sub-periods
and combines the results into one frozen raw CSV per series. The committed raw
files are used for reproducibility; rerunning a live download may produce
revisions from the provider.

### Product facts

TQQQ's investment objective, inception date, and expense ratios are not
inferred from Yahoo prices. They are recorded separately from the ProShares
product page: <https://www.proshares.com/our-etfs/leveraged-and-inverse/tqqq>.
The current metadata snapshot records a 3x daily objective, an inception date
of 2010-02-09, a 0.94% gross expense ratio, and a 0.78% net expense ratio.
These product facts should be rechecked against the latest factsheet or
prospectus before the final presentation because fees and waivers can change.

## 4. Files and their purposes

| Location | Purpose |
|---|---|
| `data/raw/TQQQ_raw.csv` | Frozen, unmodified TQQQ source extract |
| `data/raw/SQQQ_raw.csv` | Frozen, unmodified SQQQ source extract |
| `data/raw/QQQ_raw.csv` | Frozen, unmodified QQQ source extract |
| `data/raw/NDX_raw.csv` | Frozen, unmodified Nasdaq-100 source extract |
| `data/processed/part1_clean_prices.csv` | Aligned TQQQ, SQQQ, QQQ, and NDX prices and volumes |
| `data/processed/part1_clean_returns.csv` | Simple returns, log returns, prices, volumes, and review flag |
| `data/processed/clean_returns.csv` | Canonical lower-case group-wide return table |
| `data/metadata/part1_source_manifest.csv` | Provider, URL, retrieval time, date windows, and field selection |
| `data/metadata/part1_data_dictionary.csv` | Field definitions and formulas |
| `data/metadata/part1_data_quality.csv` | Row counts, date limits, duplicates, missing values, and flags |
| `data/metadata/part1_product_facts.csv` | Product facts sourced from ProShares |
| `data/metadata/part1_checksums.csv` | SHA-256 fingerprints for detecting file changes |

Every tracked CSV also has a same-folder Stata `.dta` export for lab use. The
CSV remains the source of truth; the Stata files are derived copies using
format version 118. Dates, datetimes, booleans, and variable names are converted
according to `docs/stata_exports.md`.

## 5. Transformation from raw data to analysis data

The pipeline makes the following changes. These are deliberate analytical
choices rather than corrections to the source files.

1. Parse each source date, sort observations in ascending order, and remove
   duplicate dates within each individual series.
2. Restrict the analysis to the configured window beginning 2019-01-01.
3. Use `Adj Close` for TQQQ, SQQQ and QQQ. This incorporates the provider's split and
   distribution adjustments and is the closest available price-based proxy
   for ETF total-return performance.
4. Use `Close` for NDX because the downloaded Nasdaq-100 series is a price
   index. This is a different return convention from the adjusted ETF series
   and is explicitly treated as a limitation.
5. Inner-join all four series by trading date. A date is kept only if TQQQ,
   SQQQ, QQQ, and NDX all have an observation.
6. Do not forward-fill missing prices and do not manufacture weekend or
   holiday rows.
7. Require every retained price to be present and strictly positive.
8. Calculate daily simple returns as
   `r_t = P_t / P_(t-1) - 1`.
9. Calculate log returns from simple returns as
   `g_t = log(1 + r_t)`. Log returns are not multiplied directly by three in
   the daily leverage mechanism.
10. Flag unusually large daily moves for manual review, but retain plausible
    market observations instead of deleting them automatically.

### What changed numerically

| Change | Effect |
|---|---|
| Raw history to project window | Each 4,221-row raw series is restricted to the 2019-2026 analysis period |
| Individual calendars to common calendar | Only dates shared by all four series remain, producing 1,984 price rows |
| Prices to returns | The first price row has no lagged price, producing 1,983 return rows |
| Raw close to ETF analysis price | TQQQ, SQQQ and QQQ use adjusted close rather than unadjusted close |
| Large-move review | Two observations are flagged and retained; no row is deleted merely for being extreme |

## 6. Manually reviewed extreme observations

| Date | TQQQ return | SQQQ return | QQQ return | NDX return | Treatment |
|---|---:|---:|---:|---:|---|
| 2020-03-16 | -34.47% | +32.74% | -11.98% | -12.19% | Retained and flagged |
| 2025-04-09 | +35.24% | -35.28% | +12.00% | +12.02% | Retained and flagged |

The review flag is a quality-control signal, not an instruction to winsorize or
delete the observation. Removing genuine stress events would understate VaR,
ES, and volatility-regime risk.

## 7. Replication diagnostic and interpretation

The Part 1 mechanism check initializes an idealized wealth index and applies
three times the NDX daily simple return:

```text
V_ideal,t = V_ideal,t-1 * (1 + 3 * r_NDX,t)
```

For 2019-01-02 through 2026-11-20, the current output reports:

| Metric | Current value |
|---|---:|
| Correlation: actual TQQQ daily return vs. `3 x NDX` | 0.9989 |
| Actual TQQQ final normalized NAV | 9.2307 |
| Idealized daily 3x final normalized NAV | 14.5894 |
| Actual path relative to idealized path | 36.73% lower |

This gap must not be labelled entirely as volatility decay. It also contains
fees, financing costs, trading and tracking differences, distributions, and
the convention mismatch between an ETF adjusted-return series and an index
price-return series. The diagnostic checks the daily-reset mechanism; it is not
an exact replication model for the fund.

## 8. Automated test coverage

`test_part1_data.py` currently checks seven data properties:

| Test | What it protects |
|---|---|
| `test_price_dates_are_unique_and_ascending` | Exactly 1,984 unique, ordered common dates with the expected endpoints |
| `test_prices_are_positive` | All retained TQQQ, SQQQ, QQQ, and NDX prices are strictly positive |
| `test_returns_are_complete_and_finite` | Exactly 1,983 finite simple-return observations for all four series |
| `test_exactly_two_rows_are_flagged_for_review` | The review set remains 2020-03-16 and 2025-04-09 |
| `test_sqqq_raw_data_matches_the_frozen_source_window` | SQQQ has 4,221 unique ordered rows with the expected endpoints |
| `test_canonical_returns_include_all_four_series` | The canonical table contains finite prices and returns for all four series |
| `test_sqqq_daily_returns_track_the_inverse_ndx_direction` | SQQQ daily returns remain highly correlated with the idealized `-3 x NDX` target |

`test_financial_conventions.py` adds five tests for log-to-simple return
conversion, path dependence, the simulated NAV floor, uncapped short losses,
and the positive-loss VaR/ES convention. `test_stata_exports.py` adds two tests
that require every tracked CSV to have a readable, same-sized `.dta` copy and
that verify the analysis date variable is stored correctly. The current suite
therefore contains fourteen tests in total.

Run all tests from the repository root:

```bash
python3 -m unittest discover -s tests -v
```

Passing tests establish structural consistency with the reviewed snapshot.
They do not independently prove that Yahoo Finance data are free of provider
errors, that product terms are current, or that the model is statistically
appropriate.

## 9. Version and change record

| Repository event | Change |
|---|---|
| Commit `e07760b` | Added the reviewed Part 1 download/cleaning pipeline, frozen raw files, processed files, metadata, replication outputs, and data tests |
| PR #1 / merge `f944276` | Merged the Part 1 data workstream into `main` |
| PR #2 / merge `d58ea33` | Added same-folder Stata exports, conversion documentation, and Stata export tests |
| SQQQ data update | Added raw and cleaned SQQQ data, incorporated current provider revisions to ETF adjusted closes, and regenerated the canonical table, Stata exports, metadata, tests and replication outputs |

Future data refreshes should update the source manifest, quality summary, and
checksums in the same commit as the raw and processed files. Any change to the
date window, ticker set, price convention, join rule, return formula, or review
threshold should also be described here and covered by updated tests.

## 10. Known limitations and planned extensions

- Yahoo Finance is a convenient secondary market-data source, not an exchange
  or official index-vendor feed.
- NDX uses a price-index close while TQQQ, SQQQ and QQQ use adjusted ETF prices. The
  series are useful for a mechanism check but are not perfectly matched total
  return measures.
- The fixed end date of 2026-11-20 means later market observations are not yet
  included.
- Expense ratios and other product facts can change and must be revalidated
  before final submission.
- Large-move flags identify records for review; they are not automatic evidence
  of bad data.
- The current tests validate the stored snapshot, not future live downloads.
- SQQQ is an inverse daily-reset ETF. Its return path is not equivalent to a
  short position in TQQQ.

For the shorter methodological narrative, see
`docs/part1_data_notes.md`. For exact field definitions, source records, and
file fingerprints, use the CSV files under `data/metadata/`.
