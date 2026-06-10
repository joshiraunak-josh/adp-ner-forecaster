"""Walk-forward evaluation -- the heart of the project.

How we measure accuracy (and why):

- **Walk-forward, one-step-ahead.** For each month t in the test window, the
  model sees ONLY data up to t-1, predicts month t, and we score against the
  actual. This mimics real use (you never get to peek at the future) and avoids
  the look-ahead bias a single train/test split would hide.

- **Metrics:**
  - MAE / RMSE in thousands of jobs -- interpretable ("off by ~35k on average").
  - MASE: MAE divided by the naive model's MAE. <1 means the model genuinely
    beats the naive baseline; >=1 means it doesn't earn its complexity. This is
    the number that actually decides which model to ship.
  - Directional accuracy: did we predict the right sign (job gain vs loss)?
    Secondary, because most months are gains, so the bar is easy -- reported
    for honesty, not as the selection criterion.

The selection rule is explicit: pick the model with the lowest MAE, and only
prefer a more complex model over naive if its MASE is meaningfully < 1.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Sequence


@dataclass
class Result:
    model: str
    mae: float
    rmse: float
    mase: float
    directional_acc: float
    n: int
    preds: List[float]
    actuals: List[float]


def walk_forward(changes: Sequence[float], model, min_train: int = 24):
    """Return (preds, actuals) for one-step-ahead forecasts over the test window."""
    preds, actuals = [], []
    for t in range(min_train, len(changes)):
        history = changes[:t]
        preds.append(model.predict(history))
        actuals.append(changes[t])
    return preds, actuals


def _mae(preds, actuals):
    return sum(abs(p - a) for p, a in zip(preds, actuals)) / len(preds)


def evaluate(changes: Sequence[float], models: list, min_train: int = 24) -> List[Result]:
    """Backtest every model on the same window; MASE is scaled to naive_last."""
    # Establish the naive benchmark MAE first so MASE is comparable across models.
    from .models import NaiveLast
    naive_preds, naive_actuals = walk_forward(changes, NaiveLast(), min_train)
    naive_mae = _mae(naive_preds, naive_actuals)

    results: List[Result] = []
    for model in models:
        preds, actuals = walk_forward(changes, model, min_train)
        n = len(preds)
        mae = _mae(preds, actuals)
        rmse = math.sqrt(sum((p - a) ** 2 for p, a in zip(preds, actuals)) / n)
        directional = sum(1 for p, a in zip(preds, actuals)
                          if (p >= 0) == (a >= 0)) / n
        results.append(Result(
            model=model.name, mae=mae, rmse=rmse,
            mase=mae / naive_mae if naive_mae else float("nan"),
            directional_acc=directional, n=n, preds=preds, actuals=actuals,
        ))
    results.sort(key=lambda r: r.mae)
    return results


def best_model(changes: Sequence[float], models: list, min_train: int = 24):
    """The selection rule, in code: lowest MAE wins."""
    return evaluate(changes, models, min_train)[0]
