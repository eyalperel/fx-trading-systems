# MAF run 1 — checker x 2, second read, post-run record (Amendment 2 x 2), write-ups

Planning chat, 2026-11-21. Branch `harness-mama-frama` at `8c1e648`. Specs `analysis/harness/specs/MAMA_ArticleFidelity.toml` and
`FRAMA_ArticleFidelity.toml` (pre-registered `7713f5b`, Amendment 1 `d0c9a23`). Zorro run 1 done 2026-11-21, Zorro restarted before each
script; both windows: compiling, Warning 047 (harmless, 9d.7), "MAM / FRA batch complete: 3000 rows written", no `Error` line.
Raw copies: `C:/Zorro/Data/GEN_MAM_raw_run1.csv` sha256 `7c86c37026f01871f590449dcbacef31edc576d30381bbda27cf8e138945471e`;
`C:/Zorro/Data/GEN_FRA_raw_run1.csv` sha256 `12c0e3bf87f7ab0af20454ae76503a8733d47dc67c60b32bf04c44871c2f1d27`.
**Prediction committed before the checker:** `docs/harness/MAF_RUN1_PREDICTION.md` (`8c1e648`; back-check `MAF_RUN1_BACKCHECK.py`, output
`MAF_RUN1_BACKCHECK_output.txt`). Labels: (a) source states, (b) measured, (c) inference. Run on **Sonnet, effort Medium**; if a verdict is
FAIL or anything disagrees with the prediction, STOP after step 2 and report (FAIL diagnosis is Opus / High).

**Git:** do NOT commit. At the end print ONE suggested commit command (results + Amendment 2 x 2 + write-ups + report + this brief) and STOP.

## 1. Checker (both specs)

Verify both sha256 first. Then `python analysis/harness/checker.py <spec> <raw_run1>` for MAMA and FRAMA. Write each results file the checker
names into `analysis/harness/results/` with the run-1 suffix (never overwrite). Report per spec: verdict, pass-condition items, per-kind maxima,
every control FAIL row (counts per control and kind), `[detect.info_only]` lines, IMP rows (must_pass worst, must_fail values, trailer INFO
pairs), floor rows, conditioning classification line.

## 2. Second read: compare with the prediction, row by row

Tabulate prediction vs checker for each spec:
- verdict PASS; real checks MAM 66 / FRA 98, FAIL 0; controls detected MAM 7 / FRA 6;
- per-kind maxima on real checks: MAM trace <= 1.3e-15 (mama), 1.8e-15 (fama), 1.1e-15 (alpha), 3.6e-14 (period), 7.8e-14 (phase); equivariance
  <= 6.2e-12 (period), 5.3e-11 (phase); bounds alpha exactly [SL, FL], Period max 50.0. FRA trace <= 8.9e-16 (out), 2.2e-15 (dim), 5.0e-16
  (alpha); band ramp lag 34.05274879968001 / 17.27287888640001; point ramp and flat 0; equivariance <= 6.4e-14; hull 0;
- every control's best ratio and detected kinds (prediction §MAMA / §FRAMA controls): MAM NCB 3.626e7, NCH 1.262e7, NCF 8.500e6, NC32 5.944e3 +
  bound (Period 50.000003725290505), NCP 4.328e4, NCS / NCS2 ~1.1; FRA NCE 7.99e6 + bound + lag (34.32483744584003), NCN 1.585e10 + lag
  (30.80213538996035), NC32 76.3 (thinnest), NCT 1.0e10 (bound INFO only), NCS / NCS2 trace + hull + lag + flat. The checker may group FAIL rows
  differently: explain any count difference by row id;
- IMP must_pass worst (MAM MA05 s100 alpha 1.7374657268476312e-11, MA03 s100 phase 1.1238654451517505e-10; FRA FR16 s100 alpha
  1.9337864642920977e-12) and must_fail (MAM 0.1261940444433307; FRA 7.988543995718911e-4); NCS / NCS2 replay (MAM <= 4.5e-14 checked; FRA
  <= 1.0e-13).
Any disagreement in a verdict, a detection, an IMP value beyond ~1e-14 (or beyond 1e-12 relative), or a FAIL row the prediction did not list
= STOP and report.

## 3. Amendment 2 (post-run record; append to EACH spec, text above unchanged)

As FSH Amendment 2: `[amendment_2]` (date, base_commit d0c9a23, before_run = false, no criterion changed) recording: raw sha256, results file +
sha256, verdict and counts, the second-read comparison (agreed / differences explained), and:
- MAMA: Zorro vs the source model to rounding (trace <= 7.8e-14, start-up included): **S1 confirmed in a run** (no `PI` gap with run-time pi;
  NCP = the old `PI` at 4.3e4 x); NC32's bound detection (float32 .2 + .8 > 1 lifts Period to 50.0000037); INFO inputs as classified (flat, ramp,
  s5) with their IMP trailer values (s5 phase 180 degrees = a wrap flip under the %.15f input rounding: rule 3 seen in a run); the explicit
  series lengths of `MAMA_Superseded.c` (A1.2) gave a replay to <= 4.5e-14 on checked inputs.
- FRAMA: Zorro vs the source model <= 2.2e-15; both known answers exact; NC32 the thinnest required margin (76 x); NCS / NCS2 replay <= 1.0e-13
  with the generator's call order; the planning chat's disclosed replay-order error (prediction, "Disclosed").
- Restart-Zorro rule restated for any rerun.

## 4. Write-ups (docs; labels kept)

- `docs/PROJECT_STATE.md`: "As of" line (Phase 1 step 3: + MAMA / FAMA and FRAMA verified; next: stops UltimateChannelBands / NATR). §1.1:
  replace "Baselines | MAMA, FAMA, FRAMA, Laguerre Filter, DSMA | Not reviewed ..." with a MAMA / FAMA row and a FRAMA row in the FSH style
  (source + page; review `b7bdd69` + appendix; MA-1..MA-9 / FR-1..FR-8 one line each; S1 exact pi; tooling / specs `7713f5b`; corrected .c +
  superseded + callers + Amendment 1 `d0c9a23`; prediction `8c1e648`; run 1 result with counts; (b) findings: MAMA zero start ~500 bars, alpha
  bimodal FL / SL on short cycles, Period tracks T = 10-40 within ~0.5%, ill-conditioned on flat / ramp / T < 6; FRAMA .01 floor never binds,
  D < 1 with close-only bars, start-up memory up to ~2750 bars, shared statics wrong by up to 3.3e-2, the library window was 32 = source N 32;
  callers now pass N = 32) and keep "Laguerre Filter, DSMA — not reviewed" as its own row. §1.2 Baseline row: "FAMA (MAMA's second output,
  (.5, .05)) — verified 2026-11-21" / "FRAMA (N = 32; source default 16) — verified 2026-11-21"; note that **every slot indicator of both
  strategies except stops / volatility and exit is now verified**. §4: GAP / defect rows touched (Week 9 FRAMA row: superseded by this
  verification; the `Laguerre.c` row stays). §7: a "MAMA / FAMA and FRAMA: run 1 PASS" paragraph in the established style (new: D7 family, bars
  inputs, equivariance, hull, conditioning classifier, exact pi under D3, explicit series lengths for length-less series under LookBack = 0);
  "Next: stops (UltimateChannelBands, NATR)".
- `docs/harness/HARNESS_DESIGN.md`: "D7 applied to MAMA / FRAMA" note (what was confirmed in the run: rule 3 per (input, column), s5 period a
  checked pair; W_eq 1000 for MAMA, row 1 for FRAMA; required vs info_only detections; exact pi as D3's prescribed exception; series lengths) and
  the §7 MAF status entry. D3: add one line "Exception 2026-11-20: MAMA (S1)".
- `docs/ZORRO_LIGHTC_GOTCHAS.md`: open item recorded as such (length of a `series()` without length under `LookBack = 0`, unprobed; always give
  lengths in harness-run code); change-log line. Nothing else.
- Do not edit `MAMA_FRAMA_SOURCE_REVIEW.md` (committed record).

## Done when

Report as `docs/harness/MAF_POSTRUN_REPORT.md`: checker summaries, the second-read tables, both Amendment 2 texts, the doc diffs, suite TOTAL
(`bash analysis/harness/run_tests.sh`; 853 expected, tracebacks + rerun on any ERROR). Then print ONE commit command and STOP.
