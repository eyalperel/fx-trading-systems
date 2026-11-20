# MAF stage 1 report — D7 tooling, reference models, MAMA / FRAMA spec drafts

**Date:** 2026-11-20 (Claude Code). **Brief:** `docs/harness/MAF_STAGE1_PROMPT.md`. **Branch:** `harness-mama-frama` (base `b7bdd69`), nothing
committed. No `.c` edited, no Zorro run, no generated script written. Labels: (a) source states, (b) measured / computed here, (c) inference.

## 1. Result

| | MAMA (`MAM`) | FRAMA (`FRA`) |
|---|---|---|
| Spec | `analysis/harness/specs/MAMA_ArticleFidelity.toml` | `analysis/harness/specs/FRAMA_ArticleFidelity.toml` |
| Variants | 9: MA05, MA03 (real); NCB, NCH, NCF, NC32, NCP, NCS, NCS2 (controls; NCB a control since the review) | 8: FR16, FR32 (real); NCE, NCN, NC32, NCT, NCS, NCS2 (controls) |
| Real checks | **33 per variant, 66 total** (brief: 32 / 64; difference in §5.1) | **49 per variant, 98 total** (brief: 49 / 98) |
| Real-check split | trace 21 + bound 2 + equivariance 10 | trace 37 + bound 2 + hull 1 + ramp_exact 1 + lag 1 + flat 1 + equivariance 6 |
| INFO rows per real variant | 15 (14 info-trace pairs + info-flat) | 2 (info-trace dim / alpha on point flat) |
| Inputs | 9: flat, s5..s100, ramp, copies sc40, of40 | 15: point flat, s5..s100, ramp; band rampB, s5B..s100B; copies sc40B, of40B |
| Raw columns | 304 | 305 (incl. 16 xh_ / xl_ columns) |
| Calls per bar | 67 (14 superseded) | 108 (26 superseded) |
| Perfect-run check (own-model raw, also printed `%.15f` through the CLI) | VERDICT PASS, 66/66, 7/7 controls, IMP 9/9 + 2/2 must_fail | VERDICT PASS, 98/98, 6/6 controls, IMP 8/8 + 2/2 must_fail |
| `generator.py --lint-only` | exit 3: only the stage-2 items (missing `MAMA_Superseded.c`; `MAMA.c` static `barCount`) | exit 3: only the stage-2 items (missing `FRAMA_Superseded.c`; `FRAMA.c` statics `frama_init`, `frama_prev`) |

Tests (`bash analysis/harness/run_tests.sh`, Claude Code shell): **before 740** (the documented count at `2f3b596`; a `git archive` copy of
HEAD also counts 740 tests, but 45 git-dependent tests cannot pass outside a checkout there, so it is not a clean "before" run); **after the
review changes: TOTAL 817 PASS 817 FAIL 0 ERROR 0 SKIP 0** (77 new: `test_reference_maf` 19, `test_generator_maf` 28, `test_checker_maf` 20,
`test_reference_maf_spec` 10). Earlier runs: 759 / 759 (mid-work), 816 / 816 (before the review). After the review changes one run had 1 FAIL,
a test-side error (my new NCT test asserted a PASS verdict although the edit it makes also, correctly, breaks NCT's own IMP row); fixed in the
test, rerun 817 / 817.
The 10 existing specs regenerate byte-identical scripts (test). The commit-message count must come from the user's Git Bash run.

No STOP condition was met: every floor x10 is inside its tolerance; every control has a kind >= 10x; the recomputed classification equals
the spec's lists; FRAMA NCS differs on far more than flat / start-up; no line of the brief's code needed a construct that has not compiled
before (§5.9).

## 2. Tooling (extensions only; older specs never enter the new path)

- **reference.py**: `mama_article` (all hooks of the brief incl. `pi`, `literals`, separate `dn` and SmoothPeriod `c33` / `c67`),
  `simulate_mama`; `mama_superseded(params, index)` / `simulate_mama_shared` (static `barCount` shared over the slots in call order,
  float32 literals, Zorro `PI`, series(v) re-set / padding as the old file); `frama_article(N, k, lo, literals, startup="source"|"old")`,
  `frama_windows`, `simulate_frama`; `frama_superseded(Ts, index)` / `simulate_frama_shared` (shared `frama_prev` / `frama_init`, float32
  4.6 / .01, half window T); `adaptive_article_model` (restricted grammar, no eval); `conditioning` (the rule-3 quantity); 17 IMP registry
  entries. Operation order = the brief's code (deg = 180/pi, `atan(.)*deg`, `360/P`, ...).
- **generator.py**: `[checks].adaptive = true` selects `validate_adaptive` / `to_checker_spec_adaptive` / `build_script_adaptive`.
  Bars inputs (`band_half`, `band_inputs` -> `<id>B`; `[checks].bars`), affine copies (`[inputs.equivariance]` inputs + transforms
  `{id, scale, offset}`), every column on every input, five / three columns through local scalars, per-column tolerance overrides,
  `[conditioning]`, per-table bounds / ramp_lag / conditioning lists, new kinds `equivariance`, `hull`. New generated locals carry the batch
  prefix (`fra_hb`, `fra_k_sc`, `fra_c_sc`, ...); H / L series are `SHi<j>` / `SLo<j>`.
- **checker.py**: band High / Low (`make_bars`, exported `xh_` / `xl_`, guarded at 1e-12), `adaptive_rows` (trace from row 1 with
  INFO pairs, bound with first row and relative allowance, hull, equivariance with W_eq, ramp_exact, lag, flat, info-flat),
  `conditioning_table` / `conditioning_mismatches`, `adaptive_imp_rows` (per (input, column), ratio to the column tolerance; INFO pairs in
  `info_detail` and trailer line `IMP_INFO`, never deciding), `adaptive_shared_slots`, floor guard per kind and column group
  (`floor-trace-phase`), D7 trailer.
- **tests/maf_support.py**: brief code extraction, control bodies (brief + declared edits), own-model raw files, `numbers()`.

## 3. Items 1-7 reproduced (brief rule: a difference is a finding only above max(10 x conditioning, 1e-12); effects within 1%)

| Item | Brief | Here | Verdict |
|---|---|---|---|
| 1 MAMA classification | checked s10..s100, INFO flat / ramp / s5 | identical per input; per column **s5 period is CHECKED** (4.157e-13 / 5.755e-13 <= 1e-10) | see §5.1 |
| 1 MAMA largest checked | MA05 s100 phase 1.453e-10, alpha 2.318e-11, fama 2.351e-13; MA03 1.538e-10, 1.624e-11, 6.678e-13 | identical to 4 digits | reproduced |
| 1 MAMA others | e.g. s5 period 4.086e-13, s40 period 4.583e-12, s10 phase 4.594e-12 | 4.157e-13, 4.555e-12, 4.579e-12 | operation-order differences, below the rule |
| 1 FRAMA | out max 5.773e-15; dim 5.178e-13, alpha 1.285e-12 (FR16 s100); flat dim / alpha INFO | identical to every printed digit (`skip_draws = 70`) | reproduced |
| 2 MAMA period rows >= 1000 | s10 [10.046866000871653, 10.138692660663777], s20 [19.955554535888744, 20.051537545020732], s40 [39.807136333604554, 40.18200281308779], s100 50.0 | s10 [..653, ..775], s20 [..748, ..736], s40 identical, s100 50.0 exactly | max diff 4e-15, reproduced |
| 2 MA05 FAMA rows >= 1000 | s20 [1.099446341089458, 1.1005536589105402], s100 [1.0920658491664514, 1.1079341508335487] | s20 identical; s100 [..512, ..549] | 2.2e-16, reproduced |
| 2 alpha / period bounds | alpha in [SL, FL] n >= 5, 0 before; period <= 50 | same, both variants, every input | reproduced |
| 3 MAMA equivariance | last row off <= 516; rows >= 1000: mama 1.6e-14, fama 1.6e-14, alpha 3.7e-13, period 6.2e-12, phase 5.3e-11 | last row 516 (MA05 s40 sc); mama 1.887e-14, fama 1.577e-14, alpha 3.716e-13, period 6.239e-12, phase 5.273e-11 | mama 1.9e-14 vs 1.6e-14: below the rule (rounding at 1e-14) |
| 4 IMP estimate | MA05 phase 1.124e-10, alpha 1.737e-11, fama 2.596e-13; FRAMA alpha 1.933e-12, out <= 5.1e-15 | same digits | reproduced |
| 5 FRAMA known answers | D 0.9004643264490856 / 0.9526942852216433; band D 1.773229138152978 / 1.6316125940199773; alpha 0.028528433125587088 / 0.054725914083758966; lag 34.05274879969143 / 17.27287888639891; model lag 34.05274879967843, converged from 854 / 450 | identical (model D at n = 500: ..1008 / ..6506, 1.5e-14); model lag 34.052748799678426 / 17.272878886401344; converged from n 854 / 450 | reproduced |
| 6 FRAMA bounds | alpha min 0.010051835744633504, Dimen 2.0000000000000018 | identical; hull excess 0 | reproduced |
| 7 FRAMA equivariance s40B | sc out 7.994e-15, dim 1.532e-14, alpha 2.787e-14; of 1.776e-15, 5.773e-14, 6.384e-14 | identical (max over FR16 / FR32) | reproduced |

Models vs the planning chat's review model (`test_reference_maf`): FRAMA (source, old start-up, superseded single slot) and the old MAMA
file (single slot, offsets 0 / 4 / 5 / 9) bit-identical; `mama_article` vs `mama_src` <= 8.349e-14 (operation order).

## 4. Numbers by section

### 4.1 Conditioning (rule 3; * = INFO; values = max |change| over all rows, 5 draws)

MAMA (MA05 | MA03), columns mama / fama / period / alpha / phase:

| input | MA05 | MA03 |
|---|---|---|
| flat | 5.709e-04* 3.244e-02* 4.334e+01* 4.500e-01* 9.511e+01* | 1.331e-02* 8.340e-02* 4.314e+01* 2.000e-01* 1.800e+02* |
| ramp | 2.996e-04* 2.788e-04* 9.212e+00* 4.500e-01* 3.064e+01* | 2.521e-04* 2.896e-04* 1.156e+01* 2.000e-01* 3.064e+01* |
| s5 | 4.969e-03* 1.686e-02* **4.157e-13** 4.500e-01* 1.800e+02* | 6.302e-03* 3.477e-02* **5.755e-13** 2.000e-01* 1.800e+02* |
| s10 | 6.661e-16 4.441e-16 9.948e-14 0 4.579e-12 | 6.661e-16 6.661e-16 2.274e-13 0 6.088e-12 |
| s20 | 1.110e-15 8.105e-15 3.268e-13 9.034e-14 1.217e-11 | 6.661e-16 8.882e-16 2.736e-13 0 1.133e-11 |
| s40 | 4.885e-15 2.620e-14 4.555e-12 5.568e-13 3.949e-11 | 7.105e-15 4.052e-14 4.370e-12 3.042e-13 4.181e-11 |
| s100 | 4.641e-14 2.351e-13 1.812e-12 2.318e-11 1.453e-10 | 6.017e-14 6.678e-13 1.712e-12 1.624e-11 1.538e-10 |
| sc40 | 5.551e-15 2.220e-15 4.334e-13 7.813e-14 3.272e-12 | 1.776e-15 2.554e-15 3.979e-13 3.278e-14 3.478e-12 |
| of40 | 7.105e-15 1.126e-13 8.420e-12 9.887e-13 6.520e-11 | 4.086e-14 1.952e-13 8.441e-12 5.848e-13 8.223e-11 |

FRAMA (FR16 | FR32), columns out / dim / alpha: every pair checked except point flat dim (2.000e+00*) and alpha (9.899e-01*), both
variants. Largest checked out 5.773e-15 (FR32 s5B / s10B), dim 5.178e-13 (FR16 s100), alpha 1.285e-12 (FR16 s100); copies sc40B / of40B
<= 1.453e-13. Full table in the spec (`[expected.*.conditioning].values`).

### 4.2 Floors and tolerance windows (D2 rule 3: floor x 10 <= tolerance)

| Quantity | Floor (b) | x10 | Tolerance | Window |
|---|---|---|---|---|
| MAMA trace (mama, fama, period, alpha) | 2.3176e-11 (MA05 s100 alpha, conditioning) | 2.3e-10 | 1e-9 | ok |
| MAMA trace phase | 1.5378e-10 (MA03 s100, conditioning) | 1.5e-9 | 1e-8 | ok |
| MAMA equivariance | 6.2386e-12 (period, model, rows >= 1000) | 6.2e-11 | 1e-9 | ok |
| MAMA equivariance phase | 5.2733e-11 | 5.3e-10 | 1e-8 | ok |
| MAMA IMP (estimate, %.15f x) | 1.7374e-11 (alpha); phase 1.1239e-10 | | 1e-9 / 1e-8 | ratio 0.017 / 0.011 |
| FRAMA trace | 1.9335e-12 (FR16 s100 alpha, IMP estimate) | 1.9e-11 | 1e-10 | ok |
| FRAMA equivariance | 6.3838e-14 | 6.4e-13 | 1e-10 | ok |
| FRAMA lag | 1.3003e-11 bars | 1.3e-10 | 1e-6 | ok |
| FRAMA ramp_exact, flat | 0 | 0 | 1e-12 | ok |
| FRAMA hull | 0 (model); (c) ~7e-16 expected from printing + one ulp of sin | | 1e-15 | thin, as the brief set it |

No `PI` gap in either spec (S1 exact pi; FRAMA has no trig).

### 4.3 Controls: effects and `[detect.required]` (detection ratio = max abs_diff / row tolerance on the own-model raw file)

| Control | Ratios (kinds >= 10x) | Below 10x (not required) | `[detect.required]` |
|---|---|---|---|
| MAMA NCB (.67 -> .68; control since the review) | trace 3.63e7 (s5 period only) | — | trace |
| MAMA NCH (.0962 -> .0963) | trace 1.26e7 | — | trace |
| MAMA NCF (FAMA .5 -> .51) | trace 8.5e6 | — | trace |
| MAMA NC32 (float32 literals) | trace 5.94e3, **bound 7.45e4** | — | trace, bound |
| MAMA NCP (Zorro PI) | trace 4.33e4 | — | trace |
| MAMA NCS / NCS2 | trace 1.11e9 / 1.11e9 | — | trace |
| FRAMA NCE (4.6 -> 4.61) | trace 7.99e6, bound 5.16e9, lag 2.72e5 | — | trace, bound, lag |
| FRAMA NCN (window N + 2) | trace 1.58e10, lag 3.25e6 | bound 0.0019 | trace, lag |
| FRAMA NC32 (float32 4.6 / .01) | trace 76.3 | lag 2.58, bound 0.0009 | trace |
| FRAMA NCT (old start-up + guard) | trace 1.0e10; bound 1.0e12 is INFO only (`[detect.info_only]`, review) | lag 1.3e-5 | trace |
| FRAMA NCS / NCS2 | trace 2.97e9, hull 2.87e14, lag 3.41e7, flat 2.3e11 | — | trace, hull, lag, flat |

Every brief (b) effect value reproduced to its printed digits: MAMA NCH / NCF / NC32 / NCP on s10..s100 (worst relative difference
3.5e-7), FRAMA NCE / NCN / NC32 / NCT point | band and the band-ramp values (worst 2.9e-7); NCN dim up to 1.585 (point) / 0.435 (band).

### 4.4 NCS / NCS2 per (instance, input) — vs the real model (MA05 / FR16)

MAMA (columns mama | fama; max all rows / rows >= 1000 / last row > 1e-12), identical for NCS and NCS2 except at start-up:

| input | NCS | NCS2 |
|---|---|---|
| flat | 1.1 / 0 / 50 \| 1.1 / 4.4e-16 / 107 | same |
| s5 | 1.105 / 4.6e-3 / 2999 \| 1.102 / 1.5e-3 / 2999 | 1.105 / 4.6e-3 / 2999 \| 1.102 / 1.5e-3 / 2999 |
| s10 | 1.108 / 0 / 144 \| 1.104 / 0 / 344 | 1.106 / 0 / 144 \| 1.103 / 0 / 344 |
| s20 | 1.108 / 0 / 217 \| 1.104 / 0 / 521 | 1.107 / 0 / 216 \| 1.103 / 0 / 521 |
| s40 | 1.105 / 2.2e-9 / 2999 \| 1.102 / 9.2e-10 / 2999 | 1.104 / 2.2e-9 / 2999 \| 1.101 / 9.2e-10 / 2999 |
| s100 | 1.102 / 2.5e-9 / 2999 \| 1.101 / 5.4e-9 / 2999 | same |
| ramp | 1.100 / 3.1e-4 / 2999 \| 1.100 / 3.5e-4 / 2999 | same |

(b) Only `barCount` is shared: it shifts the start-up (NCS's first five calls of the run return Price, every other call computes from bar
0). The permanent part on s5 / s40 / s100 / ramp is the old file's own MA-1 / MA-4 / MA-5 effects (long memory), not shared state.

FRAMA (out; max all rows = max rows >= 1000): flat 0.230, s5 0.228, s10 0.223 (NCS2 0.226), s20 0.215 (0.200), s40 0.113 (0.125), s100
0.068 (0.085), **ramp 0**, rampB 0.0034, s5B 0.297, s10B 0.294, s20B 0.292, s40B 0.245, s100B 0.239; last row > 1e-12 at 2985..2999
everywhere except ramp. (b) Permanent on every input except the point ramp, where alpha = 1 overwrites the shared state on every call.
The brief's STOP condition (differs only on flat or only at start-up) is not met.

### 4.5 NCB (dn .67 -> .68; a control since the review)

0 on every column of s10, s20, s40, s100 (S4 reproduced), **3.626e-02 on s5 period** (s5 period is a checked pair here, §5.1). Planning-chat
review 2026-11-20: NCB is a control, `[detect.required]` NCB = ["trace"] (3.63e7x, failing row `MAM-NCB-trace-period-s5` only); its IMP
model is unchanged. MA-2 stays review-only.

### 4.6 IMP fire tests (full precision)

| Row | Value | Ratio |
|---|---|---|
| MAMA must_fail MA05 vs the NCH model | 0.1261940444417604 (s10 phase) | 12619404.44417604 |
| MAMA must_fail NCS vs the MA05 model | 1.1078676554375795 (s10 mama) | 1107867655.4375794 |
| FRAMA must_fail FR16 vs the NCE model | 0.0007988543987603736 (s100 alpha) | 798854.3987603735 |
| FRAMA must_fail NCS vs the FR16 model | 0.29685972859365073 (s5B out) | 296859728.5936507 |
| every must_pass on its own model (exact x) | 0.0 | 0 |

Per input (must_fail, max over columns): MAMA MA05 vs NCH: s5 0.005312817357548738, s10 0.1261940444417604, s20 0.03312005748134084, s40
0.017531283523581465, s100 0.01753819451764116, sc40 0.027348646006402078, of40 0.017520644648755024 (INFO: flat 179.99999999999997, s5
179.99999999999972, ramp 27.927050399222672). MAMA NCS vs MA05: s10 1.1078676554375795, s20 1.107705692254263, s40 1.10455794529443, s100
1.1016625249361272 (INFO flat 1.1, s5 1.1053165675522005, ramp 1.100266875). FRAMA FR16 vs NCE: flat 0.0, s5 0.0003955914341757516, s10
0.0006492833638768458, s20 0.0006711280627735849, s40 0.0007934268829515312, s100 0.0007988543987603736, ramp 0.0, rampB
0.00021973951777535042, s5B 0.0007972849698498208, s10B 0.0007972849698498208, s20B 0.0007986411203804722, s40B 0.0007971923975910733, s100B
0.0007208464666039471, sc40B 0.0007971923975910733, of40B 0.0007971923975910733. FRAMA NCS vs FR16: flat 0.22995714422522195, s5
0.22771412799547885, s10 0.22349213002094315, s20 0.21475422128456523, s40 0.11338065866970992, s100 0.06756545849571327, ramp 0.0, rampB
0.0034052748799688892, s5B 0.29685972859365073, s10B 0.29374874895437153, s20B 0.29207396599184654, s40B 0.24491383829321256, s100B
0.2389526381336904.

Expected must_pass residual of a perfect run printed with `%.15f` (all inputs, worst pair): MAMA MA05 1.7374324201568925e-11 (s100 alpha),
MA03 1.1239009722885385e-10 (s100 phase), NCB 1.737e-11, NCH 2.109e-11, NCF 1.737e-11, NC32 1.983e-11, NCP 1.737e-11, NCS / NCS2 4.574e-14;
INFO pairs up to 180 degrees (s5 phase), ramp 31. FRAMA FR16 1.93345339738471e-12 (s100 alpha), FR32 2.952083022478291e-13, NCE 1.938e-12,
NCN 1.346e-12, NC32 / NCT 1.933e-12, NCS 9.592e-14, NCS2 9.992e-14; INFO pairs 0. Per-input values are in the specs
(`[imp.fire_test.exported_x_15f]`) and reproduced by `test_reference_maf_spec`.

## 5. What did not fit the brief (decisions taken, each reversible before commit)

1. **33 / 66 MAMA real checks, not 32 / 64.** D7 rule 3 classifies per (input, column); s5 period is well conditioned (Period sits on its
   floor of 6 and does not depend on the phase), so it is a checked trace. The brief's own table 1 has the same values (4.086e-13 /
   5.755e-13). The spec states 33 / 66 and explains it (pass item 1, O_S5_PERIOD).
2. **NCB is not zero on every checked input**: 3.626e-02 on s5 period (the new checked pair). Review decision (2026-11-20): NCB changed
   from INFO to a control, `[detect.required]` NCB = ["trace"]; `[source].review_only` now says MA-2 stays review-only and S4's
   "zero effect" for NCB is superseded by this finding. MAMA has 7 controls.
3. **The second superseded instance is a variant `NCS2`** in both specs (FSH used NCT, but FRAMA's NCT is the brief's old-start-up control).
   IMP must_pass covers NCS and NCS2; `[detect.required]` lists both.
4. **New detections the brief did not list**: MAMA NC32 breaks Period <= 50 (float32 .2 + .8 > 1: the blend converges to 50.0000037,
   7.45e4x); FRAMA NCE breaks alpha >= exp(-4.6) (5.2e9x); FRAMA NCT breaks the alpha bound because its body holds alpha at the initial 0
   where N3 <= 0 (n = 0, point flat). Review decision (2026-11-20) for NCT: body and model kept; the alpha bound hit is reported as INFO
   only (new spec table `[detect.info_only]` NCT = ["bound"], validated by the generator and marked "(INFO only)" in the margin line),
   `[detect.required]` NCT = ["trace"]: the old file has no alpha output, so the held 0 is our construction, not old-file behaviour.
5. **FRAMA NCS has zero effect on the point ramp** (§4.4), against the brief's (c) "large on every non-flat input".
6. **Point bars pass the Price series as High and Low** (`FRAMACore(S3, S3, S3, ...)`), not three separate series of the same values;
   band inputs and band copies get their own `SHi` / `SLo` series. Identical values, fewer series.
7. **Copies only of the equivariance inputs** (s40 / s40B), not of every sine (the D6 transform machinery copies all five). Copy ids
   `sc40`, `of40`, `sc40B`, `of40B`. Copies are not traced; they are checked by equivariance, bounds, hull and IMP, and classified (draws
   appended after the planning chat's order, so its base values are unchanged).
8. **IMP rows**: one row per (variant, list) with the worst (input, column) by ratio to its column tolerance; per-pair residuals and the
   INFO pairs go to the trailer. Floor rows per kind and column group (`floor-trace`, `floor-trace-phase`).
9. **Light-C constructs**: every construct the brief flags has compiled in a harness run (`&&` LaguerreRSI_Superseded.c:25, LRS; declarations
   after statements, FisherCore, FSH; unary minus on a variable `exp(-rx_k*PI/rx_half)` Reflex.c:60, RFX; `Length / 2` Reflex_Superseded.c:8,
   RFX). (c) `exp(-fr_e)` (minus on a bare variable as the whole argument) is not seen yet. Zorro's `trading.h:86` has a struct member
   `int N[4]` (no clash with the parameter `N`).
10. **Model API shapes**: `mama_superseded` / `frama_superseded` take the instance list and an index (as `fisher_superseded`), not `(FL, SL)` /
    `(T)`. The old FRAMA replay exports NaN for dim / alpha on early returns (the old file has no such outputs).
11. `series_len = 34` in both specs (MAMA needs 4). Rows are 0-based in the specs: alpha bound `from_n = 5` (CurrentBar 6), W_eq `n >= 1000`.
12. FRAMA conditioning needs `skip_draws = 70` to reproduce table 1 to the digit (the planning chat drew MAMA's 70 perturbations first from
    the same generator); recorded in `[conditioning]`.

## 6. Callers (grep `MAMA(`, `FRAMA(`; code only, docs excluded)

| File:line | Call | Stage 2 |
|---|---|---|
| `strategies/tests/Test_FRAMA_Laguerre_DSMA.c:87` | `FRAMA(FRAMA_T)` | Price / High / Low series, N = 32 |
| `strategies/tests/Test_FRAMA_vs_MAMA.c:38` | `MAMA(Price, FAST_LIMIT, SLOW_LIMIT, &fama_val)` | build .5 / .05 from integers |
| `strategies/tests/Test_FRAMA_vs_MAMA.c:39` | `FRAMA(FRAMA_T)` | as above |
| `strategies/tests/Test_MAMA.c:32` | `MAMA(Price, 0.5, 0.05, &fama)` | build .5 / .05 from integers |
| `strategies/tests/Test_UltimateChannelBands.c:83` | `FRAMA(16)` | as above (N = 32) |

Exactly the brief's list. Docs that mention the calls (history, unchanged): HARNESS_DESIGN, the review and models, Week13 predictions,
Week5-14 plan, Week9 note, roadmap.

## 7. Prefix grep (gotchas 1.3)

`ma_`, `maw_`, `mao_`, `fr_`, `frw_`, `fro_`, the control prefixes `mxh_ mxf_ mx32_ mxp_ mxb_` (MAMA) / `fxe_ fxn_ fx32_ fxt_` (FRAMA), and
the generated `mam_` / `fra_`: **no identifier in any `.c`, `.h`, `.py` or `.toml` outside docs uses them** (the only hits are this stage's
own files and docstrings) and none occurs in `C:/Zorro/include/*.h`. `test_generator_maf.test_03_prefixes_are_not_declared_elsewhere`
keeps this true after stage 2 (each prefix allowed only in its owning file). Gotchas 1.3 is to be updated in stage 2 (brief).

## 8. Blob hashes (pre-run ii)

`indicators/ehlers/MAMA.c` bab4cbbb5961be5720bce82fc6e487e283f7f00e, `indicators/ehlers/FRAMA.c` 3352fbe04ed691e479564bc63d46ae181334f9bb
(both last changed in `2a5eca5`; `git rev-parse b7bdd69:<path>` = `git hash-object <path>`).
