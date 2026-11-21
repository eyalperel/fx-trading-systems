# MAF stage 2 report: corrected MAMA.c / FRAMA.c, superseded copies, callers, Amendment 1 x 2, generated scripts

**Date:** 2026-11-20 (first session, stopped at §7) and 2026-11-21 (this session, completed per the planning chat's decision on §0, option 1).
**Brief:** `docs/harness/MAF_STAGE2_PROMPT.md`. **Branch:** `harness-mama-frama` at `7713f5b`, nothing committed, Zorro not run.
Labels: (a) source states, (b) measured / computed here, (c) inference.

## 0. Status: complete; STOP before commit and before any Zorro run

Done: brief §1-§6, §8 pre-run i-v for both specs (all PASS, §4), §9 Amendment 1 in both specs, §10 both generated scripts with the read-through
(§6). Suite TOTAL 853 / 853.

**The §0 STOP of the first session and its resolution.** (a) Zorro manual (`C:/Zorro/zorro.chm`, page `series`): a series without a length takes
the length of LookBack; page `lookback`: set it to 0 when no lookback is needed. (b) The old MAMA.c (kept in `MAMA_Superseded.c`) had 15
length-less `series()` calls and reads up to `[6]`; the generated scripts set `LookBack = 0`; the old file in real use ran with LookBack >= 7.
Planning chat decision, **option 1**: give each of the 15 calls an explicit length 7 (> the largest index read), no other edit; recorded as MAMA
Amendment 1 **A1.2** (control body only; values identical to the old file under its real-use LookBack >= 7 and to `mama_superseded`; no criterion /
tolerance / table / floor / effect / variant changed). Done: `MAMA_Superseded.c` now has `series(Price[0], 7)`, `series(0.0, 7)`, `series(20.0, 7)`
on all 15 calls and its header lists the edit; the test builds the expected body as old blob + renames + the explicit lengths, and the guard is
**seen to fire** when one length is removed (token check not-ok at token 67 `,` vs `)`; length scan reports `series(0.0)`; `series(Price[0])` also
reported by the scan's own check). FRAMA: **Amendment 1 A1.2 records that the input edit uses aliases** (`vars fro_High = High; ...`), allocating no
series, superseding the stage 1 spec note "its own series of them are kept"; no criterion change. Also accepted and recorded (A1.4 in both specs):
the stricter body check (function body EQUALS the pre-registered lines); no generator change.

## 1. Files

| File | State | git hash-object |
|---|---|---|
| `indicators/ehlers/MAMA.c` | corrected: header + `MAMACore` + `MAMA` (bodies = spec `[corrected_code]`, verbatim) | 74e3c731597d0bb95dca04b68e065802d8f7c3d1 (old bab4cbbb5961be5720bce82fc6e487e283f7f00e) |
| `indicators/ehlers/FRAMA.c` | corrected: header + `FRAMACore` + `FRAMA` (verbatim) | 1213ae9cb3b9a0752112c1653e2c658d6024bd7a (old 3352fbe04ed691e479564bc63d46ae181334f9bb) |
| `indicators/ehlers/MAMA_Superseded.c` | new: old blob + header; `MAMA` -> `MAMA_Superseded`; code identifiers prefixed `mao_`; explicit length 7 on the 15 `series()` calls (A1.2) | c407c0a19b23e4d0b5f7f210717f9e9251a49f95 |
| `indicators/ehlers/FRAMA_Superseded.c` | new: old blob + header; signature; input edit; `frama_` -> `fro_` | 81356dbde9da98d8555e8191c45bfe57c19a8d79 |
| 4 callers, `docs/ZORRO_LIGHTC_GOTCHAS.md` | updated (Appendix B) | |
| `analysis/harness/tests/test_maf_corrected_code.py` | new, 36 tests | |
| `analysis/harness/specs/MAMA_ArticleFidelity.toml`, `FRAMA_ArticleFidelity.toml` | Amendment 1 appended (text above unchanged), `[prerun]` | |
| `strategies/tests/GEN_MAM_MAMA.c`, `GEN_FRA_FRAMA.c` | generated (§6) | see §6 |

Full texts: Appendix A. The MAMA_Superseded parameters `Price`, `FastLimit`, `SlowLimit`, `outFAMA` keep their names (the generated script
passes them positionally; the corrected MAMACore has parameters of the same names, which is how FisherCore / FisherTransform_Superseded
coexisted in FSH run 1). Renames in MAMA_Superseded are applied to code only (not to its comments), so the original header and comments read
as before; in FRAMA_Superseded `frama_` -> `fro_` everywhere (comments included).

## 2. Callers (brief §4; diffs in Appendix B)

| File | Change |
|---|---|
| `strategies/tests/Test_FRAMA_Laguerre_DSMA.c` | `#define FRAMA_T 16` -> `#define FRAMA_N 32` (comment as briefed); `fld_mid` / `fld_hi` / `fld_lo` = `series((priceHigh() + priceLow())/2, FRAMA_N)`, `series(priceHigh(), FRAMA_N)`, `series(priceLow(), FRAMA_N)` before the call; `FRAMA(fld_mid, fld_hi, fld_lo, FRAMA_N)` |
| `strategies/tests/Test_FRAMA_vs_MAMA.c` | `FAST_LIMIT` / `SLOW_LIMIT` defines removed; `fvm_fl = 1/2`, `fvm_sl = 1/20` built at run time; `FRAMA_N 32`; `fvm_mid` / `fvm_hi` / `fvm_lo`; `MAMA(Price, fvm_fl, fvm_sl, &fama_val)`, `FRAMA(fvm_mid, fvm_hi, fvm_lo, FRAMA_N)` |
| `strategies/tests/Test_UltimateChannelBands.c` | `#define FRAMA_N 32` added (it had a bare `FRAMA(16)`, no define); `ucbf_mid` / `ucbf_hi` / `ucbf_lo`; `FRAMA(ucbf_mid, ucbf_hi, ucbf_lo, FRAMA_N)`; comment "T=16 per Week 9" updated |
| `strategies/tests/Test_MAMA.c` | `tm_fl = 1/2`, `tm_sl = 1/20`; `MAMA(Price, tm_fl, tm_sl, &fama)` |

Caller prefixes `fld_`, `fvm_`, `ucbf_`, `tm_`: grep-free in indicators/, strategies/ and `C:/Zorro/include`. Outputs and column names
unchanged. (c) The four scripts are **compile-unverified until next used**; their outputs change by design (MA-1..4, FR-1..6). (b) Observed,
not changed (not in the brief): `Test_MAMA.c` returns at `if(is(LOOKBACK))` BEFORE the MAMA call, so MAMA is not called during the lookback
(consistently, so series order is kept; the zero start then begins after the lookback). `docs/` snippets unchanged (history).

## 3. Gotchas 1.3 (brief §5)

Prefixes `ma_` (MAMACore), `maw_` (MAMA wrapper), `mao_` (MAMA_Superseded), `fr_` (FRAMACore), `frw_` (FRAMA wrapper), `fro_`
(FRAMA_Superseded) added to the table row 1.3 and the "Prefixes in use" line; one change-log row. Nothing else (Appendix B).

## 4. Tests and pre-run conditions (both specs)

Suite (`bash analysis/harness/run_tests.sh`, Claude Code shell): **before 817** (user's Git Bash at `7713f5b`), **after TOTAL 853 PASS 853
FAIL 0 ERROR 0 SKIP 0** (36 new in `test_maf_corrected_code.py`: 32 in the first session, +4 for the explicit-length checks: every series()
has an explicit length in the four files, once per spec class; the length guard fires, once per class, the FRAMA one returning early). No ERROR / FAIL, so
no rerun was needed (the first session's 849 and this 853 are the only two full runs; the MemoryError seen in earlier sessions did not appear).

| Pre-run | MAMA | FRAMA |
|---|---|---|
| (i) corrected lines verbatim | PASS: `MAMACore` body == `[corrected_code].lines`, `MAMA` body == wrapper_lines (whitespace-normalised, comments stripped) | PASS, same for `FRAMACore` / `FRAMA` |
| (i) guard fires (temp copies) | `static` before `vars ma_n`; `var ma_w1 = 0.0962;`; `ma_P[0] = ma_P[1];` removed; `ma_pi*atan(1)` -> `PI`; `vars ma_S = series(0, 7);` moved inside the `if`; wrapper `return maw_1;`: all not-ok | `static` before `vars fr_n`; `fr_k = 4.6`; `fr_N1 > 0 && fr_N2 > 0 &&` removed; `fr_n[0] < N` ; wrapper: all not-ok |
| (i) scans | no `static`, `INITRUN`, `Period`, `#include`, global var / vars, decimal literal, literal product; no `PI` token (MAMA); each scan seen to fire | same (no PI check needed) |
| (ii) old blob | `git rev-parse b7bdd69:indicators/ehlers/MAMA.c` = bab4cbbb...f7f00e | 3352fbe0...f9bb |
| (ii) token diff old -> new | asserted exactly (§4.1) | asserted exactly (§4.1) |
| (ii) superseded = renamed old blob | token-identical (comments stripped) incl. the 15 explicit lengths (A1.2); fires on `mao_barCount` left as `barCount` and on one length removed | token-identical; fires on `fro_init` left as `frama_init` |
| (iii) `test_reference_maf_spec.py` | PASS: conditioning 90 values, findings 533, floors, effects, fire tests: worst deviation 0.000e+00 in every section (self-consistency) | PASS: 90 / 419 values, worst 0.000e+00 |
| (iv) `--lint-only` | **lint clean, exit 0**, both includes resolve; 4 D2 windows ok; margins: NCB trace 3.63e7x, NCH 1.26e7x, NCF 8.5e6x, NC32 trace 5.94e3x / bound 7.45e4x, NCP 4.33e4x, NCS / NCS2 1.11e9x; L_NO_STATIC MAMA.c 0: PASS | **lint clean, exit 0**; 5 windows ok; NCE bound 5.16e9x, NCN trace 1.58e10x, NC32 trace 76.3x, NCT trace 1e10x with bound 1e12x (INFO only), NCS / NCS2 hull 2.87e14x; L_NO_STATIC FRAMA.c 0: PASS |
| (v) no-static | MAMA.c 0 hits; MAMA_Superseded.c 1 hit `mao_barCount` (line 82) | FRAMA.c 0; FRAMA_Superseded.c 2 hits `fro_init` (46), `fro_prev` (87) |
| (every `series()` has an explicit length) | PASS: MAMA.c 17 calls, MAMA_Superseded.c 15 calls, none without a length | PASS: FRAMA.c 4 calls; FRAMA_Superseded.c 0 calls (aliases) |
| (vi) callers | no `FRAMA(` with one argument, no decimal / `*_LIMIT` MAMA limit anywhere; exactly the four callers call the indicators; scans seen to fire | |
| (vii) conditioning | recomputed = spec lists (`conditioning_mismatches = []`, test_checker_maf / test_reference_maf_spec) | same |

### 4.1 Token differences old -> new (asserted in the test; "explicit other differences")

MAMA, every difference is MA-1 / MA-2 / MA-3 / MA-4 / MA-5 / S1 / MA-7 or a rename: removed the `#ifndef PI` block and 4 `PI` (MA-5, S1);
`static int barCount`, its INITRUN reset and `++` (MA-3); the price / 20 seeds and `if(barCount <= 5) return Price` (MA-1); every decimal
literal (MA-4); the old names (Smooth, Detrender, ..., alpha -> ma_S, ma_De, ..., ma_A). Added: the Core signature with four out-parameters
and their assignments, the wrapper (MA-7); 17 `series(0, n)` and 17 holds `X[0] = X[1]` (MA-1, MA-2); `ma_n` counter and `if(ma_n[0] > 5)`
(MA-1, MA-3); integer ratios (MA-4); `ma_pi = 4*atan(1)`, `ma_deg = 180/ma_pi` (S1). Other token differences, none an MA item: the old
expression `360.0/(atan(Im/Re)*180.0/PI)` is now three statements (`atan`, `*deg`, `360/`), the old local `alpha` / `DeltaPhase` are series /
locals `ma_A` / `ma_dp`, and `1.0 - alpha` uses `ma_u`. FRAMA, every difference is FR-1 .. FR-7 or a rename: `T` (x11) -> `N` (FR-1); the
`priceHigh()` / `priceLow()` series and the mid price -> parameters (FR-2); the two statics, INITRUN reset and `if(!init)` seed -> series
(FR-3, FR-4); `if(N3 <= 0) return prev` -> the `&&` guard (FR-5); `4.6`, `0.01`, `1.0` x4, `2.0` x3 -> integer-built (FR-6); the Core
signature, out assignments and wrapper (FR-7). Other: the three box loops reuse `fr_HH` / `fr_LL` (the source's HH / LL) instead of six
`Hi1..Lo3` names, and `N3` is computed over 0..N-1 directly as the source writes it (old: max of the two boxes; same value).

## 5. Decisions taken and deviations from the brief (all reversible, none touches a criterion)

1. **FRAMA_Superseded input edit read as aliases** (`vars fro_High = High; vars fro_Low = Low; var fro_price = Price[0];`): the brief's literal
   "series(priceHigh()) / series(priceLow()) -> the High / Low parameters" and the FSH precedent (`vars fto_Mid = Price;`). Confirmed by the planning
   chat and recorded as FRAMA Amendment 1 A1.2 (supersedes the stage 1 spec note).
2. **MAMA_Superseded explicit length 7** (planning chat, option 1): MAMA Amendment 1 A1.2. It is an edit outside the brief's §3 list ("NO behavioural
   edit"): a deliberate, recorded departure, values unchanged for full history.
3. **Stricter (i) check**: each function body must EQUAL its pre-registered lines (the FSH test's containment form did not fire on `static` added before
   the FIRST pre-registered line). Accepted by the planning chat; A1.4 in both specs.
4. **No generator change** (brief §7). Both scripts generated by the unchanged generator; regenerating from the amended specs into a temp directory
   gives byte-identical files (the generator itself refuses to overwrite an existing script: `FileExistsError`, exit 1, as intended).
5. **Raw-file guard wording.** The brief §10 says "no-overwrite guard" for the raw files; the generated scripts `file_delete` the raw file at INITRUN
   (the repo's convention for raw files since the earlier GEN_ scripts; the exclusive-create guard belongs to the results file, CLAUDE.md §7). Same as
   GEN_FSH; reported, not changed.
6. **Test script names**: header comment of `test_maf_corrected_code.py` lists the A1.2 edit; the number of tests 32 -> 36.

## Open items (not this stage)

- **Length of a `series()` with no length argument when `LookBack = 0` is unprobed** (planning chat item 3). (a) The manual says it takes LookBack's
  length; (b) not measured here. Candidate for a gotchas entry / a one-click probe later. Every series() the harness runs now has an explicit
  length, so the run does not depend on the answer.
- Four callers are compile-unverified until next used (§2).
- `Test_MAMA.c` returns at `if(is(LOOKBACK))` before the MAMA call (observed, not changed; §2).

## 6. Generated scripts and read-through (brief §10)

| Script | Path | Size | sha256 (in `[prerun].script_sha256` of the spec) |
|---|---|---|---|
| MAMA | `strategies/tests/GEN_MAM_MAMA.c` | 49 636 bytes, 953 lines | `ec9296175107826d632a49de330e2f08e6d68c7c0c1e80890c858303b5954adf` |
| FRAMA | `strategies/tests/GEN_FRA_FRAMA.c` | 37 076 bytes, 709 lines | `afa733e2cc186eeb5161ed2fbdbd3c96d5c9524aa6d7ef05ad114942b40db6c3` |

Method: reading the whole `run()` part and the start of each script, plus regex counts over the script and over every included file. Items:

| Check | MAMA (`GEN_MAM_MAMA.c`) | FRAMA (`GEN_FRA_FRAMA.c`) |
|---|---|---|
| includes in order, relative paths as `[zorro].include` | `<default.c>`, `../../indicators/ehlers/MAMA_Superseded.c`, `../../indicators/ehlers/MAMA.c`: OK | `<default.c>`, `.../FRAMA_Superseded.c`, `.../FRAMA.c`: OK |
| inputs built from integers before any indicator call, each `series(X, 34)` | 9 inputs, 9 series, all length 34; limits 1/2, 1/20, 3/10, 1/10 built from integers: OK | 15 prices + 16 band values (h = 2/1000), 31 series, all length 34; sc / of copies from integers: OK |
| decimal literals in the harness part | none; NC32 body: 0.0962, 0.5769, 0.075, 0.54, 0.2, 0.8, 0.33, 0.67 (deliberate float32, reported) | none; NC32 body: 4.6, 0.01 (deliberate) |
| generated statics reset at INITRUN | `mam_n`, `mam_done`, `mam_hdr`, `mam_rows`: all reset | `fra_n`, `fra_done`, `fra_hdr`, `fra_rows`: all reset |
| calls per bar (regex) | 67 = MAMACore 18 + 5 x 7 inline + 14 superseded | 108 = FRAMACore 30 + 4 x 13 inline + 26 superseded |
| order | variant-major, unconditional, fixed; NCS on 7 inputs (Y[266..278]) then NCS2 on the same 7 (Y[280..292]), as the stage 1 replay | NCS on 13 inputs (Y[246..258], T = 8) then NCS2 (Y[259..271]) |
| inline bodies | 5 (`mam_ncb/nch/ncf/nc32/ncp`), once each, prefixes `mxb_ mxh_ mxf_ mx32_ mxp_`, no statics | 4 (`fra_nce/ncn/nc32/nct`), once each, no statics |
| out-parameters | through 4 local scalars (`mam_o_fama/period/alpha/phase`), copied to Y[] right after each call, before the next | through 2 (`fra_o_dim/alpha`), copied likewise |
| raw file | `Data/GEN_MAM_raw.csv`, 304 columns (304 unique header names) | `Data/GEN_FRA_raw.csv`, 305 columns (305 unique) |
| writes before `quit()` (9d.4) | header + rows written, `mam_done` latched first, `quit()` last | same with `fra_done` |
| raw file absent | `C:/Zorro/Data/GEN_MAM_raw.csv` does not exist | `C:/Zorro/Data/GEN_FRA_raw.csv` does not exist |
| bare `Period` identifier | none (BarPeriod only) | none |
| **every `series()` has an explicit length** (planning chat item 4) | generated script 94 calls (9 inputs + 5 x 17 inline), MAMA.c 17, MAMA_Superseded.c 15: **none without a length** | generated script 47 calls (31 inputs + 4 x 4 inline), FRAMA.c 4, FRAMA_Superseded.c 0: **none without a length** |

No item failed; nothing was listed as "without length". Not checked (needs Zorro): that the scripts compile and that the row count / columns appear
as stated (the run card does that). Run card for the user, when the planning chat decides to run: **restart Zorro** before MAM and again before FRA
(A1.3); pick the script in the dropdown with the Script folder pointing at `strategies/tests` (Change Folder); one [Test] click each; expect no
line starting with `Error` in the Zorro window; expect `Data/GEN_MAM_raw.csv` (3000 rows, 304 columns) and `Data/GEN_FRA_raw.csv` (3000 rows, 305
columns). Not run here.

## Appendix A. Full texts

### `indicators/ehlers/MAMA.c` (git hash-object 74e3c731597d0bb95dca04b68e065802d8f7c3d1)

```c
// =============================================================================================================
// MAMA.c -- MESA Adaptive Moving Average (MAMA) and its FAMA
// =============================================================================================================
// SOURCE (a): Ehlers, J. F., "MESA Adaptive Moving Averages", Technical Analysis of Stocks & Commodities V.19:9
//   (2001), pp. 30-35, Sidebar Figure 1 (TradeStation code for MAMA and FAMA), PDF p. 5.
// FORMULA (a), in plain terms:
//   4-bar weighted Smooth of Price -> Hilbert-transform Detrender, I1 / Q1, jI / jQ (weights .0962 / .5769, times
//   .075*Period[1] + .54) -> phasor sums I2 / Q2 (.2 / .8 smoothed) -> homodyne Re / Im (.2 / .8 smoothed) ->
//   Period = 360 / ArcTangent(Im / Re) in degrees, bounded to .67x..1.5x the previous Period, then to 6..50, then
//   blended .2 / .8 with the previous Period -> Phase = ArcTangent(Q1 / I1) in degrees -> DeltaPhase = Phase[1] -
//   Phase, floored at 1 -> alpha = FastLimit / DeltaPhase clamped to [SlowLimit, FastLimit] -> MAMA = alpha*Price +
//   (1 - alpha)*MAMA[1]; FAMA = .5*alpha*MAMA + (1 - .5*alpha)*FAMA[1].
//   Defaults (a): Price (H+L)/2, FastLimit .5, SlowLimit .05. SmoothPeriod (.33 / .67) is computed and unused, as in
//   the source.
// USE (a): the source suggests the MAMA / FAMA crossover as a trend signal. Not implemented here; the NNFX baseline
//   rule is a template decision (PROJECT_STATE step 4).
//
// DEVIATIONS FIXED (b), review docs/harness/MAMA_FRAMA_SOURCE_REVIEW.md (MA-1..MA-9, appendix C-1..C-3, S1..S5):
//   MA-1 start-up as the source: every state starts at 0 and the body is computed from this instance's 6th call
//        (the old file seeded with the price, returned Price for 5 calls and started Period at 20).
//   MA-2 Period / Phase keep their value on a bar where Im or Re = 0 / I1 = 0 (the old file set 20 / 0).
//   MA-3 per-instance state and call counter (the old `static barCount` was shared by every call).
//   MA-4 every constant built from integers at run time (decimal literals are float32 in Zorro, gotchas 9d.1).
//   S1   exact pi built at run time (4*atan(1)) for the degree conversion: the old PI = 3.14159 moved Phase by up to
//        7.3e-5 degrees, more than the float32 literals did (D3 exception, review appendix S1). The old #ifndef PI
//        fallback (MA-5) never applied and is removed.
//   MA-7 MAMACore exports FAMA, Period, alpha and Phase; MAMA() is a thin wrapper with the old signature.
//   MA-8 this header. The old header's "APPROVED", lag, SNR, win-rate and 92.5% claims are dropped (unsourced or not
//        reproducible); its "1.5*0 = 0 trap" does not occur (b): the source's 6-bar floor acts.
//
// BEHAVIOUR (b) (review section 3 and appendix; MAMA_ArticleFidelity.toml observations):
//   * Zero start: MAMA / FAMA start at 0 and need about 500 bars to forget it (sines: start-up differences gone by
//     row ~520). (c) A strategy's LookBack must cover this.
//   * alpha is in [SlowLimit, FastLimit]; on short cycles it switches between the two limits (T = 10 / 20 bars:
//     FastLimit on 20% / 10% of bars, SlowLimit otherwise). Period follows the cycle within ~0.5% for T = 10..40 and
//     sits on its bounds outside 6..50.
//   * Ill-conditioned inputs: on a flat line (during start-up), a steady ramp and cycles shorter than 6 bars the
//     output depends on rounding (one ulp of input moved FAMA by up to 3.2e-2 / 2.8e-4 / 1.7e-2): the phase wrap at
//     +-90 degrees flips alpha between its limits. On a ramp Period wanders 36..48 and the lags are about 2.2 bars
//     (MAMA) / 7.0 bars (FAMA) at (.5, .05) (model, not exact).
//
// CALLER REQUIREMENTS: Price series of at least 4 values; call unconditionally on every bar (gotchas 3.1); build
//   FastLimit / SlowLimit from integers (var sl = 1; sl = sl/20; for .05, gotchas 9d.1). Use your own local
//   prefix: ma_ and maw_ belong to this file (gotchas 1.3).
// STATE: no statics; every series() call is unconditional and first; each instance has its own state. No includes
//   needed.
// VERIFICATION: analysis/harness/specs/MAMA_ArticleFidelity.toml (pre-registered 7713f5b). Not verified until that
//   run passes.
// =============================================================================================================

var MAMACore(vars Price, var FastLimit, var SlowLimit, var* pFama, var* pPeriod, var* pAlpha, var* pPhase)
{
    vars ma_n  = series(0, 2);     // per-instance CurrentBar (9d.9)
    vars ma_S  = series(0, 7);
    vars ma_De = series(0, 7);
    vars ma_I1 = series(0, 7);
    vars ma_Q1 = series(0, 7);
    vars ma_jI = series(0, 2);
    vars ma_jQ = series(0, 2);
    vars ma_I2 = series(0, 2);
    vars ma_Q2 = series(0, 2);
    vars ma_Re = series(0, 2);
    vars ma_Im = series(0, 2);
    vars ma_P  = series(0, 2);
    vars ma_SP = series(0, 2);
    vars ma_Ph = series(0, 2);
    vars ma_A  = series(0, 2);
    vars ma_M  = series(0, 2);
    vars ma_F  = series(0, 2);
    ma_n[0] = ma_n[1] + 1;
    // EasyLanguage: a var keeps its value on a bar where it is not assigned (MA-2)
    ma_S[0] = ma_S[1];   ma_De[0] = ma_De[1]; ma_I1[0] = ma_I1[1]; ma_Q1[0] = ma_Q1[1];
    ma_jI[0] = ma_jI[1]; ma_jQ[0] = ma_jQ[1]; ma_I2[0] = ma_I2[1]; ma_Q2[0] = ma_Q2[1];
    ma_Re[0] = ma_Re[1]; ma_Im[0] = ma_Im[1]; ma_P[0] = ma_P[1];   ma_SP[0] = ma_SP[1];
    ma_Ph[0] = ma_Ph[1]; ma_A[0] = ma_A[1];   ma_M[0] = ma_M[1];   ma_F[0] = ma_F[1];
    var ma_w1 = 962;  ma_w1 = ma_w1/10000;
    var ma_w2 = 5769; ma_w2 = ma_w2/10000;
    var ma_ka = 75;   ma_ka = ma_ka/1000;
    var ma_kb = 54;   ma_kb = ma_kb/100;
    var ma_a2 = 2;    ma_a2 = ma_a2/10;
    var ma_a8 = 8;    ma_a8 = ma_a8/10;
    var ma_c33 = 33;  ma_c33 = ma_c33/100;
    var ma_c67 = 67;  ma_c67 = ma_c67/100;
    var ma_up = 15;   ma_up = ma_up/10;
    var ma_dn = 67;   ma_dn = ma_dn/100;
    var ma_pi = 4;    ma_pi = ma_pi*atan(1);       // S1: exact pi at run time (D3)
    var ma_deg = 180; ma_deg = ma_deg/ma_pi;
    var ma_h = 1;     ma_h = ma_h/2;
    var ma_u = 1;
    var ma_pf = 0;
    var ma_p1 = 0;
    var ma_dp = 0;
    var ma_ah = 0;
    if(ma_n[0] > 5) {
        ma_S[0] = 4*Price[0] + 3*Price[1] + 2*Price[2] + Price[3];
        ma_S[0] = ma_S[0]/10;
        ma_pf = ma_ka*ma_P[1] + ma_kb;
        ma_De[0] = (ma_w1*ma_S[0] + ma_w2*ma_S[2] - ma_w2*ma_S[4] - ma_w1*ma_S[6])*ma_pf;
        ma_Q1[0] = (ma_w1*ma_De[0] + ma_w2*ma_De[2] - ma_w2*ma_De[4] - ma_w1*ma_De[6])*ma_pf;
        ma_I1[0] = ma_De[3];
        ma_jI[0] = (ma_w1*ma_I1[0] + ma_w2*ma_I1[2] - ma_w2*ma_I1[4] - ma_w1*ma_I1[6])*ma_pf;
        ma_jQ[0] = (ma_w1*ma_Q1[0] + ma_w2*ma_Q1[2] - ma_w2*ma_Q1[4] - ma_w1*ma_Q1[6])*ma_pf;
        ma_I2[0] = ma_I1[0] - ma_jQ[0];
        ma_Q2[0] = ma_Q1[0] + ma_jI[0];
        ma_I2[0] = ma_a2*ma_I2[0] + ma_a8*ma_I2[1];
        ma_Q2[0] = ma_a2*ma_Q2[0] + ma_a8*ma_Q2[1];
        ma_Re[0] = ma_I2[0]*ma_I2[1] + ma_Q2[0]*ma_Q2[1];
        ma_Im[0] = ma_I2[0]*ma_Q2[1] - ma_Q2[0]*ma_I2[1];
        ma_Re[0] = ma_a2*ma_Re[0] + ma_a8*ma_Re[1];
        ma_Im[0] = ma_a2*ma_Im[0] + ma_a8*ma_Im[1];
        if(ma_Im[0] != 0 && ma_Re[0] != 0) {
            ma_P[0] = atan(ma_Im[0]/ma_Re[0]);
            ma_P[0] = ma_P[0]*ma_deg;
            ma_P[0] = 360/ma_P[0];
        }
        ma_p1 = ma_P[1];
        if(ma_P[0] > ma_up*ma_p1) ma_P[0] = ma_up*ma_p1;
        if(ma_P[0] < ma_dn*ma_p1) ma_P[0] = ma_dn*ma_p1;
        if(ma_P[0] < 6)  ma_P[0] = 6;
        if(ma_P[0] > 50) ma_P[0] = 50;
        ma_P[0] = ma_a2*ma_P[0] + ma_a8*ma_p1;
        ma_SP[0] = ma_c33*ma_P[0] + ma_c67*ma_SP[1];
        if(ma_I1[0] != 0) {
            ma_Ph[0] = atan(ma_Q1[0]/ma_I1[0]);
            ma_Ph[0] = ma_Ph[0]*ma_deg;
        }
        ma_dp = ma_Ph[1] - ma_Ph[0];
        if(ma_dp < 1) ma_dp = 1;
        ma_A[0] = FastLimit/ma_dp;
        if(ma_A[0] < SlowLimit) ma_A[0] = SlowLimit;
        if(ma_A[0] > FastLimit) ma_A[0] = FastLimit;
        ma_M[0] = ma_A[0]*Price[0] + (ma_u - ma_A[0])*ma_M[1];
        ma_ah = ma_h*ma_A[0];
        ma_F[0] = ma_ah*ma_M[0] + (ma_u - ma_ah)*ma_F[1];
    }
    *pFama   = ma_F[0];
    *pPeriod = ma_P[0];
    *pAlpha  = ma_A[0];
    *pPhase  = ma_Ph[0];
    return ma_M[0];
}

var MAMA(vars Price, var FastLimit, var SlowLimit, var* outFAMA)
{
    var maw_1;
    var maw_2;
    var maw_3;
    return MAMACore(Price, FastLimit, SlowLimit, outFAMA, &maw_1, &maw_2, &maw_3);
}
```

### `indicators/ehlers/FRAMA.c` (git hash-object 1213ae9cb3b9a0752112c1653e2c658d6024bd7a)

```c
// =============================================================================================================
// FRAMA.c -- Fractal Adaptive Moving Average
// =============================================================================================================
// SOURCE (a): Ehlers, J. F., "Fractal Adaptive Moving Averages", Technical Analysis of Stocks & Commodities V.23:10
//   (2005), pp. 81-82, "FRAMA EasyLanguage code" sidebar, PDF p. 3.
// FORMULA (a): N = the FULL window, even (default 16). From High / Low:
//   N1 = (HH - LL)/(N/2) over bars 0..N/2-1; N2 the same over bars N/2..N-1; N3 = (HH - LL)/N over bars 0..N-1.
//   Dimen = (ln(N1 + N2) - ln(N3))/ln 2, computed only when N1, N2 and N3 are all > 0 (otherwise held; initial 0).
//   alpha = exp(-4.6*(Dimen - 1)) clamped to [.01, 1]; Filt = alpha*Price + (1 - alpha)*Filt[1];
//   Filt = Price for the first N bars. Price default (H+L)/2.
//
// DEVIATIONS FIXED (b), review docs/harness/MAMA_FRAMA_SOURCE_REVIEW.md (FR-1..FR-8, appendix C-1..C-3, S1..S5):
//   FR-1 the parameter is the source's N (full window). The old `T` was HALF the window, and every caller passed 16,
//        i.e. a 32-bar window: callers now pass N = 32 to keep that configuration (the source default is 16).
//   FR-2 Price, High and Low are parameters (the old file read priceHigh() / priceLow() itself).
//   FR-3 per-instance state (the old `static frama_prev` / `frama_init` were shared by every call: a second instance
//        or an asset loop was silently wrong, by up to 3.3e-2 on a random walk).
//   FR-4 start-up as the source (Filt = Price while CurrentBar < N + 1; the old file seeded on its first call).
//   FR-5 the source's guard: Dimen only when N1, N2, N3 > 0, otherwise held, and Filt always updated (the old file
//        returned without update when N3 <= 0 and could take log(0)).
//   FR-6 every constant built from integers at run time (4.6 and .01 were float32 literals, gotchas 9d.1).
//   FR-7 FRAMACore exports Dimen and alpha; FRAMA() is a thin wrapper.
//   FR-8 this header (the old "default T=16", "alpha -> 0.01" and "Week 9" statements are replaced).
//
// BEHAVIOUR (b) (review section 3 and appendix; FRAMA_ArticleFidelity.toml observations):
//   * Dimen <= 2 always (N1 + N2 <= 4*N3), so alpha >= exp(-4.6) = 0.01005 and the .01 floor never binds; the
//     article's "alpha = .01 at D = 2" is rounded.
//   * With overlapping bars (H > L) Dimen >= 1 (c). With H = L (close-only data) Dimen can fall below 1 and alpha
//     clamps to 1: FRAMA = price (a steady ramp gives out = price exactly).
//   * On a steady ramp with bars of constant range, Dimen and alpha are constant and FRAMA lags by (1 - alpha)/alpha:
//     34.05 bars at N = 16, 17.27 at N = 32 (range 0.004 around a slope of 1e-4 per bar).
//   * Start-up memory is long: where alpha sits near .01 (Dimen near 2, short cycles), differences from the start
//     fall as .99^n (about 2750 bars to 1e-12).
//
// CALLER REQUIREMENTS: N even (the source's rule; not checked in code); Price, High and Low series of at least N
//   values; call unconditionally on every bar (gotchas 3.1). For the source's inputs pass
//   series((priceHigh() + priceLow())/2, n), series(priceHigh(), n), series(priceLow(), n) with n >= N. Use your own
//   local prefix: fr_ and frw_ belong to this file (gotchas 1.3).
// STATE: no statics; every series() call is unconditional and first; each instance has its own state. No includes
//   needed.
// VERIFICATION: analysis/harness/specs/FRAMA_ArticleFidelity.toml (pre-registered 7713f5b). Not verified until that
//   run passes.
// =============================================================================================================

var FRAMACore(vars Price, vars High, vars Low, int N, var* pDim, var* pAlpha)
{
    vars fr_n = series(0, 2);      // per-instance CurrentBar (9d.9)
    vars fr_F = series(0, 2);
    vars fr_D = series(0, 2);
    vars fr_A = series(0, 2);
    fr_n[0] = fr_n[1] + 1;
    fr_F[0] = fr_F[1];  fr_D[0] = fr_D[1];  fr_A[0] = fr_A[1];   // EasyLanguage hold (FR-5: Dimen held)
    var fr_k  = 46;  fr_k  = fr_k/10;
    var fr_lo = 1;   fr_lo = fr_lo/100;
    var fr_u  = 1;
    var fr_l2 = 2;   fr_l2 = log(fr_l2);
    int fr_h = N/2;
    int fr_i;
    var fr_HH = High[0];
    var fr_LL = Low[0];
    for(fr_i = 1; fr_i < N; fr_i++) {
        if(High[fr_i] > fr_HH) fr_HH = High[fr_i];
        if(Low[fr_i]  < fr_LL) fr_LL = Low[fr_i];
    }
    var fr_N3 = fr_HH - fr_LL;  fr_N3 = fr_N3/N;
    fr_HH = High[0];  fr_LL = Low[0];
    for(fr_i = 0; fr_i < fr_h; fr_i++) {
        if(High[fr_i] > fr_HH) fr_HH = High[fr_i];
        if(Low[fr_i]  < fr_LL) fr_LL = Low[fr_i];
    }
    var fr_N1 = fr_HH - fr_LL;  fr_N1 = fr_N1/fr_h;
    fr_HH = High[fr_h];  fr_LL = Low[fr_h];
    for(fr_i = fr_h; fr_i < N; fr_i++) {
        if(High[fr_i] > fr_HH) fr_HH = High[fr_i];
        if(Low[fr_i]  < fr_LL) fr_LL = Low[fr_i];
    }
    var fr_N2 = fr_HH - fr_LL;  fr_N2 = fr_N2/fr_h;
    if(fr_N1 > 0 && fr_N2 > 0 && fr_N3 > 0) {
        fr_D[0] = log(fr_N1 + fr_N2) - log(fr_N3);
        fr_D[0] = fr_D[0]/fr_l2;
    }
    var fr_e = fr_D[0] - fr_u;
    fr_e = fr_k*fr_e;
    fr_A[0] = exp(-fr_e);
    if(fr_A[0] < fr_lo) fr_A[0] = fr_lo;
    if(fr_A[0] > fr_u)  fr_A[0] = fr_u;
    fr_F[0] = fr_A[0]*Price[0] + (fr_u - fr_A[0])*fr_F[1];
    if(fr_n[0] < N + 1) fr_F[0] = Price[0];
    *pDim   = fr_D[0];
    *pAlpha = fr_A[0];
    return fr_F[0];
}

var FRAMA(vars Price, vars High, vars Low, int N)
{
    var frw_1;
    var frw_2;
    return FRAMACore(Price, High, Low, N, &frw_1, &frw_2);
}
```

### `indicators/ehlers/MAMA_Superseded.c` (git hash-object c407c0a19b23e4d0b5f7f210717f9e9251a49f95)

```c
// =============================================================================================================
// SUPERSEDED -- do not use.
// Kept as the negative controls NCS / NCS2 of analysis/harness/specs/MAMA_ArticleFidelity.toml (D7 rule 7):
// the static barCount is shared by every call (MA-3); price-seeded start-up returning Price for the run's first
// 5 calls and Period / SmoothPeriod starting at 20 (MA-1); Period / Phase reset to 20 / 0 on unassigned bars (MA-2);
// float32 literals (MA-4); PI = 3.14159 (MA-5). Review: docs/harness/MAMA_FRAMA_SOURCE_REVIEW.md.
// Only edits vs the original MAMA.c (blob bab4cbbb5961be5720bce82fc6e487e283f7f00e, last commit 2a5eca5):
//   function MAMA -> MAMA_Superseded; every local / static identifier prefixed mao_ in code (barCount, Smooth,
//   Detrender, I1, Q1, jI, jQ, I2, Q2, Re, Im, Period, SmoothPeriod, Phase, MAMAout, FAMAout, DeltaPhase, alpha;
//   flat namespace, gotchas 1.3); an explicit length 7 on each of the 15 series() calls (the original had none, so
//   each took LookBack's length: zorro.chm, series; the generated scripts set LookBack = 0, the original ran with
//   LookBack >= 7; 7 > the largest index read, [6]; Amendment 1 A1.2); this header. The parameters Price, FastLimit,
//   SlowLimit, outFAMA keep their names (the generated script passes them positionally). NO other edit: the #ifndef
//   PI block, the literals, the static and its INITRUN reset are unchanged. The original header follows, unchanged (history, not fact).
// Corrected file: MAMA.c (MAMACore / MAMA).
// =============================================================================================================
///////////////////////////////////////////////////////
// MESA Adaptive Moving Average (MAMA) and FAMA
// John Ehlers
// Source: "MESA Adaptive Moving Averages"
//         TASC S&C V.19:9, September 2001
// ─────────────────────────────────────────────────
// Purpose:
//   Adaptive trend indicator using the Hilbert
//   Transform to measure instantaneous phase rate
//   of change and adapt smoothing speed to the
//   current dominant market cycle.
//
// Pipeline (7 stages):
//   Price → Smooth → Detrender → I1, Q1
//   → jI, jQ → I2, Q2 (phasor addition)
//   → Homodyne Discriminator → Period
//   → DeltaPhase → alpha → MAMA, FAMA
//
// Inputs:
//   Price     - price series, typically (H+L)/2
//   FastLimit - maximum alpha (default 0.5)
//   SlowLimit - minimum alpha (default 0.05)
//   outFAMA   - pointer to receive FAMA value
//
// Outputs:
//   return    - MAMA value
//   *outFAMA  - FAMA value
//
// Signal (NNFX Baseline role):
//   MAMA crosses above FAMA → bullish / go long
//   MAMA crosses below FAMA → bearish / go short
//   Spread width = trend strength proxy
//   Requires C1/C2 confirmation before entry
//
// Parameters (validated defaults):
//   FastLimit = 0.5   (Ehlers default — keep)
//   SlowLimit = 0.05  (Ehlers default — keep)
//   Low sensitivity to parameter changes confirmed
//   in Day 5 sensitivity analysis (FL=0.3 and
//   SL=0.10 variants gave negligible difference)
//
// Implementation notes:
//   - Period initialised to 20 (not 0) to prevent
//     bound collapse on first bar
//   - barCount guard: returns Price[0] for first 5 bars
//   - atan() used in degrees via *180/PI conversion
//   - Alpha is bimodal in practice: 92.5% of bars
//     clamp at FastLimit or SlowLimit (documented
//     Ehlers behaviour, not a bug)
//   - FAMA always smoother than MAMA (half alpha)
//   - Raw crossover: 51.3% win rate, 0.92 W/L —
//     must be paired with confirmation indicator
//
// Validation status: APPROVED — Week 7
//   EUR/USD D1 : 2591 bars, 2015-2024  ✓
//   BTC/USD H4 : 7529 bars, 2020-2023  ✓
//   Lag  FX=0 bars  BTC=0 bars         ✓
//   SNR  FX=1.22x   BTC=1.19x          ✓
///////////////////////////////////////////////////////

#ifndef PI
#define PI 3.14159265358979
#endif

var MAMA_Superseded(vars Price, var FastLimit, var SlowLimit, var* outFAMA)
{
    // Bar counter: formula needs 6 bars of history before computing
    static int mao_barCount = 0;
    if(is(INITRUN)) mao_barCount = 0;   // else the 5-bar warmup guard never fires on a stale run
    mao_barCount++;

    // All intermediate variables declared as series
    // (series retains history bar-to-bar across calls)
    var* mao_Smooth       = series(Price[0], 7);   // needs [0]..[6]
    var* mao_Detrender    = series(0.0, 7);        // needs [0]..[6]
    var* mao_I1           = series(0.0, 7);        // needs [0]..[6]
    var* mao_Q1           = series(0.0, 7);        // needs [0]..[6]
    var* mao_jI           = series(0.0, 7);
    var* mao_jQ           = series(0.0, 7);
    var* mao_I2           = series(0.0, 7);        // needs [0]..[1]
    var* mao_Q2           = series(0.0, 7);        // needs [0]..[1]
    var* mao_Re           = series(0.0, 7);        // needs [0]..[1]
    var* mao_Im           = series(0.0, 7);        // needs [0]..[1]
    // Period initialized to 20: prevents bound collapse on first bar
    // (published code initializes to 0 which causes 1.5*0=0 trap)
    var* mao_Period       = series(20.0, 7);       // needs [0]..[1]
    var* mao_SmoothPeriod = series(20.0, 7);       // needs [0]..[1]
    var* mao_Phase        = series(0.0, 7);        // needs [0]..[1]
    var* mao_MAMAout      = series(Price[0], 7);   // needs [0]..[1]
    var* mao_FAMAout      = series(Price[0], 7);   // needs [0]..[1]

    // Return flat until 6 bars of history accumulated
    if(mao_barCount <= 5) {
        *outFAMA = Price[0];
        return Price[0];
    }

    // Stage 1: Smooth price
    // 4-bar weighted average, recent bars weighted more
    mao_Smooth[0] = (4.0*Price[0] + 3.0*Price[1] + 2.0*Price[2] + Price[3]) / 10.0;

    // Stage 2: Detrender - first Hilbert Transform pass
    // Removes trend component, isolates dominant cycle
    // (.075*Period[1]+.54) = period-adaptive amplitude correction
    mao_Detrender[0] = (0.0962*mao_Smooth[0] + 0.5769*mao_Smooth[2]
                   - 0.5769*mao_Smooth[4] - 0.0962*mao_Smooth[6])
                   * (0.075*mao_Period[1] + 0.54);

    // Stage 3: InPhase and Quadrature components
    // Q1: second HT pass on Detrender -> 90 degree phase advance
    // I1: Detrender delayed 3 bars -> time-aligns with Q1
    mao_Q1[0] = (0.0962*mao_Detrender[0] + 0.5769*mao_Detrender[2]
            - 0.5769*mao_Detrender[4] - 0.0962*mao_Detrender[6])
            * (0.075*mao_Period[1] + 0.54);
    mao_I1[0] = mao_Detrender[3];

    // Stage 4: Advance phase of I1 and Q1 by 90 degrees
    // jI and jQ feed phasor addition in Stage 5
    mao_jI[0] = (0.0962*mao_I1[0] + 0.5769*mao_I1[2]
            - 0.5769*mao_I1[4] - 0.0962*mao_I1[6])
            * (0.075*mao_Period[1] + 0.54);
    mao_jQ[0] = (0.0962*mao_Q1[0] + 0.5769*mao_Q1[2]
            - 0.5769*mao_Q1[4] - 0.0962*mao_Q1[6])
            * (0.075*mao_Period[1] + 0.54);

    // Stage 5: Phasor addition for 3-bar averaging
    // Reinforces true cycle signal, partially cancels noise
    mao_I2[0] = mao_I1[0] - mao_jQ[0];
    mao_Q2[0] = mao_Q1[0] + mao_jI[0];
    // Smooth I2 and Q2 before discriminator
    mao_I2[0] = 0.2*mao_I2[0] + 0.8*mao_I2[1];
    mao_Q2[0] = 0.2*mao_Q2[0] + 0.8*mao_Q2[1];

    // Stage 6: Homodyne Discriminator
    // Multiplies signal by itself delayed 1 bar
    // Re ~ cos(DeltaPhase), Im ~ sin(DeltaPhase)
    mao_Re[0] = mao_I2[0]*mao_I2[1] + mao_Q2[0]*mao_Q2[1];
    mao_Im[0] = mao_I2[0]*mao_Q2[1] - mao_Q2[0]*mao_I2[1];
    // Smooth Re and Im
    mao_Re[0] = 0.2*mao_Re[0] + 0.8*mao_Re[1];
    mao_Im[0] = 0.2*mao_Im[0] + 0.8*mao_Im[1];

    // Extract dominant cycle period from phase change
    // atan() returns radians -> *180/PI converts to degrees
    // Published: Period = 360/ArcTangent(Im/Re) [degrees]
    if(mao_Im[0] != 0.0 && mao_Re[0] != 0.0)
        mao_Period[0] = 360.0 / (atan(mao_Im[0]/mao_Re[0]) * 180.0/PI);

    // Five-layer period bounding (exact published bounds)
    if(mao_Period[0] > 1.5*mao_Period[1])  mao_Period[0] = 1.5*mao_Period[1];
    if(mao_Period[0] < 0.67*mao_Period[1]) mao_Period[0] = 0.67*mao_Period[1];
    if(mao_Period[0] < 6.0)            mao_Period[0] = 6.0;
    if(mao_Period[0] > 50.0)           mao_Period[0] = 50.0;
    mao_Period[0] = 0.2*mao_Period[0] + 0.8*mao_Period[1];
    mao_SmoothPeriod[0] = 0.33*mao_Period[0] + 0.67*mao_SmoothPeriod[1];

    // Stage 7: Phase measurement from Q1/I1
    // atan() returns radians -> convert to degrees
    if(mao_I1[0] != 0.0)
        mao_Phase[0] = atan(mao_Q1[0]/mao_I1[0]) * 180.0/PI;

    // DeltaPhase: reversed subtraction per Ehlers convention
    // (phase decreases forward in time in his framework)
    var mao_DeltaPhase = mao_Phase[1] - mao_Phase[0];
    if(mao_DeltaPhase < 1.0) mao_DeltaPhase = 1.0;

    // Adaptive alpha: FastLimit/DeltaPhase, bounded both sides
    var mao_alpha = FastLimit / mao_DeltaPhase;
    if(mao_alpha < SlowLimit) mao_alpha = SlowLimit;
    if(mao_alpha > FastLimit) mao_alpha = FastLimit;

    // MAMA: adaptive EMA with variable alpha
    mao_MAMAout[0] = mao_alpha*Price[0] + (1.0 - mao_alpha)*mao_MAMAout[1];

    // FAMA: follows MAMA at half alpha
    // Guaranteed slower than MAMA -> crossover is meaningful
    mao_FAMAout[0] = 0.5*mao_alpha*mao_MAMAout[0] + (1.0 - 0.5*mao_alpha)*mao_FAMAout[1];

    *outFAMA = mao_FAMAout[0];
    return mao_MAMAout[0];
}
```

### `indicators/ehlers/FRAMA_Superseded.c` (git hash-object 81356dbde9da98d8555e8191c45bfe57c19a8d79)

```c
// =============================================================================================================
// SUPERSEDED -- do not use.
// Kept as the negative controls NCS / NCS2 of analysis/harness/specs/FRAMA_ArticleFidelity.toml (D7 rule 7):
// the statics frama_prev / frama_init (here fro_prev / fro_init) are the IIR state, shared by every call (FR-3);
// half-window parameter T (FR-1); price seed on the run's first call (FR-4); `if(N3 <= 0) return prev` without an
// N1 / N2 condition (FR-5); float32 literals 4.6 / 0.01 (FR-6). Review: docs/harness/MAMA_FRAMA_SOURCE_REVIEW.md.
// Only edits vs the original FRAMA.c (blob 3352fbe04ed691e479564bc63d46ae181334f9bb, last commit 2a5eca5):
//   FRAMA(int T) -> FRAMA_Superseded(vars Price, vars High, vars Low, int T); the input (the ONLY behavioural
//   edit): series(priceHigh()) / series(priceLow()) -> the High / Low parameters and (priceHigh() + priceLow()) / 2.0
//   -> Price[0]; prefix frama_ -> fro_ (flat namespace, gotchas 1.3); this header. Statics, INITRUN reset,
//   literals, guard and arithmetic unchanged. The original header follows, unchanged (history, not fact).
// Corrected file: FRAMA.c (FRAMACore / FRAMA).
// =============================================================================================================
// =============================================================
// FRAMA.c — Fractal Adaptive Moving Average
// Author: John Ehlers | Implementation: Week 9
// Reference: "Fractal Adaptive Moving Averages" TASC
//
// Adapts EMA speed using fractal dimension of price:
//   D → 1 (trending)  → alpha → 1.0  (fast, tracks price)
//   D → 2 (noisy)     → alpha → 0.01 (slow, ignores noise)
//
// Parameters:
//   T : half-period (full window = 2T bars, default T=16)
//
// Returns: FRAMA value (adaptive EMA of median price)
// =============================================================

var FRAMA_Superseded(vars Price, vars High, vars Low, int T) {

    // --- Run-scoped reset ---------------------------------------
    // Lite-C statics persist for the lifetime of the LOADED script
    // — across repeated [Test] presses and across Train->Test. The
    // old value-based seed below could not fire when fro_prev
    // held a leftover value from a previous run, so FRAMA would
    // begin holding the PREVIOUS asset's level.
    //
    // Editing a source file forces a recompile, which zeroes the
    // statics — so the normal edit-and-rerun workflow was safe. A
    // repeat [Test] press without an edit was not. Week 13 Day 2:
    // the May 2026 BTC baseline differs from a clean run by 1.8e-3
    // on row 1, decaying over subsequent bars — leftover EUR/USD
    // state in the baseline, not in the clean run.
    //
    // Flag is cleared here; seeding happens on the first valid bar.
    static int fro_init = 0;
    if(is(INITRUN)) fro_init = 0;


    // --- Build High/Low series for range computation ---
    vars fro_High = High;   // input edit: was series(priceHigh())
    vars fro_Low  = Low;    // input edit: was series(priceLow())

    // --- Median price ---
    var fro_price = Price[0];   // input edit: was (priceHigh() + priceLow()) / 2.0

    // --- Box 1: bars 0 to T-1 (most recent half) ---
    var fro_Hi1 = fro_High[0];
    var fro_Lo1 = fro_Low[0];
    int fro_i;
    for(fro_i = 1; fro_i < T; fro_i++) {
        if(fro_High[fro_i] > fro_Hi1) fro_Hi1 = fro_High[fro_i];
        if(fro_Low[fro_i]  < fro_Lo1) fro_Lo1 = fro_Low[fro_i];
    }
    var fro_N1 = (fro_Hi1 - fro_Lo1) / T;

    // --- Box 2: bars T to 2T-1 (older half) ---
    var fro_Hi2 = fro_High[T];
    var fro_Lo2 = fro_Low[T];
    for(fro_i = T+1; fro_i < 2*T; fro_i++) {
        if(fro_High[fro_i] > fro_Hi2) fro_Hi2 = fro_High[fro_i];
        if(fro_Low[fro_i]  < fro_Lo2) fro_Lo2 = fro_Low[fro_i];
    }
    var fro_N2 = (fro_Hi2 - fro_Lo2) / T;

    // --- Full window: bars 0 to 2T-1 ---
    var fro_Hi3 = fro_Hi1;
    var fro_Lo3 = fro_Lo1;
    for(fro_i = T; fro_i < 2*T; fro_i++) {
        if(fro_High[fro_i] > fro_Hi3) fro_Hi3 = fro_High[fro_i];
        if(fro_Low[fro_i]  < fro_Lo3) fro_Lo3 = fro_Low[fro_i];
    }
    var fro_N3 = (fro_Hi3 - fro_Lo3) / (2.0 * T);

    // --- IIR state: seed to price on the first valid bar ---
    // Flag-based, not value-based. See the INITRUN block above.
    static var fro_prev = 0;
    if(!fro_init) {
        fro_prev = fro_price;
        fro_init = 1;
    }

    // --- Guard: flat price → no update ---
    if(fro_N3 <= 0) return fro_prev;

    // --- Fractal dimension ---
    var fro_D = (log(fro_N1 + fro_N2) - log(fro_N3)) / log(2.0);

    // --- Adaptive alpha ---
    var fro_alpha = exp(-4.6 * (fro_D - 1.0));
    if(fro_alpha > 1.0)  fro_alpha = 1.0;
    if(fro_alpha < 0.01) fro_alpha = 0.01;

    // --- EMA update ---
    var fro_out = fro_alpha * fro_price + (1.0 - fro_alpha) * fro_prev;
    fro_prev = fro_out;

    return fro_out;
}```

## Appendix B. Caller and gotchas diffs (`git diff --ignore-cr-at-eol`)

```diff
diff --git a/docs/ZORRO_LIGHTC_GOTCHAS.md b/docs/ZORRO_LIGHTC_GOTCHAS.md
index 0afc561..da7e4e9 100644
--- a/docs/ZORRO_LIGHTC_GOTCHAS.md
+++ b/docs/ZORRO_LIGHTC_GOTCHAS.md
@@ -20,12 +20,13 @@ Light-C is not full C. Constructs that compile elsewhere will fail here.
 |---|---|---|---|
 | 1.1 | **No ternary operator `? :`** | `syntax error` at the line | Explicit `if`/`else` |
 | 1.2 | `Period` is a reserved word | Compile error or unexpected behaviour | Use `BarPeriod`, or a prefixed local. (b, Zorro 3.11, H1 run 2) `int Period` as a function parameter compiles with no Error line. Not tested as a global or static name: keep avoiding it there (c). |
-| 1.3 | 🔇 **Flat variable namespace across all included files** | Silent collision; one file overwrites another's local | Prefix every local: `rm_`, `rmo_`, `cc_`, `cyc_`, `ab_`, `mstc_`, `fi_` (FisherCore), `fto_` (FisherTransform_Superseded), `ift_` (Test_Fisher_IFT_COG) |
+| 1.3 | 🔇 **Flat variable namespace across all included files** | Silent collision; one file overwrites another's local | Prefix every local: `rm_`, `rmo_`, `cc_`, `cyc_`, `ab_`, `mstc_`, `fi_` (FisherCore), `fto_` (FisherTransform_Superseded), `ift_` (Test_Fisher_IFT_COG), `ma_` (MAMACore), `maw_` (MAMA wrapper), `mao_` (MAMA_Superseded), `fr_` (FRAMACore), `frw_` (FRAMA wrapper), `fro_` (FRAMA_Superseded) |
 | 1.4 | `void run()`, not `function run()` | Compile error | — |
 
 **Prefixes in use (do not reuse):**
 `cc_` CyberCycle · `cyc_` CorrelationCycle · `rm_`/`rmo_` RecursiveMedian ·
-`ab_` AlphaBetaFilter · `mstc_` MESAStochastic · `fi_` FisherCore · `fto_` FisherTransform_Superseded · `ift_` Test_Fisher_IFT_COG
+`ab_` AlphaBetaFilter · `mstc_` MESAStochastic · `fi_` FisherCore · `fto_` FisherTransform_Superseded · `ift_` Test_Fisher_IFT_COG ·
+`ma_` MAMACore · `maw_` MAMA wrapper · `mao_` MAMA_Superseded · `fr_` FRAMACore · `frw_` FRAMA wrapper · `fro_` FRAMA_Superseded
 
 ---
 
@@ -311,3 +312,4 @@ Found building harness H1 for `SuperSmoother2Pole.c`. Runs: H1 run 1 (FAIL, inpu
 | 2026-11-18 | Added §9d.9: `Bar` is global — a per-instance CurrentBar counter for EasyLanguage start-up rules (USE run 1) |
 | 2026-11-20 | §9d.6 addendum (b): FSH run 1 confirms `series()` first-value padding for a caller-built input series read by MaxVal / MinVal (start-up <= 8.9e-16) |
 | 2026-11-20 | §1.3: prefixes `fi_` (FisherCore), `fto_` (FisherTransform_Superseded), `ift_` (Test_Fisher_IFT_COG) added to those in use |
+| 2026-11-20 | §1.3: prefixes `ma_` (MAMACore), `maw_` (MAMA wrapper), `mao_` (MAMA_Superseded), `fr_` (FRAMACore), `frw_` (FRAMA wrapper), `fro_` (FRAMA_Superseded) added to those in use (MAF stage 2) |
diff --git a/strategies/tests/Test_FRAMA_Laguerre_DSMA.c b/strategies/tests/Test_FRAMA_Laguerre_DSMA.c
index 48edd32..4335e60 100644
--- a/strategies/tests/Test_FRAMA_Laguerre_DSMA.c
+++ b/strategies/tests/Test_FRAMA_Laguerre_DSMA.c
@@ -43,7 +43,7 @@
 // ---------------------------------------------------
 
 // --- Indicator parameters ---
-#define FRAMA_T      16    // half-period: full window = 32 bars
+#define FRAMA_N      32    // full window (source N); was T = 16 (half window) = the same 32 bars
 #define LAG_GAMMA    0.5   // Laguerre memory depth
 #define DSMA_PERIOD  20    // StdDev + SuperSmoother lookback
 #define HP_PERIOD    48    // RoofingFilter highpass cutoff
@@ -84,7 +84,11 @@ void run() {
     // Compute indicators on EVERY bar including lookback
     // so internal state is fully warmed up before output starts
     var rf_value  = RoofingFilter(Close, HP_PERIOD, SS_PERIOD);
-    var frama_val = FRAMA(FRAMA_T);
+    // FRAMA inputs as the source (Price = (H+L)/2, High, Low); own prefix, unconditional, >= FRAMA_N values
+    vars fld_mid = series((priceHigh() + priceLow())/2, FRAMA_N);
+    vars fld_hi  = series(priceHigh(), FRAMA_N);
+    vars fld_lo  = series(priceLow(), FRAMA_N);
+    var frama_val = FRAMA(fld_mid, fld_hi, fld_lo, FRAMA_N);
     var lag_val   = Laguerre(LAG_GAMMA);
     var dsma_val  = DSMA(rf_value, DSMA_PERIOD);
 
diff --git a/strategies/tests/Test_FRAMA_vs_MAMA.c b/strategies/tests/Test_FRAMA_vs_MAMA.c
index 1009ade..f8b10c8 100644
--- a/strategies/tests/Test_FRAMA_vs_MAMA.c
+++ b/strategies/tests/Test_FRAMA_vs_MAMA.c
@@ -13,12 +13,11 @@
 #include "../../indicators/ehlers/MAMA.c"
 #include "../../indicators/ehlers/FRAMA.c"
 
-// --- MAMA parameters (Ehlers defaults) ---
-#define FAST_LIMIT  0.5
-#define SLOW_LIMIT  0.05
+// --- MAMA parameters (Ehlers defaults .5 / .05): built from integers at run time in run() (gotchas 9d.1:
+//     a decimal literal such as 0.05 would be float32 at the call) ---
 
 // --- FRAMA parameter ---
-#define FRAMA_T     16     // half-period, full window = 32 bars
+#define FRAMA_N     32     // full window (source N); was T = 16 (half window) = the same 32 bars
 
 void run() {
 
@@ -34,9 +33,18 @@ void run() {
     // --- FAMA output pointer ---
     var fama_val = 0;
 
+    // --- MAMA limits from integers: FastLimit 1/2, SlowLimit 1/20 ---
+    var fvm_fl = 1;  fvm_fl = fvm_fl/2;
+    var fvm_sl = 1;  fvm_sl = fvm_sl/20;
+
+    // --- FRAMA inputs as the source (Price = (H+L)/2, High, Low); own prefix, unconditional, >= FRAMA_N values ---
+    vars fvm_mid = series((priceHigh() + priceLow())/2, FRAMA_N);
+    vars fvm_hi  = series(priceHigh(), FRAMA_N);
+    vars fvm_lo  = series(priceLow(), FRAMA_N);
+
     // --- Compute indicators on every bar including lookback ---
-    var mama_val = MAMA(Price, FAST_LIMIT, SLOW_LIMIT, &fama_val);
-    var frama_val = FRAMA(FRAMA_T);
+    var mama_val = MAMA(Price, fvm_fl, fvm_sl, &fama_val);
+    var frama_val = FRAMA(fvm_mid, fvm_hi, fvm_lo, FRAMA_N);
 
     if(is(LOOKBACK)) return;
 
diff --git a/strategies/tests/Test_MAMA.c b/strategies/tests/Test_MAMA.c
index bdb895b..c6036ef 100644
--- a/strategies/tests/Test_MAMA.c
+++ b/strategies/tests/Test_MAMA.c
@@ -29,7 +29,9 @@ void run()
 
     // --- Calculate MAMA and FAMA ---
     var fama = 0.0;
-    var mama = MAMA(Price, 0.5, 0.05, &fama);
+    var tm_fl = 1;  tm_fl = tm_fl/2;     // FastLimit .5 from integers (gotchas 9d.1)
+    var tm_sl = 1;  tm_sl = tm_sl/20;    // SlowLimit .05 from integers
+    var mama = MAMA(Price, tm_fl, tm_sl, &fama);
 
     // --- Sequential bar counter ---
     static int barCount = 0;
diff --git a/strategies/tests/Test_UltimateChannelBands.c b/strategies/tests/Test_UltimateChannelBands.c
index ffe42a1..aa27870 100644
--- a/strategies/tests/Test_UltimateChannelBands.c
+++ b/strategies/tests/Test_UltimateChannelBands.c
@@ -39,6 +39,7 @@
 // RSIH — fixed length, project Week 13 convention. Ehlers' 14 is
 // inherited from Wilder and is not his recommendation. Adaptive
 // variant registered for later comparison against this baseline.
+#define FRAMA_N       32    // full window (source N); was T = 16 (half window) = the same 32 bars
 #define RSIH_LENGTH   20
 
 // Laguerre oscillator — ARTICLE defaults, not the Week 13
@@ -79,8 +80,12 @@ void run() {
     // P3 split variable. FRAMA deliberately, not the centre line:
     // the band width IS built from (Close - centre), so splitting
     // on that would be circular. FRAMA shares no term with either
-    // width. T=16 per Week 9.
-    var frama = FRAMA(16);
+    // width. N = 32 (full window, source N; was T = 16 per Week 9 = the same 32 bars).
+    // FRAMA inputs as the source (Price = (H+L)/2, High, Low); own prefix, unconditional, >= FRAMA_N values.
+    vars ucbf_mid = series((priceHigh() + priceLow())/2, FRAMA_N);
+    vars ucbf_hi  = series(priceHigh(), FRAMA_N);
+    vars ucbf_lo  = series(priceLow(), FRAMA_N);
+    var frama = FRAMA(ucbf_mid, ucbf_hi, ucbf_lo, FRAMA_N);
 
     // NATR must be a series for the regime window. Value passed
     // INTO series() — writing [0] afterward shifts the wrong value
```
