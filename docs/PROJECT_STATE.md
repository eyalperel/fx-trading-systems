# Project State — fx-trading-systems

**As of:** 2026-11-06 (Phase 1 step 3 in progress: H1 SuperSmoother2Pole passed; harness decisions D1–D3 made)
**Replaces:** `FX_Roadmap_v2026.08.10.md` (v4.4), `Week14_Review_Plan.md`,
`Week5-14_Indicator_Plan.md`, all Week 14 handoffs, `ROADMAP_UPDATE_PROTOCOL.md`.
Those stay in git history as the record; this file is the current state.

Compiled from: project knowledge docs, the README, the Week 14 Session 1 handoffs
(parts 1–4), and summaries of 25 project chats (Nov 2025 – Sep 2026).
Items not re-verified against the repo this sitting are marked *(unverified)*.

---

## 1. What exists

### 1.1 Indicator library (Light-C, `indicators/ehlers/`)

~32 files. "Validated" was applied with different methods in different weeks, so
it does **not** mean the same thing across the library (Week 13/14 finding).

| Group | Indicators | Week 14 review status |
|---|---|---|
| Smoothers | SuperSmoother 2-pole | **Implementation verified by harness H1** (run 2 PASS, f59f6e4): Zorro computes the filter its `.c` coefficients define. **Source fidelity not yet checked**: the `.c` uses `sqrt(2)` and `PI`, Ehlers' code uses `1.414` and `3.14159`; per D1 (`docs/harness/HARNESS_DESIGN.md` §6) the fidelity check uses exact √2 and π |
| Smoothers | SuperSmoother 3-pole, UltimateSmootherE | **Reviewed** |
| Superseded | `UltimateSmoother_W5_Superseded.c` — does not implement its cited article | Reviewed, retired |
| High-pass family | HighPassFilter, RoofingFilter | **Reviewed** — code correct; tests cannot fail |
| High-pass family | Decycler | Not reviewed — may be identical to UltimateSmootherE |
| Baselines | MAMA, FAMA, FRAMA, Laguerre Filter, DSMA | Not reviewed; Week 9 (FRAMA/Laguerre/DSMA) not reproducible from repo |
| Oscillators | CyberCycle, Elegant Oscillator, Fisher, Inverse Fisher, COG, Reflex, MESA Stochastic, RSIH, Laguerre Osc, Laguerre RSI | Not reviewed |
| Zero-lag / noise | InstantTrendline, DominantCycle, Recursive Median, RMO, Alpha-Beta, Correlation Cycle | Not reviewed |
| Failed | ELI | Documented FAIL |
| Volatility | NATR, Ultimate Channel/Bands, VolatilityRegime | Not reviewed |

### 1.2 Previous slot decisions — made on indicator-level evidence only

No strategy has ever been backtested. These were chosen by lag, signal count and
correlation, not by trading results.

**Decision 2026-10-20: all slots unlocked.** These are starting candidates — the first
indicators through the new test harness — not settled answers.

| Slot | Strategy 1 | Strategy 2 | Basis |
|---|---|---|---|
| Baseline | FAMA | FRAMA | Crossover counts, 10y EUR/USD D1 |
| C1 | Fisher (10) | MESA Stochastic (20,48,10) | Indicator metrics |
| C2 | Reflex — flagged | Laguerre RSI — shortlisted | C-3b (backtest) never run |
| Stops / vol | Ultimate Channel, NATR | same | Week 13 |
| Exit | — | — | Never defined |

### 1.3 Infrastructure

- Repo: `eyalperel/fx-trading-systems` (public), local
  `C:/Users/eyalp/Documents/fx-trading-systems/`
- Zorro 3.11 (file version 3.1.1.2, (b) H1 session 2026-11-05), Git Bash, VS Code, Python/Jupyter (`python`, not `python3`)
- Data: EUR/USD D1, BTC/USD H4 (Zorro native); EUR/JPY D1, AUD/USD D1 (Darwinex MT4)
- `docs/ZORRO_LIGHTC_GOTCHAS.md` — platform reference, keep
- `analysis/null_tests/` — seeded surrogate harness (bootstrap, fGn, IAAFT, stoch-vol)
- Sources: 102 Ehlers TASC articles; *Cybernetic Analysis* (2004); 24 PDFs in project

### 1.4 Does not exist yet

- Any strategy backtest, NNFX template, or exit logic
- Walk-forward, Monte Carlo, or strategy-level surrogate test
- Swap / spread cost model
- Confirmation-set pass condition

---

## 2. Validation discipline — carried forward unchanged

1. **Dev / confirmation split.** Dev: EUR/USD D1, BTC/USD H4, EUR/JPY D1, AUD/USD D1.
   Confirmation: other majors and crosses, XAU, XAG, WTI (minors excluded). Selection
   on dev only; confirmation set untouched until a system is frozen.
2. **Pre-registration.** Criteria written and committed before the test runs.
   Amendments dated and appended, never in place.
3. **Count every variant tested** and report it with the result. *(new, Oct 2026)*
4. **A guard never seen to fire is not a guard.** Test with deliberately broken input.
5. **Test the measuring tool on a known answer first** (EMA lag = 1.50 bars).
6. **Same parameters across assets.** Per-asset retuning = overfitting.
7. **Judge an indicator by what it does**, not by what its article claims.
8. **Combinations decide.** Indicator metrics screen; backtests select (C-3b).
9. **Failures stay documented.**

---

## 3. Research results (bounded)

- **Cycle premise null test.** 64 tests, EUR/USD D1 + BTC/USD H4, one
  parameterisation, 10–48 bar band: no null rejected, min p = 0.070. Positive
  control: cycles >~4–5% of return variance would have been detected. Bounded
  result, not a general finding.
- **Slutsky–Yule.** ~20-bar zero-crossing period appears in EUR/USD, BTC and pure
  Brownian motion alike. A filter's output rhythm belongs to filter × input.
- **Volatility persists, direction doesn't.** H(returns) ≈ 0.50 on both assets;
  H(|returns|) = 0.658 (EUR/USD D1), 0.766 (BTC/USD H4).
- **Ehlers' 2015 "pink noise"** measurement is brown noise (f⁻²).

---

## 4. Known defects — open

| Ref | Defect | Impact |
|---|---|---|
| GAP-1.35 | `data/fx/` CSVs are pre-radians-fix output; one run diverges to NaN | Week 6 notebook figures describe a filter not in the library. Decycler and BTC files unchecked |
| GAP-1.33/34 | `Test_RoofingFilter.c` has no pass criterion; returns before filters run | Test cannot fail; transient in export rows 1–72. Likely pattern across all test scripts *(unverified)* |
| GAP-1.26 | HP seeding — first output starts far from steady state | Changes all downstream output when fixed |
| GAP-1.31 | `RoofingFilter.c` header cites wrong source | Comment-only |
| — | Week 9 validation not reproducible (no tracked file reads its CSVs) | FRAMA, Laguerre, DSMA status unsupported |
| — | `CyberCycle.c` statics may lack `cc_` prefix | Unconfirmed after four sittings |
| — | Decycler vs UltimateSmootherE — possibly the same filter | Unchecked |
| — | `SuperSmoother2Pole.c` "First bar" comments are misleading: `Init` is `is(INITRUN)`, not the first bar (b, `include/variables.h:182`; gotchas 9d.5) | Comment only; output unaffected (H1 run 2) |
| — | The `PI` macro is 3.14159 in Zorro 3.11 (b, `Include/trading.h:25`); used library-wide | Tiny: ~1e-6 bars of lag, ~1e-8 in filter output (gotchas 9d.2). **Decided 2026-11-06 (HARNESS_DESIGN D3): keep `PI`**; each spec records the gap in its tolerance floor |

**Inference:** given that every test script reviewed so far could not fail, the
practical status of the unreviewed library is "implemented, not verified". The
Phase 1 test harness should establish verification automatically rather than
continuing the manual review.

---

## 5. Carried forward from retired docs

Kept here because the source docs leave project knowledge (they remain in the repo).

**Known answers for the indicator harness** (computed from coefficients; matched by
simulation):

| Filter | Input | Expected | Source |
|---|---|---|---|
| SuperSmoother2Pole(20) | Flat line | Output = input (DC gain 1) | Session 2026-10-20 |
| SuperSmoother2Pole(20) | Unit sine, period 5 / 20 / 100 | Amplitude 0.0577 / 0.7042 / 0.9990 | Session 2026-10-20 |
| SuperSmoother2Pole(20) | Ramp | Lag 4.0387 bars | Session 2026-10-20 |
| RoofingFilter(48, 10) | Unit sine, period 20 / 2 | Gain 0.890038 / 0 | Week 14 Handoff 4 §8 |
| EMA (lag reference) | Ramp | Lag 1.50 bars | README, measuring-tool check |

**D-14.1 — test data design.** Correctness tests use synthetic inputs. Real-data
checks use three small committed EUR/USD D1 slices, each named by the event it
covers, never stitched together: a splice creates an artificial bend the filter
treats as signal.

**Strategy-level validation (from roadmap v4.4, Phase 2.5).**
- Walk-forward over a 3×3 grid of training/testing window lengths; stability across
  the grid is the signal, not any single window's result.
- Surrogate test on a strategy's Sharpe: run it on ~1,000 surrogate price series
  (`analysis/null_tests/`), locate the real Sharpe in that distribution, with a
  positive control (injected known edge) so a null result has a detection bound.
- Confirmation-set pass condition is written and committed before the first
  confirmation run.

**Recurring error to avoid: one number in place of a trade-off.** Seen 5+ times in
Week 14 (SNR, "more attenuation = better", mean absolute difference as lag, mid-band
attenuation as quality). Harness and backtest reports show the trade-off as a table,
not a single score.

**Debugging method (found GAP-1.35).** Predict a value from first principles, check
it against the actual file; on a miss, find which coefficient version reproduces the
file's first rows exactly.

---

## 6. Phase 0 — complete

- [x] Step 1: project instructions rewritten (two modes, validation gate)
- [x] Step 2: this document committed as `docs/PROJECT_STATE.md` (`e151871`)
- [x] Step 3: superseded docs removed from project knowledge (21 docs; all remain in
  the repo, verified 2026-10-20). Repo reorganisation deferred to the README rewrite.
- [x] Step 4: `docs/sources/NNFX_Sources.md` — VP rules + Stonehill tests from 143 videos
  (transcripts fetched by `tools/fetch_transcripts.sh`, kept outside the repo). Numbers are
  configurable defaults; risk 0.3%–2%; dead-market mode optional, off. Stonehill numeric
  results are on their blog — fetch only for shortlisted indicators.

## 7. Phase 1 — build pipeline (decided 2026-11-03)

**Platform decision:** free Zorro, **batch scripts, one click per batch**. Move to Zorro S
(€35/month, cancel anytime) only if clicking becomes the bottleneck.
- Reason: Zorro's command-line automation (`-run`, `-train`, `-h`, `-quiet`, `-a`, `-d`, `-i`)
  is **Zorro S only** (Zorro manual, "Automatization with the command line"). Free Zorro can
  only *select* a script from the command line; [Test] must be clicked.
- Workflow: Claude Code (VS Code extension) writes a batch script that loops internally over
  indicators / assets / parameter sets and writes all results to file → user clicks [Test]
  once → Claude Code reads results and writes the next batch.
- Considered and not chosen now: Python research platform with own backtest engine (free, fully
  automatic, but leaves Zorro's built-in WFO/MC/cost model). Revisit if Light-C keeps causing
  silent bugs.
- Roles: claude.ai project chat = planning, decisions, research, review.
  Claude Code in VS Code = building and testing.

**Phase 1 steps**
1. [x] Check Claude Code in VS Code works in the repo (`git status`). Done.
2. [x] Write `CLAUDE.md` (rules Claude Code reads: validation gate, gotchas, paths, batch
   workflow). Done, `176fe70`.
3. [ ] **In progress.** Indicator harness as a batch script: known-answer checks (flat line,
   waves, ramp — §5) for SuperSmoother first, then the rest of the library, PASS/FAIL to one
   results file. H1 SuperSmoother2Pole: **run 2 PASS** (28/28 checks, NC1 + NC2 fail as
   required, 6 variants; `analysis/harness/results/H1_SuperSmoother2Pole_20261105_run2.csv`,
   `f59f6e4`). **Run 1 FAIL** (7 input guards: harness input precision — float32 literals and
   the `PI` macro) is kept in the record
   (`H1_SuperSmoother2Pole_20261105.csv`, `fd40b37`). Criteria:
   `docs/preregistration/H1_SuperSmoother2Pole_Criteria.md` (+ Amendment 1). Findings:
   gotchas §9d. Reusable harness design: `docs/harness/HARNESS_DESIGN.md`; its open points
   **D1–D3 decided 2026-11-06** (§6 there): exact √2/π under a literal-constant rule;
   per-quantity tolerances inside a floor×10 / ceiling÷10 window; keep Zorro `PI`.
   Next: build reference model, generator and checker with self-tests (Claude Code), then the
   tool acceptance run (reproduce H1 on SS2, HARNESS_DESIGN §5).
4. Generic NNFX template with swappable slots and configurable defaults from `NNFX_Sources.md`.
5. Backtest engine checks on hand-calculated trades (stop, 1×ATR half exit, breakeven,
   trailing after 2×ATR) before any strategy result is trusted.

---

## Appendix — chat inventory (for archiving)

Done 2026-10-20. Chats are renamed rather than archived (claude.ai has no archive).
A `[ARCHIVED]` chat is history; where it conflicts with this document, this document wins.

| Prefix | Chats |
|---|---|
| `[REF]` | Ehlers price decomposition premise (null-test design); Claim Audit (CV and interview gaps) |
| `[ARCHIVED]` | Roadmap review; Unified FX/crypto roadmap; Integrating FX and crypto plans; Weeks 5, 6, 7 (MAMA), 8, 9, 10, 12, 13 (NATR/Channels/RSIH/Laguerre) |
| Deleted | Weeks 1, 2, 3-4, 4 Day 3-6, 7 part b, 13 Volatility & Bands; Cross-asset validation spec; rehaul_10_08_2026; Week 14 Session 1 parts 1–5 |
