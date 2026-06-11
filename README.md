# ADP National Employment Report — Tracker & Forecaster

A small command-line tool that tracks the monthly [ADP National Employment
Report](https://adpemploymentreport.com/) (the private-sector jobs number) and
forecasts the next print, with a transparent explanation of *why*.

## Quickstart

**Requires Python 3.10+.** Use `python3` on macOS/Linux; on Windows use `python`.
Run all commands from the project root (the folder that contains `adp_forecast/`).
No dependencies and no API key — it runs offline against a committed data snapshot.

The commands:
- `history --last 12` — recent historical prints
- `predict` — next-month forecast with reasoning
- `backtest` — how every model scores
- `refresh` — re-pull live data from FRED
- `unittest discover -s tests` — run the tests (offline)

```bash
python3 -m adp_forecast.cli history --last 12
python3 -m adp_forecast.cli predict
python3 -m adp_forecast.cli backtest
python3 -m adp_forecast.cli refresh
python3 -m unittest discover -s tests
```

---

## What it does

- **`history`** — the historical series: monthly private-employment level and the
  month-over-month change (the headline number).
- **`predict`** — a one-step-ahead forecast for the next print, the model used, and
  a plain-English explanation of what drove it.
- **`backtest`** — walk-forward evaluation of every model so the forecast choice is
  evidence-based, not asserted.

## Approach & key tradeoffs

**Data source — FRED, not scraping ADP.** The official ADP series is mirrored by the
St. Louis Fed as `ADPMNUSNERSA`, available from FRED's no-auth CSV endpoint. Pulling
from there is dramatically more robust than scraping `adpemploymentreport.com` or
parsing press-release PDFs, and it's properly citable. ADP remains the source of
truth; FRED is the clean transport. *Tradeoff:* a small dependency on FRED mirroring
the series promptly (it does, within the release day).

**Target = first difference of the level.** FRED carries the *level* of total private
employment (persons); the headline number everyone quotes ("+122K in May") is the
month-over-month change, so the tool differences the level. Verified against ADP press
releases (May 2026 = 132,624 − 132,502 = +122K; Dec 2025 = +37K).

**Offline-first.** A committed snapshot (`data/adp_ner_level.csv`, 2010–2026) means
`clone and run` needs no network. `refresh` re-pulls the live series and overwrites it.

**Standard library only.** ~195 monthly points doesn't justify pandas/numpy/statsmodels;
stdlib keeps the project instantly runnable with zero install friction. *Tradeoff:* at
larger scale or with richer models I'd reach for pandas + statsmodels/`sktime`.

**Simple models, serious evaluation.** The models (naive, moving averages,
seasonal-naive, exponential smoothing) are deliberately simple and share one interface.
The rigor is in the evaluation, not model flash — which matches the nature of the
series (see below).

## How I evaluated forecast accuracy — and the results

**Method: walk-forward, one-step-ahead.** For each month *t* in the test window the
model sees only data up to *t−1*, predicts *t*, and is scored against the actual. This
mirrors real use and is free of look-ahead bias (there's a test that asserts exactly
this). Metrics: **MAE** and **RMSE** (thousands of jobs), **MASE** (MAE ÷ naive's MAE;
<1 means it beats the naive baseline), and **directional accuracy** (right sign).
**Selection rule: lowest MAE.**

**Headline result (full sample, 2010–2026, 172 test months):**

| Model | MAE (k) | RMSE (k) | MASE | Dir. acc |
|---|---|---|---|---|
| **naive_last** | **84.3** | 161.0 | **1.00** | 93% |
| ses_0.5 | 102.3 | 199.5 | 1.21 | 90% |
| ses_0.3 | 114.4 | 225.6 | 1.36 | 90% |
| moving_avg_3 | 117.0 | 228.2 | 1.39 | 90% |
| moving_avg_6 | 129.9 | 269.1 | 1.54 | 88% |
| historical_mean | 144.2 | 301.0 | 1.71 | 88% |
| moving_avg_12 | 146.1 | 281.4 | 1.73 | 88% |
| seasonal_naive | 208.7 | 411.7 | 2.47 | 83% |

*(Numbers are from the committed snapshot; run `refresh` then `backtest` to regenerate
against the latest data.)*

**What this means (the honest read):**

- **Naive wins; nothing beats it.** Every MASE ≥ 1. This series has little
  month-to-month autocorrelation — close to a random walk — so the last print is the
  best cheap predictor of the next. ADP itself describes the series as volatile.
- **It's regime-dependent.** The full-sample numbers are inflated by the 2020 COVID
  shock (2020 monthly std dev ≈ 727k vs ≈ 113k for the last 36 months), which no
  moving average can smooth. Re-running on the post-COVID window narrows the gap a lot:
  in the last ~48 months naive MAE ≈ 47.8k and `ses_0.5` ≈ 48.7k — within ~2%, still
  not beating naive.
- **Directional accuracy is not skill.** 83–93% looks impressive but mostly reflects
  that most months are job gains. Reported for honesty, not used for selection.

**Decision:** ship `naive_last` as the default (it wins on MAE), but `predict` also
surfaces a smoothed `ses_0.5` estimate as a less-reactive central number, since the two
are close in the current regime. The defensible takeaway is that **for this series,
honest evaluation argues against over-modeling** — and the tool says so out loud rather
than dressing up a model that doesn't earn its complexity.

**A known limitation I want to be explicit about: data vintage.** FRED's series is the
*revised* one. The January benchmark revision rewrites history (e.g., Jan 2026 first
printed at +22K, now shows +11K). A strictly honest backtest would use point-in-time
(ALFRED vintage) data so the model never "sees" later revisions. The current backtest
slightly flatters all models by using revised data. See next steps.

## What I'd build next (another week)

1. **Point-in-time backtesting via ALFRED vintages** to remove the revision look-ahead
   above — the single biggest correctness improvement.
2. **Exogenous signals**, evaluated honestly: BLS JOLTS, jobless claims, prior-month
   BLS NFP — to test whether anything actually lowers MASE below 1.
3. **Prediction intervals**, not just point forecasts (empirical from backtest errors),
   since the honest story is about uncertainty.
4. **Forecast the sub-series** (industry / establishment-size cuts FRED also carries)
   and reconcile, which may beat forecasting the aggregate directly.
5. Confidence-aware model selection that adapts to the current volatility regime.

## Layout

```
adp_forecast/
  data.py       # FRED ingestion + local cache; level -> monthly change
  models.py     # forecasters behind one interface
  backtest.py   # walk-forward evaluation + metrics
  explain.py    # the human-readable "why"
  cli.py        # history / predict / backtest / refresh
data/adp_ner_level.csv   # committed FRED snapshot (2010-2026)
tests/test_adp_forecast.py
PROMPTS.md
```

## Data attribution

ADP National Employment Report, produced by ADP Research in collaboration with the
Stanford Digital Economy Lab. Series retrieved from FRED: Automatic Data Processing,
Inc., *Total Nonfarm Private Payroll Employment* [ADPMNUSNERSA], Federal Reserve Bank of
St. Louis, https://fred.stlouisfed.org/series/ADPMNUSNERSA.
