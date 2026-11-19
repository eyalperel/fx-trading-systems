# LRSI stage 1 — report (tooling, reference models, tests, spec draft)

**Date:** 2026-11-19. **Branch:** `harness-lrsi` (HEAD `6382607`); the work is not committed yet.
**Brief:** `docs/harness/LRSI_STAGE1_PROMPT.md`, including Amendment 1 (NCS call order, user decision A + C).
**Source review:** `docs/harness/LAGUERRERSI_SOURCE_REVIEW.md`.
**Spec draft:** `analysis/harness/specs/LRSI_ArticleFidelity.toml`. It is not committed yet, so it is not yet pre-registered.

No `.c` file was edited and Zorro was not run. Labels: (a) source states, (b) measured here, (c) inference.

## 1. Run history

- **First pass (2026-11-19).** Stopped at the brief's NCS STOP condition. The replay in variant-major order put the run's only
  seed on NCS `flat`. Every other (instance, input) pair was bit-identical to the G05 model, so no PASS/FAIL check could see the control.
- **Second pass.** The user chose A + C (Amendment 1), and this pass carried out the full stage.
- **Decision C.** The no-static lint covers L-3 (the shared statics).
- **Decision A.** NCS and NCT skip `flat`, so the seed lands on NCS `s5`. (b) The checker's start-up effect for NCS `s5`, in the
  actual call order, is **0.5979633949986088**. That equals the brief's value exactly (relative difference 0, limit 1%).
- **No STOP condition fired.** Specifically:
  - every D2 window holds;
  - every control has at least one kind at 10× or more;
  - the NCS value matches;
  - no pre-registered line raises a Light-C concern (no decimal literal, no `PI`, no `Period`, and the five `series()` calls come first: asserted).

## 2. Tooling

All changes are opt-in. The 8 existing specs regenerate **byte-identical** scripts.

| Brief item | Where | Tests |
|---|---|---|
| Real-valued parameter `[[n, d]]` → `var lrs_g1_2 = 1; lrs_g1_2 = lrs_g1_2 / 2;` | generator `real_params`, `real_param_name`, call args. **Opt-in through `[batch].real_params = true`** (§7) | `test_generator_lrsi` 04 and refusals 01 |
| Four columns per call (`l0`, `l3`, `den` by out-parameter; `out` returned) | `OUTPUT_NAMES`; the RFX / MST local-scalar call path | `test_generator_lrsi` 05 and 07; `test_checker_lrsi` columns 01 |
| Linear checks on two outputs, each against its own table | `[checks].linear_output = ["l0", "l3"]`; variant `expected_outputs`; checker `linear_views`; ids end in `-l0` / `-l3` | `test_checker_lrsi` TestTwoLinearOutputs (swapping l0 into l3 fails lag and phase; gain cannot see it, because \|L3\| = \|L0\|) |
| `rampdn` input | `[inputs].ramp_down`; generator / checker inputs | `test_generator_lrsi` 06; `test_checker_lrsi` 03 (input guard) |
| `ramp_exact` kind | `[checks].ramp_exact`; checker `osc_rows`, `_kind` → `ramp_exact` | Fires on a 0.9999999 row (\|diff\| 1e-7); 5e-13 passes the check but trips the floor guard (tolerance/10 = 1e-13); NaN gives ERROR |
| `startup` on the normalised output | `[checks].startup_output`; checker `osc_rows` | Fires on a price-seeded G05 `s20` column (0.9233174011464185 = NCP, T = 20); tolerance edge at 9e-7 / 2e-6 |
| Gate on the model's CU + CD | `gate_q(LrsiOut) = den` | Unit row (5 gated); gate 1.3 → 230 of 2300 rows gated on G05 T = 20, still PASS; gate 100 → ERROR; a broken run cannot gate its own rows away |
| `skip_inputs` (Amendment 1 A) | generator plan; checker `variant_inputs` / `variant_columns`; results header `SKIPPED_INPUTS` | No call, no column, no check; a stray `out_NCS_flat` column fires `G_HEADER`; the superseded call order is parsed from the script and equals `lrsi_shared_slots` |
| No-static lint (Amendment 1 C) | `[lint].no_static`; generator `lint_no_static` / `no_static_report`; `--lint-only` and `write_script` refuse (`L_NO_STATIC`); the checker writes an `INFO L_NO_STATIC` line to the results header | Fires on `git show 6382607:indicators/ehlers/LaguerreRSI.c`: **2 hits, `lr_init` (line 77) and `lr_prevRSI` (line 128)**. 0 hits on the pre-registered lines; comments and strings are excluded |
| `lrsi_article(g, g_l0, form, seed, hold0)` and `lrsi_superseded` (shared statics, actual call order) | reference: `simulate_lrsi`, `simulate_lrsi_shared`; `IMP_MODELS`; checker `_imp_lrsi` / `lrsi_shared_slots` | `test_reference_lrsi` |
| `[zorro].include` | spec | Lint reports only the stage-2 items (§5) |

## 3. Counts

| Quantity | Value |
|---|---|
| Variants | **9** = 3 real (G05, G07, G08) + 4 controls (NCG, NC25, NCP, NCS) + 2 info (NCH, NCT) |
| Real checks | **129** = 3 × 43. Per variant: l0 14 + l3 14 + out 15 (5 trace, 2 invariance, 1 bound, 2 ramp_exact, 5 startup). Matches the brief. No SKIP rows. |
| Checks per variant | Real 43; NCH / NCG / NC25 / NCP 41 (no invariance); NCS / NCT 13 (out only: trace, bound, ramp_exact, startup) |
| IMP rows / floor rows | 10 (9 must_pass + 1 must_fail) / 21 (3 real × 7 kinds) |
| Raw columns | **319** = 2 + 19 inputs + 298 outputs (real 46 each; 4-output controls 36; NCS / NCT 8 each) |
| Calls per bar | 109 (57 `LaguerreRSICore`, 36 inline, 16 `LaguerreRSI_Superseded`) |
| Synthetic perfect run | VERDICT PASS: 129/129; every control fails on every required kind |

## 4. Numbers (findings 1–10)

**Tables.** The L0 / L3 tables are evaluated from the product form H_L0 × A³. Against the brief: max \|diff\| **7.1e-15**.
(b) The expanded L3 polynomial (`cascade`) is only about 2e-12 accurate at gamma 0.8 (DC gain 1 − 2.1e-13), so it is not used
for the tables.

Simulated stages vs one-filter simulations, rows ≥ W: max 3.7e-13 (limit 1e-12).

`lrsi_article` vs the independent review model (`src`), every row of 9 inputs × 3 gammas: 4.4e-16.

| # | Finding | vs brief |
|---|---|---|
| 1 | Tables; ramp lag theory 1 / 10, 2.333 / 19.333, 4 / 31; measured 1.000000000000245 / 9.999999999999586 … | ≤ 7.1e-15 |
| 2 | Floors: gain 1.09e-12, phase 1.01e-13, lag 1.08e-12, flat 2.2e-15, invariance 1.05e-12; trace / startup / ramp_exact 0. Model = code, so (c) the floor is the IMP residual. All D2 windows OK. | — |
| 3 | Gate margins (15 values), tightest 0.07555156262124552 (G05, T = 100); alt 2.0 / 1.0588 / 0.6667 | exact |
| 4 | out in [0, 1] exactly; 0.0 and 1.0 are attained | exact |
| 5 | Invariance (6 values) | exact |
| 6 | Start-up G05 T = 20 rows 0–3: 0.7142857142857143, 0.7148014911433533, 0.8001802080788746, 1.0; memory 61 / 120 / 196 | ≤ 1.1e-16 (1 ulp, row 0) |
| 7 | Pinning shares (15 values) | exact |
| 8 | Ramp rows 3 / 6 / 10 and 23 / 43 / 68 | exact |
| 9 | alt out = 1/3 and 2/3 | G05 / G07 exact; **G08 differs by 8.9e-14** (not bit-exact; the brief says "exactly") |
| 10 | Flat: G05 CU + CD = 0 from row 69, holds 1.0; G07 / G08 never reach 0 | exact |

**Control effects vs the brief** (relative): NCG trace and start-up 0; NCG gain / phase / lag 2.9e-13 / 1.7e-12 / 1.3e-13; NC25 trace 0;
NC25 L3 gain / phase ≤ 1.5e-14; NC25 L3 lag 7.0 (analytic; the brief's 7.000000000000228 is a measured value); NCP start-up ≤ 5.2e-16.

## 5. Spec draft

**Tolerances:** flat 1e-9, gain 3e-5, phase 3e-5 rad, lag 1e-3, trace 3e-5, startup 1e-6, ramp_exact 1e-12, bound [0, 1] with
tol_abs 1e-12, invariance 1e-9, x 1e-12, imp 1e-9. Gate 0.01, W = 700, phase gate 0.05.

| Control | `[detect.required]` | Effect / tolerance |
|---|---|---|
| NCG (gamma + 1/1000 in L0) | gain, phase, trace, startup | 37.9×, 44.5×, 28.2× (the tightest), 4.84e3×. Lag is 4.0×, so it is not required |
| NC25 (TASC 2025 form) | gain, phase, lag, trace, startup | 1.48e4×, 5.12e4×, 3.0e3×, 1.28e4×, 3.85e5× |
| NCP (price seed alone) | startup | 9.39e5× (it is invisible on rows ≥ W) |
| NCS (superseded, instance 1) | startup | 5.98e5×, on `s5` only |

**NCS per (instance, input)**, against the G05 model:

| Pair | Result |
|---|---|
| NCS `s5` | Max 0.5979633949986088 below W. Last row with \|diff\| > 0: 69; > 1e-12: 60 (= brief). Rows ≥ W: 0 |
| Every other NCS pair, and every NCT pair (s5 … rampdn) | 0.0 on every row |

**Info variants:** NCH effect 0 everywhere (the hold never fires before a first defined value). NCT is bit-identical to G05.

**IMP fire tests:**
- must_fail G05 vs the NCG model: 0.0008469690515429118.
- Discrimination vs G05: G07 0.7307842800468098, G08 0.9674386805376683, NCG 0.0008469690514941175, NC25 0.38513302852097764.
  G05, NCH, NCP, NCS and NCT are 0 (`O_IMP_ROWS`).
- No must_fail row for NCS: it is bit-identical on rows ≥ W (stated in the spec).

**Pre-run (iii)** (`test_reference_lrsi_spec`): every number reproduces with deviation 0. That covers 78 table values, 8 + 24 floors,
40 effects, the fire tests and 146 `[findings]` keys.

**Lint (`--lint-only`):** clean except the two stage-2 items:
- the `LaguerreRSI_Superseded.c` include does not resolve yet;
- `L_NO_STATIC`: the current `LaguerreRSI.c` still has `lr_init` and `lr_prevRSI`.

## 6. Tests

| Run | TOTAL | PASS | FAIL | ERROR | SKIP |
|---|---|---|---|---|---|
| Before (`6382607`, Claude Code shell) | 555 | 555 | 0 | 0 | 0 |
| After (Claude Code shell) | **640** | 640 | 0 | 0 | 0 |

The 85 new tests are split as follows: `test_reference_lrsi` 27, `test_generator_lrsi` 25, `test_checker_lrsi` 22,
`test_reference_lrsi_spec` 11. The helper is `lrs_support.py`. `rfx_support.own_model_outputs` now also replays `LrsiShared`.
The count for the commit message comes from the user's Git Bash run.

## 7. Did not fit the brief / decisions taken here

1. **Real-valued pairs are opt-in through `[batch].real_params = true`.** An existing test (`test_generator_rff` 08) asserts that
   RFF refuses `[[48, 10]]`, so pairs could not be accepted everywhere without changing old-spec behaviour. Old specs refuse
   them as before (asserted).
2. **The second superseded instance, NCT, has role info.** Once NCS takes the seed, NCT is bit-identical to the model. A
   neg_control that no kind can detect would make the run fail. NCT still runs every bar (D6 rule 5) and is replayed by IMP in
   call order.
3. **NCS "last differing row":** 60 by the review's measure (\|diff\| > 1e-12), 69 for any nonzero difference. Both are recorded.
4. **G08 alt output** is 1/3 and 2/3 only to within 8.9e-14 (finding 9 said "exactly"). It is an INFO observation and does not
   affect any check.
5. **The ramp_exact floor guard is tight: tolerance/10 = 1e-13.** It holds because CD = 0 (or CU = 0) exactly on the ordered
   ramp, so out is exactly 1 or 0. Any Zorro deviation larger than 1e-13 there would fail the floor guard (pass item 7) even
   though the check passes.
6. **The no-static lint also refuses `write_script`** while the file has a static. Stage 2 can generate the script only after
   the corrected `LaguerreRSI.c` is written. This is intended, but it is a new refusal path.
7. **Rerun rule** (Amendment 1) is recorded in `[run_notes]` and `O_STATICS_RESET`.

## 8. Next (stage 2, not started)

1. Commit the tooling and tests, then the spec draft with this report. Committing the spec is its pre-registration.
2. Write the corrected `LaguerreRSI.c` to `[corrected_code]`, and `LaguerreRSI_Superseded.c` (the current body, renamed
   `lr_` → `lro_`).
3. Run pre-run (i)–(v), record them in Amendment 1, generate the script, and hand over the run card.
