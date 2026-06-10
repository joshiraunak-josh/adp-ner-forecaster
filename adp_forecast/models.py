"""Forecasting models for the monthly change series.

All models implement the same tiny interface (`Forecaster`): given the history
of monthly changes (in thousands), return a one-step-ahead point forecast. They
are stateless -- the pipeline re-feeds history each step -- which makes
walk-forward backtesting trivial and keeps every model independently testable.

The philosophy here is deliberate: this is a noisy, near-random series (ADP
itself calls it volatile, and it has little month-to-month autocorrelation). The
honest engineering move is to start from strong, dumb baselines and only adopt
something more complex if backtesting shows it actually beats them. So the
"models" are intentionally simple; the rigor lives in evaluation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass
class NaiveLast:
    """Forecast = last observed change. The canonical baseline for a random
    walk; the one everything else must beat to justify its existence."""
    name: str = "naive_last"

    def predict(self, changes: Sequence[float]) -> float:
        return changes[-1]


@dataclass
class MovingAverage:
    """Mean of the last k changes. Smooths the noise; k is the bias/variance
    knob. For a mean-reverting noisy series this is often very hard to beat."""
    k: int = 3

    @property
    def name(self) -> str:
        return f"moving_avg_{self.k}"

    def predict(self, changes: Sequence[float]) -> float:
        window = changes[-self.k:] if len(changes) >= self.k else changes
        return sum(window) / len(window)


@dataclass
class SeasonalNaive:
    """Forecast = the change 12 months ago. The data is already seasonally
    adjusted, so we *expect* this to be weak -- included precisely to show
    that, and to confirm SA removed the obvious seasonality."""
    name: str = "seasonal_naive"

    def predict(self, changes: Sequence[float]) -> float:
        return changes[-12] if len(changes) >= 12 else changes[-1]


@dataclass
class HistoricalMean:
    """Forecast = mean of all history. A long-run anchor; loses recent signal."""
    name: str = "historical_mean"

    def predict(self, changes: Sequence[float]) -> float:
        return sum(changes) / len(changes)


@dataclass
class SimpleExpSmoothing:
    """Exponentially weighted recent changes. alpha=1 -> naive; alpha->0 ->
    historical mean. A principled middle ground between the two baselines."""
    alpha: float = 0.3

    @property
    def name(self) -> str:
        return f"ses_{self.alpha}"

    def predict(self, changes: Sequence[float]) -> float:
        s = changes[0]
        for x in changes[1:]:
            s = self.alpha * x + (1 - self.alpha) * s
        return s


def default_models() -> list:
    """The roster we benchmark against each other."""
    return [
        NaiveLast(),
        MovingAverage(3),
        MovingAverage(6),
        MovingAverage(12),
        SeasonalNaive(),
        HistoricalMean(),
        SimpleExpSmoothing(0.3),
        SimpleExpSmoothing(0.5),
    ]
