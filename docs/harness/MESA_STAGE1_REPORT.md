# MESA stage 1 — report (tooling, reference models, tests, spec draft)

**Date:** 2026-11-19. **Branch:** `harness-mesa` (HEAD `c760160`), work uncommitted at the time of writing.
**Brief:** `docs/harness/MESA_STAGE1_PROMPT.md`. **Source review:** `docs/harness/MESASTOCHASTIC_SOURCE_REVIEW.md` (`3f0de96`).
**Spec draft:** `analysis/harness/specs/MESA_ArticleFidelity.toml` (not yet committed, so not yet pre-registered).
No `.c` file was edited and Zorro was not run. Labels: (a) source states, (b) measured here, (c) inference.

## 1. Run history

- A first session was cut off by a laptop restart (2026-11-19, about 01:14). Its partial edits to `checker.py`, `generator.py`,
  `reference.py` and the draft spec were left uncommitted, with a backup in `stash@{0}`. The stash is untouched and matched
  the working tree when this session resumed.
- (b) Line endings: the committed blobs are LF and the working copy is CRLF for every file (`core.autocrlf=true`,
  `git ls-files --eol` shows `i/lf w/crlf`). The resume brief assumed the three `.py` files had been switched to CRLF; they had not.
  `git diff --stat` showed only real changes. Decided 2026-11-19 (user): no conversion.
- (b) Review of the partial work: nothing was cut off and the code was consistent. The suite passed unchanged at 460/460. The gaps
  were the missing tests, two inconsistencies in the spec text (fixed, §6), and the bound's `actual` column (fixed, §2).

## 2. Tooling (D6 rules 1–4, extensions only)

| Brief item | Where | Tests |
|---|---|---|
| Three outputs per call (`roof`, `stoc` by out-parameter, `out` returned) | generator `OUTPUT_NAMES` / `RETURN_NAMES` / `LINEAR_NAMES`; the call path is the RFX one | `test_generator_mst` 02–04 |
| Three-parameter variants `[L, HP, SS]` | existing `params` list | `test_generator_mst` 02, 06 (refusals); `test_checker_mst` 03 |
| Two-sided absolute bound `[0, 1]`, tol_abs 1e-12, read from `bound_output = "stoc"`; Reflex form unchanged | checker `m_bound_two_sided`, `osc_rows`; generator validation | `test_checker_mst` TestTwoSidedBound (fires on 1.0000001 and on −1e-9) |
| `expected` / `actual` report the breached side (min if the low side is breached, max otherwise) | checker `osc_rows` (decision 6, 2026-11-19) | as above: the −1e-9 row reports `actual = -1e-09`, `expected = 0.0` |
| Trace gate on the model's range (HH − LL) / amplitude; a sine gated out entirely = ERROR | checker `gate_q`, `m_trace`, `m_invariance_q` | `test_checker_mst` TestTraceGateOnTheModelRange (46 rows gated at g = 0.03, reported, then FAIL on a used row) |
| `mesa_article(L, hp, ss, win, scale, fallback, da_final, literals, final_seed)`, `mesa_code`, `mesa_superseded`, `simulate_mesa`; IMP_MODELS for every variant | reference | `test_reference_mst` |
| Roof via the RFF model, agreement ≤ 1e-12 | `simulate_mesa` uses `cascade(hp, ss)`, seed `zero` | (b) max \|diff\| **5.0e-15** against the stage-by-stage RFF model (3 (hp, ss) × 8 inputs, code and article) |
| Start-up INFO (`startup_info`); IMP only on rows ≥ W | checker / generator | `test_checker_mst` 04, 05; TestImpReplay 04 |
| `[zorro].include` | spec | lint reports only `MESAStochastic_Superseded.c` as missing (stage 2) |
| The 7 existing specs regenerate byte-identical | — | `test_generator_mst` 01: **7/7 identical** (H1, SS2F, SS3F, HPF, RFF, USE, RFX) |

(b) Independent check of the model: a bar-by-bar translation of the EasyLanguage sidebar, with its own coefficients and loops
(`test_reference_mst.independent_mesa`), equals `simulate_mesa` to 2.4e-12 (sines, three parameter sets). The guard fires on
window 21 (1.1e-1), Zorro `PI` (1.9e-6), zero final seed (0.44), a1 + 1e-3 (3.4e-4) and fallback 0 (0.5).
Also (b): `mesa_superseded` output / 100 = the window-21 corrected model to ≤ 1e-12 (scale and fallback are both ×100 and the
smoothing is linear).

## 3. Counts

| Quantity | Value |
|---|---|
| Variants | 11 = 4 real (L14, L20, L30, S20) + 5 controls (NCW, NCA, NCP, NC1, NCS) + 2 info (NCL, NCZ) |
| Real checks | **84** = 4 × 21 (Roof: flat + 5 gains + alt gain + 5 phases + ramp residual = 13; out: 5 trace + 2 invariance = 7; stoc: 1 bound). Matches the brief. |
| Checks per variant | real 21; NCL / NCZ / NCW / NCA / NCP / NC1 19 (no invariance); NCS 5 (trace only: no roof, no stoc) |
| SKIP rows | 10 (alt phase of every variant that exports roof) |
| IMP rows / floor rows | 13 (11 must_pass + 2 must_fail) / 20 (4 real × gain, phase, resid, trace, invariance) |
| Raw columns | **308** = 2 + 18 inputs + 288 outputs (real 34 each = 8 roof + 8 stoc + 18 out; 3-output controls 24; NCS 8) |
| Calls per bar / Y slots | 128 (88 `MESAStochasticCore`, 32 inline, 8 `MESAStochastic_Superseded`) / 368 |
| Synthetic perfect run (own-model raw file) | VERDICT PASS: 84/84 real, every control fails on every required kind |

## 4. Roof tables (expected, `roof_article`, exact constants)

| T | Roof(48,10) gain | phase (rad) | Roof(48,20) gain | phase (rad) |
|---|---|---|---|---|
| 5 | 0.22329246373117576 | -1.7262724708581951 | 0.057431618504874854 | -2.0732111242169586 |
| 10 | 0.6812189601598664 | -1.0206179300609162 | 0.23365848260774072 | -1.8117540367506426 |
| 20 | 0.8900165495219391 | -0.05338683922280379 | 0.6487070206488631 | -0.8564295844658709 |
| 40 | 0.7405714692715243 | 0.769984001215179 | 0.719862160915718 | 0.3805302637415229 |
| 100 | 0.3152095678349821 | 1.8340513846255355 | 0.31497347991604596 | 1.6917733148669594 |
| alt (T = 2) gain | 6.034247078565135e-18 | SKIP | 1.5107043619184775e-18 | SKIP |

(b) Against the brief: max \|diff\| **1.69e-13** (limit 1e-12). T = 20 equals PROJECT_STATE §5 (0.8900165495219391) exactly.

## 5. Findings 1–9 reproduced (models vs the brief's (b) values)

| # | Finding | Deviation from the brief |
|---|---|---|
| 1 | Roof tables | ≤ 1.69e-13 abs |
| 2 | Roof `PI` floors (48,10) gain 5.277790209312627e-07, phase 1.328475247808214e-06; (48,20) gain 4.409028506735524e-07, phase 1.5671661010019378e-06 | agree at the brief's 4 digits |
| 3 | Trace floors (`PI` gap), largest L14 T = 100 = 3.875319340873595e-06 | ≤ 8.0e-7 relative |
| 4 | Gate margins, tightest L14 T = 100 = 0.02839652184680958 | ≤ 5.8e-14 abs |
| 5 | Stoc in [0, 1] exactly (0.0 and 1.0 attained); out at L20 T = 100 in [-0.029452071305996183, 1.02945207130599] | exact / ≤ 2e-15 |
| 6 | Invariance (float64) | round-off only, see list below |
| 7 | Start-up rows 0–3 (out 0.5, 0.5632987004029524, 0.6999002012721725, 0.8320600073104027; Stoc 0.5, 1, 1, 1); final-seed max diff 0.4367012995970475, last row 59 | ≤ 1e-12 / exact |
| 8 | M-1 shows only at T > L (NCW at T = 40 / 100: 0.06206839941904896 / 0.08053344297750009) | ≤ 7.7e-13 relative |
| 9 | No statics: D6 rule 5 not applicable (`O_NO_STATICS`) | — |

**Round-off differences (accepted 2026-11-19, decision 4).** All are ≤ 4.5e-13, both the brief's and the model's, and far below
every tolerance (invariance 1e-9, trace 5e-5). They come from floating-point order of operations and input construction:

| Quantity | Brief | Model |
|---|---|---|
| invariance scale10 / offset L14 | 2.124e-13 / 3.649e-13 | 4.4353e-13 / 6.5681e-13 |
| invariance scale10 / offset L20 | 1.064e-13 / 2.658e-13 | 1.9351e-13 / 3.4250e-13 |
| invariance scale10 / offset L30 | 5.324e-14 / 1.245e-13 | 9.8366e-14 / 1.9346e-13 |
| invariance scale10 / offset S20 | 5.068e-14 / 1.223e-13 | 4.1489e-13 / 3.5938e-13 |
| NCW (window 21) T = 5 / 10 / 20 | 7.1498e-14 / 1.1213e-14 / 4.2188e-15 | 7.5939e-14 / 1.1546e-14 / 6.4948e-15 |
| NC1 (L = 22) T = 5 / 10 / 20 | 1.2013e-13 / 2.1760e-14 / 8.1046e-15 | 1.2779e-13 / 2.2232e-14 / 1.2622e-14 |

`test_reference_mst` requires both values to stay below 1e-12 and prints each pair.

## 6. Spec draft: tolerances, floors, controls, IMP

**Tolerances** (D2 rule 3 window; lint: all 6 floor windows OK):

| Quantity | Tolerance | Floor (max over real) | floor × 10 |
|---|---|---|---|
| Roof gain | 3e-5 | 5.277790241509095e-07 | 5.3e-6 |
| Roof phase | 3e-5 rad | 1.567166116878127e-06 | 1.6e-5 |
| Roof ramp residual | 1e-9 | 9.491639793472638e-17 | 9.5e-16 |
| Roof flat | 1e-9 | 0 | 0 |
| trace | **5e-5** (this spec; the D6 default 3e-5 fails: floor × 10 = 3.88e-5) | 3.875319340873595e-06 | 3.9e-5 |
| invariance | 1e-9 | 4.43312053732825e-13 | 4.4e-12 |
| bound | [0, 1], tol_abs 1e-12 | — (exact by construction) | — |

Gate g = 0.01; W = 700; phase gate 0.05; floor guard trace tol/10 = 5e-6.

**Controls** (own-model effects measured with the checker; `[detect.required]`):

| Control | Required | Effect / tolerance |
|---|---|---|
| NCW window L + 1 | trace | 0.08053609924665306 (1.61e3×) |
| NCA final-SS a1 + 1/1000 | trace | 0.0007950728414501951 (**15.9×**, the tightest) |
| NCP HPPeriod 40 | gain, phase, trace | 0.07543229129532691 (2.51e3×), 0.1661996125421643 (5.54e3×), 0.4581775531393987 (9.16e3×) |
| NC1 L = 22 | trace | 0.1561252709006048 (3.12e3×) |
| NCS superseded file | trace | 101.85048536084172 (2.04e6×) |

**NCS bound (decision 2, 2026-11-19).** The brief said "bound fires on NCS". That was a planning-chat error: it read the model's
Stoc (max 100.00000000000001), but the superseded file returns only `out`. The run therefore has no `stoc` column and no bound row
for NCS. NCS is detected by trace alone (2.04e6×), which meets D2 per-control detection. The decision is recorded in `O_NCS_BOUND`
and in the spec header.

**INFO variants** (never PASS/FAIL):
- NCL, the article as printed: Roof gain 9.930912469835462e-05 (3.3×), phase 0.00024997116087721594 (8.3×), trace
  0.0006125625890712749 (12.3×). Article-form trace by T: 6.170130371996319e-05, 0.00016527359999052305, 0.0001580120786146555,
  0.00027302012118501917, 0.0006125625890712749. These are up to 2.4e-4 relative from the brief's values.
  **Construction (decision 3, 2026-11-19):**
  - The literals are built from integers: k = 707/1000, f = 1414/1000, g = 314159/100000.
  - The degree terms are converted with the Zorro `PI` macro: HP argument k·2.0·PI/HPPeriod; SS a1 = exp(−f·g/SSPeriod); b1 cosine
    f·PI/SSPeriod. The same SS is used for both passes.
  - The NCL body is pre-registered in the spec now (it is not written in stage 2) and uses exactly these lines, as does the IMP
    model `mesa_printed(20,48,10)`. `test_reference_mst` asserts the body text, the model coefficients (≤ 1e-15) and the wording
    of `O_NCL`.
- NCZ, the source's zero final seed: the start-up INFO row in the synthetic run is 0.4367013790854729 (rows < W, against the L20
  article model). From row 60 on it equals the library, so its IMP discrimination is 0.0 (`O_NCZ_IMP`).

**IMP fire tests** (synthetic own-model raw file, rows ≥ 700):
- must_fail L20 replayed with the NCA model: 0.0007941944211215524.
- must_fail NCS replayed with the L20 `mesa_article`: 101.85048536084172.
- Discrimination of each variant against the L20 `mesa_code` model:

| Variant | Discrimination |
|---|---|
| L14 | 0.6186225701532286 |
| L20 | 0.0 |
| L30 | 0.6810594509228197 |
| S20 | 0.6363837299515696 |
| NCL | 0.0009239790461956776 |
| NCZ | 0.0 |
| NCW | 0.15051468862821074 |
| NCA | 0.0007941944211215524 |
| NCP | 0.6186225701532286 |
| NC1 | 0.26438798675700037 |
| NCS | 101.8504853471644 |

(b) L14 and NCP have the same discrimination value. This is not an error: at T = 100 both runs saturate Stoc at 0 or 1 on the
same row, so both differences equal 1 − Stoc_L20 there.

**Spec text fixed (decision 5, 2026-11-19):** `O_WINDOW` and `O_OUTPUT_UNBOUNDED` now quote the `[findings]` values (one value per
quantity). `test_reference_mst_spec.test_observations_quote_the_findings` checks this.

**Pre-run (iii)** (`test_reference_mst_spec`): every number in the spec reproduces with **deviation 0** (≤ 1e-9 required):
expected tables (44 values), floors (24 + 6), effects (31 values), the IMP fire tests and discrimination, and all 113 `[findings]`
keys. Pre-run (ii): the current `MESAStochastic.c` blob is `a8c51bacf951cd1aa7a0d1c2f39347824ca1d6bf`, the value the spec records.

## 7. Tests

| Run | TOTAL | PASS | FAIL | ERROR | SKIP |
|---|---|---|---|---|---|
| Before (partial tree, 2026-11-19) | 460 | 460 | 0 | 0 | 0 |
| After (Claude Code shell, 2026-11-19) | **540** | 540 | 0 | 0 | 0 |

The 80 new tests are in `test_checker_mst` (34), `test_generator_mst` (16), `test_reference_mst` (19) and
`test_reference_mst_spec` (11), with the helper `mst_support.py`. Test counts for commit messages come from the user's Git Bash run
(CLAUDE.md §8).

## 8. Next (stage 2, not started)

1. Commit the tooling and tests, then the spec draft with this report. Committing the spec is its pre-registration.
2. Write the corrected `MESAStochastic.c` to `[corrected_code]`, and `MESAStochastic_Superseded.c` (the current body, renamed
   `mstc_` → `mstco_`). Then run pre-run (i)–(iv) and record them in Amendment 1, generate the script, and hand over the run card.
