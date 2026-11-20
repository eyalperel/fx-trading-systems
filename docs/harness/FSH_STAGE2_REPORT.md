# FSH stage 2 report — corrected FisherTransform.c, FisherTransform_Superseded.c, callers, Amendment 1, generated script

Written for: the planning chat and the user (review of stage 2 before commit). 2026-11-19, branch `harness-fisher`, Claude Code (Sonnet, Medium). Brief: `docs/harness/FISHER_STAGE2_PROMPT.md`. Spec pre-registered at `258b24a`. Nothing committed, Zorro not run. Labels: (a) source states, (b) measured here, (c) inference.

## 0. Summary

| Item | Result |
|---|---|
| Corrected `FisherTransform.c` (FisherCore + wrapper, spec lines verbatim) | written, blob `a05231d426a93bf8a0fe024b3283b55d01cc4531` |
| `FisherTransform_Superseded.c` (NCS / NCT control) | written, blob `970c76b7ac142b03ed702c814dda312413465d51` |
| Callers (F-2) | 2 updated, compile-unverified |
| `test_fsh_corrected_code.py` | 19 tests, all guards seen to fire |
| Generator change | none (no A1.2) |
| Pre-run i / ii / iii / iv / v (+ vi callers) | all PASS |
| Suite | before TOTAL 719 PASS 719; after TOTAL 738 PASS 738 FAIL 0 ERROR 0 SKIP 0 (two runs after the last change, same result; the first after the test and script, the second after Amendment 1) |
| Generated script | `strategies/tests/GEN_FSH_FisherTransform.c`, sha256 `4429d87d9154778dac10aa160605a9b66e655d69b04462284f3cd9e119526f19` |
| STOP conditions | none triggered |
| Criterion / tolerance / table / floor / effect / variant changed | none (the spec diff is 32 added lines, 0 removed) |

## 1. `indicators/ehlers/FisherTransform.c` (full text)

The two function bodies are the spec's `[corrected_code]` lines and wrapper lines, only indented by four spaces (test (i) is whitespace-normalised). The header is comments only and replaces the old one; every statement is labelled (a) / (b) / (c) as the brief lists. Dropped: the unsourced "extreme readings (±2.5) are statistically meaningful" claim. Added (c): the default `series()` length is LookBack (from the spec notes).

```c
// =============================================================================
// FisherTransform.c  (corrected; replaces the version of blob 259954ed, see below)
//
// Source (a): Ehlers, "Using The Fisher Transform", Technical Analysis of Stocks &
//   Commodities V.20:11 (2002), pp. 40-42, Fig. 5 (EasyLanguage), p. 41.
// Formula in Light-C terms (a): Price input (default (H+L)/2), Len (default 10);
//   raw   = 2*((Price - MinL)/(MaxH - MinL) - .5), MinL / MaxH over the last Len values
//           of Price including the current one;
//   Value1 = .33*raw + .67*Value1[1];
//   if Value1 > .99 then Value1 = .999; if Value1 < -.99 then Value1 = -.999
//           (the trigger and the set value differ, as printed);
//   Fish  = .5*ln((1 + Value1)/(1 - Value1)) + .5*Fish[1];
//   trigger = Fish[1].
// (a) The book version (Cybernetic Analysis, 2004, Fig. 1.7, p. 7: .5 / .5, .9999,
//   .25*ln) is a DIFFERENT indicator; it is not implemented here (review section 1).
//
// Deviations fixed (b), review docs/harness/FISHER_SOURCE_REVIEW.md (bdc83da):
//   F-1 per-instance state: the old static ft_Value1, static ft_Fish and the global
//       ft_Trigger were shared by every call, so a second instance or an asset loop
//       silently corrupted every instance (up to 2.7 in Fish; review section 3).
//   F-2 Price is a parameter (the old file read priceHigh() / priceLow() itself).
//   F-3 the constants are built from integers (the old float32 literals moved Fish
//       by up to 1.29e-5).
//   F-7 FisherCore exports raw, Value1, the range and the trigger.
//   F-8 this header.
// Outputs after the first ~100 bars of a single instance on one asset differ from the
// old file only by the F-3 rounding (<= 1.3e-5 on these test inputs); any second
// instance or asset loop was wrong.
//
// Our guard (b, F-4): when MaxH - MinL is not > 0 (flat window), raw = 0
//   (mid-channel). Not in the source (it divides by zero).
//
// Caller requirements:
//   - pass a series of at least Len values (MaxVal / MinVal read Price[0..Len-1]);
//     the default series() length is LookBack (c).
//   - for the source's input use  vars fi_mid = series((priceHigh() + priceLow())/2);
//   - call unconditionally every bar, before any LOOKBACK return (gotchas 3.1).
//   - trigger: FisherCore(..., &trig) or the caller's own Fish[1].
//
// Start-up: the source defines none (review F-5). Value1 and Fish start at 0 on the
//   instance's first call; the window is padded with the first value until Len values
//   exist (gotchas 9d.6). Treat the first ~100 bars as warm-up (the harness uses W = 700).
//
// Behaviour (b, review section 3 and the spec observations): raw in [-1, 1];
//   |Value1| <= .999; |Fish| <= ln(1999) = 7.6004 (reached on a steady trend).
//   Fisher SATURATES on long cycles: at T = 100 about two thirds of bars sit at the
//   clamp and Fish at about +-7.6; at T = 40, Len 10, 20% of bars. Readings beyond
//   +-2.5 are routine on any cycle with T >= 20 (Len 10). The Fish feedback is not an
//   EMA: the gain from arctanh(Value1) to Fish is 1/(1 - .5) = 2.
//
// Use stated by the source (a): Fish crossing its one-bar-delayed trigger identifies
//   cyclic turning points. Not implemented here.
//
// STATE: no statics; both series() calls are unconditional and first; each instance
//   has its own state. No includes needed.
//
// Verification: analysis/harness/specs/FSH_ArticleFidelity.toml (pre-registered 258b24a).
//   NOT VERIFIED until that run passes.
// =============================================================================

var FisherCore(vars Price, int Len, var* pRaw, var* pV1, var* pRng, var* pTrig) {
    vars fi_V = series(0, 2);
    vars fi_F = series(0, 2);
    var fi_a = 33;   fi_a = fi_a/100;
    var fi_b = 67;   fi_b = fi_b/100;
    var fi_t = 99;   fi_t = fi_t/100;
    var fi_c = 999;  fi_c = fi_c/1000;
    var fi_h = 1;    fi_h = fi_h/2;
    var fi_hi = MaxVal(Price, Len);
    var fi_lo = MinVal(Price, Len);
    var fi_rng = fi_hi - fi_lo;
    var fi_raw = 0;
    if(fi_rng > 0) {
        fi_raw = Price[0] - fi_lo;
        fi_raw = fi_raw/fi_rng;
        fi_raw = fi_raw - fi_h;
        fi_raw = fi_raw*2;
    }
    fi_V[0] = fi_a*fi_raw + fi_b*fi_V[1];
    var fi_nt = 0;   fi_nt = fi_nt - fi_t;
    var fi_nc = 0;   fi_nc = fi_nc - fi_c;
    if(fi_V[0] > fi_t)  fi_V[0] = fi_c;
    if(fi_V[0] < fi_nt) fi_V[0] = fi_nc;
    var fi_u = 1;
    var fi_num = fi_u + fi_V[0];
    var fi_den = fi_u - fi_V[0];
    fi_F[0] = fi_h*log(fi_num/fi_den) + fi_h*fi_F[1];
    *pRaw  = fi_raw;
    *pV1   = fi_V[0];
    *pRng  = fi_rng;
    *pTrig = fi_F[1];
    return fi_F[0];
}

var FisherTransform(vars Price, int Len) {
    var fi_w1;
    var fi_w2;
    var fi_w3;
    var fi_w4;
    return FisherCore(Price, Len, &fi_w1, &fi_w2, &fi_w3, &fi_w4);
}
```

## 2. `indicators/ehlers/FisherTransform_Superseded.c` (full text)

The current body (blob `259954ed90f4674733f41c46b6694c5f1320cfd0`) with only: function renamed to `FisherTransform_Superseded(vars Price, int Period)`; line 42's `series((priceHigh() + priceLow()) * 0.5)` replaced by the parameter; every `ft_` -> `fto_`; header. I kept `fto_Mid` as an alias (`vars fto_Mid = Price;`) so every later use of the body stays unchanged, which keeps the diff to one line. Statics, literals, guard, clamp, INITRUN resets and the trigger global are untouched.

```c
// =============================================================================
// FisherTransform_Superseded.c
//
// SUPERSEDED - do not use. Kept as the negative control NCS / NCT of
// FSH_ArticleFidelity (F-1 file statics and a global trigger shared by every call;
// F-3 float32 literals). Only edit vs the original (blob 259954ed): the input is a
// parameter (for synthetic inputs). Corrected file: FisherTransform.c.
//
// Edits vs the original body (b): function FisherTransform(int Period) ->
// FisherTransform_Superseded(vars Price, int Period); the input line
// `series((priceHigh() + priceLow()) * 0.5)` -> the Price parameter (kept as the
// alias `vars fto_Mid = Price;` so that every later use is unchanged); every ft_
// identifier -> fto_ (flat namespace, gotchas 1.3). Statics, literals (.33, .67, .99,
// .999), the guard, the clamp, the INITRUN resets and the trigger global are unchanged.
// =============================================================================

// Global trigger line — accessible from test script after each call
var fto_Trigger = 0;

var FisherTransform_Superseded(vars Price, int Period) {

    // --- Price input: midpoint bar (H+L)/2 ---
    // Ehlers explicitly uses midpoint, not Close, in the original EasyLanguage
    vars fto_Mid = Price;   // the ONLY behavioural edit: input is a parameter (was series((priceHigh() + priceLow()) * 0.5))

    // --- Channel: highest high and lowest low over Period bars ---
    var fto_MaxH = MaxVal(fto_Mid, Period);
    var fto_MinL = MinVal(fto_Mid, Period);

    // --- Normalize price to [-1, +1] ---
    // Maps current price position within the Period channel to [-1, +1]
    // Guard against zero range (flat price — unlikely on real data, possible in warmup)
    var fto_raw = 0;
    if(fto_MaxH - fto_MinL > 0)
        fto_raw = 2.0 * ((fto_Mid[0] - fto_MinL) / (fto_MaxH - fto_MinL) - 0.5);

    // --- Stage 1: smooth the normalized input ---
    // EMA with alpha=0.33 (0.33 + 0.67 = 1.0 — proper EMA)
    // Prevents single-bar channel spikes from contaminating the transform input
    static var fto_Value1 = 0;
    if(is(INITRUN)) fto_Value1 = 0;   // statics persist across runs
    fto_Value1 = 0.33 * fto_raw + 0.67 * fto_Value1;

    // --- Clamp to prevent log(0) or log(negative) in the transform ---
    // Check fires at ±0.99; assignment is ±0.999 — matches Ehlers' exact code
    if(fto_Value1 >  0.99) fto_Value1 =  0.999;
    if(fto_Value1 < -0.99) fto_Value1 = -0.999;

    // --- Capture previous Fisher as trigger BEFORE updating Fish ---
    // fto_Trigger holds Fish from the previous bar — this is the signal line
    static var fto_Fish = 0;
    if(is(INITRUN)) fto_Fish = 0;   // statics persist across runs
    fto_Trigger = fto_Fish;

    // --- Stage 2: Fisher transform + smooth output ---
    // 0.5 * log((1+x)/(1-x)) is arctanh(x) — the Gaussian-shaping transform
    // + 0.5 * fto_Fish is a second EMA (alpha=0.5) applied to the output
    // This light feedback smooths the output without distorting the distribution
    fto_Fish = 0.5 * log((1.0 + fto_Value1) / (1.0 - fto_Value1)) + 0.5 * fto_Fish;

    return fto_Fish;
}
```

Token diff vs the old blob (test `test_ii_superseded_is_the_renamed_old_blob`): token-identical to the old blob after (1) `ft_` -> `fto_`, (2) the function header, (3) the input line. Nothing else differs (header comments are not tokens). Guards seen to fire (each reported ok=False): one `fto_` left as `ft_` (first difference at token 78), `0.33` -> `0.34` (95), `0.99` -> `0.98` (107), the input alias -> `series(Price[0])` (18).

## 3. Callers (F-2)

```diff
diff --git a/strategies/tests/Test_Fisher_IFT_COG.c b/strategies/tests/Test_Fisher_IFT_COG.c
index cb22c5d..04b2cdf 100644
--- a/strategies/tests/Test_Fisher_IFT_COG.c
+++ b/strategies/tests/Test_Fisher_IFT_COG.c
@@ -47,9 +47,14 @@ void run() {
     // =========================================================================
 
     // --- Fisher Transform (Period=10) ---
-    // Returns current bar Fisher value; ft_Trigger = previous bar (signal line)
-    var fisher = FisherTransform(10);
-    var f_trig = ft_Trigger;
+    // Returns current bar Fisher value; f_trig = previous bar (signal line, FisherCore out-parameter)
+    // Input is the source's (H+L)/2 series (F-2); the series holds >= Len values, unconditional, before the call.
+    vars fi_mid = series((priceHigh() + priceLow())/2, 10);
+    var fi_raw = 0;
+    var fi_v1 = 0;
+    var fi_rng = 0;
+    var f_trig = 0;
+    var fisher = FisherCore(fi_mid, 10, &fi_raw, &fi_v1, &fi_rng, &f_trig);
 
     // --- Elegant Oscillator (BandEdge=20) ---
     // IFT Redux pipeline: derivative → RMS normalize → soft-limit → SuperSmoother
diff --git a/strategies/tests/Test_S1_C2_Audit.c b/strategies/tests/Test_S1_C2_Audit.c
index fd1dcd9..b5623d6 100644
--- a/strategies/tests/Test_S1_C2_Audit.c
+++ b/strategies/tests/Test_S1_C2_Audit.c
@@ -26,10 +26,12 @@ void run()
 
     vars Price = series(priceClose());
 
-    // Compute before the lookback guard. Both calls unconditional,
+    // Compute before the lookback guard. All calls unconditional,
     // fixed order - series() allocates by call order.
     var reflexVal = Reflex(Price, REFLEX_LENGTH);
-    var fisherVal = FisherTransform(FISHER_PERIOD);
+    // Fisher takes the source's (H+L)/2 input (F-2), NOT the close series Price built for Reflex.
+    vars fisherMid = series((priceHigh() + priceLow())/2, FISHER_PERIOD);
+    var fisherVal = FisherTransform(fisherMid, FISHER_PERIOD);
 
     if(is(LOOKBACK)) return;
 
```

(c) Neither script was run. Their outputs change by design (F-1..F-3). They are **compile-unverified until next used**. `Test_Fisher_IFT_COG.c` keeps its output columns (`fisher`, `fisher_trig`, ...). `Test_S1_C2_Audit.c` uses a separate (H+L)/2 series, not its close `Price` built for Reflex. In the S1 audit script the Fisher series is now allocated after Reflex's calls (call order); Reflex's own slots are unchanged. `docs/roadmap/` snippets are left as history. No other caller exists: the test scans `strategies/`, `indicators/`, `analysis/` `.c` files.

## 4. `test_fsh_corrected_code.py` (19 tests)

Modelled on `test_lrs_corrected_code.py`. Guard-fire evidence (printed by the test run, every one reported not-ok):

| Altered copy of `FisherTransform.c` | Result |
|---|---|
| `static var fi_hi = ...` added before `var fi_hi` | core: lines not found verbatim |
| `var fi_a = 33;   fi_a = fi_a/100;` -> `var fi_a = 0.33;` (division removed) | core: not found |
| `vars fi_V = series(0, 2);` moved inside `if(fi_rng > 0) {` | core: not found |
| clamp set value `fi_c` -> `fi_t` | core: not found |
| `*pTrig = fi_F[1];` -> `fi_F[0]` | core: not found |
| Fish feedback `fi_h*fi_F[1]` -> `fi_F[0]` | core: not found |
| wrapper `return FisherCore(...)` -> `return fi_w1;` | wrapper: not found |
| wrong function name; lines only in comments | not ok |
| scans: `static` added -> lint hit `fi_hi`; `0.33` -> decimal-literal scan sees it; `2*0.5*1` -> literal-product scan sees it; `var ft_Trigger = 0;` added -> global-var scan and `ft_` scan see it | each fires |
| superseded: one `fto_` left as `ft_`, `0.33`->`0.34`, `0.99`->`0.98`, input -> `series(Price[0])` | ok=False |
| (vi) old interface `FisherTransform(10)` + `ft_Trigger` | both reported |
| (ii) two single-token changes (`fi_h*log` -> `fi_a*log`, `>` -> `>=`) | exact token difference no longer matches |

Test-writing note (deviation, my mistakes, not code): the first run of the new file had 3 failures, all in my test, not in the code: two mutations that kept the token multiset (a num/den swap), one search string absent from the old blob (`* 0.5;` vs `* 0.5)`), and one mutation that hit the header comment instead of the code line. All three fixed in the test before the suite run; the guard now fires on each.

## 5. Generator

No change. The five-column call path, `series_len = 21`, the per-output checks and the no-static lint generated the FSH layout as is (stage 1 expectation held). No A1.2. No reason found that the layout is unsafe in Light-C (no STOP).

## 6. Pre-run conditions

| # | Condition | Result | Evidence |
|---|---|---|---|
| i | corrected file contains spec lines verbatim; guard seen to fire | PASS | §4: 19 tests OK |
| ii | old blob recorded; diff only F-1, F-2, F-3, F-7, F-8; superseded = renames + input + header | PASS | below |
| iii | `test_reference_fsh_spec.py` | PASS (5 tests) | largest deviation per section below |
| iv | `generator.py ... --lint-only` clean, both includes resolve, no-static passes | PASS | below |
| v | no-static: 0 hits new `FisherTransform.c`; 2 on the superseded file | PASS | below |
| vi | the two callers updated, no other caller | PASS (compile-unverified) | §3 |

**(ii) old blob** `259954ed90f4674733f41c46b6694c5f1320cfd0` (`git rev-parse 258b24a:indicators/ehlers/FisherTransform.c`, equal to the working copy before this stage). Token multiset difference old -> new (FisherCore + wrapper), asserted exactly by the test:

- REMOVED: `static` x2, `if` x2, `is` x2, `INITRUN` x2, `ft_Trigger` x2 (F-1, the two statics, their INITRUN resets and the global trigger); `priceHigh`, `priceLow`, `+`, `ft_Mid` x4 (F-2); `0.33`, `0.67`, `0.99` x2, `0.999` x2, `0.5` x4, `1.0` x2 (F-3); `2.0`, one `-`; the `ft_*` identifiers (renamed to `fi_*`); `Period` x3 (named `Len`); `(` / `)` x9 each.
- ADDED: `FisherCore` x2, the four out-parameters and their four assignments and the wrapper's `fi_w1..fi_w4` and `&` x4 (F-7); `fi_V` / `fi_F` with `series` (F-1); integer constants `33 67 99 999 1000 100 1 2` (F-3); `fi_nt`, `fi_nc`, `fi_u`, `fi_num`, `fi_den`, `fi_hi`, `fi_lo`, `fi_rng` locals.
- **Other token differences, listed explicitly (none is an F-item):**
  1. `2.0 * ((x - lo) / (hi - lo) - 0.5)` is four statements (`fi_raw = Price[0] - fi_lo; /fi_rng; - fi_h; *2`): pre-registered in the spec notes, same arithmetic, same order.
  2. `Period` is `Len` (spec signature).
  3. The guard tests `fi_rng` (one subtraction) instead of repeating `MaxH - MinL` (same value).
  4. The trigger is `fi_F[1]` via `*pTrig` instead of a copy of the static.
  5. `fi_nt` / `fi_nc` (negated thresholds) are built with `0 - x` instead of the literal `-0.99` (F-3 consequence).
  
  `MaxVal`, `MinVal`, `log`, the guard and clamp conditions: unchanged. No other token differs. Two single-token changes of the new file change the difference (guard seen to fire).

**(iii)** largest deviation per section: findings 0.000e+00 (296 values), floor 0.000e+00 (4), effects 0.000e+00 (38), imp_fire_test 0.000e+00 (both fire values; own-model and discrimination values reproduced). (c) 0 is self-consistency: the spec was generated from this reference.

**(iv) lint INFO lines** (`--lint-only`, exit 0, "lint clean; nothing written"): D2 floors (x10 within tolerance): trace 1.064e-11, invariance 5.319e-12, ramp_exact 0, bound 0, trigger 0, flat_zero 0. Control margins (all >= 10x): NCW trace 1.3e+09x; NCC trace 2.31e+09x / ramp_exact 2.31e+12x; NCK trace 3.8e+09x / ramp_exact 3.8e+12x; NCL trace 1.21e+09x; NC32 trace 1.29e+04x / ramp_exact 1.29e+07x / bound 1.29e+07x; NCS trace 8.54e+09x / ramp_exact 9.2e+12x / flat_zero 1.06e+12x; NCT trace 8.54e+09x / ramp_exact 9.2e+12x / flat_zero 9.88e+11x. NCB (role info): trace 2.71e+09x, ramp_exact 2.65e+12x, bound 9e+08x. Four `L_FLOAT32` exemption INFO lines (NC32: 0.33, 0.67, 0.99, 0.999). `INFO L_NO_STATIC indicators/ehlers/FisherTransform.c: 0 static tokens (comments excluded): PASS`. Both includes resolved (no missing-file issue).

**(v)** `lint_no_static`: 0 hits on `FisherTransform.c`; on `FisherTransform_Superseded.c` 2 hits: `fto_Value1` (line 40), `fto_Fish` (line 51). Asserted in the test (seen firing on the real superseded file) and on a corrected-file copy with `static var fi_hi`.

## 7. Suite

`bash analysis/harness/run_tests.sh` (Claude Code shell):
- before this stage: `TOTAL 719  PASS 719  FAIL 0  ERROR 0  SKIP 0`
- after (test + script): `TOTAL 738  PASS 738  FAIL 0  ERROR 0  SKIP 0`
- after Amendment 1 appended: `TOTAL 738  PASS 738  FAIL 0  ERROR 0  SKIP 0`

No ERROR or FAIL in any full run (the known `test_checker_amend1.test_cli` MemoryError did not appear). The commit-message count must come from the user's Git Bash run (CLAUDE.md §8).

## 8. Amendment 1 (appended to the spec)

`[amendment_1]` (2026-11-19, base_commit 258b24a, before_run = true, criterion_changed = false): A1.1 pre-run records, A1.3 run note (restart Zorro before any rerun: the generated script returns at INITRUN before any indicator call, so the superseded file's INITRUN resets never run). The numbering skips A1.2 as in LRSI (A1.2 is reserved for a generator change; none needed). `[prerun]`: cond_i..cond_vi, tests_before 719 / tests_after 738 / tests_added 19, suite line, the three blob hashes, script path and sha256, `script_check`. Diff vs 258b24a: 32 lines added, 0 removed (`git diff` checked); the TOML still parses. Added beyond the brief's list: `cond_vi` (callers), because the spec's pass condition lists it as pre-run item (vi).

## 9. Generated script

`python analysis/harness/generator.py analysis/harness/specs/FSH_ArticleFidelity.toml` wrote `strategies/tests/GEN_FSH_FisherTransform.c` (41,220 bytes), sha256 `4429d87d9154778dac10aa160605a9b66e655d69b04462284f3cd9e119526f19`. Read-through (each point checked on the file, counts by regex):

| Check | Result |
|---|---|
| Includes in order, paths as `[zorro].include` | `#include <default.c>`, then `"../../indicators/ehlers/FisherTransform_Superseded.c"`, then `"../../indicators/ehlers/FisherTransform.c"` (lines 20-22) |
| 18 inputs built from integers before any indicator call; each `series(X[k], 21)` | yes: `lvl = 11/10`, `amp = 1/100`, `slp = 1/10000`, `pi_x = 4*atan(1)` etc.; 18 `series(X[k], 21)` lines S0..S17, all before the first call |
| No decimal literal in the harness part | none; the only decimal literals are in comments and the four NC32 lines (below) |
| Every generated static reset at INITRUN | `fsh_n, fsh_done, fsh_hdr, fsh_rows` reset (line 262); only 4 statics in the file |
| Calls unconditional, fixed order, 100 per bar | counted: `FisherCore` 36 (FR10 and FR20 x 18 inputs incl. invariance copies), `fsh_ncb / ncw / ncc / nck / ncl / nc32` 8 each (48), `FisherTransform_Superseded` 16 = 100 |
| Inline bodies once each, locals uniquely prefixed | `fsh_ncb`, `fsh_ncw`, `fsh_ncc`, `fsh_nck`, `fsh_ncl`, `fsh_nc32` each defined once; locals `ncb_ ncw_ ncc_ nck_ ncl_ n32_`; each has its own two `series(0, 2)` |
| NC32's float32 literals (deliberate, the control) | `n32_a = 0.33; n32_b = 0.67; n32_t = 0.99; n32_c = 0.999;` (lines 221-224) |
| NCS then NCT order | `Y[420..427] = FisherTransform_Superseded(S0..S7, 10)` NCS on flat, s5, s10, s20, s40, s100, ramp, rampdn; then `Y[428..435]` NCT on the same 8 = 16 calls |
| No `Period` identifier outside the superseded file | only `BarPeriod` in the script |
| Out-parameters through local scalars, copied before the next call | `fsh_o_raw / fsh_o_v1 / fsh_o_rng / fsh_o_trig`, copied to Y[] right after each call |
| Raw file `Data/GEN_FSH_raw.csv`, 376 columns | 376 header columns counted; header written once (`fsh_hdr`); rows `%.15f` |
| Header and rows before `quit()` (9d.4) | yes; `fsh_done = 1` latched, then `quit(...)`; the EXITRUN branch and its marker file are not a check |
| Raw file does not exist yet | `C:/Zorro/Data/` exists; no `GEN_FSH*` file there |

**Deviation to flag:** the brief asks for a "no-overwrite guard" on the raw file. The generated script **deletes** the raw file at INITRUN (`file_delete(FSH_RAW)`), as the earlier generated scripts do (the LRS record says "the exclusive-create guard belongs to the results file"). I did not change the generator (brief §5: no change expected). The no-overwrite guard is in the checker's results file. If you want a script-side guard, that is a generator change (A1.2) and your decision.

## 10. Deviations from the brief and open points

1. Raw-file guard as above (the script deletes at INITRUN rather than refusing to overwrite). No change made.
2. `Test_S1_C2_Audit.c`'s comment "Both calls unconditional" changed to "All calls unconditional" (three calls now).
3. Amendment 1 also carries `cond_vi` (not in the brief's cond_i..cond_v list), see §8.
4. The two `.c` files are LF in the working copy (as written); the repo is LF, so git will show no CRLF noise for them. `Test_S1_C2_Audit.c` kept its CRLF line endings; `Test_Fisher_IFT_COG.c` its LF.
5. `GEN_FSH_FisherTransform.c` embeds no spec hash, so appending Amendment 1 after generating it does not change the script (suite re-run green after the amendment).
6. (c) NOT VERIFIED: the corrected file's compile in Light-C (the `*pRaw = ...` out-parameter and `int Len` patterns are the same as ReflexCore / MESAStochasticCore / LaguerreRSICore, which compiled). The run will show any `Error` line; the run card must say "expect no line starting with `Error` in the Zorro window".

## 11. Run card for the user (when the commits are in)

1. Restart Zorro (A1.3).
2. Script dropdown -> `[Change Folder]` -> the repo's `strategies/tests/` folder; pick `GEN_FSH_FisherTransform`.
3. One [Test] click, no asset change; EUR/USD D1 clock is set in the script.
4. Expect: no line starting with `Error`; final message `FSH batch complete: 3000 rows written`.
5. Output: `C:/Zorro/Data/GEN_FSH_raw.csv` (3001 lines, 376 columns). Tell me when it is done; then the checker runs and the results file `FSH_ArticleFidelity_<date>.csv` is written (a separate step).

## 12. Suggested git commands (the user runs them)

```
git status --short
git add indicators/ehlers/FisherTransform.c indicators/ehlers/FisherTransform_Superseded.c strategies/tests/Test_Fisher_IFT_COG.c strategies/tests/Test_S1_C2_Audit.c analysis/harness/tests/test_fsh_corrected_code.py
git commit -m "FSH: corrected FisherTransform.c (FisherCore + wrapper), FisherTransform_Superseded.c, caller updates, corrected-code test (<N> tests from your Git Bash run)"
git add analysis/harness/specs/FSH_ArticleFidelity.toml strategies/tests/GEN_FSH_FisherTransform.c docs/harness/FISHER_STAGE2_PROMPT.md docs/harness/FSH_STAGE2_REPORT.md
git commit -m "FSH: Amendment 1 (pre-run records i-vi), generated script GEN_FSH_FisherTransform.c, stage 2 brief and report"
```

## 13. Post-review fix (2026-11-20, planning chat, gotchas 1.3 flat namespace)

Requested by the planning chat; no criterion, tolerance, table, floor, effect or variant changed, FisherCore's code lines untouched. The text in §1 and §3 above shows the files before this fix; this section supersedes it where they differ.

1. `strategies/tests/Test_Fisher_IFT_COG.c`: caller locals `fi_mid, fi_raw, fi_v1, fi_rng` renamed to `ift_mid, ift_raw, ift_v1, ift_rng` (they collided with FisherCore's `fi_raw` / `fi_rng` in the flat namespace). Nothing else changed. Now: `vars ift_mid = series((priceHigh() + priceLow())/2, 10);`, `var ift_raw = 0; var ift_v1 = 0; var ift_rng = 0; var f_trig = 0;`, `var fisher = FisherCore(ift_mid, 10, &ift_raw, &ift_v1, &ift_rng, &f_trig);`.
2. `indicators/ehlers/FisherTransform.c`, header comments only: the caller example is now `vars mid = series((priceHigh() + priceLow())/2);` and one line was added: "use the caller's own prefix for its locals, never fi_ (FisherCore's prefix; flat namespace, gotchas 1.3)." New blob `63a8c0f53255cffd63ec541ad4f1c057b5d8ae67` (was `a05231d426a93bf8a0fe024b3283b55d01cc4531`). Test (i) still passes (code lines verbatim).
3. New checks in `test_fsh_corrected_code.py` (now 21 tests): `test_vi_no_other_file_declares_fi_identifiers` (every `.c` under strategies/, indicators/, analysis/ other than FisherTransform.c declares no `fi_` identifier, comments excluded; the scan is also asserted to see FisherCore's own) and `test_vi_fi_scan_fires_on_the_old_caller` (a temp copy of the old caller reports `['fi_mid', 'fi_raw']`). Before the rename the scan would have reported Test_Fisher_IFT_COG.c (the only offender; the generated script mentions `fi_` in a comment only).
4. Amendment 1 `[prerun]` updated in place (still uncommitted): `blob_FisherTransform_c_new`, cond_i and cond_vi evidence, test counts (719 -> 740, added 21) and the suite line. Spec diff vs 258b24a is still additions only (0 removed lines).
5. Generated script: regenerated into a scratch directory (the generator refuses to overwrite) and compared: sha256 `4429d87d9154778dac10aa160605a9b66e655d69b04462284f3cd9e119526f19`, identical to `strategies/tests/GEN_FSH_FisherTransform.c`; the file in the repo was not rewritten.
6. `--lint-only`: clean, exit 0, `INFO L_NO_STATIC indicators/ehlers/FisherTransform.c: 0 static tokens`. Suite: `TOTAL 740  PASS 740  FAIL 0  ERROR 0  SKIP 0` (Claude Code shell). Still compile-unverified: the renamed caller (not run).
7. Test-file note: while adding the test I mangled escape sequences twice in my own edits; the file was repaired, compiles and passes. The file was normalised to CRLF, like the other test files in the working copy.
