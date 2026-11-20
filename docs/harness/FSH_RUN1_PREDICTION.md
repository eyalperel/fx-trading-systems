# FSH run 1 — planning-chat prediction (written BEFORE the checker)

**Date:** 2026-11-20. **Spec:** `analysis/harness/specs/FSH_ArticleFidelity.toml` (pre-registered `258b24a`, Amendment 1 `cb93b65`).
**Raw file:** `C:/Zorro/Data/GEN_FSH_raw.csv`, sha256 `8b8b61a0d1357da6277df9f18e8c01c0a1ce4870ec86cbd9b30d475f93f9857a`, 3001 lines,
376 columns. Zorro window (user, 2026-11-20): "GEN_FSH_FisherTransform compiling...", "Warning 047: EUR/USD first bar on 2008-01-07"
(harmless, gotchas 9d.7), "Test: GEN_FSH_FisherTransform EUR/USD 2008..2024", "FSH batch complete: 3000 rows written". No `Error` line.
Zorro restarted before the run (first run of this script).
**Back-check:** `docs/harness/FSH_RUN1_BACKCHECK.py` (own model `docs/harness/FISHER_REVIEW_MODEL.py`; independent of
`analysis/harness`). Trace and start-up compare with the model fed inputs **rebuilt from integers** (LRS A2.3 lesson); IMP feeds the
model the exported %.15f x, as the checker's IMP does.
Labels: (a) source states, (b) measured here, (c) inference.

## Prediction

**VERDICT: PASS.** 56 / 56 real checks PASS; 7 / 7 controls detected; IMP 10 / 10 must_pass + 2 / 2 must_fail fire; 0 gated rows.

## Real variants FR10, FR20 (b): Zorro vs the model, rows >= W = 700

| Kind | FR10 max | FR20 max | Tolerance |
|---|---|---|---|
| input guard (x vs integers) | 4.440892098500626e-16 (all inputs) | same | 1e-12 |
| trace raw (T5..T100) | 4.996004e-16 | 4.996004e-16 | 1e-9 |
| trace v1 | 5.551115e-16 | 5.551115e-16 | 1e-9 |
| trace out (Fish) | 8.881784e-16 (T40, T100) | 8.881784e-16 | 1e-9 |
| bound raw / v1 / out (excess over the bound) | 0 / 0 / 0 | 0 / 0 / 0 | 1e-12 / 1e-12 / ln(1999)·1e-12 |
| ramp_exact raw ±1, v1 ±.999, out vs model (ramp, rampdn) | 0 (all six) | 0 (all six) | 1e-12 |
| trigger trig[n] = out[n-1], all base inputs | 0 (bit-exact) | 0 | 0 |
| invariance scale10 / offset | 2.656542e-12 / 5.319301e-12 | 5.320189e-13 / 1.056932e-12 | 1e-9 |
| flat_zero raw, v1, out | 0 | 0 | 1e-12 |
| gated rows (range g = 0.01, clamp g2 = 1e-6, model) | 0 | 0 | — |
| start-up INFO, out rows < W, T5..T100 | <= 8.882e-16 | <= 8.882e-16 | INFO |

(b) **Zorro equals the source model to rounding (<= 8.9e-16) on every exported stage, start-up included.** No `PI`, no float32
literal in the corrected code. (b) On both ramps |out| = ln(1999) exactly (bound excess 0.0): the bound is attained in float64 (stage 1
report §4). (b) Start-up also agrees to rounding, i.e. Zorro pads the window with x[0] as the model assumes (9d.6) and `series(0, 2)`
starts Value1 and Fish at 0 — confirmed in a run for this indicator; still INFO (F-5, the source defines no start-up).

## Controls vs the FR10 model (b): best ratio per kind (value / tolerance), FAIL rows

| Control | trace | bound | ramp_exact | flat_zero | FAIL rows (of its checks) |
|---|---|---|---|---|---|
| NCW (.331) | 1.3e9 | 0 | 0 | 0 | 10 of 26 |
| NCC (clamp set .99) | 2.31e9 | 0 | 2.31e12 | 0 | 8 of 26 |
| NCK (log gain .25) | 3.8e9 | 0 | 3.8e12 | 0 | 7 of 26 |
| NCL (window 11) | 1.21e9 | 0 | 0 | 0 | 9 of 26 |
| NC32 (float32 literals) | 1.29e4 | 1.69e6 | 1.29e7 | 0 | 16 of 26 |
| NCS (superseded, instance 1) | 8.54e9 | 0 | 9.2e12 | 1.06e12 | 8 of 9 |
| NCT (superseded, instance 2) | 8.54e9 | 0 | 9.2e12 | 9.88e11 | 8 of 9 |

Total control FAIL rows: **66**. Every [detect.required] kind fires at >= 10x: NCW trace; NCC trace + ramp_exact; NCK trace + ramp_exact;
NCL trace (T = 20 / 40 / 100 only; T = 5 / 10 PASS, finding: invisible at T <= L); NC32 trace + bound + ramp_exact; NCS / NCT trace +
ramp_exact + flat_zero. (c) The checker's per-row counts may group rows differently (e.g. bounds over the invariance copies); the
verdict and the per-kind detection are the prediction, the row counts are for comparison.

Each control also equals ITS OWN model to rounding (all rows, every output): NCW 8.882e-16, NCC 8.882e-16, NCK 5.551e-16, NCL
8.882e-16, NC32 8.882e-16; NCS / NCT (shared-statics replay in the generator's call order) 5.551e-16 / 5.551e-16. So the superseded
statics started at 0 (fresh load) and the replay order is the script's.

**NCB (INFO, the book):** equals its own model to <= 8.882e-16 (trace). As expected it is NOT within the FR10 bounds / known answers:
v1 reaches .9999 (bound-v1 and exact-v1 excess 9.0e-4 over .999), |out| <= 4.951718775643 (bound-out excess -2.648684). Reported,
never PASS/FAIL.

## IMP (b): model fed the exported x, rows >= W

| Variant | must_pass value | Variant | must_pass value |
|---|---|---|---|
| FR10 | 5.234035e-12 | NCK | 2.979672e-12 |
| FR20 | 1.474376e-12 | NCL | 3.629763e-12 |
| NCB | 2.979672e-12 | NC32 | 5.234035e-12 |
| NCW | 5.748291e-12 | NCS (shared replay) | 1.319833e-12 |
| NCC | 3.518075e-12 | NCT (shared replay) | 1.487477e-12 |

All <= 1e-9. must_fail: FR10 vs the NCW model **1.304495832918544**; NCS vs the FR10 model **9.198226649480118** (both fire).
(b) FR10's 5.234035e-12 equals stage 1's pre-run IMP estimate (report §5, 5.234e-12): the IMP residual is the %.15f rounding of x
divided by the range, as predicted; the Zorro-vs-model trace (with integer-built inputs) is ~4 orders smaller.

## Floor (b)

Measured trace floor (Zorro vs model) 8.9e-16; x10 = 8.9e-15 <= 1e-9. The stage 1 worst-case estimate (1.064e-11, x perturbed by 1
ulp) was conservative by ~4 orders: Zorro's `sin` / `log` agree with Python's here. Floor guard (tol/10 = 1e-10): every real trace row
passes it.

## For the second read

Compare with the checker: verdict; real-check count 56 and FAIL 0; per-kind maxima above; control detection per required kind and the
FAIL-row counts (66 total, per control above); IMP must_pass values (to ~1e-15) and both must_fail values (to the printed digits);
gated rows 0. Any disagreement is a finding to explain before the result is accepted.
