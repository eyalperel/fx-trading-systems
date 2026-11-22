# ATR run 1 — planning-chat prediction (read 1 of 2, written before the checker)

2026-11-22, planning chat. HARNESS_DESIGN §4: the raw file is read by independent code BEFORE Claude Code's checker; the checker's result
is then compared with this file row by row. Labels: (a) source states, (b) measured here, (c) inference.

**Run:** `strategies/tests/GEN_ATR_MT4.c` (sha256 `02b6a636…c4eb`, committed `5c5d700`), one [Test] click, Zorro restarted first. Zorro window:
`GEN_ATR_MT4 compiling…`, `Warning 047: EUR/USD first bar on 2008-01-07` (harmless, 9d.7), `Test: GEN_ATR_MT4 EUR/USD 2008..2024`,
`ATR batch complete: 3000 rows written`; **no line starting with `Error`**.
**Raw:** `C:/Zorro/Data/GEN_ATR_raw.csv` copied to `GEN_ATR_raw_run1.csv` by the planning chat (byte-identical); sha256
`4f22e7c1834f1c72637f89a733c8e5e3557b76d1a1f54e2c791e32a03f22a441`; 3000 rows x 304 columns, every row complete, n = 0..2999.
**Code:** `docs/harness/ATR_RUN1_BACKCHECK.py` (models from the planning chat's `ATR_STAGE1_NUMBERS.py`, never `checker.py` /
`reference.py`; model inputs rebuilt from the spec's integers; NCS / NCS2 replayed in the generated order). Full output:
`docs/harness/ATR_RUN1_BACKCHECK_output.txt`.

## Predicted verdict: **PASS**

| Item | Prediction (b) |
|---|---|
| Input guard | max \|exported - integer-built\| 4.441e-16 <= 1e-12 |
| Real checks | **90 / 90 PASS** (AT14 45, AT20 45: trace 32, bound 2 + window_hull 1, known_value 6, equivariance 4) |
| Largest real values (AT14 / AT20) | trace 5.000e-16 / 4.996e-16 (atr:s10B / atr:s5B); bound tr >= H - L 6.695e-17 (allowance 1e-15); atr >= 0 and window_hull 0; known_value 0 (exact); equivariance 6.002e-15 (tr:sc) |
| Floor | Zorro vs the integer-built model, real variants, every column and input: 5.000e-16 (x10 = 5.0e-15 <= 1e-12) |
| Controls (vs the AT14 model) | all 7 detected on every `[detect.required]` kind; FAIL checks per kind below; **142 control FAIL checks** |
| IMP must_pass (own model fed the exported `%.15f` inputs) | AT14 / AT20 1.380839886877538e-15 (of40B:tr); NCW / NC0 / NCWi / NCZ 1.198693921899974e-15 (s20B:tr); NCR 9.322512380116610e-16 (s5B:tr); NCS 2.694242398626479e-15 (s5:atr); NCS2 2.620082970028470e-15 (s100B:atr): all <= 1e-12 |
| IMP must_fail | AT14 vs the Wilder (NCWi) model 1.830629142554713e-03; NCS vs the AT14 model 9.044766946307133e-03: both detected (spec: 1.8306291425544303e-03, 9.044766946306704e-03) |
| NCS order | the generated-order replay (integer-built inputs) equals the raw NCS / NCS2 columns to 5.000e-16 |

Controls, FAIL checks per kind (max ratio to the kind's tolerance):

| Control | trace | bound | window_hull | known_value | total | required (spec) |
|---|---|---|---|---|---|---|
| NCW | 15 (7.67e9) | 0 | 1 (3.83e12) | 5 (4.00e8) | 21 | trace, window_hull, known_value |
| NC0 | 15 (2.74e8) | 0 | 1 (3.51e10) | 5 (2.86e7) | 21 | trace, window_hull, known_value |
| NCWi | 10 (1.87e8) | 0 | 1 (6.10e10) | 0 | 11 | trace, window_hull |
| NCR | 24 (1.18e10) | 0 | 0 | 2 (1.00e8) | 26 | trace, known_value |
| NCZ | 15 (9.71e9) | 0 | 0 | 0 | 15 | trace |
| NCS | 16 (9.04e9) | 1 (1.57e12) | 1 (5.20e12) | 6 (4.49e9) | 24 | trace, bound, window_hull, known_value |
| NCS2 | 16 (9.26e9) | 1 (1.75e12) | 1 (5.46e12) | 6 (4.01e9) | 24 | trace, bound, window_hull, known_value |

(b) The blind inputs are as pre-registered: NCW / NC0 / NCZ blind on the point flat only (15 trace FAILs = atr on 15 inputs; tr unchanged);
NCWi on every constant-TR input (10 FAILs = atr on the 10 sine inputs); NCR on flat, flatB, rampB, rampdnB (24 = tr and atr on 12 inputs).
The bound row for the controls (other than NCS) sits at 6.69e-2 x its 1e-15 allowance: the `tr >= H - L` row of the band inputs, ulp level.

## Counting convention and disclosed error

(c) My counts are checks (one per (kind, column, input) as in the spec's pass condition), not data rows. If the checker counts a control's bound
kinds as two rows (atr >= 0, tr >= H - L) and the hull as a third, the totals above are unchanged (only atr >= 0 fails, for NCS / NCS2).
**Disclosed prediction-side error, fixed before this file was written:** the first version of the back-check computed the AT14-vs-Wilder
must_fail over the 16 base inputs only (1.870e-4); the spec's maximum is on the sc40B copy (scale 10). The loop now covers every exported input
(the FSH Amendment 2 lesson, repeated here); no other value changed.

## What the checker should show for a PASS

Verdict PASS; 90 real checks PASS; 7 / 7 controls detected on their required kinds with the counts above (a different count with the same
verdict is a convention difference to explain, not a failure); IMP 9 / 9 must_pass + 2 must_fail; floor rows PASS; 0 gated rows; no ERROR.
Any difference beyond ulp level in a value above is a finding to explain in Amendment 2 before the result is accepted.
