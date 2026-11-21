# MAF run 1 — post-run report (checker x 2, second read, Amendment 2 x 2, write-ups)

Claude Code (Sonnet), 2026-11-21. Branch `harness-mama-frama` at `8c1e648`. Brief: `docs/harness/MAF_POSTRUN_PROMPT.md`. Labels: (b) measured, (c) inference.

## 1. Checker

Both raw sha256 verified before the run (sha256sum): MAM `7c86c370…471e`, FRA `12c0e3bf…1d27`, equal to the brief.
Command: `python analysis/harness/checker.py <spec> C:/Zorro/Data/GEN_{MAM,FRA}_raw_run1.csv --out-dir analysis/harness/results --date 20261121`.

| | MAMA_ArticleFidelity | FRAMA_ArticleFidelity |
|---|---|---|
| Verdict | **PASS** | **PASS** |
| Variants run | 9 (2 real + 7 controls) | 8 (2 real + 6 controls) |
| Real checks | 66 PASS / 0 FAIL / 0 ERROR | 98 PASS / 0 FAIL / 0 ERROR |
| Controls detected (required kinds, >= 10x) | 7 / 7 | 6 / 6 |
| Control FAIL rows | 71 (NCB 1, NCH 18, NCF 4, NC32 15, NCP 17, NCS 8, NCS2 8) | 129 (NCE 24, NCN 35, NC32 17, NCT 23, NCS 15, NCS2 15) |
| IMP must_pass | 11 / 11, worst MA05 s100 alpha 1.7374657268476312e-11; MA03 s100 phase 1.1239009722885385e-10 | 10 / 10, worst FR16 s100 alpha 1.9337864642920977e-12 |
| IMP must_fail | MA05 vs NCH model 0.1261940444433307; NCS 1.107867655437579 | FR16 vs NCE model 7.988543995718911e-4; NCS 0.2968597285936496 |
| Floor rows | 8 / 8 PASS (trace 2.318e-11, trace_phase 1.538e-10, equiv 6.239e-12, equiv_phase 5.273e-11) | 10 / 10 PASS (trace 1.933e-12, equiv 6.384e-14, ramp_exact 0, lag 1.300e-11, flat 0) |
| Lint L_NO_STATIC | 0 tokens, PASS | 0 tokens, PASS |
| Results file | `MAMA_ArticleFidelity_20261121.csv` sha256 `e11c3fee…f0c0` | `FRAMA_ArticleFidelity_20261121.csv` sha256 `d9bf1bff…7c89` |

`[detect.info_only]`: FRAMA NCT bound (1.0e12 x, INFO as registered). No other info_only line. Conditioning classification: the results files carry the
INFO inputs (MAMA flat, ramp, s5: 30 INFO rows; FRAMA point flat dim / alpha: 4 INFO rows), as classified before the run. No guard fired.
The raw copies are gitignored (`*_raw_run*.csv`) and were not copied into `results/`; the sha256 is in each Amendment 2.

## 2. Second read: prediction vs checker

Verdict, counts, detections, IMP values and bounds agree. Nothing hit a STOP condition of the brief (verdict, detection, IMP beyond ~1e-14, unlisted FAIL row).
Differences are ulp-level only, listed in full:

| Quantity | Prediction | Checker | Diff | Note |
|---|---|---|---|---|
| MAM trace mama / alpha / period | 1.3e-15 / 1.1e-15 / 3.6e-14 | 1.332e-15 / 1.096e-15 / 3.553e-14 | agree | |
| MAM trace **fama** | 1.8e-15 | 1.998e-15 (s40) | 2e-16 | ulp-level |
| MAM trace **phase** | 7.8e-14 | 8.171e-14 (s40, both variants) | 3.7e-15 | ulp-level |
| MAM equivariance (all) | period 6.2e-12, phase 5.3e-11 (mama 1.9e-14, fama 1.5e-14) | 6.210e-12, 5.273e-11 (1.865e-14, 1.532e-14), alpha 3.710e-13 | agree | |
| MAM bounds | alpha [SL, FL] exact, Period max 50.0 | diffs 0 | agree | |
| MA05 IMP worst (s100 alpha) | 1.7374657268476312e-11 | 1.7374657268476312e-11 | 0 | |
| **MA03 IMP worst (s100 phase)** | 1.1238654451517505e-10 | 1.1239009722885385e-10 | 3.5e-15 abs, 3e-5 rel | within ~1e-14 |
| MAM must_fail (MA05 vs NCH) | 0.1261940444433307 | 0.1261940444433307 | 0 | |
| MAM controls, best ratio | NCB 3.626e7, NCH 1.262e7, NCF 8.500e6, NC32 5.944e3 + bound 7.45e4 (Period 50.000003725290505), NCP 4.328e4, NCS / NCS2 ~1.1 abs | 3.626e7, 1.262e7, 8.500e6, 5.944e3 + 7.451e4 (50.000003725290505), 4.328e4, 1.108 / 1.107 abs (ratio 1.1e9) | agree | |
| MAM NCS / NCS2 replay | <= 4.5e-14 | 4.552e-14 | agree | |
| FRA trace dim | <= 2.2e-15 | 2.220e-15 (FR32) | agree | |
| FRA trace **out** | <= 8.9e-16 | FR16 6.661e-16; **FR32 1.110e-15** (s10) | 2.2e-16 | ulp-level, FR32 only |
| FRA trace **alpha** | <= 5.0e-16 | FR16 4.996e-16; **FR32 2.165e-15** (s100B) | 1.7e-15 (4.3x) | FR32 only; ~2e-5 of tolerance 1e-10 |
| FRA band-ramp lag | 34.05274879968001 / 17.27287888640001 | 34.052748799681034 / 17.272878886401035 | ~1e-12 | the prediction's own model values; checker deltas to the exact answer 1.04e-11 / 2.1e-12 |
| FRA point ramp / flat | 0 | ramp 2.22e-16 (1 ulp at 1.1011), flat 0 | 2.2e-16 | ulp |
| FRA equivariance | <= 6.4e-14 | alpha 6.400e-14, dim 5.795e-14, out 1.155e-14 | agree | |
| FRA hull | 0 | 4.441e-16 (inside the allowance) | ulp | |
| FR16 IMP worst (s100 alpha) | 1.9337864642920977e-12 | 1.9337864642920977e-12 | 0 | |
| FRA must_fail (FR16 vs NCE) | 7.988543995718911e-4 | 7.988543995718911e-4 | 0 | |
| FRA controls | NCE 7.99e6 + bound + lag 34.32483744584003, NCN 1.585e10 + lag 30.80213538996035, NC32 76.3 (thinnest), NCT 1.0e10 (bound INFO), NCS / NCS2 trace + hull + lag + flat | same (NCE 7.989e6, 5.157e9, 2.721e5; NCN 1.585e10, 3.251e6; NC32 76.27; NCT 1.000e10; NCS 2.969e9 / 2.873e14 / 3.405e7 / 2.300e11) | agree | |
| FRA NCS / NCS2 replay | <= 1.0e-13 | 9.570e-14 / 1.004e-13 | agree | |

(c) The FRAMA FR32 maxima above the stated values mean the prediction's "<= 8.9e-16 / 5.0e-16" did not cover the N = 32 variant for out and alpha.
Not examined further. Flagged here for the planning chat since the brief says to report anything that disagrees; none of these changes a verdict, a
detection or a margin.

## 3. Amendment 2 (appended to each spec, text above unchanged)

`analysis/harness/specs/MAMA_ArticleFidelity.toml` and `FRAMA_ArticleFidelity.toml`: new `[amendment_2]` table, keys date 2026-11-21, base_commit d0c9a23,
before_run = false, after_run = true, criterion_changed = false, `changes` = A2.1 run result (sha256s, counts, maxima), A2.2 read twice (agreed /
differences), A2.3 findings, A2.4 variants and the restart-Zorro rule. `git diff --stat --ignore-cr-at-eol`: 13 insertions each, 0 deletions;
both files still parse with `tomllib`. The full texts are in the spec files (not repeated here); content as the brief required:
MAMA: S1 confirmed in a run, NCP at 4.3e4 x, NC32 bound (Period 50.0000037), INFO inputs with s5 phase 179.99999999999963 degrees (wrap flip, rule 3),
explicit series lengths (A1.2) giving the NCS replay <= 4.5e-14. FRAMA: Zorro vs model <= 2.2e-15, both known answers exact, NC32 the thinnest required
margin (76 x), NCS / NCS2 replay <= 1.0e-13 with the generator's call order, the planning chat's disclosed replay-order error.

## 4. Doc diffs (`git diff --stat --ignore-cr-at-eol`)

| File | Change |
|---|---|
| `docs/PROJECT_STATE.md` (+9 / -6 lines) | As-of line; §1.1 MAMA / FAMA row and FRAMA row, "Laguerre Filter, DSMA — not reviewed" kept as its own row; §1.2 Baseline row and the "every slot indicator ... except stops / volatility and exit is now verified" note; §4 Week 9 row; §7 "MAMA / FAMA and FRAMA: run 1 PASS" paragraph, "Next: stops (UltimateChannelBands, NATR)" |
| `docs/harness/HARNESS_DESIGN.md` (+4) | D3 line "Exception 2026-11-20: MAMA (S1)"; "D7 applied to MAMA / FAMA and FRAMA" note; §7 MAF status entry |
| `docs/ZORRO_LIGHTC_GOTCHAS.md` (+2) | 9d.10 row (open item, unprobed, always give lengths in harness-run code) and a change-log line |
| `docs/harness/MAMA_FRAMA_SOURCE_REVIEW.md` | not edited (committed record) |

(c) Wording to check in the planning chat: the PROJECT_STATE rows quote the review's MA-1..MA-9 / FR-1..FR-8 as in `MAMA_FRAMA_SOURCE_REVIEW.md` §4 and the
D7 note's required / info_only wording is generic per control (I did not re-read the spec's `[detect.required]` tables line by line).

## 5. Test suite

`bash analysis/harness/run_tests.sh`, Claude Code shell, run twice (before and after the doc edits): **TOTAL 853  PASS 853  FAIL 0  ERROR 0  SKIP 0** both times.
No intermittent `test_checker_amend1.test_cli` error seen. Per CLAUDE.md §8, test counts for a commit message come from the user's Git Bash run.

## 6. Not done / for the user

No git command was run. Not copied: the raw CSVs (gitignored, sha256 in the amendments). Untracked files to add: the two results files, this report, the brief.
