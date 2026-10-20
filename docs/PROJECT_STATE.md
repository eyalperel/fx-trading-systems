# Project State — fx-trading-systems

**As of:** 2026-10-18 (rehaul, Phase 0)
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
| Smoothers | SuperSmoother 2-pole, 3-pole, UltimateSmootherE | **Reviewed** |
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
- Zorro 2.70+, Git Bash, VS Code, Python/Jupyter (`python`, not `python3`)
- Data: EUR/USD D1, BTC/USD H4 (Zorro native); EUR/JPY D1, AUD/USD D1 (Darwinex MT4)
- `docs/ZORRO_LIGHTC_GOTCHAS.md` — platform reference, keep
- `analysis/null_tests/` — seeded surrogate harness (bootstrap, fGn, IAAFT, stoch-vol)
- Sources: 102 Ehlers TASC articles; *Cybernetic Analysis* (2004); 24 PDFs in project

### 1.4 Does not exist yet

- Any strategy backtest, NNFX template, or exit logic
- Walk-forward, Monte Carlo, or strategy-level surrogate test
- Swap / spread cost model
- Confirmation-set pass condition
- Written NNFX rules from VP / Stonehill sources (see §5)

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

**Inference:** given that every test script reviewed so far could not fail, the
practical status of the unreviewed library is "implemented, not verified". The
Phase 1 test harness should establish verification automatically rather than
continuing the manual review.

---

## 5. Next — Phase 0 remaining

- [x] Step 1: project instructions rewritten (two modes, validation gate)
- [ ] Step 2: this document — review and commit as `docs/PROJECT_STATE.md`
- [ ] Step 3: retire superseded docs (repo `docs/archive/`, project knowledge)
- [ ] Step 4: compile NNFX rules (VP) and indicator rankings (Stonehill) with sources

Then Phase 1: Claude Code + Zorro CLI pipeline, generic NNFX template with
swappable slots, automated indicator checks.

---

## Appendix — chat inventory (for archiving)

All superseded by this document. Archive or delete in the claude.ai UI.

| Period | Chats |
|---|---|
| Nov 2025 – Jan 2026 | Roadmap review; Unified FX/crypto roadmap; Integrating FX and crypto plans; Week 1; Week 2 |
| Feb – May 2026 | Week 3-4 Light-C; Week 4 Day 3-6; Week 5 SuperSmoother; Week 6 High-Pass; Week 7 MAMA (a, b); Week 8 Cyber Cycle; Week 9 FRAMA/Laguerre/DSMA |
| Jul – Aug 2026 | Week 10 Fisher/IFT/COG; Cross-asset validation spec; Ehlers price decomposition premise; Week 12 Noise reduction; Week 13 (two chats); Claim Audit; rehaul_10_08_2026 |
| Sep 2026 | Week 14 Session 1 parts 1–5 |

Chats worth keeping un-archived for reference: **Ehlers price decomposition premise**
(the null-test design) and **Claim Audit** (CV and interview gaps).
