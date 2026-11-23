# Data Dictionary

## Canonical file

`data/processed/clean_returns.csv`

| Column | Type | Definition |
|---|---|---|
| `date` | date | Common trading date in `YYYY-MM-DD` format |
| `qqq_adj_close` | float | Adjusted close or total-return-consistent price for QQQ |
| `tqqq_adj_close` | float | Adjusted close or total-return-consistent price for TQQQ |
| `sqqq_adj_close` | float | Adjusted close or total-return-consistent price for SQQQ |
| `qqq_simple_return` | float | `P_t / P_(t-1) - 1` |
| `qqq_log_return` | float | `log(P_t / P_(t-1))` |
| `tqqq_simple_return` | float | `P_t / P_(t-1) - 1` |
| `sqqq_simple_return` | float | `P_t / P_(t-1) - 1` |

## Validation rules

- Dates are unique, ascending, and restricted to common available dates.
- Prices are strictly positive.
- Returns are finite wherever present.
- Only the first aligned observation may have missing returns.
- Intermediate values retain full floating-point precision.
- The data metadata identifies source, retrieval timestamp, sample dates, and adjustment method.

## Part 1 supplementary files

The committed Part 1 mechanism check predates the complete canonical file and
uses TQQQ, QQQ and the Nasdaq-100 Index (`^NDX`). It is intentionally stored as
`data/processed/part1_clean_returns.csv`; it must not be passed to code that
expects the SQQQ columns in the canonical contract.

Its detailed fields and formulas are recorded in
`data/metadata/part1_data_dictionary.csv`. The source and quality records are
`part1_source_manifest.csv`, `part1_data_quality.csv`, and
`part1_checksums.csv` in the same metadata directory.
