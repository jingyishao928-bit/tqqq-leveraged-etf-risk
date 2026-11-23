# Project Conventions and Guardrails

## Scope

This repository supports the RMSC 5003 Topic 10 group project on leveraged ETFs. Read the project README, data dictionary, model specification, and relevant upstream modules before making changes.

## Financial conventions

- Initial products: QQQ as the 1x comparator, TQQQ as the +3x ETF, and SQQQ as the -3x ETF. Verify all product facts from issuer material.
- Fit stochastic models to underlying log returns when the selected model requires log returns.
- Convert simulated log returns to simple returns before applying daily leverage.
- An ideal daily leveraged return is approximately `beta * simple_underlying_return` before explicit fees, financing costs, and tracking differences.
- Never multiply a multi-day log return by beta and call it a daily-reset ETF return.
- Shorting TQQQ is not equivalent to buying SQQQ. Calculate each position from its own wealth path.
- VaR and ES are reported as positive losses. State position, notional, horizon, confidence level, currency, and model with every result.
- Do not square-root scale multi-day risk when paths can be simulated directly.
- Backtests must be chronological and free of look-ahead bias. Kupiec and Christoffersen tests apply to VaR exceptions, not automatically to ES.
- Treat volatility decay as path-dependent. Do not claim that it guarantees a loss in every period.

## Data contract

- The canonical processed file is `data/processed/clean_returns.csv`.
- The date column is named `date`, formatted `YYYY-MM-DD`, sorted ascending, unique, and not stored as an unnamed CSV index.
- Preserve full precision in intermediate data. Round only presentation tables.
- Record source, retrieval time, adjustment treatment, common sample dates, row counts, and checksums in `data/metadata/`.
- Never commit credentials, API keys, cookies, or personal data.

## Engineering rules

- Use the settings in `config/project.yaml`; do not duplicate constants across modules.
- Use a local random-number generator seeded from configuration and pass it explicitly to simulations.
- Functions must document inputs, units, shapes, and outputs.
- Generated figures go to `outputs/figures/`; generated tables go to `outputs/tables/`.
- Add or update tests for financial logic, signs, data leakage, and reproducibility.
- Do not invent data, parameters, citations, or results. Mark incomplete work as TODO and fail clearly rather than silently generating placeholders.
- Do not directly push to `main`. Use a focused branch and pull request.

