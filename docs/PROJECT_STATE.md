# Project State — fx-trading-systems

**As of:** 2026-11-19 (Phase 1 step 3 in progress: SS2, SS3, HighPassFilter, RoofingFilter, UltimateSmootherE, Reflex and MESAStochastic verified; oscillator harness family (D6) built; next: decision pending)
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
| Smoothers | SuperSmoother 2-pole | **Implementation verified** (H1 run 2 PASS, f59f6e4) **and source fidelity verified** (SS2F run 1 PASS, 763601e, 2026-11-12): Zorro output matches Ehlers' TASC V.42:04 formula (√2 and π exact per D1) within gain 5.7e-7 / lag 5.4e-6 bars, which is the Zorro `PI` gap (D3); tolerances 3e-5 / 1e-3; 4 negative controls detected; 8 variants. Not tested: start-up seeding (article: output = Price for the first 3 bars; excluded by warmup) |
| Smoothers | SuperSmoother 3-pole | **Corrected and verified 2026-11-16.** The previous file was a hybrid matching neither cited source (real pole a1 instead of a1², 2-pole input average); it had been listed as "Validated". Kept as `SuperSmoother3Pole_Hybrid_Superseded.c`. Corrected to *Cybernetic Analysis* (2004) Fig. 13.11 with √3 (D1 Amendment 1: the printed 1.738 is a typo, the book's Table 13.4 uses 1.732). SS3F run 1 PASS (`09c05ad`): 28/28, 6 controls detected, IMP replay ≤ 3.4e-14, Zorro vs book = `PI` gap (gain 9.0e-7, lag 7.7e-6); 10 variants. Passband overshoot to gain 1.0046 (P = 10) |
| Smoothers | UltimateSmootherE | **Corrected and verified 2026-11-18.** Source: Ehlers, "The Ultimate Smoother", TASC V.42:04 (2024): US = input − HP, with the V.42:04 $HighPass (a third HP, not HP-A of `HighPassFilter.c`). Two deviations corrected (`ad8eae5`): D-1 folded literal `1.414 * PI` (gotchas 9d.8) → `us_k*PI`, `us_k = sqrt(2.0)` (D1 rule 1); D-2 global `Bar < 4` (comment said 4 bars; source seeds 3) → per-instance counter `us_n` = EasyLanguage CurrentBar (gotchas 9d.9). Spec `USE_ArticleFidelity.toml` (`ca4454b` + Amendments 1–2). **Run 1 PASS** (`41c8d76`): 64/64 (flat, 5 gains, alt gain, 5 phases, ramp lag, 3 start-ups) × P = 10/14/20/30; 6 controls (incl. NCS = 4-bar seed, detected by start-up only, 834×; NCX = x − HP-A); IMP ≤ 8.0e-15; Zorro vs article = `PI` gap (gain 6.5e-7, phase 7.6e-7 rad). (b) DC gain 1, Nyquist gain 0, ramp lag 0; but passband gain up to ~1.27 (T ≈ 1.3P) and phase at T = P ≈ −0.62 rad: the article's "zero lag" holds at DC only |
| Superseded | `UltimateSmoother_W5_Superseded.c` — does not implement its cited article | Reviewed, retired |
| High-pass family | HighPassFilter | **Corrected and verified 2026-11-17.** Source: HP-A, TASC V.32:1 (2014), same lines in V.33:09 / V.36:03 (Ehlers published three different HPs; HARNESS_DESIGN D4 note). Two deviations corrected (`d22ef57`): `0.707` → √2/2 (D1 rule 1) and price-level seed → zero seed (GAP-1.26). Spec `HP_ArticleFidelity.toml` (`2069d86` + Amendments 1–2). **Run 1 FAIL** (`a361e4b`, one control-model row: Zorro literal fold, gotchas 9d.8) → **run 2 PASS** (`512781c`): 56/56 (flat, gain, **phase**, ramp residual, start-up), 8 controls, IMP ≤ 6.7e-15 on the real variants; Zorro vs article = `PI` gap (gain 4.0e-7, phase 8.1e-7 rad). Leads price: 1.81 bars at T = 20, P = 48 (INFO) |
| High-pass family | RoofingFilter | **Verified 2026-11-17.** Source: TASC V.32:1 Roofing sidebar (HP-A(48) → SuperSmoother(10) on `(HP + HP[1])/2`, both histories start at 0). Code already matched; header corrected (GAP-1.31) and locals prefixed (`b249142`). Spec `RFF_ArticleFidelity.toml` (`b6b5c5d` + Amendments 1–2). **Run 1 PASS** (`d1395d3`): 64/64 (flat, 5 gains, Nyquist gain via a new alternating input, 5 phases, ramp residual, 3 start-ups) × (48,10), (30,10), (125,10), (48,20); 7 controls; IMP ≤ 3.5e-12; Zorro vs article = `PI` gap (gain 5.6e-7, phase 1.6e-6 rad). Start-up equals the source's zero start (HP's first output is 0). Gain at T = 20: 0.8900165 (§5 corrected) |
| High-pass family | Decycler | Not reviewed. (c) Probably not the same filter as UltimateSmootherE: same construction (price − HP) but the *Decyclers* article (V.33:09) uses HP-A, while UltimateSmootherE uses the V.42:04 HP; unchecked until Decycler.c is read |
| Baselines | MAMA, FAMA, FRAMA, Laguerre Filter, DSMA | Not reviewed; Week 9 (FRAMA/Laguerre/DSMA) not reproducible from repo |
| Oscillators | Reflex | **Corrected and verified 2026-11-18.** Source: Ehlers, "Reflex: A New Zero-Lag Indicator", TASC V.38:02 (2020). Review `docs/harness/REFLEX_SOURCE_REVIEW.md` (`05be788`): R-1 file-static MS shared by every call (silent wrong output with two instances or an asset loop) → per-instance series; R-2 int `Length/2` → real `.5*Length`, SuperSmoother computed in-file; R-3 float32 weights → built from integers; R-4 start-up undefined in the source (INFO); R-5 header. New `ReflexCore(Price, Length, &sum, &ms)` exports the linear stage; `Reflex()` wrapper unchanged for callers (`5840f20`). Old file kept as `Reflex_Superseded.c` (control NCS/NCT). Spec `RFX_ArticleFidelity.toml` (`960ae09` + Amendment 1). **Run 1 PASS** (`ad487b7`): 84/84 (Sum: flat, 5 gains, alt gain, 5 phases, ramp residual; Reflex: 5 trace, bound, 2 invariance) × L = 14/20/21/30; 8 controls (incl. the real superseded file, 76 FAIL rows); IMP ≤ 2.8e-12; Zorro vs article = `PI` gap (trace 1.57e-6). Read twice, agreed on every row. (b) **Not zero-lag at its own design period:** Sum has phase 0 at T = L but the SuperSmoother(L/2) adds −0.62 rad (≈ 2 bars at L = 20). (b) On flat/ramp input Reflex is rounding noise / rounding noise (|r| up to 2.86 in the article model): never read it there. \|Reflex\| ≤ 5 exactly |
| Oscillators | MESA Stochastic | **Corrected and verified 2026-11-19.** Source: TASC V.32:1 (2014) sidebar. Review `docs/harness/MESASTOCHASTIC_SOURCE_REVIEW.md` (`3f0de96`): M-1 window `StochPeriod + 1` → `StochPeriod`; M-2 scale 0–100 → 0–1 (exports before `0332395` are ×100); M-6 fallback 50 → 0.5; M-9 `MESAStochasticCore` exports Roof and raw Stoc; M-8 header; M-4 HP seeding fixed upstream (GAP-1.26); M-5 final seed kept (start-up INFO). Old file kept as `MESAStochastic_Superseded.c` (control NCS). Spec `MESA_ArticleFidelity.toml` (`0fd34ee` + Amendment 1 `4843ee2` + Amendment 2). **Run 1 PASS** (`17a8604`): 84/84 real checks, 5/5 controls detected (29 FAIL rows), IMP ≤ 8.9e-16, floor 20/20; Zorro vs article = `PI` gap (trace 3.9e-6). Read twice, agreed with the pre-run prediction (`57b1abf`). (b) A window-length error (21 vs 20 bars) is invisible on sines with T ≤ L (≤ 7.6e-14) and shows only at T > L (6.2e-2 / 8.1e-2 at T = 40 / 100). (b) The final output is not bounded to [0, 1] (−0.0295 to 1.0295 at T = 100); only the raw Stoc is exactly bounded, so the source's .2 / .8 thresholds act on a signal that can exceed [0, 1] |
| Oscillators | CyberCycle, Elegant Oscillator, Fisher, Inverse Fisher, COG, RSIH, Laguerre Osc, Laguerre RSI | Not reviewed |
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
| C1 | Fisher (10) | MESA Stochastic (20,48,10) — verified 2026-11-19 (0–1 scale; source lines .2 / .8) | Indicator metrics |
| C2 | Reflex — flagged; verified 2026-11-18 (not zero-lag at T = L, §1.1) | Laguerre RSI — shortlisted | C-3b (backtest) never run |
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
| GAP-1.26 | HP seeding — first output starts far from steady state | **Fixed in HighPassFilter.c 2026-11-17** (`d22ef57`, zero seed as the source). RoofingFilter re-verified 2026-11-17 (RFF run 1 PASS). MESAStochastic re-verified 2026-11-19 (MST run 1 PASS). Not yet re-verified: Decycler, RMO |
| — | MESA Stochastic exports made before `0332395` (e.g. `Test_MESAStochastic.c`, `Test_C2_LaguerreRSI.c`, `Test_LagSine.c`, `Test_RecursiveMedian.c` outputs, any notebook reading them) are on 0–100 and used the 21-bar window | Not comparable with the verified indicator |
| — | Week 9 validation not reproducible (no tracked file reads its CSVs) | FRAMA, Laguerre, DSMA status unsupported |
| — | `CyberCycle.c` statics may lack `cc_` prefix | Unconfirmed after four sittings |
| — | Decycler vs UltimateSmootherE — possibly the same filter | (c) 2026-11-18: probably different HPs (V.33:09 HP-A vs V.42:04 HP); USE run 1 control NCX (= x − HP-A(20)) differs from UltimateSmootherE(20) by gain 0.22. Confirm when Decycler is reviewed |
| — | `SuperSmoother2Pole.c` "First bar" comments are misleading: `Init` is `is(INITRUN)`, not the first bar (b, `include/variables.h:182`; gotchas 9d.5) | Comment only; output unaffected (H1 run 2) |
| — | Generated scripts' EXITRUN `printf` + marker file never fire (gotchas 9d.4; no marker from any run, re-confirmed SS2F run 1) | Dead code presented as a check; run cards must not rely on it. Remove or replace with a check written before `quit()` |
| — | Harness ramp-lag check assumes DC gain 1: a DC-gain error reads as lag ((x − y)/s = (1 − G)·x/s + G·τ; NC-B 35 bars) | **Resolved 2026-11-16:** HARNESS_DESIGN D4 (`032d766`): sine phase + ramp residual; ramp lag only at DC gain 1; `m_flat` generalised |
| — | Literal products folded at compile time to an unpredictable float32 (gotchas 9d.8, probe `ba54022`) | UltimateSmootherE.c fixed 2026-11-18 (`ad8eae5`). Remaining in DominantCycle.c:24–25/46–47, InstantTrendline.c:63; each spec replaces them |
| — | `L_FLOAT32` exemption is not written to the results header (lint output only) | Run records should carry every pre-registered exception; small tooling task |
| — | Intermittent test errors (`test_cli` MemoryError in Claude Code's shell, ×2; once 4/144 ERRORs in Git Bash, cause not captured) | CLAUDE.md §8 now requires tracebacks + rerun; watch |
| — | `docs/indicators/SuperSmoother_Notes.md`: SS3 sections dated before 2026-11-16 describe the superseded hybrid (Key Finding 2, coefficients, SS3 table rows, SS3 Period column) | Flagged by a notice in the file; not re-measured for the corrected SS3 |
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
| RoofingFilter(48, 10) | Unit sine, period 20 / alternating (period 2) | Gain 0.8900165495219391 (phase −0.05338683922280379 rad) / ~6e-18 | RFF spec `[known_answer_T20]`, 2026-11-17. **Corrected:** the earlier 0.890038 (Week 14 Handoff 4 §8) was computed from the old code (0.707 HP), not the article; it differs by 2.1e-5. A period-2 sine cannot be built (sin(πn) = 0), hence the alternating input |
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
   **Reusable harness built and accepted 2026-11-07** (`417da02`, branch `harness-step2`):
   reference model, checker, generator + TOML spec format, 27/27 self-tests; tool acceptance run
   reproduced H1 byte-identically (HARNESS_DESIGN §7). Run tests: `bash analysis/harness/run_tests.sh`.
   **SS2 source fidelity: run 1 PASS, 2026-11-12** (`763601e`, branch `harness-ss2f`). Spec
   `analysis/harness/specs/SS2_ArticleFidelity.toml` (`eaba250` + Amendment 1 `b941c06` + Amendment 2
   `02a6fca`); gain tol 3e-5, lag 1e-3. 28/28 real checks; NC-A, NC-B, NC1, NC2 detected on their required
   kinds; OX: 37/37 raw columns identical to H1 run 2 raw; 8 variants. Tooling 40/40 tests (checker CLI:
   `python analysis/harness/checker.py <spec.toml> <raw.csv>`). Raw sha256 `39c9ce95…a89e` (copy kept
   locally, `*_raw_run*.csv` is gitignored).
   **SS3 source fidelity + implementation: run 1 PASS, 2026-11-16** (`09c05ad`, branch `harness-ss3f`). Source
   *Cybernetic Analysis* Fig. 13.11; D1 Amendment 1 (rule 4, `9789fb5`): printed `1.738` → √3, justified by the
   book's own Table 13.4. The existing `SuperSmoother3Pole.c` was a hybrid matching neither cited source; corrected
   (`172fb4e`), hybrid kept as `SuperSmoother3Pole_Hybrid_Superseded.c` and used as negative control NCH. Spec
   `analysis/harness/specs/SS3_ArticleFidelity.toml` (`867f952` + Amendment 1 `a1dbce5`); gain tol 3e-5, lag 1e-3.
   New in this spec: IMP replay check (implementation question answered in the same run, no H1-style run needed)
   and floor guard (pass item 7). 28/28; NCA, NCB, NCL, NCH, NC1, NC2 detected on required kinds; IMP ≤ 3.4e-14;
   10 variants. Tooling 65/65 tests. Raw sha256 `eacb27cc…88f5` (local copy).
   **Order C decided 2026-11-16:** verify the indicators on the shortlisted slot path first (§1.2): MESAStochastic (C1) →
   RoofingFilter → HighPassFilter; UltimateChannelBands (stops) → UltimateSmootherE; Reflex (C2) → SuperSmoother2Pole
   (verified). Decycler deferred (used only by `Test_Decycler.c`). Steps 4–5 may be built in parallel; **no backtest
   result is read until every slot indicator in it has passed.**
   **HighPassFilter: run 2 PASS 2026-11-17** (`512781c`, branch `harness-hpf`; details §1.1 and HARNESS_DESIGN §7). New in
   this spec: D4 checks (phase, ramp residual, start-up), IMP own-model replay for every control, D5 amendment corrections.
   Workflow from now on: every run is read twice (planning-chat back-check + prediction, then checker; HARNESS_DESIGN §4).
   Tooling 198/198 tests. Raw sha256 `40dec81a…4898` (runs 1 and 2 byte-identical).
   **RoofingFilter: run 1 PASS 2026-11-17** (`d1395d3`, branch `harness-rff`; details §1.1 and HARNESS_DESIGN §7). New in
   this spec: two-parameter variants, include lists, alternating (Nyquist) input, phase gate binding (alt phase SKIP), cascade
   reference models. Read twice: planning-chat back-check agreed on every verdict row. Tooling 286/286. Raw sha256
   `edb3400f…c810`.
   **UltimateSmootherE: run 1 PASS 2026-11-18** (`41c8d76`, branch `harness-use`; details §1.1 and HARNESS_DESIGN §7). New in
   this spec: start-up seed mode `pass<n>` (the source's first-n-bars = Price rule), complement model `one_minus`, variant role `info`
   (NCL, article as printed, reported never PASS/FAIL), per-instance CurrentBar counter in the corrected .c (gotchas 9d.9). Read twice:
   planning-chat back-check agreed on every verdict and FAIL count. Tooling 361/361. Raw sha256 `b47897d9…4745c74`.
   **Decided 2026-11-18: oscillator family first (option B), Reflex before MESAStochastic.** Reason: C1/C2 are the entry signals
   (the template cannot trade without C1), their dependencies were already verified, and Reflex.c carried a live shared-state bug.
   UltimateChannelBands deferred: it reads High/Low itself (`series(priceHigh())`), so it needs a High/Low/Close signature change
   before the harness can test true range; (c) possibly off the first template's critical path if NNFX_Sources gives ATR stops
   (to check from the source, not memory).
   **Reflex: run 1 PASS 2026-11-18** (`ad487b7`, branch `harness-rfx`; details §1.1). New: HARNESS_DESIGN **D6** (oscillator check
   set: export the linear stage, trace replay with a model-MS gate, exact bound, invariance, multi-instance control, start-up INFO;
   `5087c39`); tooling `853dc20` (multi-output calls, trace/bound/invariance, shared-state replay) + `62b4e97` (out-parameters via
   local scalars, `&Y[k]` never compiled). Planning-chat prediction committed before the checker (`901b3a0`); the checker agreed on
   every verdict and all 76 control FAIL rows. Tooling 460/460. Raw sha256 `f1ab5494…1d75` (local copy).
   **MESAStochastic: run 1 PASS 2026-11-19** (branch `harness-mesa`; details §1.1). Review `3f0de96`, tooling `85b7431`, spec `0fd34ee`,
   corrected .c + superseded control + test `0332395`, Amendment 1 + script `4843ee2`, prediction `57b1abf`, results `17a8604`. New in
   this spec: three-output calls (out, Roof, raw Stoc), two-sided bound on the raw Stoc (the final output has no exact bound), gate
   on the model's HH − LL range, trace tolerance 5e-5 chosen by D2 rule 3 (the 3e-5 default failed the window). Resumed after an
   interrupted session (stash backup). Read twice: the checker agreed with the pre-run prediction on verdict, counts and compared
   values. Tooling 555/555. Raw sha256 `0c53641a…efddefda` (local copy).
   **Next: decision pending (planning chat).** Remaining oscillator-family slot candidates: Fisher Transform (C1, Strategy 1) and
   Laguerre RSI (C2, Strategy 2); baselines (FAMA / FRAMA) and stops (UltimateChannelBands, NATR) after.
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
