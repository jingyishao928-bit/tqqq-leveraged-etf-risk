# RMSC 5003 Topic 10 Leveraged ETF Risk

This private course repository studies how a daily leveraged ETF converts underlying returns into multi-day performance and tail risk. The initial product set is QQQ, TQQQ, and SQQQ. Product facts, sample dates, and empirical conclusions must be verified before presentation or submission.

## Research questions

1. How do daily leverage and rebalancing create path-dependent multi-day returns?
2. How well do GBM and GARCH-t models represent the underlying return process?
3. What are the long and short VaR and ES of the selected leveraged ETF?
4. How do risk and performance change across volatility regimes and relative to a 1x benchmark?
5. Do out-of-sample VaR forecasts pass coverage and independence tests?

## Repository workflow

```text
raw data -> processed returns -> fitted model -> simulated paths
         -> VaR/ES and scenarios -> backtesting -> figures/tables
```

Read `AGENTS.md`, `CONTRIBUTING.md`, and `docs/data_dictionary.md` before changing code. Never push directly to `main`; work on a feature branch and open a pull request.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Tests

The repository includes standard-library tests for the financial conventions
and the reviewed Part 1 data snapshot. See
[tests/README.md](tests/README.md) for the detailed data period, sources,
transformations, quality checks, change record, and test coverage.

```bash
python -m unittest discover -s tests -v
```

## Planned execution order

```bash
python scripts/01_download_data.py
python scripts/02_prepare_data.py
python scripts/03_fit_models.py
python scripts/04_run_simulation.py
python scripts/05_calculate_risk.py
python scripts/06_run_backtest.py
```

Scripts are scaffolds until their owners implement and test the corresponding modules. Do not present placeholder output as an empirical result.

## Reviewed data status

The reviewed TQQQ, SQQQ, QQQ and Nasdaq-100 source extracts are available in
both CSV and Stata formats. The lower-case canonical analysis file is
`data/processed/clean_returns.csv`. The `part1_clean_*` compatibility files
retain the established wide-column format used by the Part 1 TQQQ mechanism
check.

```bash
python scripts/01_download_part1_data.py
python scripts/02_part1_replication.py
```

To rerun only the cleaning step from the frozen raw CSV files, or to use the
equivalent Stata workflow, run:

```bash
python scripts/01_download_part1_data.py --clean-existing-raw
```

```stata
do "stata/run_part1_pipeline.do" "`c(pwd)'"
```

Start with [`docs/data_guide.md`](docs/data_guide.md) for the complete source,
date-range, file-selection, variable, formula, cleaning, quality-control and
usage guide. See `docs/part1_data_notes.md` for the shorter methodological
narrative and `docs/part1_deliverables.md` for the five-slide product, data and daily-compounding plan.

## Team ownership

Generated results are grouped by presentation part under `outputs/part1/`
through `outputs/part5/`. Existing Part 1 figures and CSV/DTA tables are in
`outputs/part1/figures/` and `outputs/part1/tables/`; Parts 2-5 are reserved
empty directories. See [output layout](outputs/README.md) for the convention.
Shared raw/processed data and audit metadata remain under `data/`.

| Workstream | Main responsibility | Primary locations |
|---|---|---|
| A | Product research, integration, slides and report | `docs/product_profile.md`, `slides/`, `report/` |
| B | Data, return definitions and NAV mechanics | `data.py`, `mechanics.py`, scripts 01-02 |
| C | GBM/GARCH-t estimation and simulation | `models.py`, `simulation.py`, scripts 03-04 |
| D | VaR/ES, scenarios and 1x benchmark | `risk.py`, `scenarios.py`, script 05 |
| E | Backtesting, coverage tests and limits | `backtesting.py`, script 06 |

Ownership means primary review responsibility, not exclusive permission to edit a file.
