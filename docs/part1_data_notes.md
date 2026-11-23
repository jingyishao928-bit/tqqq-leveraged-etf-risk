# Part 1 Data Notes

## What was downloaded

The dataset contains daily observations for TQQQ, SQQQ, QQQ and the
Nasdaq-100 Index (`^NDX`). TQQQ is the +3x daily ETF, SQQQ is the -3x daily
inverse ETF, QQQ is the non-leveraged ETF benchmark, and NDX is used as the
underlying index for the daily leverage mechanism. SQQQ is a separate product
path and must not be treated as equivalent to shorting TQQQ.

The raw request range is 2010-02-11 to 2026-11-20. The common project window
is 2019-01-01 to 2026-11-20. Because the first return requires a previous
price, the cleaned price table starts on 2019-01-02 and the return table has
1,983 observations from 2019-01-03 onward.

## Sources

Historical observations were downloaded from Yahoo Finance historical data:

- TQQQ: https://finance.yahoo.com/quote/TQQQ/history/
- SQQQ: https://finance.yahoo.com/quote/SQQQ/history/
- QQQ: https://finance.yahoo.com/quote/QQQ/history/
- Nasdaq-100: https://finance.yahoo.com/quote/%5ENDX/history/

The transport script uses Yahoo's chart endpoint in shorter date chunks. The
raw CSV files are preserved, and
`data/metadata/part1_source_manifest.csv` records the data fields, date windows
and retrieval timestamp. Product facts such as TQQQ's daily objective, fees
and inception date should be cited from ProShares' own product page or current
factsheet, not inferred from the price CSV.

## Cleaning decisions

1. Convert dates to a standard date type, sort ascending and remove duplicate
   dates within each source file.
2. Use adjusted close for TQQQ, SQQQ and QQQ so distributions and splits are
   reflected in ETF performance. Use the unadjusted close for NDX because it
   is an index series in this dataset.
3. Inner-join the four series on common trading dates. Do not manufacture
   weekend or holiday observations and do not forward-fill prices.
4. Check that all retained prices are present and positive.
5. Calculate simple returns first, then calculate log returns as
   `log(1 + simple_return)`.
6. Flag unusually large daily moves for manual review. Do not delete them
   automatically: 2020-03-16 and 2025-04-09 are retained as plausible market
   observations in both the leveraged and inverse ETF series.

## Reproducible cleaning code

The primary CSV workflow is implemented in
`scripts/01_download_part1_data.py`. To rebuild the processed CSV files from
the frozen raw CSV files without downloading new observations or changing the
source manifest, run:

```bash
python scripts/01_download_part1_data.py --clean-existing-raw
```

The Stata workflow is implemented in `stata/01_clean_part1_data.do` and
`stata/02_part1_replication.do`. It applies the same price fields, common-date
join, date range, return definitions and manual-review thresholds to the raw
DTA files. From the repository root, run:

```stata
do "stata/run_part1_pipeline.do" "`c(pwd)'"
```

The Python CSV files remain the reviewed source of truth. The Stata workflow
provides a second, executable route for lab work and code submission.

## The Part 1 replication diagnostic

The idealized daily-reset path is initialized at the first cleaned TQQQ price
and compounded using the NDX simple return:

`V_ideal,t = V_ideal,t-1 * (1 + 3 * r_NDX,t)`.

This is a mechanism check, not a claim that actual TQQQ equals this formula.
Actual TQQQ also reflects fees, financing, trading costs, tracking error,
distributions and the mismatch between an index price return and ETF total
return. The resulting gap is therefore useful evidence for discussion, not a
reason to delete data or force the curves to match.

## Results to mention in the presentation

For the current common window, the diagnostic has 1,984 price rows and 1,983
return observations. The actual and idealized daily returns have a high
correlation, while the cumulative NAV paths diverge materially. The exact
values are in `outputs/part1/tables/table_part1_replication.csv`; use those values in
slides rather than manually retyping numbers.

Use `data/processed/clean_returns.csv` for new group-wide analysis. The
`part1_clean_*` files remain available for the existing replication script and
now include SQQQ fields without changing the TQQQ-versus-NDX calculation.
