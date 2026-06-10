# PROMPTS.md — AI session log

> This is my working log of AI use on this project, per the assignment.
> **Primary tool: Claude (chat).** The session below is the real one that built
> this project; I verified every piece by running it locally. I'm keeping this
> log honest, including dead ends and things I rejected — and I'll append any
> further sessions (Cursor/ChatGPT/Claude Code) as I touch the code.
>
> _Rounak: before submitting — confirm this matches your memory, paste any
> verbatim prompts you want at higher fidelity, and add any sessions not below.
> Keep it truthful; they explicitly asked for the unsanitized log._

---

## Session 1 — Claude (chat) — design, build, evaluation

**My prompt (substance):** Shared the full take-home assignment (track the ADP
National Employment Report, forecast the next print, CLI, README + PROMPTS) and
asked for help solving it end to end.

**What we did and what I did with the output:**

1. **Data source decision.** Asked Claude where the ADP numbers could be pulled
   programmatically. First instinct floated was scraping `adpemploymentreport.com`
   or parsing press-release PDFs — **rejected** as fragile. Claude searched and
   found the series is mirrored on FRED (`ADPMNUSNERSA`) with a no-auth CSV
   endpoint. **Used:** FRED as the ingestion source. (Verified the series exists
   and is current to May 2026.)

2. **Dead end / correction — level vs. change.** Open question: is the FRED
   series the headline *change* or the *level*? Rather than assume, fetched the
   actual FRED observations and confirmed it's a **level** in persons
   (Feb 2026 = 132,333,000…). Differenced it and matched the published headline
   prints (May = +122K, Dec = +37K). **Used:** first-difference of the level as
   the modeling target. This caught a wrong assumption before it cost me.

3. **Model + evaluation design.** Claude proposed simple baselines (naive, moving
   averages, seasonal-naive, exponential smoothing) behind one interface, scored
   by walk-forward one-step-ahead backtesting (MAE/RMSE/MASE/directional).
   **Used as-is** — it fit the "simple components, serious evaluation" framing I
   wanted, and matches that this series is near-random.

4. **Bug caught by tests #1.** First fingerprint-style number handling — actually
   in the earlier practice project — and here a **seasonal-naive test assertion
   was wrong** (expected the value 12 months back off by one). Running the suite
   surfaced it; corrected the test after confirming the model was right.

5. **Surprising backtest result — investigated, didn't hide.** The full-sample
   backtest showed **naive beats every other model** (all MASE ≥ 1). Instead of
   tuning until something "won," dug into why: the 2020 COVID shock dominates the
   error (std dev ≈ 727K in 2020 vs ≈ 113K recently). Re-ran on the post-COVID
   window — gap narrows to ~2% but naive still wins. **Used:** kept naive as the
   default and wrote the honest finding into the README, surfacing a smoothed
   alternative for users who want a less reactive number.

6. **Stdlib-only decision.** Chose no external dependencies (no pandas/numpy) so
   the project clones and runs instantly; documented where I'd reach for
   pandas/statsmodels at scale. **Used.**

7. **Generated code** for `data.py`, `models.py`, `backtest.py`, `explain.py`,
   `cli.py`, and tests. **Edited / verified:** ran the full test suite (10 tests)
   and all CLI commands against the real data; fixed the test bug above; tightened
   the "smoothed alternative" wording in the CLI when it overstated how close the
   models were ("statistically tied" → accurate "within ~2% in the recent regime").

**Net:** Claude did the heavy lifting on scaffolding and the first draft of every
file; my contribution was the design calls (FRED, difference-the-level,
evaluation-over-model-flash, stdlib), verifying every output by running it,
catching/fixing the bugs, and insisting the honest backtest story go in the README
rather than a flattering one.

---

## Session 2 — <tool> — <date>   _(add as needed)_

**Prompt(s):**

**What I did with the output (used as-is / edited / rejected and why):**
