# MST run 1 — planning-chat back-check and prediction (before the checker)

**Date:** 2026-11-19 (planning chat). Written and committed BEFORE `checker.py` is run on this file (HARNESS_DESIGN §4,
read-twice rule). Spec `analysis/harness/specs/MESA_ArticleFidelity.toml` (pre-registered `0fd34ee`, Amendment 1 `4843ee2`).
**Raw file:** `C:/Zorro/Data/GEN_MST_raw.csv`, 3000 rows + header, 308 columns,
sha256 `0c53641af0416324de3629e2744358f3d31e084ef224800ab12241b16fddefda`.
**Zorro window (user, 2026-11-19):** compiled; `Warning 047: EUR/USD first bar on 2008-01-07` (harmless, gotchas 9d.7);
`MST batch complete: 3000 rows written`; no line starting with `Error`. Zorro restarted before the run.
**Code:** `docs/harness/MST_RUN1_BACKCHECK.py` (own models and measurements, numpy; reads no harness module).
Labels: (a) source states, (b) measured here, (c) inference.

## Method (b)

- Inputs rebuilt independently (level 1.1, sine amplitude 0.01, alt 1.1 ± 0.01 starting +, ramp slope 1e-4, sc = amplitude 0.1,
  of = level 2.2): max |x_raw − x_expected| = **4.441e-16** over all 18 inputs.
- Roof: least-squares fit (sin, cos, constant) over rows ≥ 700, compared with the analytic H(e^jw) of HP-A(48) → SS(10 or 20),
  exact √2 and π. Flat / ramp: max |roof| rows ≥ 700. Alt: amplitude of the alternating component.
- Trace: max |out − article model out| over rows ≥ 700, per sine; model = library conventions (window history = first Roof,
  fallback 0.5, final SS seeded at the first Stoc), exact π; gate = model (HH − LL)/0.01 ≥ 0.01.
- Bound: min / max of raw Stoc over every row of all 8 base inputs.
- Invariance: max |out(sc or of) − out(s)| rows ≥ 700, 5 sines.
- IMP (own-model replay): same model with Zorro `PI` = float32(3.14159); NCL with 0.707 / 1.414 / 3.14159 built exactly and
  Zorro `PI` in the degree conversions (O_NCL); NCZ zero final seed; NCW window 21; NCA final a1 + 1e-3; NCP HP 40; NC1 L 22;
  NCS window 21, scale 100.

## Results (b)

**Real variants: all PASS.**

| Variant | flat | ramp res | alt gain | Roof gain max | Roof phase max (rad) | trace max (T = 100) | gated | Stoc min / max | invariance | IMP |
|---|---|---|---|---|---|---|---|---|---|---|
| L14 | 0 | 0 | 0 | 5.278e-07 | 1.328e-06 | 3.875e-06 | 0 | 0.0 / 1.0 | 3.810e-13 | 5.551e-16 |
| L20 | 0 | 0 | 0 | 5.278e-07 | 1.328e-06 | 3.257e-06 | 0 | 0.0 / 1.0 | 2.560e-13 | 5.551e-16 |
| L30 | 0 | 0 | 0 | 5.278e-07 | 1.328e-06 | 2.467e-06 | 0 | 0.0 / 1.0 | 1.320e-13 | 5.551e-16 |
| S20 | 0 | 0 | 0 | 4.409e-07 | 1.567e-06 | 2.301e-06 | 0 | 0.0 / 1.0 | 1.260e-13 | 5.551e-16 |

Trace per T (5, 10, 20, 40, 100): L14 3.279e-07, 8.784e-07, 1.065e-06, 1.730e-06, 3.875e-06; L20 3.279e-07, 8.784e-07,
8.398e-07, 1.451e-06, 3.257e-06; L30 3.279e-07, 8.784e-07, 8.398e-07, 8.661e-07, 2.467e-06; S20 1.082e-07, 2.411e-07,
1.005e-06, 1.667e-06, 2.301e-06. These equal the pre-run `PI`-gap floors (spec [floor]) to the printed digits: Zorro vs article =
the `PI` gap, nothing else. Floor guard: trace ≤ 5e-6 (largest 3.875e-06), gain ≤ 3e-6, phase ≤ 3e-6: all hold.

**Controls: every one detected on its required kind.**

| Control | Required | Measured (b) | Predicted FAIL rows |
|---|---|---|---|
| NCW | trace | trace 3.279e-07, 8.784e-07, 8.398e-07, **6.207e-02, 8.054e-02** | 2 (trace T = 40, 100) |
| NCA | trace | trace 3.778e-04, 7.951e-04, 3.855e-04, 3.272e-04, 3.438e-04 | 5 (trace) |
| NCP | gain, phase, trace | gain 3.981e-04, 5.929e-03, 2.987e-02, 7.543e-02, 7.309e-02; phase 2.542e-02, 5.575e-02, 1.062e-01, 1.662e-01, 1.634e-01; trace 7.338e-03 … 4.582e-01 | 15 (5 gain, 5 phase, 5 trace) |
| NC1 | trace | trace 3.279e-07, 8.784e-07, 8.398e-07, **1.268e-01, 1.561e-01** | 2 (trace T = 40, 100) |
| NCS | trace | trace 6.380e+01, 8.374e+01, 9.734e+01, 1.016e+02, 1.019e+02 | 5 (trace) |

All other control rows (flat, ramp residual, alt gain, bound, and NCW / NCA / NC1 gain and phase) PASS.
**Predicted control FAIL rows: 29.** The alt phase is SKIP for every variant that exports Roof (10 rows).

**INFO variants (never PASS / FAIL):** NCL gain 6.353e-05, 9.931e-05, 5.421e-06, 5.705e-05, 6.563e-05; phase 1.308e-04 …
2.500e-04; trace 6.170e-05 … 6.126e-04 (= spec NCL effects). NCZ = the real L20 values from row 700 on (start-up only, M-5).

**IMP:** must_pass 11/11 at ≤ 8.9e-16 (NCS 8.882e-16, all others ≤ 5.551e-16); must_fail L20 vs NCA model 7.942e-04 (T = 10),
NCS vs L20 article model 1.019e+02: both fail as required.

**Start-up (INFO):** L20 s20 rows 0–3 out 0.5, 0.56329862, 0.69989999, 0.83205974; Stoc 0.5, 1, 1, 1 (finding 7: 0.5,
0.5632987004, 0.6999002013, 0.8320600073; difference = `PI` gap). Flat Stoc = 0.5 on every row (fallback fires, M-6).

## Prediction for the checker

**VERDICT PASS.** 84/84 real checks PASS; 5/5 controls detected on every required kind (29 FAIL rows); 10 alt-phase SKIP;
0 gated rows; IMP 11/11 must_pass + 2/2 must_fail; floor 20/20. Any disagreement with the checker, row by row, is a finding to
explain before the result is accepted.
