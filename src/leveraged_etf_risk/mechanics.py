"""Return transformations and daily-reset wealth mechanics."""

from __future__ import annotations

from math import exp, isfinite
from typing import Iterable


def log_to_simple_return(log_return: float) -> float:
    """Convert one log return to a simple return."""
    if not isfinite(log_return):
        raise ValueError("log_return must be finite")
    return exp(log_return) - 1.0


def leveraged_simple_return(
    underlying_simple_return: float,
    beta: float,
    daily_fee: float = 0.0,
    daily_financing: float = 0.0,
) -> float:
    """Map an underlying simple return to an idealized daily ETF return.

    Fees and financing are decimal daily return deductions. The function does
    not silently cap the return; the wealth function applies a nonnegative NAV
    floor when required.
    """
    values = (underlying_simple_return, beta, daily_fee, daily_financing)
    if not all(isfinite(value) for value in values):
        raise ValueError("all return inputs must be finite")
    return beta * underlying_simple_return - daily_fee - daily_financing


def compound_wealth(
    returns: Iterable[float],
    initial_wealth: float = 1.0,
    nav_floor: float = 0.0,
) -> float:
    """Compound simple returns while enforcing a nonnegative NAV floor."""
    if initial_wealth < nav_floor or nav_floor < 0:
        raise ValueError("wealth and NAV floor must be nonnegative")
    wealth = float(initial_wealth)
    for simple_return in returns:
        if not isfinite(simple_return):
            raise ValueError("returns must be finite")
        wealth = max(nav_floor, wealth * (1.0 + simple_return))
        if wealth == nav_floor:
            break
    return wealth


def long_loss_from_terminal_wealth(terminal_wealth: float) -> float:
    """Loss on a unit-notional long position; positive values are losses."""
    return 1.0 - terminal_wealth


def short_loss_from_terminal_wealth(terminal_wealth: float) -> float:
    """Loss on a unit-notional short position; losses are unbounded above."""
    return terminal_wealth - 1.0

