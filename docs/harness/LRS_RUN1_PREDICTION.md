# LRS run 1 — planning-chat back-check and prediction (written BEFORE the checker)

**Date:** 2026-11-19. **Spec:** `analysis/harness/specs/LRSI_ArticleFidelity.toml` (pre-registered `824a3cc`, Amendment 1 `b85cfd9`).
**Script:** `strategies/tests/GEN_LRS_LaguerreRSI.c`, sha256 `ef8255712751b0f59db1ce0edcd83052ce7dac80e2c2694b315b453e0d46b443`.
**Run:** Zorro restarted, one [Test] click, 2026-11-19 16:27. Message window: `Warning 047: EUR/USD first bar on 2008-01-07`
(harmless, gotchas 9d.7), `LRS batch complete: 3000 rows written`, **no line starting with `Error`** (pass item 4).
**Raw:** `C:/Zorro/Data/GEN_LRS_raw.csv`, 17190003 bytes, 3001 lines, 319 columns, sha256
`97125fecc4afae0e83219a1ea364e021ea713ed239621b06153d684eff1c2e3d`.
**Method:** `docs/harness/LRS_RUN1_BACKCHECK.py` (this commit): own float64 models (book term order, written in the planning chat,
not imported from `reference.py`), own measurements (least-squares sine / alt fit on rows >= 700, ramp lag = mean of the last 100
ramp rows, trace / start-up = max |out - model| on rows >= 700 / < 700, gate = model (CU + CD)/amplitude >= 0.01), independent of
`checker.py`. Labels: (a) source states, (b) measured/computed, (c) inference.

## Prediction

**VERDICT: PASS.**

| Item | Prediction (b) |
|---|---|
| Input guard | max \|x - recomputed from integers\| = 4.441e-16 (tol 1e-12): PASS |
| 1. Real checks | **129 / 129 PASS** (3 variants x 43) |
| 2. Controls | all 4 detected on every required kind (below) |
| 3. Guards / ERROR / NaN | none; NCH and NCT INFO; NCS:flat and NCT:flat have no column |
| 4. `Error` lines | none (message window above) |
| 5. Variant count | 9 (3 real + 4 controls + 2 info) |
| 6. IMP | must_pass 9 / 9 (max 8.539e-13, NC25); must_fail G05 vs NCG model = 0.0008469690517214912: fires |
| 7. Floor guard | every real quantity <= tol / 10 (largest ratio: invariance 1.051e-12 vs 1e-10) |

**Real variants, max |diff| per kind** (n = number of checks):

| Kind (tol) | G05 | G07 | G08 |
|---|---|---|---|
| gain, l0 + l3, 5 sines + alt (3e-5), n = 12 | 1.043e-12 | 3.732e-13 | 6.189e-13 |
| phase, l0 + l3, 5 sines + alt (3e-5 rad), n = 12 | 1.492e-13 | 3.975e-13 | 3.570e-13 |
| flat, l0 + l3 (1e-9), n = 2 | 0 | 1.110e-15 | 1.998e-15 |
| ramp lag, l0 + l3 (1e-3), n = 2 | 1.030e-12 | 2.299e-12 | 1.130e-12 |
| trace, 5 sines (3e-5) | 8.252e-13 | 2.912e-13 | 2.552e-13 |
| startup, 5 sines (1e-6) | 5.992e-13 | 2.193e-13 | 1.857e-13 |
| bound [0, 1] (1e-12) | 0 | 0 | 0 |
| ramp_exact, ramp = 1 / rampdn = 0 (1e-12), n = 2 | 0 | 0 | 0 |
| invariance sc / of (1e-9), n = 2 | 1.051e-12 | 3.640e-13 | 3.010e-13 |

Gated rows: 0 (model margin >= 0.0756, spec finding 3).

(b) The residuals are ~1e-12, not ~1e-15 as in MST: the raw values are `%.15f` (absolute resolution 1e-15 on x ~ 1.1), and the
normalisation CU / (CU + CD) divides that rounding by CU + CD (down to ~7.6e-4 at T = 100), i.e. ~1e-15 / 7.6e-4 ~ 1e-12. The largest
trace / startup / IMP residuals are at T = 100, where CU + CD is smallest. (c) Inference from the pattern, not a separate test.

**Controls — every FAIL row predicted** (60 rows: NCG 32, NC25 22, NCP 5, NCS 1). Required kinds ([detect.required]):

| Control | Required | Predicted FAIL rows by kind |
|---|---|---|
| NCG | gain, phase, trace, startup | gain 10 (l0 + l3: T = 5, 10, 20, 40 + alt; T = 100 below tol), phase 10 (T = 5..100), ramp lag 2 (not required, 4.0x), trace 5, startup 5 |
| NC25 | gain, phase, lag, trace, startup | l3 only: gain 6 (5 sines + alt), phase 5, ramp lag 1; out: trace 5, startup 5. l0 unchanged (0 FAIL) |
| NCP | startup | startup 5 (0.597963394998609, 0.93928219261069, 0.9233174011464161, 0.6160813372907101, 0.2142857142857142) |
| NCS | startup | startup on s5 only: 0.597963394998609; every other NCS / NCT row <= 8.3e-13 |

Row values (full precision) are listed by `LRS_RUN1_BACKCHECK.py` (section "Control FAIL rows"); selected:
NCG trace T = 100 0.0008469690517224349 (spec 0.0008469690514941175), NCG startup T = 20 0.004842369898410526 (spec
0.0048423698983621755), NC25 l3 ramp lag 2.9999999999989724 (10 vs 7), NC25 l3 alt gain 0.3209876543206749, NCS / NCP s5 startup
0.597963394998609 (spec 0.5979633949986088).
(c) Row COUNTS assume the checker applies to controls the same check list as to real variants (no invariance; NCS / NCT: out checks
only). The firm prediction is the verdict and the required kinds; a different count with the same verdict is to be explained, not a FAIL.

NCH (info): no row would FAIL (identical to G05 on every checked row: the 0.5 initial hold never fires). NCT (info): <= 8.3e-13
from the G05 model on every row.

**IMP must_pass** (own model, rows >= W; l0 / l3 / den on every base input, out on sines + copies, gated): G05 8.508e-13,
G07 4.778e-13, G08 3.765e-13, NCG 6.630e-13, NC25 8.539e-13, NCP 8.252e-13, NCH 8.252e-13, NCS 8.252e-13, NCT 8.252e-13.
