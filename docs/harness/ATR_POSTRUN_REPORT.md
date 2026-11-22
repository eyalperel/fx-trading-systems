# ATR run 1 — post-run report (checker, read 2 of 2, comparison with the prediction, Amendment 2)

Claude Code (Sonnet 5.5), 2026-11-22. Branch `harness-atr` at `348838b`. Brief: `docs/harness/ATR_POSTRUN_PROMPT.md`. Labels: (b) measured, (c) inference.
The prediction files (`ATR_RUN1_PREDICTION.md`, `ATR_RUN1_BACKCHECK.py`, `_output.txt`) were read, not edited. Nothing committed, Zorro not run.

## 1. Checker

Raw `C:/Zorro/Data/GEN_ATR_raw_run1.csv` sha256 verified before the run (sha256sum): `4f22e7c1834f1c72637f89a733c8e5e3557b76d1a1f54e2c791e32a03f22a441`, equal to the brief.
Command: `python analysis/harness/checker.py analysis/harness/specs/ATR_MT4Fidelity.toml C:/Zorro/Data/GEN_ATR_raw_run1.csv` (exit 0).
Results file `analysis/harness/results/ATR_MT4Fidelity_20261122.csv` (new, no earlier file existed), sha256 `a1d08f2acd0e649e10405fc00535eada4e4e99f5cc5bab8568989474c2fda362`;
367 data rows: 90 real, 260 neg_control, 11 imp, 6 floor.

| | ATR_MT4Fidelity |
|---|---|
| Verdict | **PASS** |
| Variants run | 9 (2 real AT14 / AT20 + 7 controls) |
| Real checks | 90 PASS / 0 FAIL / 0 ERROR (AT14 45, AT20 45) |
| Controls detected (required kinds, >= 10x) | 7 / 7 |
| Control FAIL rows | 142 of 260 (NCW 21, NC0 21, NCWi 11, NCR 26, NCZ 15, NCS 24, NCS2 24) |
| IMP must_pass | 9 / 9, worst AT14 / AT20 1.3808398868775384e-15 |
| IMP must_fail | AT14 vs Wilder model 0.0018306291425547131; NCS vs AT14 model 0.009044766946307133 |
| Floor rows | 6 / 6 PASS |
| Gated rows / INFO inputs / guards fired | 0 / 0 / none |
| Lint L_NO_STATIC | ATR.c 0 static tokens, PASS |

## 2. Comparison with the prediction

| Item | Prediction | Checker | Result |
|---|---|---|---|
| Verdict | PASS | PASS | AGREE |
| Real checks / PASS | 90 / 90 (AT14 45, AT20 45; trace 32, bound 2 + window_hull 1, known_value 6, equivariance 4) | 90 / 90, same per-kind counts | AGREE |
| Trace max AT14 | 5.000e-16 (atr:s10B) | 5.000e-16 (atr s10B, n=890) | AGREE |
| Trace max AT20 | 4.996e-16 (atr:s5B) | 4.996e-16 (atr s5, n=2632; s5B also 4.996e-16) | AGREE on value; location is a tie at the printed precision (see D1) |
| Bound tr >= H - L / atr >= 0 | 6.695e-17 (allowance 1e-15) / min 0 | min -6.695e-17 (abs_diff 6.695e-17) / min 0 | AGREE |
| window_hull / known_value | 0 / 0 | 0 / 0 | AGREE |
| Equivariance max | 6.002e-15 (tr:sc) | 6.002e-15 (tr sc40B vs 10 x s40B, n=920), both variants | AGREE |
| Floor | 5.000e-16 (Zorro vs integer-built model) | trace 5.000e-16 / 4.996e-16, equivariance 6.002e-15, known_value 0, tol 1e-13 | AGREE (convention, D2) |
| Control FAIL counts per kind | NCW 15/0/1/5; NC0 15/0/1/5; NCWi 10/0/1/0; NCR 24/0/0/2; NCZ 15/0/0/0; NCS 16/1/1/6; NCS2 16/1/1/6 (trace/bound/hull/known) | identical for all 7 (recomputed from the CSV, and the footer) | AGREE |
| Control totals | 21 / 21 / 11 / 26 / 15 / 24 / 24 = 142 | same | AGREE |
| Control max ratios | as the prediction table | NCW 7.673e9 / 3.833e12 / 4.0e8; NC0 2.738e8 / 3.506e10 / 2.857e7; NCWi 1.87e8 / 6.098e10; NCR 1.176e10 / 1.0e8; NCZ 9.711e9; NCS 9.045e9 / 1.572e12 / 5.205e12 / 4.49e9; NCS2 9.259e9 / 1.747e12 / 5.464e12 / 4.008e9; non-NCS bound rows 6.695e-2 | AGREE |
| IMP AT14 / AT20 | 1.380839886877538e-15 | 1.3808398868775384e-15 | AGREE (prediction printed 16 digits) |
| IMP NCW / NC0 / NCWi / NCZ | 1.198693921899974e-15 | 1.1986939218999737e-15 | AGREE |
| IMP NCR | 9.322512380116610e-16 | 9.32251238011661e-16 | AGREE (identical) |
| IMP NCS | 2.694242398626479e-15 | 2.6942423986264785e-15 | AGREE |
| IMP NCS2 | 2.620082970028470e-15 | 2.62008297002847e-15 | AGREE (identical) |
| IMP must_fail AT14 vs Wilder | 1.830629142554713e-03 | 0.0018306291425547131 | AGREE |
| IMP must_fail NCS vs AT14 | 9.044766946307133e-03 | 0.009044766946307133 | AGREE (identical) |
| Gated rows | 0 | 0 | AGREE |
| NCS order replay | equals raw to 5.000e-16 | IMP replay <= 2.7e-15 on the exported inputs | AGREE (different inputs, both ulp) |

Differences (none above ulp level, none changes a verdict, detection or margin):
- **D1, AT20 trace max location.** Prediction names atr s5B, checker atr s5. Both rows print 4.996e-16 (ratio 4.996e-4); the checker keeps the first of equal printed maxima, the prediction the last. Same value. (c) Last-bit order not examined.
- **D2, floor convention.** The prediction's floor line is the trace quantity only; the checker lists trace / equivariance / known_value separately, against the floor tolerance 1e-13. The prediction's equivariance 6.002e-15 is the same number as the checker's equivariance floor row. Not a numeric difference.
- **D3, counting convention.** Prediction counts checks per (kind, column, input); the checker lists the control bound kind as two rows (atr >= 0, tr >= H - L) and the hull as one. Totals are identical (only NCS / NCS2 fail the atr >= 0 row).
- **D4, digits.** Spec's own must_fail values (1.8306291425544303e-03, 9.044766946306704e-03, integer-built inputs) vs the checker's (exported %.15f inputs): 2.8e-16 / 4.3e-16 absolute, as the prediction already stated.

No STOP condition hit.

## 3. Amendment 2

Appended as `[amendment_2]` at the end of `analysis/harness/specs/ATR_MT4Fidelity.toml` (date 2026-11-22, base 348838b, before_run = false, after_run = true,
criterion_changed = false; A2.1 run record, A2.2 read-twice comparison, A2.3 findings, A2.4 variants and rerun note). 13 lines added, text above unchanged; no
criterion, tolerance, table, floor, effect or variant changed. The spec still parses (tomllib), and a rerun of the checker into a temp directory still gives PASS 90/0/0
with the results CSV body identical.

A2.3 observations: (1) Zorro equals the MT4 ATR source model to rounding, start-up included; known answers exact. (2) Thinnest required margins NCWi trace 1.87e8 x and NC0 known_value 2.857e7 x. (3) NCS / NCS2 replay <= 2.7e-15. (4) `tr - (H - L)` min is -6.695e-17 on band inputs, inside the pre-registered 1e-15 allowance. Nothing else observed.

## 4. Full checker console output

```
INFO D2 floor trace: floor 8.882e-16 x10 = 8.882e-15 <= tolerance 1.000e-12 -> window ok
INFO D2 floor equivariance: floor 1.776e-15 x10 = 1.776e-14 <= tolerance 1.000e-12 -> window ok
INFO D2 floor known_value: floor 4.407e-17 x10 = 4.407e-16 <= tolerance 1.000e-12 -> window ok
INFO D2 margin NCW: error/tolerance trace 7.67e+09x, bound 0x, window_hull 3.83e+12x, known_value 4e+08x -> 10x margin met (window_hull)
INFO D2 margin NC0: error/tolerance trace 2.74e+08x, bound 0x, window_hull 3.51e+10x, known_value 2.86e+07x -> 10x margin met (window_hull)
INFO D2 margin NCWi: error/tolerance trace 1.87e+08x, bound 0x, window_hull 6.1e+10x, known_value 4.41e-05x -> 10x margin met (window_hull)
INFO D2 margin NCR: error/tolerance trace 1.18e+10x, bound 0x, window_hull 0x, known_value 1e+08x -> 10x margin met (trace)
INFO D2 margin NCZ: error/tolerance trace 9.71e+09x, bound 0x, window_hull 0x, known_value 4.41e-05x -> 10x margin met (trace)
INFO D2 margin NCS: error/tolerance trace 9.04e+09x, bound 1.57e+12x, window_hull 5.2e+12x, known_value 4.49e+09x -> 10x margin met (window_hull)
INFO D2 margin NCS2: error/tolerance trace 9.26e+09x, bound 1.75e+12x, window_hull 5.46e+12x, known_value 4.01e+09x -> 10x margin met (window_hull)
VERDICT: PASS  (real checks PASS=90 FAIL=0 ERROR=0)
results: C:\Users\eyalp\Documents\fx-trading-systems\analysis\harness\results\ATR_MT4Fidelity_20261122.csv
```

## 5. Test suite

`bash analysis/harness/run_tests.sh` (Claude Code shell): **TOTAL 950  PASS 950  FAIL 0  ERROR 0  SKIP 0**. No ERROR or FAIL, so no rerun. (One run; the known intermittent `test_checker_amend1.test_cli` MemoryError did not appear.) Count equals the 950 recorded in Amendment 1; the spec edit added no tests. The commit-message count must come from the user's Git Bash run.
