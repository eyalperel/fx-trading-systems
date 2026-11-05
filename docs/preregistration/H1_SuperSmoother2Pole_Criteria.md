# H1 — SuperSmoother 2-Pole harness: pre-registered acceptance criteria

**Status:** PRE-REGISTERED. Written 2026-11-04, before any harness code exists.
**Approved by:** user, 2026-11-04.
**Implements:** PROJECT_STATE §7, Phase 1 step 3 (first indicator through the harness).
**Under test:** `indicators/ehlers/SuperSmoother2Pole.c`, as committed at the time of the run.

Amendments are appended at the end, dated. Nothing above the Amendments heading is edited
after the first run.

Labels: (a) source states · (b) measured / computed here · (c) inference.

---

## 1. Purpose

Show that `SuperSmoother2Pole(Price, Period)` produces the output its coefficients imply,
on synthetic inputs whose correct answer is known from the math. This is a correctness
test of the code only. It says nothing about trading value.

## 2. Inputs (synthetic, no market data)

Each run is **N = 3000 bars**. The first **W = 500 bars** are warmup and are excluded from
all measurements.

| Input | Definition (bar index n = 0 … 2999) |
|---|---|
| Flat | x[n] = 1.1 |
| Sine, period T | x[n] = 1.1 + 0.01·sin(2πn/T), for T ∈ {5, 10, 20, 40, 100} |
| Ramp | x[n] = 1.1 + 0.0001·n |

Inputs sit around price level 1.1 so that magnitudes resemble EUR/USD (c: chosen so any
price-magnitude guard behaves as it would on real data).

## 3. Measurements (how each number is computed)

| Quantity | Method |
|---|---|
| Flat error | max \|y[n] − 1.1\| over bars n ≥ W |
| Sine gain at T | Least-squares fit of y[n] = a·sin(2πn/T) + b·cos(2πn/T) + c over n ≥ W; gain = √(a²+b²) / 0.01 |
| Ramp lag | mean of (x[n] − y[n]) / 0.0001 over the last 100 bars |

**Do not measure gain as the peak of y.** (b) Bars sample a period-20 wave every 18°, so
the true peak is usually missed: peak-based gain read 0.6967 against the true 0.7042 (−1.1%)
in the 2026-11-04 check. That would fail a correct filter at the tolerance below.

## 4. Expected values

(b) Computed from the transfer function of the filter's coefficients,
H(z) = c0(1 + z⁻¹) / (1 − c2·z⁻¹ − c3·z⁻²), with c1 = exp(−√2·π/P), c2 = 2·c1·cos(√2·π/P),
c3 = −c1², c0 = (1 − c2 − c3)/2, and lag = 0.5 + (c2 + 2·c3)/(1 − c2 − c3).
Confirmed independently by simulating the recursion with the inputs and methods above
(Python, 2026-11-04): all values agree to 6 decimals.
The P=20 values match PROJECT_STATE §5 (session 2026-10-20).

| Period | Flat error | Gain T=5 | T=10 | T=20 | T=40 | T=100 | Ramp lag (bars) |
|---|---|---|---|---|---|---|---|
| 10 | 0 | 0.224200 | 0.695059 | 0.966116 | 0.997024 | 0.999785 | 1.825321 |
| 14 | 0 | 0.116965 | 0.446731 | 0.894265 | 0.991557 | 0.999643 | 2.704175 |
| 20 | 0 | 0.057665 | 0.238406 | 0.704174 | 0.969143 | 0.999037 | 4.038666 |
| 30 | 0 | 0.025669 | 0.108551 | 0.404454 | 0.870678 | 0.995811 | 6.277073 |

## 5. Tolerances

| Check | PASS if |
|---|---|
| Flat | error ≤ 1e-9 |
| Sine gain | \|actual − expected\| ≤ 1e-4 |
| Ramp lag | \|actual − expected\| ≤ 1e-3 bars |

Each check is one row in the results file: 4 periods × 7 checks = **28 checks**.

## 6. Negative controls (must FAIL)

Run the same 7 checks against two deliberately broken filters, compared to the **P=20**
expected values. These test the harness itself: a harness that passes a broken filter is
broken. (a) PROJECT_STATE §2 rule 4: a guard never seen to fire is not a guard.

| Control | Broken how | Gain T=20 | Ramp lag | Expected result |
|---|---|---|---|---|
| NC1 | Period 21 passed, checked against P=20 values | 0.669 | 4.262 | FAIL |
| NC2 | `cos(√2·180/P)`: cos argument in degrees (gotchas §2) | 0.531 | 5.426 | FAIL |

(b) Values from the 2026-11-04 simulation. Both pass the flat check (flat error 0),
because c0 forces unit gain at zero frequency whatever the coefficients are. **The flat
check does not test coefficients;** it tests startup and seeding. The sine and ramp checks
test the coefficients.

A control "FAILs as required" if at least one of its sine-gain or ramp-lag checks fails.

## 7. Pass condition for H1

H1 passes only if **all** of the following hold:
1. All 28 real checks PASS.
2. Both NC1 and NC2 FAIL as required (§6).
3. No row is ERROR, and no output value is NaN or infinite.
4. The results file reports the variant count: 4 periods + 2 negative controls = **6 variants**.

Any other outcome is H1 FAIL. A FAIL is recorded and kept (PROJECT_STATE §2 rule 9),
and the cause is found before anything is changed.

## 8. Things this run is also expected to reveal (c)

- `SuperSmoother2Pole.c` keeps state with `series()` and an `Init` flag inside an included
  file. ZORRO_LIGHTC_GOTCHAS §3.2 and §9b flag both as unreliable there. (c) If they
  misbehave, the flat check or the early ramp rows should show it.
- Whether Zorro resolves `#include "../../indicators/..."` from the script's folder
  (CLAUDE.md §3). A deliberately wrong include path must fail to compile.

These are observations to report, not pass conditions.

---

## Amendments

### Amendment 1 — 2026-11-05 (before any run; no results seen)

**Reason.** Claude Code's plan review (2026-11-05) showed that two statements above are
wrong. Every registered check excludes bars n < 500 (§3), and a startup transient decays to
about 1e-32 by then, even at P=30. So no registered check can observe startup or seeding.

**A1.1 Correction to §6 and §8.** The flat check tests unit gain at zero frequency **in
steady state**. It does **not** test startup or seeding, contrary to §6 ("it tests startup and
seeding") and §8 bullet 1 ("the flat check or the early ramp rows should show it"). Those
sentences stand above as written and are superseded by this amendment.

**A1.2 Observations block (reported, not part of the verdict).** The results file adds a
separately labelled block, computed per variant (P10, P14, P20, P30, NC1, NC2):

| ID | Observation |
|---|---|
| O1 | max \|y − 1.1\| on the flat input over n = 0 … 499 |
| O2 | the first bar n at which the flat-input error stays ≤ 1e-9 for all later bars |
| O3 | raw output rows n = 0 … 9 for the flat and ramp inputs |

No pass/fail is attached to O1–O3. (c) There is no trustworthy expected value for startup
yet, because how `series()` seeds the filter state in Zorro is the uncertain part. Any future
pass criterion on startup needs its own dated amendment, written before the run it applies to.

**A1.3 Clarification of §2.** Each input value x[n], for n = 0 … 2999, is fed to every filter
**exactly once**, in order. A run in which any x[n] is fed twice or skipped (for example by
the INITRUN call) is an ERROR, not a PASS.

**A1.4 Unchanged.** §3–§5 (measurements, expected values, tolerances), §6's negative controls
and their required outcome, and the §7 pass condition are unchanged.
