# MAF stage 2 — corrected MAMA.c / FRAMA.c, superseded copies, callers, pre-run records (Amendment 1 x 2), generated scripts

Planning chat, 2026-11-20. Branch `harness-mama-frama`. Stage 1 (tooling + both specs, pre-registered) at `7713f5b`
(`analysis/harness/specs/MAMA_ArticleFidelity.toml`, `analysis/harness/specs/FRAMA_ArticleFidelity.toml`). Stage 1 report:
`docs/harness/MAF_STAGE1_REPORT.md`. Review: `docs/harness/MAMA_FRAMA_SOURCE_REVIEW.md` (`b7bdd69` + appendix in `7713f5b`).
The planning chat reviewed stage 1 before commit: all of report §5 accepted except two items, both applied before `7713f5b`: NCB is a control
(trace on s5:period, 3.63e7x); FRAMA NCT required on trace only (bound hit INFO, `[detect.info_only]`). User's Git Bash: 817/817 at `7713f5b`.
Labels: (a) source states, (b) measured / computed, (c) inference. Run on **Sonnet, effort Medium**.

**Git:** do NOT commit. At the end print ONE suggested commit command covering everything (so every commit is green) and STOP. Do NOT
click / run Zorro.

## 1. Corrected `indicators/ehlers/MAMA.c`

Two functions, bodies = the MAMA spec's `[corrected_code]` lines and wrapper lines, VERBATIM: `MAMACore(...)` then `MAMA(...)` (the old
signature, so callers that use only MAMA / FAMA keep compiling). Remove the `#ifndef PI` block (MA-5: it never applied). Header (comments
only, replaces the whole old header), each statement labelled (a) / (b) / (c) or dropped:
- Source (a): Ehlers, "MESA Adaptive Moving Averages", *Technical Analysis of Stocks & Commodities* V.19:9 (2001), pp. 30-35, Sidebar Fig. 1
  (TradeStation code), PDF p. 5. Pipeline in plain terms: 4-bar weighted Smooth -> Hilbert-transform Detrender, I1 / Q1, jI / jQ -> phasor sums
  I2 / Q2 -> homodyne Re / Im -> Period (bounded 0.67x..1.5x the previous, then 6..50, then blended) and Phase = atan(Q1 / I1) in degrees ->
  DeltaPhase = Phase[1] - Phase, floored at 1 -> alpha = FastLimit / DeltaPhase clamped to [SlowLimit, FastLimit] -> MAMA = EMA(alpha) of Price;
  FAMA = EMA(alpha / 2) of MAMA. Defaults (a): Price (H+L)/2, FastLimit .5, SlowLimit .05. (a) Use stated by the source: the MAMA / FAMA
  crossover as a trend signal (not implemented here; the NNFX baseline rule is a template decision, step 4).
- Deviations fixed (b), review `docs/harness/MAMA_FRAMA_SOURCE_REVIEW.md`: MA-1 start-up as the source (every state 0, computed from the
  instance's 6th call; the old file seeded with the price, returned Price for 5 calls and started Period at 20); MA-2 Period / Phase keep their
  value on a bar where Im or Re = 0 / I1 = 0 (the old file set 20 / 0); MA-3 per-instance state and counter (the old `static barCount` was
  shared by every call); MA-4 constants built from integers (float32 literals); S1 exact pi built at run time for the degree conversion (the old
  `PI` = 3.14159 moved Phase by up to 7.3e-5 degrees, more than the float32 literals: D3 exception, review appendix); MA-7 `MAMACore` exports
  FAMA, Period, alpha and Phase; MA-8 this header (the old header's "APPROVED", lag, SNR, win-rate, 92.5% and "1.5*0 = 0 trap" claims are
  dropped: unsourced or not reproducible; (b) the trap does not occur, the source's 6-bar floor acts).
- (b) Behaviour (review §3 and appendix; spec observations): **zero start: MAMA / FAMA start at 0 and need ~500 bars to forget it** (sines:
  start-up differences gone by row ~520); a strategy's LookBack must cover this (c). alpha is in [SlowLimit, FastLimit]; on short cycles it
  switches between the two limits (T = 10 / 20: FL on 20% / 10% of bars, SL otherwise). Period follows the cycle within ~0.5% for T = 10..40 and
  sits on its bounds outside 6..50. **Ill-conditioned inputs:** on a flat line (during start-up), a steady ramp and cycles shorter than 6 bars,
  the output depends on rounding (one ulp of input moved FAMA by up to 3.2e-2 / 2.8e-4 / 1.7e-2): the phase wrap at +-90 degrees flips alpha
  between its limits. On a ramp Period wanders 36..48 and the lags are about 2.2 bars (MAMA) / 7.0 bars (FAMA) at (.5, .05) (model, not exact).
- Caller requirements: Price series of at least 4 values; call unconditionally every bar (gotchas 3.1); build FastLimit / SlowLimit from
  integers (`var x = 1; x = x/20;` for .05: gotchas 9d.1).
- STATE: no statics; every `series()` call unconditional and first; each instance has its own state. No includes needed.
- Verification line: `analysis/harness/specs/MAMA_ArticleFidelity.toml` (pre-registered `7713f5b`). Not verified until that run passes.

## 2. Corrected `indicators/ehlers/FRAMA.c`

Two functions, bodies = the FRAMA spec's `[corrected_code]` lines and wrapper lines, VERBATIM: `FRAMACore(...)` then
`FRAMA(vars Price, vars High, vars Low, int N)`. Header, labelled as above:
- Source (a): Ehlers, "Fractal Adaptive Moving Averages", *TASC* V.23:10 (2005), pp. 81-82, "FRAMA EasyLanguage code" sidebar, PDF p. 3.
  N = the FULL window, even (default 16); N1 = (HH - LL)/(N/2) over bars 0..N/2-1, N2 the same over N/2..N-1, N3 = (HH - LL)/N over 0..N-1,
  all from High / Low; Dimen = (ln(N1 + N2) - ln(N3))/ln 2, computed only when N1, N2, N3 > 0 (else held); alpha = exp(-4.6 (Dimen - 1)) clamped
  to [.01, 1]; Filt = alpha Price + (1 - alpha) Filt[1]; Filt = Price for the first N bars. Price default (H+L)/2.
- Deviations fixed (b): FR-1 **the parameter is the source's N (full window); the old `T` was HALF the window, and every caller passed 16 = a
  32-bar window: callers now pass N = 32 to keep that configuration** (the source default is 16); FR-2 Price, High, Low are parameters; FR-3
  per-instance state (the old `static frama_prev` / `frama_init` were shared by every call: a second instance or an asset loop was silently
  wrong, by up to 3.3e-2 on a random walk); FR-4 start-up as the source; FR-5 the source's guard (N1, N2, N3 > 0, Dimen held, Filt always
  updated; the old file returned without update and could take log(0)); FR-6 constants from integers; FR-7 `FRAMACore` exports Dimen and alpha;
  FR-8 this header.
- (b) Behaviour: Dimen <= 2 always (N1 + N2 <= 4 N3), so alpha >= exp(-4.6) = 0.01005 and **the .01 floor never binds**; the article's
  "alpha = .01 at D = 2" is rounded. With overlapping bars (H > L) Dimen >= 1 (c); with H = L (close-only data) Dimen can fall below 1 and alpha
  clamps to 1 (FRAMA = price; a steady ramp gives out = price exactly). On a steady ramp with bars of constant range, Dimen and alpha are
  constant and FRAMA lags by (1 - alpha)/alpha (34.05 bars at N = 16, 17.27 at N = 32, range 0.004 around a slope of 1e-4 per bar).
  **Start-up memory is long:** where alpha sits near .01 (Dimen near 2, short cycles), differences from the start fall as .99^n (~2750 bars to
  1e-12).
- Caller requirements: N even (the source's rule; not checked in code); Price, High, Low series of at least N values; call unconditionally
  every bar; for the source's inputs pass `series((priceHigh() + priceLow())/2)`, `series(priceHigh())`, `series(priceLow())`.
- STATE, verification line as for MAMA (`FRAMA_ArticleFidelity.toml`, `7713f5b`).

## 3. Superseded copies (new; the NCS / NCS2 controls)

- `indicators/ehlers/MAMA_Superseded.c`: the CURRENT `MAMA.c` (blob `bab4cbbb5961be5720bce82fc6e487e283f7f00e`) with ONLY: function
  `MAMA` -> `MAMA_Superseded`; every local / static identifier prefixed `mao_` (flat namespace, 1.3; `Price`, `FastLimit`, `SlowLimit`,
  `outFAMA` parameters may keep their names if the spec's call layout uses them positionally: say which); NO behavioural edit (keep the
  `#ifndef PI` block, the literals, the barCount static and its INITRUN reset).
- `indicators/ehlers/FRAMA_Superseded.c`: the CURRENT `FRAMA.c` (blob `3352fbe04ed691e479564bc63d46ae181334f9bb`) with ONLY: function
  `FRAMA(int T)` -> `FRAMA_Superseded(vars Price, vars High, vars Low, int T)`; the input reads `series(priceHigh())` / `series(priceLow())`
  -> the `High` / `Low` parameters and `frama_price` -> `Price[0]` (the ONLY behavioural edit); prefix `frama_` -> `fro_`.
- Header of each: "SUPERSEDED — do not use. Kept as negative controls NCS / NCS2 of <spec> (shared statics; <file-specific defects>). Only
  edits vs the original: <list>. Corrected file: <name>." Report the token diff vs the old blob (renames + header [+ the FRAMA input] only).

## 4. Callers

Update exactly the four callers stage 1 listed (report §6), nothing else; each script keeps its outputs and column names:
- `strategies/tests/Test_FRAMA_Laguerre_DSMA.c:87` and `strategies/tests/Test_FRAMA_vs_MAMA.c:39`, `strategies/tests/Test_UltimateChannelBands.c:83`:
  build the three series (script-own prefix, unconditional, before the call, length >= 32) and call `FRAMA(<mid>, <hi>, <lo>, 32)`. Replace
  `#define FRAMA_T 16` by `#define FRAMA_N 32` with the comment "full window (source N); was T = 16 (half window) = the same 32 bars".
- `strategies/tests/Test_MAMA.c:32` and `strategies/tests/Test_FRAMA_vs_MAMA.c:38`: FastLimit / SlowLimit built from integers (`.5` = 1/2,
  `.05` = 1/20; `#define FAST_LIMIT 0.5` would still be a float32 literal at the call: replace it).
- (c) These scripts are not run in this stage; their outputs change by design (MA-1..4, FR-1..6). Say in the report that they are
  compile-unverified until next used. `docs/` snippets stay as they are (history).

## 5. Gotchas 1.3

Add the prefixes `ma_` (MAMACore), `maw_` (MAMA wrapper), `mao_` (MAMA_Superseded), `fr_` (FRAMACore), `frw_` (FRAMA wrapper), `fro_`
(FRAMA_Superseded) to the "Prefixes in use" line and table 1.3, and a change-log row. Nothing else in the gotchas file.

## 6. Corrected-code test (new): `analysis/harness/tests/test_maf_corrected_code.py`

As `test_fsh_corrected_code.py`, for both files:
- each corrected file contains its spec's corrected lines and wrapper lines verbatim (whitespace-normalised, comments stripped);
- each superseded file equals its old blob after the listed renames / edits (comments stripped);
- no `static`, no global `var`, no decimal literal (digits with a `.`) and no expression starting with a product or quotient of literals in the
  corrected files; no `PI` token in the corrected MAMA.c;
- no caller in the repo still calls `FRAMA(` with one argument or passes a decimal literal as a MAMA limit;
- guard fires on temp copies, at least: MAMA: `static` before `vars ma_n`; `var ma_w1 = 962;` -> `var ma_w1 = 0.0962;` (division removed);
  `ma_P[0] = ma_P[1];` removed (MA-2 hold); `ma_pi*atan(1)` -> `PI`; `vars ma_S = series(0, 7);` moved inside the `if`; FRAMA: `static` before
  `vars fr_n`; `fr_k = 46` -> `fr_k = 4.6` (division removed); the guard `fr_N1 > 0 && fr_N2 > 0 &&` removed; `fr_n[0] < N + 1` -> `fr_n[0] < N`;
  in each superseded file, one `mao_` / `fro_` left unprefixed.

## 7. Generator

(b) Stage 1: the five- and three-column call paths, bars inputs, copies, `series_len = 34` and the D7 kinds generate both layouts, and own-model
synthetic raw files gave 66/66 and 98/98 with every control detected. **No generator change is expected.** If one is needed, it may change the
script layout only (never a criterion, tolerance, table, floor, effect or variant); the 10 existing specs must still regenerate as recorded,
the full suite must pass, and the change goes in Amendment 1 as A1.2. If the layout looks unsafe in Light-C, STOP and report.

## 8. Pre-run conditions (each spec's pass_condition, pre-run i-v) — all must PASS, for BOTH specs

- (i) `test_maf_corrected_code.py` passes; guard-fire evidence for each broken copy above.
- (ii) old blobs recorded (MAMA `bab4cbbb...f7f00e`, FRAMA `3352fbe0...f9bb`); the diff old -> new is only the review's listed deviations
  (+ the Core / wrapper structure): list every other token difference explicitly. Superseded files: renames + header (+ FRAMA input) only.
- (iii) `test_reference_maf_spec.py` passes; record the largest deviation per section.
- (iv) `python analysis/harness/generator.py <spec> --lint-only` clean for both, now with both includes resolving and the no-static check
  passing; record the INFO lines (D2 windows, per-control margins incl. NCB and NCT's info-only bound, conditioning classification, L_NO_STATIC).
- (v) no-static lint: 0 hits on each corrected file; seen to fire on each NEW superseded file (MAMA 1 hit `mao_barCount` or as renamed;
  FRAMA 2 hits), not only on the old blobs.
- Full suite: `bash analysis/harness/run_tests.sh` (report TOTAL; tracebacks + rerun on any ERROR, CLAUDE.md §8).

## 9. Amendment 1 (append to EACH spec; text above unchanged)

Same form as FSH Amendment 1 (`cb93b65`): `[amendment_1]` (date, base_commit 7713f5b, before_run = true, A1.1 = pre-run records; A1.2 only if
§7 needed a generator change; no criterion / tolerance / table / floor / effect / variant changed) + `[prerun]` cond_i..cond_v, tests_before /
tests_after / suite line, blob hashes (old corrected-file blob, new corrected file, new superseded file; `git hash-object`), script sha256.
Run note: **restart Zorro before the run and between the two scripts** (the superseded statics are reset only by a recompile; generated scripts
return at INITRUN before any indicator call). If ANY criterion would need to change, STOP and report instead.

## 10. Generated scripts

`python analysis/harness/generator.py <spec>` for each -> `strategies/tests/GEN_MAM_MAMA.c`, `strategies/tests/GEN_FRA_FRAMA.c` (report actual
paths); sha256 into `[prerun]`. Check by reading each script (report each item):
- the two includes in order (superseded, corrected), relative paths as in `[zorro].include`;
- every input series built from integers before any indicator call, each `series(X, 34)`; FRAMA band H / L and the sc / of copies built from
  integers; no decimal literal in the harness part (control bodies excepted: NC32's float32 literals are deliberate, report them); every
  generated static reset at INITRUN;
- every call unconditional, fixed order, variant-major as stage 1's replay used; calls per bar 67 (MAMA) / 108 (FRAMA) as in the stage 1
  report; inline bodies once each with unique local prefixes; the superseded calls as NCS then NCS2 in the order the replay used;
- out-parameters through local scalars, copied before the next call;
- raw files `Data/GEN_MAM_raw.csv` (304 columns) and `Data/GEN_FRA_raw.csv` (305 columns), no-overwrite guard; header and rows written
  before `quit()` (9d.4);
- confirm neither raw file exists yet under `C:/Zorro/Data/` (or report it).

## Done when

Write the report as `docs/harness/MAF_STAGE2_REPORT.md`: both corrected .c files and both superseded files (full text), the caller diffs, the
gotchas diff, test summary with guard-fire evidence, generator change (expected none), pre-run i-v for both specs, suite TOTAL before / after,
script names + sha256 and the read-through checks, any deviation from this brief. Then print ONE commit command and STOP: no commit, no Zorro run.
