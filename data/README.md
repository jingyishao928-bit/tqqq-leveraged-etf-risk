# Data policy

`raw/` stores frozen source extracts only after the group confirms the source terms and documents the retrieval. `processed/` stores reproducible analysis inputs. `metadata/` stores provenance records, dates, row counts, adjustment treatment, and checksums.

The canonical processed dataset is `processed/clean_returns.csv`. Its schema is defined in `docs/data_dictionary.md`.

Do not commit API keys, cookies, account identifiers, or unreviewed downloads. Small course datasets may be force-added after review so the instructor can reproduce the analysis without relying on a live data service.

