"""Risk measures using the project's positive-loss convention."""

from __future__ import annotations

from math import ceil, isfinite
from typing import Iterable


def _validated_losses(losses: Iterable[float]) -> list[float]:
    values = sorted(float(loss) for loss in losses)
    if not values or not all(isfinite(loss) for loss in values):
        raise ValueError("losses must be a nonempty collection of finite values")
    return values


def value_at_risk(losses: Iterable[float], confidence: float) -> float:
    """Return the nearest-rank empirical loss quantile."""
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must lie strictly between zero and one")
    values = _validated_losses(losses)
    index = max(0, ceil(confidence * len(values)) - 1)
    return values[index]


def expected_shortfall(losses: Iterable[float], confidence: float) -> float:
    """Return the mean loss at or beyond the empirical VaR threshold."""
    values = _validated_losses(losses)
    threshold = value_at_risk(values, confidence)
    tail = [loss for loss in values if loss >= threshold]
    return sum(tail) / len(tail)

