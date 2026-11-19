# MESA post-run records — Amendment 2, PROJECT_STATE, HARNESS_DESIGN

Planning chat, 2026-11-19. Branch `harness-mesa` (HEAD `17a8604`). Write-up only: no code, no tooling, no Zorro.
Labels: (a) source states, (b) measured/computed, (c) inference.

**Git:** do NOT commit. At the end print the suggested commands (one commit for all three files) and STOP.
Pattern to follow: the RFX post-run records (`48211bf` RFX Amendment 2, `a6c323c` PROJECT_STATE / HARNESS_DESIGN).

## Facts of the run (b)

- Spec `analysis/harness/specs/MESA_ArticleFidelity.toml`: pre-registered `0fd34ee`, Amendment 1 (pre-run i–iv) `4843ee2`.
- Corrected `.c` + `MESAStochastic_Superseded.c` + test `0332395`. Tooling `85b7431`. Suite 555/555 (user's Git Bash).
- Zorro run 1, 2026-11-19, after a Zorro restart: compiled, `Warning 047` only, no `Error` line, 3000 rows. Raw sha256
  `0c53641af0416324de3629e2744358f3d31e084ef224800ab12241b16fddefda` (local copy `*_raw_run1.csv`, gitignored).
- Planning-chat back-check + prediction committed before the checker: `57b1abf` (`docs/harness/MST_RUN1_PREDICTION.md`,
  code `docs/harness/MST_RUN1_BACKCHECK.py`). Predicted VERDICT PASS.
- Checker: **run 1 PASS** (`17a8604`, `analysis/harness/results/MST_ArticleFidelity_20261119.csv`): 84/84 real, 5/5 controls
  detected (29 FAIL rows: NCW 2, NCA 5, NCP 15, NC1 2, NCS 5), 10 alt-phase SKIP, 0 gated rows, IMP 11/11 must_pass + 2/2
  must_fail, floor 20/20. Read twice: the checker agreed with the prediction on verdict, every count and every compared value.
- Scope of the second read: Claude Code compared verdict, counts, traces, control values, NCL and IMP fire values; it did not
  diff bound / flat / ramp / alt / invariance values or the start-up rows. Those are in the planning-chat back-check (Stoc 0.0 /
  1.0 on every real variant; flat, ramp residual, alt gain 0; invariance ≤ 3.810e-13; start-up L20 s20 rows 0–3 out 0.5,
  0.56329862, 0.69989999, 0.83205974; flat Stoc = 0.5 on every row) and all PASS in the checker. Record this, no action.
- Zorro vs article = the `PI` gap: Roof gain 5.278e-07 / 4.409e-07, phase 1.328e-06 / 1.567e-06 rad; trace max 3.875e-06
  (L14, T = 100). Own-model replay (IMP) ≤ 8.9e-16.
- Variants tested: 11 (4 real + 5 controls + 2 info).

## Findings to record (b), with their (c) consequence

1. **A window-length error is invisible on sines whose period divides into the window** (M-1): 21 vs 20 bars differed by
   ≤ 7.6e-14 at T = 5 / 10 / 20 and by 6.2e-2 / 8.1e-2 at T = 40 / 100; NC1 (L = 22) the same pattern. (c) Every windowed
   indicator spec (stochastic, min/max, rolling rank) must test sines with T > L, not only T ≤ L.
2. **Normalisation amplifies the `PI` gap where the range is small:** the trace floor peaks at T = 100 (HH − LL smallest, gate
   margin 0.028 at L14). The D6 default trace tolerance 3e-5 failed the D2 window here; this spec used 5e-5 (stated before the
   run). (c) The D6 default is a starting point; each oscillator spec measures its own window (D2 rule 3), as the rule already says.
3. **The final output is not bounded** (overshoot −0.0295 to 1.0295 at T = 100); the exact bound applies to the raw Stoc.
   (c) Thresholds such as the source's .2 / .8 act on the smoothed output, which can exceed [0, 1].
4. **Start-up:** the final-seed choice (M-5) affects rows < 60 only; the zero-range fallback fires on bar 0 and on flat input.
5. **NCS bound:** the superseded file exports only `out`, so the bound could not be checked on it; trace caught it at 2.04e6×.
   The stage-1 brief's "bound fires on NCS" was a planning-chat error, corrected before pre-registration.

## 1. Spec Amendment 2 (append; text above unchanged)

`[amendment_2]`: date 2026-11-19, base_commit `17a8604`, after_run = true, "post-run record; no criterion changed". Sections as
RFX Amendment 2: run facts (above), second-read scope note, findings 1–5, variant count 11.

## 2. `docs/PROJECT_STATE.md`

- **As of** line: 2026-11-19; SS2, SS3, HighPassFilter, RoofingFilter, UltimateSmootherE, Reflex and **MESAStochastic** verified;
  next: decision pending (below).
- **§1.1** Oscillators: a new **MESA Stochastic** row in the Reflex style: "Corrected and verified 2026-11-19. Source: TASC
  V.32:1 (2014) sidebar. Review `docs/harness/MESASTOCHASTIC_SOURCE_REVIEW.md` (`3f0de96`): M-1 window StochPeriod + 1 →
  StochPeriod; M-2 scale 0–100 → 0–1 (exports before `0332395` are ×100); M-6 fallback 50 → 0.5; M-9 `MESAStochasticCore`
  exports Roof and raw Stoc; M-8 header; M-4 HP seeding fixed upstream (GAP-1.26); M-5 final seed kept (start-up INFO). Old file
  `MESAStochastic_Superseded.c` (control NCS). Spec `MESA_ArticleFidelity.toml` (`0fd34ee` + Amendment 1). Run 1 PASS
  (`17a8604`): 84/84 …; IMP ≤ 8.9e-16; Zorro vs article = `PI` gap (trace 3.9e-6). Read twice, agreed." plus findings 1 and 3 as
  (b) one-liners. Remove MESA Stochastic from the "Not reviewed" oscillator list.
- **§1.2** C1 Strategy 2 cell: "MESA Stochastic (20,48,10) — verified 2026-11-19 (0–1 scale; source lines .2 / .8)".
- **§4** GAP-1.26 row: MESAStochastic re-verified 2026-11-19 (MST run 1); remaining: Decycler, RMO. Add a row: "MESA Stochastic
  exports made before `0332395` (e.g. `Test_MESAStochastic.c`, `Test_C2_LaguerreRSI.c`, `Test_LagSine.c`,
  `Test_RecursiveMedian.c` outputs, any notebook reading them) are on 0–100 and used the 21-bar window: not comparable with the
  verified indicator".
- **§7** step 3: an MST entry in the RFX style (spec, tooling, new: three-output calls, two-sided bound, gate on the model range,
  trace tolerance 5e-5 by D2 rule 3; resumed after an interrupted session, stash backup; read twice). Tooling 555/555.
  Then: "**Next: decision pending (planning chat).** Remaining oscillator-family slot candidates: Fisher Transform (C1,
  Strategy 1) and Laguerre RSI (C2, Strategy 2); baselines (FAMA / FRAMA) and stops (UltimateChannelBands, NATR) after."

## 3. `docs/harness/HARNESS_DESIGN.md`

- Under D6: a dated note "D6 applied to MESAStochastic, 2026-11-19": rule 3 two-sided bound on an exported intermediate (raw
  Stoc) when the final output has no exact bound; rule 2 gate on the model's HH − LL; rule 5 not applicable when the indicator
  has no statics (recorded, no invented control); trace tolerance 5e-5 for this spec (the 3e-5 default failed the D2 window,
  finding 2); finding 1 (windowed indicators need T > L sines).
- §7: an MST status entry in the RFX style, with the commit chain `3f0de96` (review), `85b7431` (tooling), `0fd34ee` (spec),
  `0332395` (.c), `4843ee2` (Amendment 1 + script), `57b1abf` (prediction), `17a8604` (results), and the counts above.

## Done when

Report the three diffs (summary + any line you were unsure of), confirm the spec text above Amendment 2 is unchanged
(`git diff` shows additions only at the end of the toml), run `bash analysis/harness/run_tests.sh` (the spec tests read the
toml; report TOTAL), print the suggested commit command, STOP.
