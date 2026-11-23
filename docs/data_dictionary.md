# Data Dictionary

## Canonical file

`data/processed/clean_returns.csv`

| Column | Type | Definition |
|---|---|---|
| `date` | date | Common trading date in `YYYY-MM-DD` format |
| `qqq_adj_close` | float | Adjusted close or total-return-consistent price for QQQ |
| `tqqq_adj_close` | float | Adjusted close or total-return-consistent price for TQQQ |
| `sqqq_adj_close` | float | Adjusted close or total-return-consistent price for SQQQ |
| `ndx_close` | float | Unadjusted Nasdaq-100 Index close used for the mechanism benchmark |
| `qqq_volume` | integer | Reported QQQ daily volume |
| `tqqq_volume` | integer | Reported TQQQ daily volume |
| `sqqq_volume` | integer | Reported SQQQ daily volume |
| `ndx_volume` | integer | Reported Nasdaq-100 Index volume from the source feed |
| `qqq_simple_return` | float | `P_t / P_(t-1) - 1` |
| `qqq_log_return` | float | `log(P_t / P_(t-1))` |
| `tqqq_simple_return` | float | `P_t / P_(t-1) - 1` |
| `tqqq_log_return` | float | `log(P_t / P_(t-1))` |
| `sqqq_simple_return` | float | `P_t / P_(t-1) - 1` |
| `sqqq_log_return` | float | `log(P_t / P_(t-1))` |
| `ndx_simple_return` | float | `P_t / P_(t-1) - 1` |
| `ndx_log_return` | float | `log(P_t / P_(t-1))` |
| `manual_review_flag` | boolean | Flags daily moves exceeding the documented review thresholds |

## Validation rules

- Dates are unique, ascending, and restricted to common available dates.
- Prices are strictly positive.
- Returns are finite wherever present.
- Only the first aligned observation may have missing returns.
- Intermediate values retain full floating-point precision.
- The data metadata identifies source, retrieval timestamp, sample dates, and adjustment method.

## Part 1 compatibility files

The Part 1 mechanism check uses TQQQ, SQQQ, QQQ and the Nasdaq-100 Index
(`^NDX`). Its established wide-column files remain available as
`data/processed/part1_clean_prices.csv` and
`data/processed/part1_clean_returns.csv` so the existing replication script
continues to work. New group-wide code should use the lower-case canonical
file `data/processed/clean_returns.csv`.

Its detailed fields and formulas are recorded in
`data/metadata/part1_data_dictionary.csv`. The source and quality records are
`part1_source_manifest.csv`, `part1_data_quality.csv`, and
`part1_checksums.csv` in the same metadata directory.
