# Data policy

`raw/` stores frozen source extracts only after the group confirms the source terms and documents the retrieval. `processed/` stores reproducible analysis inputs. `metadata/` stores provenance records, dates, row counts, adjustment treatment, and checksums.

The canonical processed dataset is `processed/clean_returns.csv`. Its schema is defined in `docs/data_dictionary.md`.

The reviewed dataset aligns TQQQ, SQQQ, QQQ and the Nasdaq-100 Index. The
canonical table is `processed/clean_returns.csv`. The compatibility tables
`processed/part1_clean_prices.csv` and `processed/part1_clean_returns.csv`
retain the established column names used by the Part 1 replication script.
The source manifest, field dictionary, quality checks and SHA-256 digests are
in `metadata/part1_*.csv`.

Each tracked CSV also has a same-folder Stata `.dta` copy for use in the lab.
The CSV files remain the source of truth. See `docs/stata_exports.md` for the
file list, conversion rules, Stata commands and rebuild instructions.

The complete human-readable description of the Part 1 date ranges, sources,
cleaning changes, flagged observations, replication diagnostic, automated test
coverage, and update protocol is in
[tests/README.md](../tests/README.md).

Do not commit API keys, cookies, account identifiers, or unreviewed downloads. Small course datasets may be force-added after review so the instructor can reproduce the analysis without relying on a live data service.
