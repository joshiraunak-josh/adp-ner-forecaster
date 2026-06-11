# PROMPTS.md — AI session log

> An honest log of AI use on this project, per the assignment. **Primary tool:
> Claude (chat).** I used it heavily — it proposed the design and produced the
> first drafts of the code. My role was to supply the problem and requirements,
> review and question the approach, verify every output by running it, catch
> bugs, and decide what to accept, change, and reject. I've kept dead ends in,
> as requested.
>
> _Note to reviewer: this is a curated log of the substantive sessions, not a
> verbatim transcript. Lower-level mechanics (shell/Git troubleshooting) are
> omitted as noise; everything that shaped the submission is here._

---

## Session 1 — Claude (chat) — design, build, evaluation

**My prompt (substance):** Shared the assignment (track the ADP National
Employment Report, forecast the next print, CLI + README + PROMPTS) and asked for
help designing and building it end to end.

**Decisions, dead ends, and what I did with the output:**

- **Data source.** Claude flagged that scraping `adpemploymentreport.com` or
  parsing the press-release PDFs would be fragile — that approach was
  **rejected**. It found the series is mirrored on FRED (`ADPMNUSNERSA`) via a
  no-auth CSV endpoint. **Accepted** FRED as the source; I agree it's the robust,
  citable choice.

- **Dead end / correction — level vs. change.** Open question whether the FRED
  series was the headline *change* or the *level*. Rather than assume, Claude
  pulled the actual observations and confirmed it's a **level** in persons, then
  differenced it and checked against published prints (May 2026 = 132,624 −
  132,502 = +122K; Dec 2025 = +37K). **Accepted** first-difference of the level as
  the target; the verification against real prints is why I trust it.

- **Models + evaluation.** AI proposed simple baselines (naive, moving averages,
  seasonal-naive, exponential smoothing) behind one interface, scored by
  walk-forward one-step-ahead backtesting (MAE / RMSE / MASE / directional).
  **Used as-is** — fit my "simple models, serious evaluation" intent.

- **Surprising result — investigated, didn't hide.** The backtest showed **naive
  beats every other model** (all MASE ≥ 1). Instead of tuning until something
  "won," I dug into why: the 2020 COVID shock dominates the error (std dev ≈ 727K
  in 2020 vs ≈ 113K recently). Re-ran on the post-COVID window — gap narrows to
  ~2%, naive still wins. **Decision:** keep naive as default, surface a smoothed
  alternative, and write the honest finding into the README rather than a
  flattering one.

- **Bug caught by tests.** Running the suite surfaced an off-by-one in my own
  seasonal-naive **test assertion** (the model was correct, the test was wrong).
  **Edited** the test after confirming the expected value.

- **Edited for accuracy.** The CLI's "smoothed alternative" line first said the
  models were "statistically tied"; I **changed** it to "within ~2% in the recent
  regime," which is what the numbers actually support.

- **Stdlib-only + offline-first.** Claude proposed no external dependencies (no
  pandas/numpy) for instant clone-and-run, plus a committed data snapshot so it
  works offline. **Accepted** and documented as tradeoffs in the README.

- **AI in the runtime — deliberately none.** Considered an LLM-based forecaster;
  **rejected** it — it wouldn't beat naive on this near-random series and adds
  cost/opacity. The AI-forward part is how I *built* the tool, not a model bolted
  into the runtime.

**Net:** Claude proposed the design and generated the first draft of every file.
I supplied the problem and requirements, reviewed and questioned the approach,
made the final accept/reject decisions, verified all output by running the full
test suite and CLI, caught and fixed the bugs above, and pushed for the honest
backtest finding to go in the README rather than a flattering one. The
architecture choices below (FRED, difference-the-level, evaluation-over-model-flash,
stdlib) were Claude's proposals that I evaluated and accepted because I agree with
the reasoning and can defend it.

---

## Session 2 — Claude (chat) — review & robustness pass

**My prompt (substance):** Asked for a review of the code, tests, and README
before submitting, and help making the run instructions reviewer-proof.

**What I did with the output:**

- **README run instructions.** Made the commands `python3` with a note for
  Windows (`python`) and "run from the project root," after I hit a `python` vs
  `python3` mismatch running a fresh clone myself.

- **Block-paste fix.** Found that pasting the whole command block (with inline
  `# comments`) into zsh failed — zsh passed the comments as arguments. **Edited**
  the README to move descriptions into a list above a comment-free command block,
  so it runs cleanly whether pasted as a block or line by line. Added explicit
  clone-and-run steps at the top.

- **Test-coverage review.** Confirmed the tests cover the correctness-critical
  paths (change derivation verified against published prints; backtest proven
  look-ahead-free; model math + edge cases). Consciously left CLI glue and the
  live FRED fetch untested given the time-box — noted as a deliberate scope call.

- **Repo hygiene.** Added a `.gitignore` and removed committed `__pycache__`
  build artifacts so the repo is clean.

---

## Other tools

_(None besides Claude. If you used ChatGPT / Cursor / Copilot / Claude Code at any
point, add a session here with the prompts and what you did with the output.)_
