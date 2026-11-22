# ATR stage 1 — report (tooling + reference models + spec draft)

2026-11-21. Brief: `docs/harness/ATR_STAGE1_PROMPT.md`. Branch `harness-atr` at `e11270a`. Nothing committed, no `.c` file written, no Zorro run, no generated
script run (the script was built in memory and linted only). Labels: (a) source states, (b) measured / computed here, (c) inference.
Written for: the planning chat (review before stage 2).

## 1. What ran

| | |
|---|---|
| Tests (`bash analysis/harness/run_tests.sh`) | before **853** PASS (`ddf9776` + `e11270a`, run at the start); after **926** PASS, 0 FAIL, 0 ERROR (+73: reference 18, checker 24, generator 23, spec numbers 8) |
| Reruns | the first full run after the edits was **924 PASS / 1 FAIL** (`test_generator_maf.TestRefusals.test_01_inputs_bars_equivariance`: my flat-band relaxation made `band_inputs = ["flat"]` legal; cause found and made an opt-in flag, see 4.4); two clean runs after (926 / 926, 926 / 926). The known intermittent `test_checker_amend1` MemoryError was not seen. (b) The 853 tests that existed before also pass on their own with the modified tooling (run without the ATR modules: 853 / 0 failures / 0 errors) |
| Existing specs | (b) all **12** regenerate **byte-identical** scripts (sha256 per spec in `analysis/harness/tests/regen_baseline.json`, taken before the first edit; the test is seen to fire: one byte more changes the hash); MAMA / FRAMA own-model checker rows and conditioning tables unchanged |
| Spec | `analysis/harness/specs/ATR_MT4Fidelity.toml` (id_prefix `ATR`): **9 variants** = 2 real (AT14, AT20) + 7 controls (NCW, NC0, NCWi, NCR, NCZ, NCS, NCS2); 16 inputs + 2 copies |
| Variants counted | 9 in the spec (CLAUDE.md 4.3). The planning chat's numbers cover AT14 / AT20 and the controls NCW, NC0, NCWi, NCR, NCZ, NCS; NCS2 is the second instance of NCS |
| Real checks | **45 per variant, 90 total, equal to the brief**: trace 32 (tr, atr x 16 inputs) + bound 3 (`bound-atr`, `bound-tr-range`, `whull-atr`) + known answers 6 + equivariance 4. A perfect own-model run: 90 / 90 PASS, 7 / 7 controls detected on every required kind, 11 IMP rows PASS, floor rows PASS, 0 ERROR (test_checker_atr) |
| Raw file / script | 304 columns, 3000 rows, 148 calls per bar (AT14 18, AT20 18, each of the 7 controls 16), generated in memory only (`GEN_ATR_MT4`, 671 lines) |
| Lint | `generator.py <spec> --lint-only`: only the two stage-2 issues, both caused by the missing file: `L_INCLUDE ../../indicators/nnfx/ATR.c` and `L_NO_STATIC indicators/nnfx/ATR.c not found`. Nothing else (D2 floors "window ok", every control "10x margin met") |

## 2. Planning-chat numbers (items 1-6) reproduced

`python docs/harness/ATR_STAGE1_NUMBERS.py` reproduces `ATR_STAGE1_NUMBERS_output.txt` byte for byte (diff empty). The tooling (`reference.atr_mt4`, the checker's
classifier, `reference.atr_shared`) reproduces it as follows. Rule of the brief: a difference is a finding only above 10x the item-1 value of that
(input, column) or 1e-15.

| item | planning | tooling | diff | verdict |
|---|---|---|---|---|
| 1 conditioning, 32 (variant, input) pairs, tr and atr | all CHECKED, max AT14 tr 4.441e-16 / atr 3.965e-16, AT20 3.442e-16 | same seed 20261121, same draw order: every printed value (`%.3e`) identical, 0 INFO | 0 mismatches | PASS (pre-run (vii): `conditioning_mismatches = []`; guard fires on an injected INFO) |
| 2 known answers, rows >= P | flat 0; flatB / rampB / rampdnB <= 4.407e-17; ramp / rampdn <= 1.102e-17 (AT14), 1.118e-17 (AT20); rows 0..P-1 exactly 0; start-up s20 AT14 0.002107897511639391, AT20 0.0020000000000000018 | identical (start-ups equal to the last digit) | 0 | PASS |
| 3 bounds | ATR min 0, TR-(H-L) min 0, hull violation 0 | identical, all 18 inputs incl. copies, both variants | 0 | PASS |
| 4 equivariance s40B | AT14 sc tr 1.998e-15, atr 4.701e-16; of tr 4.441e-16, atr 6.332e-17; AT20 sc atr 4.406e-16, of atr 4.510e-17 | AT14 sc tr **1.776e-15**, atr **6.748e-16**; of tr 4.441e-16, atr **2.938e-16**; AT20 sc atr 5.794e-16, of atr 2.218e-16 | <= 2.3e-16 | inside the rule (limit 10 x item-1 = 7e-16 .. 4e-15). Cause (b): the planning script builds the copy bars as `10x - 9.9 + 10h`, the generated script as `k * High + c` (the generator and checker do this; max difference of the two bar constructions 1.1e-15). Run through the tooling model, the planning-style bars give exactly 1.998e-15 / 4.701e-16. Not a finding |
| 5 IMP estimate | AT14 tr 8.882e-16 atr 3.782e-16; AT20 tr 8.882e-16 atr 3.652e-16; floor x10 8.9e-15 | identical to 4 digits | 0 | PASS |
| 6 control effects (atr, per input, 5 planning controls x 16 inputs) | printed `%.2e` | all 80 values equal at 3 digits (the test allows 1%) | 0 | PASS |
| model vs the planning model | operation order differs (mine: first window summed newest to oldest, as the corrected code; planning: oldest to newest) | max abs diff over 32 inputs x 2 variants and the 5 control hooks: **0.0** | 0 | the order does not matter on these inputs |

## 3. Conditioning table (rule 3)

Values are max over 5 draws and all rows; bound 1e-13 (trace tolerance / 10). Every pair CHECKED; **no INFO pair** in either variant. The two copies are classified by the tooling only (not in the planning output).

| input | AT14 tr | AT14 atr | AT20 tr | AT20 atr |
|---|---|---|---|---|
| flat | 4.441e-16 | 3.965e-16 | 4.441e-16 | 3.442e-16 |
| flatB | 0.000e+00 | 0.000e+00 | 0.000e+00 | 0.000e+00 |
| ramp | 4.441e-16 | 3.219e-17 | 4.441e-16 | 2.256e-17 |
| rampB | 0.000e+00 | 0.000e+00 | 0.000e+00 | 0.000e+00 |
| rampdn | 4.441e-16 | 3.215e-17 | 4.441e-16 | 2.259e-17 |
| rampdnB | 0.000e+00 | 0.000e+00 | 0.000e+00 | 0.000e+00 |
| s5 | 4.441e-16 | 2.255e-16 | 4.441e-16 | 1.752e-16 |
| s5B | 4.441e-16 | 2.168e-16 | 4.441e-16 | 1.769e-16 |
| s10 | 4.441e-16 | 1.518e-16 | 4.441e-16 | 1.227e-16 |
| s10B | 4.441e-16 | 1.240e-16 | 4.441e-16 | 1.058e-16 |
| s20 | 4.441e-16 | 1.065e-16 | 4.441e-16 | 7.806e-17 |
| s20B | 4.441e-16 | 1.219e-16 | 4.441e-16 | 7.459e-17 |
| s40 | 4.441e-16 | 6.906e-17 | 4.441e-16 | 5.096e-17 |
| s40B | 4.441e-16 | 7.351e-17 | 4.441e-16 | 4.770e-17 |
| s100 | 4.441e-16 | 6.540e-17 | 4.441e-16 | 4.689e-17 |
| s100B | 4.441e-16 | 6.516e-17 | 4.441e-16 | 4.765e-17 |
| sc40B | 4.441e-16 | 1.128e-16 | 4.441e-16 | 1.128e-16 |
| of40B | 8.882e-16 | 1.308e-16 | 8.882e-16 | 9.563e-17 |

## 4. Tooling additions (generator / checker / reference; opt-in, existing specs unchanged)

4.1 The three of the brief: **`scale` role** (`[checks].scale_columns`: copy = |k| x base, offset ignored; refused together with `level_columns`), **`window_hull`**
(`[checks].window_hull = { atr = "tr" }`: atr within [min, max] of tr over the last P rows, rows >= the table's `window`; a variant that exports no tr
(NCS / NCS2) is checked against the model's TR), **`rampdn`** (`[inputs].ramp_down = true` in the adaptive path; it existed since LRS in the oscillator path only).

4.2 Needed by the above, **not named in the brief** (decision for you if you disagree): `[checks].known_value` (new kind; the brief allowed "or reuse
flat / ramp_exact"; they do not generalise to per-input constants at rows >= P); `[checks].range_bound = ["tr"]` (tr >= High - Low, rows >= 1: the brief's bound list
needs it, but a constant bound cannot express it); `[tolerances.bound].abs` / `[tolerances.window_hull].abs` (the bound is 0, so the D6 relative allowance
|bound| x 1e-12 would be 0; tolerance of a bound row = |bound| x value + abs; absent -> old behaviour); expected tables carry `window` (first row of the
known-value / hull checks); `[checks].bar_args = "hlc"` (the call passes High, Low, Close, not Price, High, Low); `[inputs].band_flat = true` (flatB; see 4.4).

4.3 Reference models (restricted grammar, no eval): `atr_mt4(P, tr_kind, avg, first, startup)`, `atr_shared(Ps, index)` + `simulate_atr_shared`, nine `IMP_MODELS`
entries, `adaptive_article_model("atr_mt4(N)")`. Checker: `adaptive_shared_outputs` / IMP learn `AtrShared`; `_kind` knows `whull-` / `known-`.

4.4 The one regression I caused and fixed: allowing a flat band input made `test_generator_maf` (which pins `band_inputs = ["flat"]` as refused for FRAMA / MAMA)
fail; it is now refused unless `[inputs].band_flat = true`.

4.5 The only edit to an existing test file: `maf_support.py` (one `isinstance` includes `AtrShared`).

**Guards seen to fire** (each has a deliberately broken input in the tests; CLAUDE.md 4.4):

| guard | broken input | seen |
|---|---|---|
| `scale` role | atr of copy sc40B x (1 + 1e-9) on one row; copy of40B with the offset added | FAIL; with the transform offset changed to 123.456 the checks still PASS (offset ignored); as a `level` column the same copy FAILs (the role matters) |
| `scale` / `level` clash | `level_columns = ["atr"]` while `scale_columns` contains it | spec refused (ADAPTIVE_BAD) |
| `window_hull` | flatB (TR constant: atr sits on both edges) +1e-12, +4e-4 x 1e-9, -1e-12; rows < P; AT20 | FAIL (ratio > 100); +4e-16 / +5e-16 PASS; a 1e-6 error at row 10 does not touch the hull row (it fails the trace) |
| `known_value` | flatB +1e-9 (FAIL), +1e-13 (PASS); ramp row 14 +1e-9 (FAIL), row 13 (PASS, trace FAIL) | seen |
| `bound-atr` | s5 atr row 100 -0.01 (FAIL); flat -1e-16 (PASS), -1e-14 (FAIL) | seen |
| `bound-tr-range` | rampB tr row 50 -1e-9 (FAIL), -5e-16 (PASS), row 0 -1e-3 (not read, PASS) | seen |
| old bound behaviour | `tol_bound_abs = 0` | tolerance 0.0, result unchanged |
| input guards | clock_close x 100; `xh_s5B` +1e-9 | G_CLOCK, G_INPUT_MISMATCH |
| IMP | AT14 replayed with the AT20 model; AT14 vs the Wilder model; NCS vs the AT14 model | FAIL (must_pass) / PASS (must_fail, ratio 1.8e9 / 9.0e9) |
| call-order replay | NCS replayed in the input-major order | differs from the perfect run by > 1e-6 (test) |
| conditioning pre-run (vii) | an INFO entry injected into the AT14 table | 1 mismatch |
| no-static lint | the NCS body | 1 hit (`ats_prev`, line 1); 0 hits on the corrected code and on NC0 / NCWi / NCR / NCZ; the spec-wired check fires on a temp `ATR.c` holding the NCS body and is clean on the corrected body |
| existing-spec hashes | one byte appended | hash changes |
| refusals | bad `bar_args`, hull of a column on itself, `known_value` on an unknown input, bad `range_bound`, non-bool `ramp_down`, missing `window`, missing tolerance, `abs` on `trace`, flat band without `band_flat` | each refused with its code |

## 5. Floors and the tolerance window per quantity (D2 rule 3)

| quantity | tolerance | floor (b) | floor x 10 | smallest required effect | / 10 | window |
|---|---|---|---|---|---|---|
| trace (tr, atr) | 1e-12 | 8.882e-16 (IMP estimate; conditioning max 4.441e-16) | 8.88e-15 | NCWi 1.870e-4 (atr, s40) | 1.9e-5 | ok both sides |
| equivariance (scale) | 1e-12 | 1.776e-15 (model, sc tr) | 1.78e-14 | real variants only (no control is called on the copies) | - | ok |
| known_value | 1e-12 | 4.407e-17 | 4.4e-16 | NC0 2.857e-5 (required) | 2.9e-6 | ok |
| imp | 1e-12 | 8.882e-16 (`%.15f` replay); NCS / NCS2 replays up to 2.207e-15 (the shared state carries the rounding) | 8.9e-15 / 2.2e-14 | must_fail 1.831e-3, 9.045e-3 | - | ok |
| bound (abs 1e-15 + rel 1e-12) | 1e-15 | model: atr min 0, TR-(H-L) min 0 | structural | NCS atr < 0 (1.57e12 x) | - | ok |
| window_hull (net of 1e-12 relative, abs 1e-15) | 1e-15 | model violation 0 on every input | structural | NC0 3.5e10 x | - | ok |

(b) No `floor x 10 > tolerance`: no STOP. Note on `window_hull` (does not fit the brief literally): "fires on one row out by 1e-12 relative" cannot hold: at the ATR scale
(4e-4) 1e-12 relative is 4e-16, inside the allowance (relative part + 1e-15 absolute). The test fires on 1e-12 ABSOLUTE (= 2.5e-9 relative) and on a 1e-9 relative excess,
and records that 4e-16 / 5e-16 pass. If you want a stricter hull, the absolute part is the knob (a spec change before the commit).

## 6. Controls: effects and `[detect.required]`

Effect = max |control - AT14| over all rows (atr unless stated); detection ratio = effect / row tolerance on the own-model raw file (D2 Amendment 1). Every control has
at least one required kind >= 10x: **no STOP**. Blind inputs = effect <= 1e-11 (the planning chat's lists, reproduced).

| control | effect (b) | blind inputs | rows where it differs (> 10 tol) | ratios (kind: x tolerance) | `[detect.required]` |
|---|---|---|---|---|---|
| NCW (Length 15) | 7.673e-3 (s5B) | flat | 14 .. 2999 | trace 7.67e9, window_hull 3.83e12, known_value 4.0e8 | trace, window_hull, known_value |
| NC0 (TR[0] in the first window) | 2.738e-4 (s10B) | flat | 14 .. 2999 (persistent) | trace 2.74e8, window_hull 3.51e10, known_value 2.86e7 | trace, window_hull, known_value |
| NCWi (Wilder) | 1.870e-4 (s40) | flat, flatB, ramp, rampB, rampdn, rampdnB | 15 .. 2999 | trace 1.87e8, window_hull 6.10e10; known_value 4.4e-5 (below 10x) | trace, window_hull |
| NCR (TR = H - L) | atr 7.892e-3 (s5), tr 1.176e-2 | flat, flatB, rampB, rampdnB | tr 1 .. 2999, atr 14 .. 2999 | trace 1.18e10, known_value 1.0e8; window_hull 0 | trace, known_value |
| NCZ (start-up mean) | 9.711e-3 (s5B) | flat | **1 .. 13 only** | trace 9.71e9; known_value 4.4e-5 and window_hull 0 (rows >= P identical to AT14) | trace |
| NCS (shared static, instance 1) | see 7 | - | - | trace 9.04e9, bound 1.57e12, window_hull 5.20e12, known_value 4.49e9 | trace, bound, window_hull, known_value |
| NCS2 (instance 2) | see 7 | - | - | trace 9.26e9, bound 1.75e12, window_hull 5.46e12, known_value 4.01e9 | trace, bound, window_hull, known_value |

`[detect.info_only]` is not used: every kind >= 10x is required (the brief's rule); kinds at 0 / below 10x are listed in `[detect].source` as non-discriminating.
Judgement for you: for NCS the kinds `bound` (the shared static drives atr negative, min about -1.6e-3) and `window_hull` are consequences of the shared state rather than the
construct itself; they are >= 10^12 x the tolerance, so I required them. Say if you prefer them INFO-only. NCZ is caught on trace only, from row 1 (as the brief predicted).

## 7. NCS in the generated call order

Order parsed from the generated script text (the `// <variant> <input>` of each call line), not from the input list: **per bar, NCS on the 16 inputs, then NCS2 on the same 16**
(variant-major, 32 calls, the static shared by all of them); the 16 are `flat, s5, s10, s20, s40, s100, ramp, rampdn, flatB, rampB, rampdnB, s5B, s10B, s20B, s40B, s100B`
(base inputs first, then the bands in `[inputs].band_inputs` order). The checker's `adaptive_shared_slots` yields the same 32 pairs (test). max |NCS - AT14| over all rows:

- NCS: flat 4.49e-3, s5 9.04e-3, s10 5.23e-3, s20 3.49e-3, s40 3.16e-3, s100 3.54e-3, ramp 4.02e-3, rampdn 4.02e-3, flatB 3.72e-3, rampB 3.72e-3, rampdnB 3.72e-3, s5B 9.03e-3, s10B 5.26e-3, s20B 3.48e-3, **s40B 2.570e-3 (minimum)**, s100B 2.96e-3
- NCS2: flat 3.74e-3, s5 8.65e-3, s10 5.08e-3, s20 3.25e-3, s40 3.05e-3, s100 3.52e-3, ramp 4.01e-3, rampdn 4.01e-3, flatB 3.71e-3, rampB 3.71e-3, rampdnB 3.71e-3, s5B 9.26e-3, s10B 5.69e-3, s20B 3.70e-3, s40B 3.24e-3, s100B 3.70e-3

Minimum over (instance, input) = **2.570e-3** (NCS, s40B) = 2.57e9 x the trace tolerance; none below 10x (the brief expected none). The planning chat's assumed orders gave 2.581e-3
(instance-major) and 3.265e-3 (input-major) over ITS input-list order (flat, flatB, ramp, ...), which differs from the script's order; the input-major order over the script's own 16
inputs gives 2.806e-3 (NCS2, s40). The numbers depend on the order, as the MAF lesson says; a test shows that reordering `band_inputs` changes the generated order. The spec stores the generated-order value.

## 8. IMP fire-test values (full precision)

(b) A perfect run printed with `%.15f` (own-model raw file, x / High / Low rounded as Zorro exports them), max over the columns per (variant, input); the ratio to the 1e-12 tolerance
is <= 2.2e-3. Worst pair per variant is in the spec (`[imp.fire_test.exported_x_15f]`): AT14 / AT20 / NCW / NC0 / NCWi / NCZ 8.881784197001252e-16 (s5:tr), NCR 8.881784197001252e-16
(s5B:tr), NCS 2.207001942311493e-15 (s5:atr), NCS2 2.127638343285554e-15 (s100B:atr). Per-pair values: `atr_support.numbers()["imp15"][...]["detail"]`.

| input | AT14 | AT20 | NCW | NC0 | NCWi | NCR | NCZ | NCS | NCS2 |
| flat | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 2.127638343285554e-15 | 1.8923664718561994e-15 |
| s5 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 0.0 | 8.881784197001252e-16 | 2.207001942311493e-15 | 1.9080874033572393e-15 |
| s10 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 0.0 | 8.881784197001252e-16 | 2.1911725905932045e-15 | 1.9239167550755276e-15 |
| s20 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 0.0 | 8.881784197001252e-16 | 2.095979639848977e-15 | 1.9400713674455616e-15 |
| s40 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 0.0 | 8.881784197001252e-16 | 1.969127985668173e-15 | 1.9079789831399907e-15 |
| s100 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 0.0 | 8.881784197001252e-16 | 1.9557922989466014e-15 | 1.9376861226660935e-15 |
| ramp | 2.220446049250313e-16 | 2.220446049250313e-16 | 2.220446049250313e-16 | 2.220446049250313e-16 | 2.220446049250313e-16 | 0.0 | 2.220446049250313e-16 | 1.9557922989466014e-15 | 1.9376861226660935e-15 |
| rampdn | 2.220446049250313e-16 | 2.220446049250313e-16 | 2.220446049250313e-16 | 2.220446049250313e-16 | 2.220446049250313e-16 | 0.0 | 2.220446049250313e-16 | 1.9557922989466014e-15 | 1.9376861226660935e-15 |
| flatB | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1.9557922989466014e-15 | 1.9376861226660935e-15 |
| rampB | 2.220446049250313e-16 | 2.220446049250313e-16 | 2.220446049250313e-16 | 2.220446049250313e-16 | 2.220446049250313e-16 | 2.220446049250313e-16 | 2.220446049250313e-16 | 1.9557922989466014e-15 | 1.9376861226660935e-15 |
| rampdnB | 2.220446049250313e-16 | 2.220446049250313e-16 | 2.220446049250313e-16 | 2.220446049250313e-16 | 2.220446049250313e-16 | 2.220446049250313e-16 | 2.220446049250313e-16 | 1.9557922989466014e-15 | 1.939746106793816e-15 |
| s5B | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 1.95590071916385e-15 | 1.9873425821659296e-15 |
| s10B | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 1.908412664008985e-15 | 2.0032261439928423e-15 |
| s20B | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 1.9400713674455616e-15 | 2.0326622329758237e-15 |
| s40B | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 1.8923664718561994e-15 | 2.048491584694112e-15 |
| s100B | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 8.881784197001252e-16 | 1.8923664718561994e-15 | 2.127638343285554e-15 |
| sc40B | 8.881784197001252e-16 | 8.881784197001252e-16 | - | - | - | - | - | - | - |
| of40B | 8.881784197001252e-16 | 8.881784197001252e-16 | - | - | - | - | - | - | - |

`must_pass` on the exact own-model file: 0.0 for all 9 variants. `must_fail`: AT14 replayed with the NCWi (Wilder) model **0.0018306291425544303** (ratio 1.831e9); NCS replayed with the AT14
model **0.009044766946306704** (ratio 9.045e9). Discrimination (each variant's own output replayed with the AT14 model): AT14 0.0, AT20 0.010616854905823711 (sc40B:atr), NCW 0.007672586913747551,
NC0 0.0002737651885733358, NCWi 0.0001870053855561963, NCR 0.011755705045852771 (s5:tr), NCZ 0.009710565162951434, NCS 0.009044766946306704, NCS2 0.009259101256852854.

## 9. Greps

- `ATRMT4` / `ATRMT4Core` over `C:/Zorro/include/*` (also with `-w`): **no hit**. Zorro's own ATR-family names there: `ATR` (two overloads, `functions.h:308-309`), `ATRS`, `NATR`, `TrueRange` (`func_list.h`): our names do not collide.
- Callers of `ATRMT4` in the repo: none.
- Prefixes `at_`, `atw_`, `ats_` (and my control prefixes `ax0_`, `axi_`, `axr_`, `axz_`) over `*.c`, `*.h`, `*.toml`: **no use** outside the ATR spec. The only other hit of `at_` is a Python helper `at_bars` in `docs/learning/highpass_playground.py` (not a C identifier). Stage 2 adds them to gotchas 1.3.

## 10. What did not fit the brief / decisions for you

1. `window_hull` "fires on a row out by 1e-12 relative": not possible with the pre-registered allowance (section 5); implemented as 1e-12 absolute. Needs your OK or a spec change before the commit.
2. Tooling beyond the three named (4.2): `known_value`, `range_bound`, absolute allowances, `window`, `bar_args`, `band_flat`. All opt-in; I think they are the minimum.
3. "Trace from row 1" is read as D7's row 1 = n 0 (start-up included); "equivariance rows >= 1" as n >= 1 (at n = 0 both columns are 0 on every input, so nothing is lost); known answers and hull from n = P (0-based, ATR[P] = row P). The spec header states the convention.
4. The spec's `[detect.required]` follows the brief's rule literally; no `[detect.info_only]`; see section 6 for the NCS judgement.
5. Series length: the spec's `series_len = 22` (>= Length + 1 for AT20 = 21). Pre-run (vi), stage 2: `series(0, Length + 2)` with an expression length must compile and allocate per call in Light-C; fallback pre-registered (fixed bound 64 with a `Length <= 62` guard).
6. Not written (stage 2 by the brief): `indicators/nnfx/ATR.c`, the `XCHK_ATRMT4_vs_ATRS.c` script (criterion pre-registered in the spec's `[cross_check]`: rows >= 100, max relative diff <= 1e-9, 1 variant), the Amendment 1 / pre-run records, gotchas 1.3 prefixes, the HARNESS_DESIGN "D7 applied to ATR" paragraph, PROJECT_STATE. The five inline control bodies are in the spec (derived from the brief's code block by `atr_support.control_body`; a test asserts the spec equals the derivation).
7. The brief's commit split would leave the tooling commit red: the new tests load the spec. See the commands below.
8. Windows line endings: working copy CRLF, repo LF; plain `git diff --stat` and `--ignore-cr-at-eol` agree (no whole-file churn): 4 modified files, 258 insertions, 20 deletions; new files are LF.

## 11. Suggested git commands (you run them; one step at a time, wait for the output of each)

```
git diff --stat --ignore-cr-at-eol          # first; expect checker, generator, reference, maf_support only
git status --short
```
The brief's split (tooling + tests + numbers + brief; then the spec) makes commit 1 fail its own new tests (they load the spec). Recommended instead, each commit green (853 / 926):
```
git add analysis/harness/checker.py analysis/harness/generator.py analysis/harness/reference.py analysis/harness/tests/maf_support.py docs/harness/ATR_STAGE1_NUMBERS.py docs/harness/ATR_STAGE1_NUMBERS_output.txt docs/harness/ATR_STAGE1_PROMPT.md
git commit -m "harness: ATR tooling (scale role, window_hull, known_value, range bound, rampdn / flat bars, hlc call order), atr_mt4 / atr_shared models, planning numbers"
git add analysis/harness/specs/ATR_MT4Fidelity.toml analysis/harness/tests/atr_support.py analysis/harness/tests/regen_baseline.json analysis/harness/tests/test_reference_atr.py analysis/harness/tests/test_checker_atr.py analysis/harness/tests/test_generator_atr.py analysis/harness/tests/test_reference_atr_spec.py docs/harness/ATR_STAGE1_REPORT.md
git commit -m "harness: ATR_MT4Fidelity spec draft (AT14 / AT20, 7 controls, 90 real checks), ATR stage 1 tests and report"
```
Test counts for commit messages come from your Git Bash run (CLAUDE.md section 8); mine: 853 before, 926 after.
