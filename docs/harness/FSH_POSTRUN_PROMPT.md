# FSH run 1 — checker, second read, post-run record (Amendment 2), write-ups

Planning chat, 2026-11-20. Branch `harness-fisher` at `6e79c16`. Spec `analysis/harness/specs/FSH_ArticleFidelity.toml` (pre-registered
`258b24a`, Amendment 1 `cb93b65`). Zorro run 1 done 2026-11-20 (restarted before the run; window: compiling, Warning 047 (harmless,
9d.7), "FSH batch complete: 3000 rows written", no `Error` line). Raw `C:/Zorro/Data/GEN_FSH_raw.csv`, local copy
`GEN_FSH_raw_run1.csv`, sha256 `8b8b61a0d1357da6277df9f18e8c01c0a1ce4870ec86cbd9b30d475f93f9857a` (user's Git Bash).
**Prediction committed before the checker:** `docs/harness/FSH_RUN1_PREDICTION.md` (`6e79c16`; back-check script
`docs/harness/FSH_RUN1_BACKCHECK.py`). Labels: (a) source states, (b) measured, (c) inference. Run on **Sonnet, effort Medium**;
if the verdict is FAIL or anything disagrees with the prediction, STOP after step 2 and report (FAIL diagnosis is Opus / High).

**Git:** do NOT commit. At the end print the suggested commands (one commit: results + Amendment 2 + write-ups + this brief) and STOP.

## 1. Checker

`python analysis/harness/checker.py analysis/harness/specs/FSH_ArticleFidelity.toml C:/Zorro/Data/GEN_FSH_raw_run1.csv` (sha256
above; verify it first). Write the results file the checker names into `analysis/harness/results/` with the run-1 suffix (never
overwrite). Report the verdict, items 1–7 of the pass condition, the per-kind maxima, every control FAIL row, IMP and floor rows.

## 2. Second read: compare with the prediction, row by row

Compare and tabulate (prediction vs checker): verdict (PASS); real checks 56, FAIL 0; per-kind maxima (trace raw / v1 / out
4.996004e-16 / 5.551115e-16 / 8.881784e-16; invariance FR10 2.656542e-12 / 5.319301e-12, FR20 5.320189e-13 / 1.056932e-12; bounds,
ramp_exact, trigger, flat_zero 0); gated rows 0; per-control detection on each [detect.required] kind and FAIL-row counts (NCW 10,
NCC 8, NCK 7, NCL 9, NC32 16, NCS 8, NCT 8; total 66 — the prediction notes the checker may group rows differently: explain any count
difference by row id); IMP must_pass values (FR10 5.234035e-12 … NCT 1.487477e-12) and must_fail (1.304495832918544,
9.198226649480118); floor guard rows. Any disagreement in verdict, a detection, an IMP value beyond ~1e-15, or a FAIL row the
prediction did not list = STOP and report.

## 3. Amendment 2 (post-run record; append, text above unchanged)

As LRSI Amendment 2: `[amendment_2]` (date, base_commit cb93b65, before_run = false, no criterion changed) recording: raw sha256,
results file + sha256, verdict and counts, the second-read comparison (agreed / differences explained), Zorro vs the source model to
rounding (<= 8.9e-16; no `PI` gap), start-up matched to rounding (INFO; 9d.6 padding and the zero start confirmed in a run), the
measured floor vs the stage 1 estimate (1.064e-11 was conservative by ~4 orders), NC32 bound and ramp_exact as required detections,
ramp |out| = ln(1999) exactly in float64 (the review's "approached, not attained" holds mathematically, not in float64), NCB INFO
values (v1 reaches .9999; |out| <= 4.951718775643). Restart-Zorro rule restated for any rerun.

## 4. Write-ups (docs; labels kept)

- `docs/PROJECT_STATE.md`: header "As of" line; §1.1 replace the Oscillators "Fisher" entry (from the "Not reviewed" row) with its own
  row in the LRS style: source TASC V.20:11 Fig. 5 p. 41 (book Fig. 1.7 = INFO variant); review `bdc83da` (F-1..F-9 one line each);
  tooling `c1c222e`; spec `258b24a` + Amendment 1 `cb93b65` + Amendment 2; corrected .c + superseded control + callers + test `800c797`;
  prediction `6e79c16`; run 1 result with counts; (b) findings: saturation (T = 100: ~2/3 of bars clamped, Fish ±7.6; ±2.5 routine at
  T >= 20, Len 10), window error invisible at T <= L, |Fish| <= ln(1999) reached on a trend, shared statics corrupted a second instance
  by up to 2.7, old float32 literals moved Fish by up to 1.29e-5. §1.2: C1 Strategy 1 "Fisher (10) — verified 2026-11-20 (source A;
  saturates on long cycles)". §7: a "Fisher: run 1 PASS" paragraph in the established style; "Next: baselines FAMA / FRAMA". Note in
  §1.2 / §7 that BOTH strategies' C1 indicators are now verified; Strategy 1's C2 (Reflex) was verified 2026-11-18, so Strategy 1's
  entry pair is fully verified too.
- `docs/harness/HARNESS_DESIGN.md`: "D6 applied to FisherTransform" note (no linear stage: normalisation divides by the range, so no
  v1 gain / phase checks; three exported stages each with an exact bound; second gate on the clamp distance because a clamp flip makes
  Fish jump 1.154; trace tolerance 1e-9, below the D6 default, because there is no `PI` gap and 3e-5 could not see NC32; the shared
  state is the IIR state itself, so NCT is a control, unlike LRS; series_len 21 for windowed indicators reading the caller's series;
  new kinds trigger and flat_zero) and the §7 FSH status entry.
- `docs/ZORRO_LIGHTC_GOTCHAS.md`: §9d.6 addendum (b): FSH run 1 confirms `series()` padding with the first value for a caller-built
  input series read by MaxVal / MinVal (start-up rows equal the padded-window model to <= 8.9e-16); §1.3 add `fi_` FisherCore,
  `fto_` FisherTransform_Superseded, `ift_` Test_Fisher_IFT_COG to the prefixes in use; change log lines.
- Do not edit `FISHER_SOURCE_REVIEW.md` (committed record); the float64 ramp correction lives in Amendment 2.

## Done when

Report (append as `docs/harness/FSH_POSTRUN_REPORT.md`): checker output summary, the second-read table, Amendment 2 text, the doc
diffs, suite TOTAL (`bash analysis/harness/run_tests.sh`; 740 expected, tracebacks + rerun on any ERROR). Then STOP: no commit.
