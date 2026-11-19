# RFX run 1 — planning-chat back-check and prediction (first reading)

**Date:** 2026-11-18. **Written BEFORE the checker is run** (HARNESS_DESIGN §4, every run read twice).
**Run:** `strategies/tests/GEN_RFX_Reflex.c` (sha256 `bbf9680c…83cd`, committed `353c94f`), one [Test] click on a fresh
load. Zorro window: `Warning 047: EUR/USD first bar on 2008-01-07` (harmless, gotchas 9d.7), no line starting with `Error`,
`RFX batch complete: 3000 rows written`.
**Raw:** `C:/Zorro/Data/GEN_RFX_raw.csv`, 3000 rows + header, 340 columns,
sha256 `f1ab5494281e531bd971ea3fcbd22a538cb88df9d577dcc2dba9c3b0b98d1d75`.
**Method (b):** own Python code written in the planning chat, independent of `checker.py` / `reference.py`: article models
(exact sqrt2/pi, real half length) for the expected values; own-model replays (Zorro float32 `PI`, each control's own
coefficients; NCS / NCT = one float32-weight MS shared by 16 calls per bar, L20 then L14, inputs in column order) on the
EXPORTED x columns; least-squares sine fit over rows >= 700; trace gate on the model MS. Labels: (b) measured here,
(c) inference.

## Observations on the raw file (b)

- Input guard: max |x - exact| = 4.4e-16 (tol 1e-12), all 18 input columns.
- Values are written as `%.15f`: absolute resolution 1e-15 (ramp residual reads exactly 1.0e-15). Far below every tolerance;
  (c) `%.3e` / `%.17g` would be needed only if a quantity ever approaches 1e-14.
- Gated rows: 0 in every variant (gate margin as predicted, finding 7).

## Real variants — predicted 84/84 PASS

| Variant | Sum gain | Sum phase (rad) | trace | invariance | resid | flat | max \|r\| | IMP (own model) |
|---|---|---|---|---|---|---|---|---|
| L14 | 4.660e-07 | 9.037e-07 | 1.242e-06 | 2.066e-12 | 0 | 0 | 5.000000000000001 | 2.5e-12 |
| L20 | 5.609e-07 | 1.103e-06 | 1.570e-06 | 1.437e-12 | 1.0e-15 | 0 | 5.000000000000000 | 1.5e-12 |
| L21 | 5.296e-07 | 1.101e-06 | 1.554e-06 | 1.598e-12 | 1.0e-15 | 0 | 5.000000000000000 | 1.2e-12 |
| L30 | 5.380e-07 | 1.003e-06 | 1.435e-06 | 2.197e-12 | 1.0e-15 | 0 | 5.000000000000000 | 2.2e-12 |
| tol | 3e-5 | 3e-5 | 3e-5 | 1e-9 | 1e-9 | 1e-9 | 5(1+1e-12) | 1e-9 |

Alt gain: fitted 0 (|diff| = the expected <= 1.3e-17); alt phase SKIP in all 11 sum-exporting variants.
**Floor guard (pass item 7):** every real value <= tol/10 (gain 3e-6, phase 3e-6, trace 3e-6). The tightest, trace 1.570e-6
(L20), equals the planning chat's pre-run `PI`-gap floor to 4 digits: (b) the Zorro-side floor IS the `PI` gap.

## Controls — predicted FAIL rows per kind (tolerances as the spec)

| Control | gain (of 5) | alt gain | phase (of 5) | trace (of 5) | bound | flat / resid | Total FAIL rows | Required kinds detected |
|---|---|---|---|---|---|---|---|---|
| NCA | 3 (max 6.025e-4) | 0 | 4 (2.321e-3) | 4 (3.305e-3) | 0 | 0 | 11 | gain, phase, trace ✔ |
| NC2 | 5 (1.710e-1) | 0 | 5 (1.858e-1) | 5 (2.647e-1) | 0 | 0 | 15 | ✔ |
| NC1 | 5 (2.399e-1) | 0 | 5 (1.323) | 5 (1.742) | 0 | 0 | 15 | ✔ |
| NCH | 4 (3.140e-2) | 0 | 5 (6.664e-2) | 5 (9.348e-2) | 0 | 0 | 14 | ✔ |
| NCK | 5 (5.085e-2) | 0 | 0 (1.103e-6) | 0 (1.570e-6) | 0 | 0 | 5 | gain ✔ |
| NCW | 0 (5.6e-7) | 0 | 0 (1.1e-6) | 5 (5.096e-3) | 0 (4.9386) | 0 | 5 | trace ✔ |
| NCS | — | — | — | 5 (1.348) | **1** (5.000000055879355) | — | 6 | trace ✔ (+ bound, not required; O_BOUND_FLOAT32) |
| NCT | — | — | — | 5 (1.878) | 0 (3.9208) | — | 5 | trace ✔ |

NCL (INFO, never PASS/FAIL): gain 1.055e-4, phase 2.075e-4, trace 2.954e-4 (spec O_NCL: 1.0553e-4 / 2.0749e-4 / 2.9544e-4).

## IMP

- must_pass (13): own-model replay max |Zorro - replay| over rows >= 700: real <= 2.5e-12; controls <= 2.8e-12
  (NCS 2.8e-13, NCT 2.4e-13 with the shared-MS replay). All << 1e-9.
- must_fail (2): NCS vs L20 article 1.347901 (spec 1.347900877); L20 vs the NCW model > 1e-9 (planning chat measured
  9.15e-4 on s20 alone; spec fire test 5.096e-3 over the sines). Both fire.

## Prediction

**Run 1 PASS**: 84/84 real checks; all 8 controls fail on every required kind (FAIL rows: NCA 11, NC2 15, NC1 15, NCH 14,
NCK 5, NCW 5, NCS 6 incl. 1 bound, NCT 5 = 76); 0 guard, 0 ERROR, 0 gated rows; IMP 13/13 must_pass, 2/2 must_fail; floor
guard holds (trace 1.570e-6 <= 3e-6). (c) A difference from the checker on any row is a finding to explain before the
result is accepted.
