# LRSI stage 2 — corrected LaguerreRSI.c, LaguerreRSI_Superseded.c, pre-run records (Amendment 1), generated script

Planning chat, 2026-11-19. Branch `harness-lrsi`. Tooling `c2fcd44`; spec pre-registered at `824a3cc`
(`analysis/harness/specs/LRSI_ArticleFidelity.toml`). Stage 1 report: `docs/harness/LRSI_STAGE1_REPORT.md`. The planning chat
checked the spec draft against its own numbers before commit: L0 gains (G05), NCG trace max 0.0008469690514941175, NCG start-up max
0.0048423698983621755, NCS `s5` start-up 0.5979633949986088, tolerances = the pre-registered defaults, 129 real checks, IMP lists;
accepted stage 1's five departures (opt-in real params, NCT info, product-form L3, ramp_exact floor guard 1e-13 — (c) exact by IEEE
on ordered stages, no-static lint blocks generation until the .c exists). User's Git Bash: 640/640 at `c2fcd44`.
Labels: (a) source states, (b) measured/computed, (c) inference. Run on **Sonnet, effort Medium**.

**Git:** do NOT commit. At the end print the suggested commands (one commit for the two .c files + their test, one for
Amendment 1 + generated script; a third only if the generator had to change) and STOP. Do NOT click / run Zorro.

## 1. Corrected `indicators/ehlers/LaguerreRSI.c`

Two functions, bodies = `[corrected_code].lines` and `.wrapper_lines` of the spec, verbatim:
`var LaguerreRSICore(vars Close, var gamma, var* pL0, var* pL3, var* pDen)` then `var LaguerreRSI(vars Close, var gamma)`.
Header (comments only, replaces the whole old header), each statement labelled (a)/(b)/(c) or dropped:
- Source (a): Ehlers, *Cybernetic Analysis for Stocks and Futures* (Wiley 2004), ch. 14 "Time Warp — Without Space Travel",
  Fig. 14.8 (EasyLanguage), p. 221; Fig. 14.9 (EFS) agrees. Formula as `[source]` in Light-C terms: L0 = EMA with alpha 1 − gamma;
  L1..L3 allpass stages; CU / CD over the three adjacent pairs; RSI = CU / (CU + CD), 0–1; book default gamma 0.5; reference lines
  .2 / .8. Input: Close (the companion Laguerre FILTER, Fig. 14.5 / `Laguerre.c`, uses (H+L)/2 — not this indicator).
- Deviations fixed (b), review `docs/harness/LAGUERRERSI_SOURCE_REVIEW.md` (`6382607`): L-1 zero start as the source (was: every
  stage seeded to the first Close, that bar skipped, 0.5 returned); L-2 hold the previous value when CU + CD = 0, initial 0, per
  instance (was a static starting at 0.5); L-3 no statics (the old `lr_init` / `lr_prevRSI` were shared by every call: a second
  instance or asset started differently and could return another instance's value); L-5 `LaguerreRSICore` exports L0, L3 and
  CU + CD; L-6 this header. **Outputs before this fix differ in the first ~60 / 120 / 196 bars (gamma 0.5 / 0.7 / 0.8); after
  that they are identical** (review §3).
- Start-up (a/b): the source starts every stage at 0 and computes from the first bar; this file does the same (each
  `series(0, 2)` history starts at 0 on the instance's first call). Treat the first ~200 bars as warm-up (the harness uses W = 700).
- (b) Behaviour: the output lies in [0, 1] exactly. On a steadily rising (falling) price it is exactly 1 (0) once the four stages
  are ordered ("lock to lock", saturation by design, not a defect: it then reports THAT price trends, not how strongly). The share
  of bars pinned at 0 or 1 grows with the cycle length (spec O_PIN). On a flat price the result is a held value or rounding noise.
- (a) Use stated by the source (p. 221 / 225): buy after the line crosses back above .2, sell after it crosses back below .8 (the
  book's sell sentence says "price"; (c) probably the line). Not implemented here.
- (b) Callers: gamma 0.5 is exact in float32; 0.7 / 0.8 are not (gotchas 9d.1) — build them at run time from integers
  (`var g = 7; g = g/10;`). Same output range and scale (0–1) as MESAStochastic (C1, Strategy 2).
- Drop the old claims or label them: "P-LR1 35–55% of bars" → (c) with a pointer to the registered predictions file, or drop;
  the 2025-article note → (b): its L1 uses L0[1] in the first term, a delayed EMA rather than an allpass (review L-6).
- STATE: no statics; all five `series()` calls unconditional, before any use (gotchas 3.1); each instance has its own state.
  Callers invoke unconditionally every bar. No includes needed (no dependency).
- Verification line: `analysis/harness/specs/LRSI_ArticleFidelity.toml` (pre-registered `824a3cc`). Not verified until that run passes.

## 2. `indicators/ehlers/LaguerreRSI_Superseded.c` (new; the NCS / NCT control)

The CURRENT `LaguerreRSI.c` body (blob `b05f725176eff59b4ba1b68f299395c1c774ddff`) verbatim, function renamed `LaguerreRSI` ->
`LaguerreRSI_Superseded`, every `lr_` identifier -> `lro_` (flat namespace, gotchas 1.3). Nothing else changes: both statics, the
price seed, the early `return 0.5`, the `Close[0] > 0` guard and the INITRUN resets all stay. Header: "SUPERSEDED — do not use.
Kept as the negative control NCS / NCT of LRSI_ArticleFidelity (L-1 price seed, L-2 hold starting at 0.5, L-3 file statics shared
by every call). Corrected file: LaguerreRSI.c." The old header may stay or go (comments are stripped by the test). Report the token
diff vs the old blob (must be renames + header only).

## 3. Corrected-code test (new, as `test_mst_corrected_code.py`)

`analysis/harness/tests/test_lrs_corrected_code.py`:
- `LaguerreRSI.c` contains `[corrected_code].lines` inside `LaguerreRSICore` and `wrapper_lines` inside `LaguerreRSI`
  (whitespace-normalised, comments stripped).
- `LaguerreRSI_Superseded.c` equals the old blob after the renames (comments stripped).
- No `static` in `LaguerreRSI.c` (the spec's no-static lint, same function); no expression starting with a product or quotient of
  decimal literals (9d.8).
- Show the guard firing on temp copies, at least: `static` added before `var lr_CU`; `vars lr_L0 = series(0, 2);` ->
  `series(Close[0], 2)`; `lr_R[0] = lr_R[1];` removed; L1 line `lr_L0[1] - gamma*lr_L0[0]` -> `lr_L0[1] - gamma*lr_L0[1]` (the 2025
  form); `lr_k = lr_k - gamma;` removed; `vars lr_R = series(0, 2);` moved inside the `if`; in the superseded file, one `lro_` left
  as `lr_`.

## 4. Generator

(b) Stage 1: the four-column call path, `skip_inputs` and real params generate the LRS layout, and a synthetic own-model raw file
gave 129/129 with every control detected. **No generator change is expected.** If one turns out to be needed, it may change the
script layout only (never a criterion, tolerance, table, floor, effect or variant); the 8 existing specs (H1, SS2F, SS3F, HPF, RFF,
USE, RFX, MST) must still regenerate as recorded, the full suite must pass, and the change goes in Amendment 1 as A1.2. If you see a
reason the layout is unsafe in Light-C, STOP and report.

## 5. Pre-run conditions (spec pass_condition, pre-run i–v) — all must PASS

- (i) `test_lrs_corrected_code.py` passes on the new files; guard-fire evidence for each broken copy above.
- (ii) old blob `b05f7251…4ddff` recorded; the diff old -> new `LaguerreRSI.c` is only L-1, L-2, L-3, L-5, L-6 (+ the new
  `LaguerreRSICore` / wrapper structure): list every other token difference explicitly. Superseded file: renames + header only.
- (iii) `test_reference_lrsi_spec.py` passes; record the largest deviation per section.
- (iv) `python analysis/harness/generator.py analysis/harness/specs/LRSI_ArticleFidelity.toml --lint-only` clean, now including
  both includes resolving and the no-static check passing; record the INFO lines (D2 windows, per-control margins, NCH / NCT info
  lines, skipped pairs, L_NO_STATIC).
- (v) no-static lint: 0 hits on the new `LaguerreRSI.c`; 2 hits (`lro_init`, `lro_prevRSI`) when pointed at the new superseded file
  (seen to fire on the real file, not only on the old blob).
- Full suite: `bash analysis/harness/run_tests.sh` (report TOTAL; tracebacks + rerun on any ERROR, CLAUDE.md §8).

## 6. Amendment 1 (append to the spec; text above unchanged)

Same form as MESA Amendment 1: `[amendment_1]` (date, base_commit 824a3cc, before_run = true, changes A1.1 = pre-run records; A1.2
only if §4 needed a generator change; no criterion / tolerance / table / floor / effect / variant changed) + `[prerun]`
cond_i..cond_v, tests_before / tests_after / suite line, blob hashes of LaguerreRSI.c old (b05f7251…) and new,
LaguerreRSI_Superseded.c new (`git hash-object`). Add the run note: **restart Zorro before any rerun** (generated scripts return at
INITRUN before any indicator call, so the superseded file's own INITRUN resets never run; a second [Test] press would seed nothing;
brief Amendment 1). If ANY criterion would need to change, STOP and report instead.

## 7. Generated script

`python analysis/harness/generator.py analysis/harness/specs/LRSI_ArticleFidelity.toml` -> the script the spec names (expected
`strategies/tests/GEN_LRS_LaguerreRSI.c`; report the actual name). Record its sha256 in `[prerun]`. Check by reading the script
(report each):
- the two includes in order (LaguerreRSI_Superseded.c, LaguerreRSI.c), relative paths as in [zorro].include;
- gamma built from integers before any call (1/2, 7/10, 4/5) — no decimal literal gamma; inputs flat, s5..s100, alt, ramp,
  rampdn and the 10 invariance copies built from integers before any indicator call; every generated static reset at INITRUN;
- every call unconditional, fixed order: `LaguerreRSICore` for G05 / G07 / G08 on every base input and their copies; inline
  bodies (NCH, NCG, NC25, NCP) present once each, locals uniquely prefixed, 1/1000 built from a variable;
  `LaguerreRSI_Superseded(S, gamma 1/2)` as NCS then NCT on the 8 non-flat base inputs (NO flat call for either), and the FIRST
  superseded call of each bar is NCS on `s5`; calls per bar = 109 (stage 1 report); no `Period` identifier; no expression starting
  with a product or quotient of decimal literals (9d.8);
- out-parameters through local scalars, copied before the next call;
- raw file `Data/GEN_LRS_raw.csv`, 319 columns, no-overwrite guard; header and rows written before `quit()` (9d.4).
- Confirm the raw file does not exist yet under `C:/Zorro/Data/` (or report it).

## Done when

Report: both .c files (full text), test summary with guard-fire evidence, generator change (expected none), pre-run i–v, suite
TOTAL before/after, script name + sha256 and the read-through checks above, any deviation from this brief. Then STOP: no commit,
no Zorro run.
