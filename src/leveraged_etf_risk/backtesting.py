"""Chronological VaR backtesting interfaces."""


def run_backtest(*args, **kwargs):
    raise NotImplementedError("Backtesting must be implemented without look-ahead bias")

