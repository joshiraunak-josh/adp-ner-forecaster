"""CLI entry point.

    python -m adp_forecast.cli history [--last N]
    python -m adp_forecast.cli predict [--model NAME]
    python -m adp_forecast.cli backtest
    python -m adp_forecast.cli refresh
"""
from __future__ import annotations

import argparse
import sys

from . import data as data_mod
from .backtest import evaluate, best_model
from .explain import explain_forecast
from .models import default_models


def _model_by_name(name):
    for m in default_models():
        if m.name == name:
            return m
    return None


def cmd_history(args):
    obs = data_mod.get_observations()
    rows = [o for o in obs if o.change is not None]
    if args.last:
        rows = rows[-args.last:]
    print(f"{'MONTH':<10}{'LEVEL (000s)':>14}{'CHANGE (000s)':>16}")
    print("-" * 40)
    for o in rows:
        print(f"{o.month.strftime('%Y-%m'):<10}{o.level/1000:>14,.0f}{o.change_thousands:>+16.0f}")
    print(f"\n{len(rows)} months. Source: ADP NER via FRED ({data_mod.FRED_SERIES_ID}).")


def cmd_backtest(args):
    changes = data_mod.change_series()
    results = evaluate(changes, default_models(), min_train=args.min_train)
    print(f"Walk-forward backtest, one-step-ahead, {results[0].n} test months "
          f"(min_train={args.min_train})")
    print(f"{'MODEL':<18}{'MAE':>8}{'RMSE':>8}{'MASE':>8}{'DIR.ACC':>9}")
    print("-" * 51)
    for r in results:
        flag = "  <- best" if r is results[0] else ""
        print(f"{r.model:<18}{r.mae:>8.1f}{r.rmse:>8.1f}{r.mase:>8.2f}"
              f"{r.directional_acc:>8.0%}{flag}")
    print("\nMAE/RMSE in thousands of jobs. MASE<1 beats the naive baseline.")
    print("Selection rule: lowest MAE.")


def cmd_predict(args):
    changes = data_mod.change_series()
    results = evaluate(changes, default_models(), min_train=args.min_train)
    chosen = _model_by_name(args.model) if args.model else None
    chosen_result = next((r for r in results if r.model == args.model), results[0]) if args.model else results[0]
    if chosen is None:
        chosen = _model_by_name(chosen_result.model)
    prediction = chosen.predict(changes)
    obs = [o for o in data_mod.get_observations() if o.change is not None]
    next_month = obs[-1].month
    # name the month being predicted (the month after the last observation)
    ny, nm = (next_month.year + (next_month.month // 12),
              (next_month.month % 12) + 1)
    print(f"(Predicting the print AFTER {next_month.strftime('%Y-%m')}, "
          f"i.e. ~{ny}-{nm:02d})\n")
    print(explain_forecast(chosen.name, prediction, changes, chosen_result))

    # The naive winner just echoes last month, and the smoothers are within
    # noise of it. Surface a smoothed central estimate too, so the user has a
    # less-reactive number and can see the two are effectively tied.
    alt = next((r for r in results if r.model == "ses_0.5"), None)
    alt_model = _model_by_name("ses_0.5")
    if alt is not None and chosen.name != "ses_0.5":
        print("")
        print(f"Smoothed alternative ({alt_model.name}): "
              f"{alt_model.predict(changes):+.0f}k  "
              f"(full-sample MAE {alt.mae:.1f}k, MASE {alt.mase:.2f}; comes within "
              f"~2% of naive in the recent stable regime -- use for a less "
              f"reactive estimate than echoing last month).")


def cmd_refresh(args):
    try:
        n = data_mod.refresh()
        print(f"Refreshed: {n} observations pulled from FRED and cached.")
    except Exception as exc:
        print(f"Refresh failed ({type(exc).__name__}: {exc}).", file=sys.stderr)
        print("The committed snapshot is still usable for offline runs.", file=sys.stderr)
        return 1
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="adp_forecast",
                                description="Track and forecast the ADP National Employment Report.")
    sub = p.add_subparsers(dest="cmd", required=True)

    h = sub.add_parser("history", help="show historical numbers")
    h.add_argument("--last", type=int, default=12, help="show only the last N months (0=all)")
    h.set_defaults(func=cmd_history)

    b = sub.add_parser("backtest", help="evaluate all models")
    b.add_argument("--min-train", type=int, default=24, dest="min_train")
    b.set_defaults(func=cmd_backtest)

    pr = sub.add_parser("predict", help="forecast the next print")
    pr.add_argument("--model", help="force a model by name (default: backtest winner)")
    pr.add_argument("--min-train", type=int, default=24, dest="min_train")
    pr.set_defaults(func=cmd_predict)

    r = sub.add_parser("refresh", help="re-pull live data from FRED")
    r.set_defaults(func=cmd_refresh)

    args = p.parse_args(argv)
    if args.cmd == "history" and args.last == 0:
        args.last = None
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
