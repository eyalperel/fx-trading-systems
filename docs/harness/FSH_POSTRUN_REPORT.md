# FSH run 1 — post-run report (Claude Code, Sonnet, 2026-11-20)

Branch `harness-fisher` at `6e79c16`. Nothing committed. Labels: (a) source states, (b) measured, (c) inference.

## 1. Checker

Raw `C:/Zorro/Data/GEN_FSH_raw_run1.csv`, sha256 `8b8b61a0d1357da6277df9f18e8c01c0a1ce4870ec86cbd9b30d475f93f9857a` (verified before the run, matches the brief).
Results `analysis/harness/results/FSH_ArticleFidelity_20261120.csv`, sha256 `fb4c364af7867634a1bec97b74da97d1672356d95665c68f757b038fadf13b75`.

**VERDICT: PASS.** 10 variants (FR10, FR20 real; NCW, NCC, NCK, NCL, NC32, NCS, NCT controls; NCB info). Real checks 56 PASS / 0 FAIL / 0 ERROR.
7/7 controls detected on every `[detect.required]` kind at >= 10x; 66 control FAIL rows. IMP 10/10 must_pass, 2/2 must_fail fire. Floor 10/10 PASS. 0 gated rows. L_NO_STATIC: 0 hits.

The checker was run twice by mistake (it names its file by date); both results files had the identical sha256 above, and the untracked `_run2.csv` was deleted (planning-chat decision). Recorded in Amendment 2, A2.3.

## 2. Second read: prediction vs checker

| Item | Prediction | Checker | Result |
|---|---|---|---|
| Verdict / real checks | PASS, 56, FAIL 0 | PASS, 56, FAIL 0 | agree |
| trace raw / v1 / out (FR10 = FR20) | 4.996004e-16 / 5.551115e-16 / 8.881784e-16 | same | agree |
| bound, ramp_exact, trigger, flat_zero | 0 | 0 | agree |
| invariance maxima (offset values) | FR10 5.319301e-12, FR20 1.056932e-12 | 5.319e-12, 1.057e-12 | agree |
| gated rows | 0 | 0 | agree |
| control FAIL rows | NCW 10, NCC 8, NCK 7, NCL 9, NC32 16, NCS 8, NCT 8 (66) | same, per control | agree |
| required-kind detection, all 7 controls | all fire | all fire, ratios as predicted | agree |
| IMP must_pass, 9 of 10 | FR10 5.234035e-12, NCB 2.979672e-12, NCW 5.748291e-12, NCC 3.518075e-12, NCK 2.979672e-12, NCL 3.629763e-12, NC32 5.234035e-12, NCS 1.319833e-12, NCT 1.487477e-12 | same to the printed digits (CSV full precision) | agree |
| IMP must_pass FR20 | 1.474376e-12 | 5.262457136723242e-12 (at of100) | **differs**, explained (i) |
| must_fail NCS vs FR10 model | 9.198226649480118 | 9.198226649480118 | agree (16 digits) |
| must_fail FR10 vs NCW model | 1.304495832918544 | 1.3044958329186862 | **differs by 1.4e-13**, explained (ii) |
| floor | measured 8.9e-16; stage 1 estimate 1.064e-11 | INFO line shows the estimate 1.064e-11 | agree; recorded A2.4 |

Differences:
- (i) FR20 IMP: the planning-chat back-check replayed IMP on the 8 base inputs only. Over all 18 inputs it gives 5.262457e-12, matching the checker (planning-chat decision). Prediction-side omission; the back-check script is unchanged.
- (ii) FR10 must_fail: 1.4e-13 absolute, above the ~1e-15 comparison limit; both fire by 9 orders over 1e-9. Explained by the planning chat (b): same cause as (i); the back-check's must_fail loop also covered the base inputs only. Over all 18 inputs it gives 1.3044958329186862 at of100, the checker's value to every digit. Prediction-side omission.
- (iii) NCT margins print 8.542e9 / 9.201e12 against the prediction's rounded 8.54e9 / 9.2e12 (rounding only).

## 3. Amendment 2

Appended to `analysis/harness/specs/FSH_ArticleFidelity.toml` (`[amendment_2]`, date 2026-11-20, base_commit cb93b65, before_run = false, criterion_changed = false; parses; text above unchanged). A2.1 result and counts; A2.2 second read and differences; A2.3 duplicate checker run; A2.4 floor estimate vs measured; A2.5 findings (Zorro = model to rounding, start-up/9d.6, NC32 detections, ramp |out| = ln(1999) in float64, NCB INFO values 0.9999 / 4.951718775643098 read from the results file, NCL T <= L invisible, NCT a real control); A2.6 variant count and the restart-Zorro rule.

## 4. Doc diffs (`git diff --stat --ignore-cr-at-eol`)

- `docs/PROJECT_STATE.md` (+6/-4 before the §1.2 note, now +8 or so): "As of" line; §1.1 own Fisher row (review/tooling/spec/code/prediction/run 1, F-1..F-9, findings); §1.2 C1 cell and a note that both C1s and Strategy 1's entry pair are verified; §7 "Fisher Transform: run 1 PASS" paragraph; "Next: baselines FAMA / FRAMA".
- `docs/harness/HARNESS_DESIGN.md`: "D6 applied to FisherTransform" note and the §7 FSH status entry.
- `docs/ZORRO_LIGHTC_GOTCHAS.md`: 9d.6 addendum (b), §1.3 prefixes `fi_` / `fto_` / `ift_` (table row and prefix list), two change-log lines.
- `FISHER_SOURCE_REVIEW.md` untouched.

## 5. Suite

`bash analysis/harness/run_tests.sh` (Claude Code shell): TOTAL 740 PASS 740 FAIL 0 ERROR 0 SKIP 0. No ERROR or FAIL, so no rerun. The commit-message count should come from your Git Bash run.

## 6. Stated limits

The NCB |out| and v1 values were read from the results CSV. Per-kind maxima were computed from the CSV `abs_diff` column (4 significant digits). The Fisher row in PROJECT_STATE states the saturation numbers (2/3 clamped at T = 100, +-7.6, +-2.5 routine at T >= 20) as given in the decision text; I did not re-derive them from `FISHER_SOURCE_REVIEW.md` this session.
