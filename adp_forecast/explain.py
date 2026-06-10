"""Turn a forecast into a plain-English explanation -- the 'understand why'
requirement. Interpretability matters more than cleverness here: a user should
see exactly what drove the number."""
from __future__ import annotations

import statistics
from typing import List, Sequence

from .backtest import Result


def explain_forecast(model_name: str, prediction: float, changes: Sequence[float],
                     backtest: Result) -> str:
    recent = changes[-6:]
    recent_str = ", ".join(f"{x:+.0f}k" for x in recent)
    vol = statistics.pstdev(changes[-24:]) if len(changes) >= 2 else 0.0
    last = changes[-1]

    lines = []
    lines.append(f"Prediction for next print: {prediction:+.0f}k private-sector jobs.")
    lines.append("")
    lines.append(f"Model: {model_name} (selected by walk-forward backtest).")
    lines.append(f"  Why this model: lowest out-of-sample MAE ({backtest.mae:.1f}k) "
                 f"over {backtest.n} months; MASE {backtest.mase:.2f} vs the naive "
                 f"baseline ({'beats' if backtest.mase < 1 else 'does not beat'} naive).")
    lines.append("")
    lines.append("What drove the number:")
    lines.append(f"  Last 6 monthly changes: {recent_str}")
    lines.append(f"  Most recent print: {last:+.0f}k")
    lines.append(f"  Recent volatility (24-mo std dev): {vol:.0f}k")
    lines.append("")
    lines.append("Caveat: the ADP series is volatile with little month-to-month")
    lines.append("autocorrelation, so a typical error of tens of thousands is")
    lines.append("expected. The forecast is a smoothed central estimate, not a")
    lines.append("precise call -- see the backtest for honest error bounds.")
    return "\n".join(lines)
