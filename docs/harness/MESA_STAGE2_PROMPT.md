# MESA stage 2 — corrected MESAStochastic.c, MESAStochastic_Superseded.c, pre-run records (Amendment 1), generated script

Planning chat, 2026-11-19. Branch `harness-mesa`. Tooling `85b7431`; spec pre-registered at `0fd34ee`
(`analysis/harness/specs/MESA_ArticleFidelity.toml`). Stage 1 report: `docs/harness/MESA_STAGE1_REPORT.md`. The planning chat
checked the spec draft against its own numbers before commit: Roof tables (T = 20 gain = PROJECT_STATE §5 to 6.5e-15), floors
(largest trace 3.875e-06, L14 T = 100), tolerances (trace 5e-5), W = 700, gate 0.01, bound [0, 1], every control effect
(NCA 7.95e-04 = 15.9x is the tightest), corrected code identical to the brief. User's Git Bash: 540/540 at `85b7431`.
Labels: (a) source states, (b) measured/computed, (c) inference.

**Git:** do NOT commit. At the end print the suggested commands (one commit for the two .c files + their test, one for
Amendment 1 + generated script; a third only if the generator had to change) and STOP. Do NOT click / run Zorro.

## 1. Corrected `indicators/ehlers/MESAStochastic.c`

Two functions, bodies = `[corrected_code].lines` and `.wrapper_lines` of the spec, verbatim:
`var MESAStochasticCore(vars Price, int StochPeriod, int HPPeriod, int SSPeriod, var* pRoof, var* pStoc)` then
`var MESAStochastic(vars Price, int StochPeriod, int HPPeriod, int SSPeriod)`.
Header (comments only, replaces the old "NAMING CAUTION" block), each statement labelled (a)/(b)/(c) or dropped:
- Source (a): Ehlers, "Predictive And Successful Indicators", TASC V.32:1 (2014), pp. 16–25, sidebar "EasyLanguage Code To
  Compute The MESA Stochastic Indicator" (PDF p. 8). Formula as `[source]`, in Light-C terms: RoofingFilter(48, 10) ->
  stochastic over the last Length Roof values -> SuperSmoother(10) on the stochastic. Source default Length 20; 48 and 10 are
  fixed in the source, `HPPeriod` / `SSPeriod` are this library's generalisation (M-7); `SSPeriod` is used for both
  SuperSmoother passes, as the source reuses the same coefficients.
- Deviations fixed (b), review `docs/harness/MESASTOCHASTIC_SOURCE_REVIEW.md` (`3f0de96`): M-1 window StochPeriod bars (was
  StochPeriod + 1); M-2 output scale 0–1 as the source (was 0–100: **exports made before this fix are x100**); M-6 zero-range
  fallback 0.5 (was 50); M-9 `MESAStochasticCore` exports Roof and the raw stochastic; M-8 this header.
- Zero range (b/c): the source has no guard (it divides 0/0 when the window high equals the low). The fallback 0.5 is a library
  choice (mid-range: a flat market cannot produce a 0.2 / 0.8 crossing). It fires on the first bar and on flat input.
- Start-up (a): no rule in the source. (b) Roof starts at 0 (HighPassFilter zero seed, GAP-1.26 fixed upstream); the final
  SuperSmoother starts at the first stochastic value (series seeding) where the source starts at 0: the difference is gone
  after row 59 (spec finding 7). Treat the first ~60 bars as warm-up (the harness uses W = 700).
- (b) Bounds: the raw stochastic lies in [0, 1] exactly; the final output does NOT (it overshoots, about −0.03 to 1.03 on a
  long-period sine: spec finding 5). Thresholds such as the source's .2 / .8 apply to the final output.
- (b) The window length matters only for cycles longer than the window (spec O_WINDOW: 21 vs 20 bars differs by <= 8e-14 at
  T <= 20, by 6e-2 to 8e-2 at T = 40 / 100).
- (c) Keep, labelled as inference, the useful part of the old note: the indicator uses three fixed periods; it does not measure
  or adapt to a dominant cycle despite the "MESA" name; the stochastic stage rescales by the rolling range. Drop the
  unlabelled claims ("unaffected by the null test", "~10x amplitude") or label them (c) with a pointer to
  `docs/research/Cycle_Premise_Conclusions_and_Impact.md`.
- STATE: no statics; both `series()` calls unconditional, before any use (gotchas 3.1); every instance has its own window and
  final-smoother state. Callers invoke unconditionally every bar. Include order: HighPassFilter.c, SuperSmoother2Pole.c,
  RoofingFilter.c, MESAStochastic.c (gotchas 5.3).
- Verification line: `analysis/harness/specs/MESA_ArticleFidelity.toml` (pre-registered `0fd34ee`). Not verified until that
  run passes.

## 2. `indicators/ehlers/MESAStochastic_Superseded.c` (new; the NCS control)

The CURRENT `MESAStochastic.c` body (blob `a8c51bacf951cd1aa7a0d1c2f39347824ca1d6bf`) verbatim, function renamed
`MESAStochastic` -> `MESAStochastic_Superseded`, every `mstc_` identifier -> `mstco_` (flat namespace, gotchas 1.3). Nothing else
changes: the `StochPeriod + 1` window, the `100.0 *` scale, the fallback `50` and the `SuperSmoother2Pole` / `RoofingFilter`
calls all stay. Header: "SUPERSEDED — do not use. Kept as the negative control NCS of MESA_ArticleFidelity (M-1 window
StochPeriod + 1, M-2 scale 0–100, fallback 50). Corrected file: MESAStochastic.c." The old NAMING CAUTION comment may stay or
go (comments are stripped by the test). Report the token diff vs the old blob (must be renames + header only).

## 3. Corrected-code test (new, as `test_rfx_corrected_code.py`)

`analysis/harness/tests/test_mst_corrected_code.py`:
- `MESAStochastic.c` contains `[corrected_code].lines` inside `MESAStochasticCore` and `wrapper_lines` inside `MESAStochastic`
  (whitespace-normalised, comments stripped).
- `MESAStochastic_Superseded.c` equals the old blob after the renames (comments stripped).
- No `static` in `MESAStochastic.c`; no expression starting with a product or quotient of decimal literals (9d.8).
- Show the guard firing on temp copies, at least: window `StochPeriod)` -> `StochPeriod + 1)`; loop `mstc_i < StochPeriod` ->
  `<=`; `mstc_Stoc = mstc_Stoc/2;` removed; `(mstc_Roof[0] - mstc_LL)` -> `100.0*(mstc_Roof[0] - mstc_LL)`;
  `vars mstc_S = series(mstc_Stoc, 3);` moved inside the `if`; `static` added to `var mstc_HH`; in the superseded file,
  one `mstco_` left as `mstc_`.

## 4. Generator

(b) Stage 1: the three-output call path (local-scalar out-parameters, `62b4e97`) already generates the MST layout, and a
synthetic own-model raw file gave VERDICT PASS. **No generator change is expected.** If one turns out to be needed, it may change
the script layout only (never a criterion, tolerance, table, floor, effect or variant); the 7 existing specs + MST must still
regenerate as recorded, the full suite must pass, and the change goes in Amendment 1 as A1.2. If you see a reason the layout is
unsafe in Light-C, STOP and report.

## 5. Pre-run conditions (spec pass_condition, pre-run i–iv) — all must PASS

- (i) `test_mst_corrected_code.py` passes on the new files; guard-fire evidence for each broken copy above.
- (ii) old blob `a8c51bac…d6bf` recorded; the diff old -> new `MESAStochastic.c` is only M-1, M-2, M-6, M-8, M-9 (+ the new
  `MESAStochasticCore` / wrapper structure): list every other token difference explicitly. Superseded file: renames + header only.
- (iii) `test_reference_mst_spec.py` passes; record the largest deviation per section.
- (iv) `python analysis/harness/generator.py analysis/harness/specs/MESA_ArticleFidelity.toml --lint-only` clean, now including
  all five includes resolving; record the INFO lines (D2 windows, per-control margins, NCL / NCZ info lines).
- Full suite: `bash analysis/harness/run_tests.sh` (report TOTAL; tracebacks + rerun on any ERROR, CLAUDE.md §8).

## 6. Amendment 1 (append to the spec; text above unchanged)

Same form as RFX Amendment 1: `[amendment_1]` (date, base_commit 0fd34ee, before_run = true, changes A1.1 = pre-run records;
A1.2 only if §4 needed a generator change; no criterion / tolerance / table / floor / effect / variant changed) + `[prerun]`
cond_i..cond_iv, tests_before / tests_after / suite line, blob hashes of MESAStochastic.c old (a8c51bac…) and new,
MESAStochastic_Superseded.c new (`git hash-object`). If ANY criterion would need to change, STOP and report instead.

## 7. Generated script

`python analysis/harness/generator.py analysis/harness/specs/MESA_ArticleFidelity.toml` -> the script the spec names (expected
`strategies/tests/GEN_MST_MESAStochastic.c`; report the actual name). Record its sha256 in `[prerun]`. Check by reading the
script (report each):
- the five includes in dependency order (HighPassFilter.c, SuperSmoother2Pole.c, RoofingFilter.c, MESAStochastic_Superseded.c,
  MESAStochastic.c), relative paths as in [zorro].include;
- the alt input and the 10 invariance copies (sc*, of*): built from integers, before any indicator call; alt sign static reset
  at INITRUN; every generated static reset at INITRUN (O_STATICS_RESET);
- every call unconditional, fixed order: `MESAStochasticCore` for L14 / L20 / L30 / S20 on every base input and their copies,
  NCP (20, 40, 10) and NC1 (22, 48, 10) on every base input; the inline bodies (NCW, NCA, NCL, NCZ) present once each, locals
  uniquely prefixed, constants such as 1/1000 built from a variable; `MESAStochastic_Superseded(S, 20, 48, 10)` on the 8 base
  inputs; calls per bar = 128 (state the count, stage 1 report §3); no `Period` identifier; no expression starting with a
  product or quotient of decimal literals (9d.8);
- NCL body = the construction in O_NCL (literals from integers, degrees converted with Zorro `PI`), the same as IMP model
  `mesa_printed(20,48,10)`;
- out-parameters through local scalars, copied before the next call;
- raw file `Data/GEN_MST_raw.csv` (or as named by the spec), 308 columns, no-overwrite guard; header and rows written as the
  generator now does; writes happen before `quit()` (9d.4).
- Confirm the raw file does not exist yet under `C:/Zorro/Data/` (or report it).

## Done when

Report: both .c files (full text), test summary with guard-fire evidence, generator change (expected none), pre-run i–iv, suite
TOTAL before/after, script name + sha256 and the read-through checks above, any deviation from this brief. Then STOP: no commit,
no Zorro run.
