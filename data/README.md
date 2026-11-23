# Data policy

`raw/` stores frozen source extracts only after the group confirms the source terms and documents the retrieval. `processed/` stores reproducible analysis inputs. `metadata/` stores provenance records, dates, row counts, adjustment treatment, and checksums.

The canonical processed dataset is `processed/clean_returns.csv`. Its schema is defined in `docs/data_dictionary.md`.

The reviewed Part 1 mechanism dataset is stored separately as
`processed/part1_clean_prices.csv` and
`processed/part1_clean_returns.csv`. It aligns TQQQ, QQQ and the Nasdaq-100
Index and therefore does not replace the planned canonical file, which also
requires SQQQ. Its source manifest, field dictionary, quality checks and
SHA-256 digests are in `metadata/part1_*.csv`.

Each tracked CSV also has a same-folder Stata `.dta` copy for use in the lab.
The CSV files remain the source of truth. See `docs/stata_exports.md` for the
file list, conversion rules, Stata commands and rebuild instructions.

Do not commit API keys, cookies, account identifiers, or unreviewed downloads. Small course datasets may be force-added after review so the instructor can reproduce the analysis without relying on a live data service.
