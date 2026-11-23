# Stata data exports

Every tracked CSV table in this repository has a same-folder Stata copy with
the same base name. For example:

```text
data/processed/part1_clean_returns.csv
data/processed/part1_clean_returns.dta
```

The CSV files remain the source of truth. Rebuild all Stata files from the
repository root with:

```bash
python scripts/export_part1_stata.py
```

Verify existing files without rewriting them with:

```bash
python scripts/export_part1_stata.py --check-only
```

## Stata cleaning code

The Python export command above converts every tracked CSV to DTA and checks
the conversion. The repository also contains a native Stata analysis route:

```stata
do "stata/run_part1_pipeline.do" "`c(pwd)'"
```

This route reads the frozen raw DTA files, rebuilds
`part1_clean_prices.dta` and `part1_clean_returns.dta`, and then rebuilds the
two replication DTA tables. Its cleaning logic matches the Python workflow:

1. Use adjusted close for TQQQ, SQQQ and QQQ and close for NDX.
2. Remove duplicate dates, sort ascending and keep common trading dates.
3. Restrict the sample to 2019-01-01 through 2026-11-20.
4. Reject missing or non-positive retained prices.
5. Calculate simple and log returns from adjacent trading observations.
6. Retain large moves and mark them with `manual_review_flag`.

## Export conventions

- Files use Stata format version 118, readable by Stata 14 and later,
  including Stata/MP 18.
- Calendar dates such as `Date` and `accessed_on` are stored as Stata daily
  dates with the `%td` format.
- `downloaded_at_utc` is converted to UTC before its timezone is removed and
  is stored as a Stata datetime with the `%tc` format. Stata stores it to
  millisecond precision.
- Boolean fields are stored as byte values: `0` means false and `1` means
  true.
- Stata variable names use letters, numbers and underscores and are limited
  to 32 characters. The original CSV column name is retained as the Stata
  variable label. In the current raw price files, `Adj Close` becomes
  `Adj_Close` and `Stock Splits` becomes `Stock_Splits`.
- Each export is read back immediately and checked against the prepared CSV
  data for column names, dimensions, dates, text and numeric values.

## Included files

The current export set contains 14 files:

```text
data/metadata/part1_checksums.dta
data/metadata/part1_data_dictionary.dta
data/metadata/part1_data_quality.dta
data/metadata/part1_product_facts.dta
data/metadata/part1_source_manifest.dta
data/processed/part1_clean_prices.dta
data/processed/part1_clean_returns.dta
data/processed/clean_returns.dta
data/raw/NDX_raw.dta
data/raw/QQQ_raw.dta
data/raw/SQQQ_raw.dta
data/raw/TQQQ_raw.dta
outputs/tables/part1_replication_path.dta
outputs/tables/table_part1_replication.dta
```

In Stata, open a file from the repository root with, for example:

```stata
use "data/processed/part1_clean_returns.dta", clear
describe
summarize
format Date %tdCCYY-NN-DD
```
