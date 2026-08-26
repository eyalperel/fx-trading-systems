# Week 14 — Guided Review and Library Consolidation

**Date:** 2026-08-14
**Supersedes:** the Week 14 sections in `docs/roadmap/FX_Roadmap_v2026.08.10.md`
and `docs/indicators/Week5-14_Indicator_Plan.md`
**Runs before:** Phase 2.5 (Backtesting Bootcamp)

---

## 1. Purpose

**The purpose of this week is that I can hold the whole project in my head.**

Thirteen weeks produced 26 indicators, four amendments to a pre-registered
criteria document, ten registered predictions in the last week alone, a
surrogate-testing research programme, and a scope correction that withdrew two
principles and an elimination criterion. Every one of those was a decision I made
with a reason at the time. The reasons are written down. **Being able to reach them
under question is a separate skill, and it is the one this week builds.**

This surfaced during the 2026-08-10 rescope: I could not, unprompted, say why C-7
existed, what the Reflex flag rested on, or what the null tests had established as
opposed to what they had been used for. That is not a documentation failure — the
documents were correct. It is a retrieval and articulation gap.

Phase 2.5 makes that gap expensive. Strategy-level decisions depend on which
indicator does what, which validations are trustworthy, and which parameters were
chosen rather than measured. Carrying an incomplete picture into backtesting means
building on assumptions I cannot check.

### 1.1 The secondary purpose

Consolidation — the master table, the NNFX map, the README — was Week 14's original
brief and still needs doing. It becomes the **output** of the review rather than its
method, for a specific reason.

**`UltimateSmoother.c` did not implement its cited article, and passed validation
anyway.** Recorded as VALIDATED and "near-zero-lag" in Week 5; measured in Week 13 at
3.87 bars against SuperSmoother's 4.04. The Week 5 check used detrended
cross-correlation, later found to report 0.00 bars for an EMA with a true lag of
1.50. **The method could not have detected the discrepancy.**

**Week 9's validation is not reproducible.** No tracked file reads
`FRAMA_Laguerre_DSMA_*.csv`. Three indicators marked VALIDATED with no artifact.

So **"validated" does not mean the same thing across the library.** Tabulating
existing status without re-examining it would carry that inconsistency into Phase
2.5.

These defects are also the best teaching material available. Explaining *why* the
Week 5 method could not have failed requires group delay, cross-correlation, and
what a validation is actually for. Fixing the file takes minutes. Being able to
explain it is the point.

---

## 2. How sessions run

**I explain first. Claude probes. Gaps surface. We fix what is broken.**

The artifacts are material for that conversation, not its object. A session that
consists of reading documents and agreeing with them produces nothing.

### 2.1 The loop

| Step | What happens |
|---|---|
| **Recall** | I explain the topic from memory — mechanism, why it was built, what was decided. Before reading anything. |
| **Probe** | Claude asks what would have changed the decision, what the alternative was, what the number means. Wrong answers are the useful ones. |
| **Read** | The actual artifact — source article, `.c` file, notes, notebook. Compared against what I just said. |
| **Gap check** | What is missing, wrong, unreproducible, or undocumented — in my understanding *and* in the repo. |
| **Fix** | Batched to the end of the session. |

### 2.2 Rules for Claude

- **Do not hand me the answer when I say I don't know.** Reconstruct: hint, ask a
  smaller question, build from a concrete case. Slowly is correct here.
- **Worked example first, with small made-up numbers and arithmetic shown.** The
  general rule second. Never the formula first. This applies to the whole review,
  not only to new material.
- **One concept per step. Pause. Wait.**
- **Follow my questions when they diverge from the agenda.** The plan is a
  scaffold, not a schedule.
- **Bring external material when it would help** — a video, a textbook section, a
  cleaner explanation than paraphrase. DSP fundamentals in particular are better
  learned from a source built to teach them.
- **Restate jargon in plain words the moment it appears.**
- **If I say "clear" quickly and repeatedly without asking anything, check rather
  than accelerate.**

### 2.3 Two standing questions

Asked at every topic, both arising from §1.1:

1. **Could the validation method have failed?** If the check could not have
   detected a wrong implementation, the validation is not evidence.
2. **Can it be reproduced from the repo alone?** If the artifact is not tracked,
   the status is a claim, not a record.

### 2.4 What counts as a finding

Logged as gaps, equally:

- A repo defect — wrong implementation, missing test, unreproducible result
- **"I don't remember why we did that"** — an undocumented decision, or a
  documented one I cannot reach
- A number I can state but not interpret
- A parameter I cannot say was chosen rather than measured

The second and third are the reason for the week. They are not embarrassments to
move past quickly.

---

## 3. Sessions

One chat per session, each ending with a handoff note. Grouped by function rather
than by week, because understanding an indicator means comparing it against others
doing the same job. Session 6 is cross-cutting, where the by-week view matters.

| # | Session | Covers |
|---|---|---|
| 1 | Foundation filters | SuperSmoother 2P/3P, UltimateSmoother + UltimateSmootherE, HighPass, RoofingFilter, Decycler |
| 2 | Baselines | MAMA/FAMA, FRAMA, DSMA, Laguerre filter, InstantTrendline |
| 3 | Oscillators and normalisers | CyberCycle, Elegant Oscillator, Fisher, Inverse Fisher, COG, MESA Stochastic, RSIH, Laguerre Oscillator |
| 4 | Zero-lag, predictive, noise reduction | Reflex, ELI, Recursive Median + RMO, Alpha-Beta, Correlation Cycle |
| 5 | Volatility and regime | NATR, Ultimate Channels/Bands, volatility regime classifier, DominantCycle |
| 6 | Validation methods | Lag measurement, group vs phase delay, surrogate methodology, the guards, the GOTCHAS |
| 7 | Decisions and criteria | C1/C2 selection, the four amendments, pre-registration record, what is locked and on what evidence |
| 8 | Consolidation | Master comparison table, NNFX map, README, Phase 2 retrospective |

**Duration is elastic and expected to overrun.** Sessions may split. A session that
takes three sittings because the mathematics needed rebuilding from the ground up
has succeeded, not failed.

---

## 4. Open items inventory

Consolidated from Week 12's carry-forward, Week 13's retrospective, and the
2026-08-10 rescope. Each is assigned to a session or explicitly deferred.

### 4.1 Reproducibility and correctness

| Item | Source | Session |
|---|---|---|
| Week 9 validation not reproducible — FRAMA, Laguerre, DSMA | `Week9_Validation_Not_Reproducible.md` | 2 |
| `UltimateSmoother.c` vs `UltimateSmootherE.c` — which is referenced where, and what Week 5's claims should now say | Week 13 §3.1 | 1 |
| Elegant Oscillator (EBS) implemented but has no test script | Rescope audit, 2026-08-10 | 3 |
| `DominantCycle.c` STEP 5 omits Ehlers' EMA smoothing term | Week 13 §7 | 5 |
| `CyberCycle.c` statics lack the `cc_` prefix (GOTCHAS 1.3) | Week 13 §7 | 1 or 6 |
| CSVs and `AssetsDarwinex.csv` live outside version control | Week 13 §7 | 6 |
| Duplicate `InstantTrendline_Validation.md` in `docs/` and `docs/indicators/` | Week 12 §12 | 2 |

### 4.2 Voided by the 2026-08-10 rescope

| Item | Original target | Disposition |
|---|---|---|
| **Action 10 — null-test Reflex and MESA Stochastic** | Week 14 | **VOID.** Registered under Principle 6, which the rescope withdrew. Indicators are classified by mechanism; no surrogate test is required to admit one to the library. Recorded here rather than dropped so it does not resurface as an unexplained gap. |

### 4.3 Deferred to Phase 2.5 or later

| Item | Source | Why deferred |
|---|---|---|
| C-3b resolution for both C2 slots (Reflex, Laguerre RSI) | Week 12 §12, Week 13 §2.6 | Strategy-level test; needs a backtest |
| Swap cost modelling before C-3b | `Swap_Cost_Modelling_Open.md` | Input to the C-3b backtest |
| Confirmation-set pass condition — pre-registered before the first confirmation run | `Scope_Correction_2026-08-10.md` §5 | Requires metrics that do not exist until Phase 2.5 |
| EUR/JPY and AUD/USD history downloads | `Data_Availability_2026-08-12.md` | Development set stays two-asset until complete |
| Alpha-Beta gain sweep at 0.02/0.05/0.10/0.20 | Week 12 §12 | Low priority |
| RSIH adaptive-length variant vs fixed-20 | Week 13 §7 | Comparison, not a blocker |
| Does RM help on genuinely corrupted data? | Week 12 §12 | Only if RM is proposed for live use |
| Autocorrelation periodogram Light-C port | Week 12 §12 | Only if a future test rejects |
| `ROADMAP_UPDATE_PROTOCOL.md` rewrite, including narrowing trigger 3 | Raised 2026-08-14 | Belongs with the Phase 2.5 rewrite the file already calls for |

### 4.4 Outside the repository

CV and portfolio narration work is tracked separately in `audit/` (gitignored). A
parallel track with a different audience; it does not belong in the technical
record. Noted here only so its absence is deliberate.

---

## 5. Deliverables

- **Master comparison table** — every indicator: mechanism, measured lag, bandwidth,
  parameters, cross-asset behaviour, NNFX role, and **how it was validated**
- **NNFX component map** — verification of the map Week 13 partially filled, with
  the evidence for each slot named
- **README update** — accurate against the reviewed library
- **Phase 2 retrospective**

The validation column is new. It exists because §1.1 showed that status alone does
not distinguish a checked implementation from an unchecked one.

**These are the artifacts. The understanding is the deliverable.**

---

## 6. What this does not change

No indicator is removed, no decision reopened on framing grounds, and no measured
result revised. Corrections come from re-measurement or from a source check, not
from a change of view.

Locked components stay locked unless a review finds a defect in the evidence that
locked them: FAMA and FRAMA baselines, Fisher and MESA Stochastic C1 slots. Reflex
stays flagged. Laguerre RSI stays shortlisted. Both C2 slots resolve in Phase 2.5.
