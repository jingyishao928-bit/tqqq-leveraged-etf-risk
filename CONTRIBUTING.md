# Contributing

## Branch workflow

1. Pull the latest `main`.
2. Create a focused branch such as `feat/data-pipeline`, `feat/garch-model`, or `fix/var-sign`.
3. Change only the files needed for the task, but update shared interfaces when the pull request explains the impact.
4. Run `python -m unittest discover -s tests -v`.
5. Open a pull request and request at least one teammate review.

## Commit messages

Use short, factual messages, for example:

- `Add adjusted-price data validation`
- `Implement long and short VaR calculation`
- `Fix look-ahead error in rolling backtest`

## Pull request checklist

- [ ] Inputs and outputs follow the documented contract.
- [ ] Financial signs, units, horizons, and confidence levels are explicit.
- [ ] No credentials or personal information are included.
- [ ] Tests pass.
- [ ] Figures and tables can be regenerated from code.
- [ ] Empirical claims are supported by generated results and cited data.

