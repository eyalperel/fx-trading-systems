# MAF run 1 — planning-chat prediction (written BEFORE the checker)

**Date:** 2026-11-21. **Code:** `d0c9a23` (branch `harness-mama-frama`). **Raw files (run 1, copies kept locally, gitignored):**
`C:/Zorro/Data/GEN_MAM_raw_run1.csv` sha256 `7c86c37026f01871f590449dcbacef31edc576d30381bbda27cf8e138945471e` (3000 rows, 304 columns);
`C:/Zorro/Data/GEN_FRA_raw_run1.csv` sha256 `12c0e3bf87f7ab0af20454ae76503a8733d47dc67c60b32bf04c44871c2f1d27` (3000 rows, 305 columns).
Zorro window, both runs (user, screenshots): no line starting with `Error`; `Warning 047: EUR/USD first bar on 2008-01-07` (harmless, gotchas
9d.7); "MAM / FRA batch complete: 3000 rows written". Zorro restarted before each script. No NaN / inf in either file.
**Back-check:** `docs/harness/MAF_RUN1_BACKCHECK.py` (planning chat; independent of `reference.py` / `checker.py`: review models with the corrected
code's operation order; inputs rebuilt from integers as the generator does; full output in `docs/harness/MAF_RUN1_BACKCHECK_output.txt`).
Labels: (b) computed here, (c) inference.

## Verdict predicted: **PASS / PASS**

| | MAMA_ArticleFidelity | FRAMA_ArticleFidelity |
|---|---|---|
| Real checks | **66 / 66 PASS** (33 per variant) | **98 / 98 PASS** (49 per variant) |
| Controls detected | 7 / 7 (NCB, NCH, NCF, NC32, NCP, NCS, NCS2) | 6 / 6 (NCE, NCN, NC32, NCT, NCS, NCS2) |
| IMP must_pass (checked pairs) | worst MA05 s100 alpha 1.737e-11 (ratio 1.7e-2); MA03 s100 phase 1.124e-10 (1.1e-2) | worst FR16 s100 alpha 1.934e-12 (1.9e-2) |
| IMP must_fail | MA05 with the NCH model 0.1261940444433307 | FR16 with the NCE model 7.988543995718911e-4 |
| Gated / INFO | INFO traces: flat, ramp, s5 (except s5:period, checked) | INFO traces: dim, alpha on point flat |

## (b) Inputs

Rebuilt inputs equal the exported x / xh / xl to <= 4.4e-16 (the %.15f export resolution) on every input of both files.

## (b) MAMA

- **Trace vs the source model (all rows, from row 1):** max over checked pairs, both variants: mama 1.3e-15, fama 1.8e-15, alpha 1.1e-15,
  Period 3.6e-14, Phase 7.8e-14 (tol 1e-9 / 1e-8: ~1e5 x margin). **Zorro equals the source model to rounding, start-up included; no `PI` gap**
  (S1 confirmed in a run). INFO inputs agree to the same level here (<= 3.0e-14) because the model is fed the same integer-built inputs;
  their IMP (fed the exported x) shows the ill-conditioning: s5 Phase 180 degrees (a wrap flip), as rule 3 predicted.
- **Bounds:** alpha in [SL, FL] exactly on rows n >= 5 (MA05 [0.05, 0.5], MA03 [0.1, 0.3]); Period max 50.0 exactly. PASS.
- **Equivariance (s40, rows >= 1000):** max mama 1.9e-14, fama 1.5e-14, alpha 3.7e-13, Period 6.2e-12, Phase 5.3e-11. PASS.
- **Controls vs the MA05 model (best ratio to tol):** NCB s5:period 3.626e7 x; NCH s10:phase 1.262e7 x; NCF s40:fama 8.500e6 x; NC32 s5:period
  5.944e3 x and **Period max 50.000003725290505** (bound, 7.45e4 x: float32 .2 + .8 > 1); NCP s100:period 4.328e4 x; NCS / NCS2 mama / fama
  1.10-1.11 (price seed vs zero start). Own-model IMP of every control <= 2.1e-2 x tol on checked pairs.
- **NCS / NCS2 replay** (old file: shared `barCount`, counter 14 i + j + 1, float32 literals, Zorro `PI`, price seeds, series defaults): matches
  Zorro to <= 4.5e-14 on checked inputs; 5.0e-3 (s5) / 1.7e-4 (ramp) on INFO inputs (ill-conditioned, replayed on the exported x).

## (b) FRAMA

- **Trace (all rows):** every checked pair <= 8.9e-16 (out), 2.2e-15 (dim), 5.0e-16 (alpha) (tol 1e-10). Start-up included.
- **Bounds:** alpha [0.010051835744634, 1.0] (export rounding of exp(-4.6) = 0.010051835744633586); Dimen max 2.000000000000002 (FR16,
  inside the 1e-12 relative allowance); hull excess 0. PASS.
- **Known answers:** point ramp |out - x| 0 (both); band ramp lag 34.05274879968001 vs 34.05274879969143 (1.1e-11) / 17.27287888640001 vs
  17.27287888639891 (1.1e-12); point flat out = 1.1 exactly. PASS.
- **Equivariance (s40B, all rows):** <= 1.2e-14 (out), 5.8e-14 (dim), 6.4e-14 (alpha). PASS.
- **Controls vs the FR16 model:** NCE trace s100:alpha 7.99e6 x, lag 34.32483744584003 (2.7e5 x), alpha min 0.01 (bound); NCN trace s5:dim
  1.585e10 x, lag 30.80213538996035 (3.3e6 x); NC32 trace s100:alpha **76.3 x** (the thinnest margin; lag 2.6 x, not required); NCT trace
  s5:dim 1.0e10 x (bound: alpha min 0.0, INFO only as registered); NCS / NCS2 out 3.4e-3 (rampB) .. 0.297 (s5B), 0 on the point ramp (alpha = 1
  overwrites the shared state), hull excess 0.287, flat 0.230, band ramp lag 0 vs 34.05.
- **NCS / NCS2 replay** (one shared `fro_prev` / `fro_init`, 26 calls per bar in the generator's order flat, s5 .. s100, ramp, rampB .. s100B,
  then NCS2): matches Zorro to <= 1.0e-13 on every input.

## Disclosed while back-checking (prediction-side, before the checker)

My first NCS replay used the input order flat, ramp, s5 ...; it disagreed with Zorro by up to 0.30. The generator's order (ramp after the
sines, `GEN_FRA_FRAMA.c` lines 591-616) gives 1.0e-13. The error was in my replay, not in the run. (c) Lesson as FSH Amendment 2: a back-check
of a shared-state control must take the call order from the generated script, not from the input list.

## Read-twice comparison to make after the checker

Verdict and counts; every control's detected kinds and ratios above; IMP must_pass worst values and must_fail values at full precision; the
floor lines; NCS / NCS2 per-input values; bound values (NC32 Period 50.000003725290505, NCE / NCT alpha minima).
