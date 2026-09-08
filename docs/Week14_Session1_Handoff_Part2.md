# Week 14 — Session 1 Handoff (part 2 of 3)

**Date:** 2026-08-31 (second sitting)
**Covered:** SuperSmoother 3-pole, UltimateSmoother, UltimateSmootherE
**Not covered:** family status-table rewrite, HighPass, RoofingFilter, Decycler
**Repo:** acd46fa -> 82b69a1. Nine commits total across both sittings.

Read part 1 first (`docs/Week14_Session1_Handoff.md`). This continues its
section 8.

---

## 1. What reconstructed cleanly

- **SS3's mechanism.** Third feedback term, `K*Filt[3]`, identified from memory
  after one counting slip. Correct.
- **Why keep both SS2 and SS3.** Correct — different placement on the
  lag/rejection trade-off, chosen from the frequency response.
- **dB.** Not recalled; taught in session. Landmarks converted correctly
  afterwards (-3 dB -> 71%, -7 dB -> just under 50%).
- **The design of UltimateSmoother, derived before opening any file.** Asked how
  to remove lag without restoring noise, the answer given was `price - fast part`,
  with the fast part from a high-pass filter. That is Ehlers' published design
  exactly. The naive `smooth + alpha*(price - smooth)` was proposed first and
  correctly abandoned once tested — and that first proposal turns out to be what
  the Week 5 file implements. Both ideas, in order, matching both files in the repo.
- **Stability.** After one worked example, correctly identified that the larger
  pole magnitude governs settling time.

## 2. What did not reconstruct

- **GAP-1.14.** UltimateSmoother's mechanism and design goal not recalled;
  recall extended only to "a better lag/smoothing trade-off," which describes
  every Ehlers smoother and distinguishes nothing. Rebuilt in session.
- **SS3's behaviour** beyond "more complex frequency response" — built from the
  measured response rather than recalled.

## 3. Findings

### 3.1 SS3's advantage is far narrower than documented

`Period` does not mean the same thing for the two filters. SS2's -3 dB point sits
at ~1.0x Period; SS3's at ~1.57x. So SS3(20) corners near 31 bars and SS3(30) near
47. Comparing SS3(20) against SS2(20) compares filters placed differently.

Matched at -3 dB ~20 bars (SS2 Period=20 vs SS3 Period=12.8):

| period | SS2(20) | SS3(12.8) | winner |
|---|---|---|---|
| 3 | 1.6% | 0.6% | SS3 |
| 5 | 5.8% | 3.1% | SS3 |
| 8 | 15.4% | 13.3% | SS3 |
| 10 | 23.8% | 25.4% | SS2 |
| 14 | 43.6% | 51.6% | SS2 |
| 20 | 70.4% | 70.7% | — |
| 30 | 91.2% | 82.5% | SS2 |
| 50 | 98.7% | 91.9% | SS2 |
| 100 | 99.9% | 97.7% | SS2 |
| **lag** | **4.04 bars** | **5.17 bars** | **SS2** |

SS3 wins only at roughly 3-8 bar periods. It costs +1.13 bars of lag, 7-9 points
more attenuation of 30-50 bar moves, and is worse just above the corner — the
steeper edge does not pay off until well past it.

Cell 12's "SS3 beats SS2 at ALL frequencies" is contradicted at every period
above 10, and its recommendation to "use SS3(28-30) to match SS2(20)" runs the
wrong way: matching needs SS3 near Period=13.

### 3.2 The stability reason in the notes was invalid

"Net feedback > 1.0" is not a stability test. Counterexample:

    y[t] = 0.1*x[t] + 2.5*y[t-1] - 1.6*y[t-2]

Coefficients sum to 0.9 and it diverges — 124 by bar 20 on a constant input of 1.

The correct test is **pole magnitude**: the poles are the roots of the feedback
polynomial, and every root must have magnitude below 1. SS3(20)'s are 0.626,
0.626, 0.443. The largest also sets memory length: 0.626^20 is about 0.00009, so
contaminated state clears within ~20 bars.

Note this revises the working definition used in part 1. "Pole = one feedback
term" counts poles correctly but is not what a pole is, and says nothing about
stability.

### 3.3 UltimateSmootherE's zero lag is real, exact, and narrow

The measurement is sound. `Test_USLag.c` feeds a synthetic ramp, uses no market
data, and includes SS2 as a de facto control. Verified end to end: Zorro lite-C
output at bar 2697 agrees with an independent scipy computation to four decimals
on all three filters.

| filter | ramp lag |
|---|---|
| UltimateSmootherE.c | 0.0000 |
| UltimateSmoother_W5_Superseded.c | 3.8725 |
| SuperSmoother2Pole.c | 4.0387 |

**Why it is exact.** `UltimateSmootherE = Price - HighPass(Price)`. Recovered
from the coefficients: the discarded component's weights normalise to exactly
1, -2, 1, the numerator of a 2-pole high-pass. That pattern regroups as

    (P[t] - P[t-1]) - (P[t-1] - P[t-2])

— the change in the change, a discrete second derivative. The second derivative
of a straight line is exactly zero, so on a ramp the high-pass outputs nothing
and US = Price. An algebraic identity, not a tuning result, and it holds at every
Period: changing Period changes the scale of those weights, not their ratio.

**The limit, which matters more than the result.** A ramp is a straight line;
real price is not. The moment price bends the second derivative is non-zero, the
high-pass produces output, and the filter subtracts something real. What is
established is zero lag on straight-line input. Lag on a curve, a turn, or a
cycle is unmeasured, and nothing in this repo answers it.

### 3.4 The Week 5 file implements an approach that cannot work

`UltimateSmoother_W5_Superseded.c` is SuperSmoother plus a fraction of the
residual:

    Residual = Price[0] - SS[0]
    US[0]    = SS[0] + gamma*(Residual + US[1] - SS[1])

Three things:

- `gamma` is numerically identical to `c0`, SuperSmoother's own input
  coefficient — not a separately derived correction term. Value 0.0395.
- The residual is never smoothed, despite a comment claiming it is.
- The approach cannot work in principle. `Price - SS` is lag and removed noise
  summed into one number; expanding the correction gives
  `gamma*Price + (1-gamma)*SS`, a blend, so recovered lag always arrives with
  proportional noise.

It removes 0.166 bars of 4.04 — 4.1%. Week 5 recorded it VALIDATED and
"near-zero-lag," and its own header specified detrended cross-correlation as the
check.

### 3.5 Process defect: corrections do not propagate backwards

Week 13 found and documented all of 3.4 (`UltimateSmoother_Lag_2026-08-12.md`,
`Week13_Notes.md` 3.1). `SuperSmoother_Notes.md` was never updated, so the false
claim remained the first thing a reader met, with the correction three documents
downstream.

There is no mechanism for propagating a correction back to the document that made
the original claim. Found by grep, not by any check. **This likely affects other
weeks and is the more transferable finding of the two sittings.**

### 3.6 One scalar standing in for a trade-off — instances 4 and 5

Part 1 logged three. Two more here:

- coefficient sum used as a stability test, where the honest test needs all pole
  magnitudes
- "SS3 better?" defined as more attenuation, where the honest answer needs the
  fast end and the slow end separately

Five instances across two sittings. This is the review's principal recurring
finding.

## 4. Gaps

| ref | finding | status |
|---|---|---|
| GAP-1.9 | "SS3 beats SS2 at ALL frequencies" invalid | FIXED — b93df97, 22b0665 |
| GAP-1.12 | Instability claim unsourced and its reason invalid | RESOLVED — reason wrong; conclusion still unverified against the article, which is not in the repo |
| GAP-1.13 | Is there 3-8 bar energy in EUR/USD D1 or BTC/USD H4 at all? Determines whether SS3's only advantage is worth +1.13 bars of lag. Answerable from a spectrum; does not need a backtest. | open — Phase 2.5 or a short standalone |
| GAP-1.14 | UltimateSmoother mechanism not recalled | closed — reconstructed |
| GAP-1.15 | No mechanism to propagate corrections back to the originating document | open — process, not filter |
| GAP-1.16 | `UltimateSmootherE`'s lag on non-straight-line input is unmeasured. The 0.0000 result establishes nothing about curves or turns. | open |
| GAP-1.10 | Also applies to `Test_USLag.c`: its CSV is written to the Zorro install directory, untracked | open |

## 5. Commits

| commit | what |
|---|---|
| b93df97 | SS3 claims corrected in `SuperSmoother_Notes.md` |
| 22b0665 | SS3 correction cell appended to the notebook; cell 12 left intact |
| 4b229f6 | `UltimateSmoother.c` -> `UltimateSmoother_W5_Superseded.c`; dead include removed; fix scripts gitignored |
| ba32b2f | Header and comments corrected in the superseded file |
| 758aa4b | Week 13's finding propagated into Week 5's notes |
| 9a789d2 | New `docs/methods/Lag_Cancellation_Derivation.md` |
| 82b69a1 | Naming disambiguated across LaguerreOsc and Week13_Notes |

Every code change was verified by re-running `Test_USLag.c` and confirming the
output was byte-identical to the pre-change baseline.

## 6. Decisions taken

- **U-12 option B.** The Week 5 file was renamed rather than leaving prose to
  compensate, and rather than a full swap that would touch live callers.
- **Keep the dead end.** Retained as a documented artifact, explicitly not for
  use — the reasoning is instructive.
- **Records are not rewritten.** Notebook cell 12 and `Week13_Notes.md` keep
  their body text; corrections go alongside, not over.
- **Header notes are a judgement call**, not a numeric cap. Live code and current
  docs get fixed; dated records get a header only where the ambiguity would
  actually mislead. `Week13_P1_P4_Results.md` deliberately got nothing.
- **`docs/methods/`** is a new directory for reasoning that spans indicators.

## 7. Next sitting starts here

1. **The family status-table rewrite** in `SuperSmoother_Notes.md` — deferred
   twice, now unblocked. The header still reads `Status: VALIDATED` and
   `Last Updated: Week 5 Day 6`; the file has been edited three times since.
2. **HighPass** — needed for its own sake and because
   `Lag_Cancellation_Derivation.md` leans on it.
3. **RoofingFilter**, then **Decycler**.
4. **CyberCycle.c** statics missing the `cc_` prefix (GOTCHAS 1.3) — plan 4.1
   suggests session 6; confirm.

**Open decision, unchanged from part 1:** whether to re-run Week 5's validation
with the frequency-response method, and whether GAP-1.10 is solved by committing
the CSVs or by moving validation to synthetic inputs, which need no data.

**Suggested carry-forward question for HighPass**, given 3.3: the derivation says
UltimateSmootherE subtracts a high-pass. Session 1 never measured that high-pass
on anything but a straight line. Measuring it on a curve is the natural way into
GAP-1.16.
