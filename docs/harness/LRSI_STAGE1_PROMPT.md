# LRSI stage 1 — tooling + reference models + spec draft (LaguerreRSI)

Planning chat, 2026-11-19. Decisions accepted by the user: L-1..L-7 (`docs/harness/LAGUERRERSI_SOURCE_REVIEW.md`, `6382607`),
HARNESS_DESIGN **D6** (oscillator family, third indicator). Real variants G05 / G07 / G08, controls as listed. Build mode, speed
over polish; the validation gate is unchanged (CLAUDE.md). Labels: (a) source states, (b) measured/computed, (c) inference.
Run on **Opus, effort High**.

**Git:** branch `harness-lrsi` (at `6382607`, created by the user). Do NOT commit. At the end print the `git add` / `git commit`
commands you suggest (one commit for tooling+tests, one for the spec draft), and STOP. No `.c` edit, no Zorro run.

## Source (a): Ehlers, *Cybernetic Analysis for Stocks and Futures* (Wiley 2004), ch. 14, Fig. 14.8, p. 221

```
Inputs: gamma(.5);   Vars: L0(0), L1(0), L2(0), L3(0), CU(0), CD(0), RSI(0);
L0 = (1 - gamma)*Close + gamma*L0[1];
L1 = - gamma *L0 + L0[1] + gamma *L1[1];
L2 = - gamma *L1 + L1[1] + gamma *L2[1];
L3 = - gamma *L2 + L2[1] + gamma *L3[1];
CU = 0;  CD = 0;
If L0 >= L1 then CU = L0 - L1 Else CD = L1 - L0;
If L1 >= L2 then CU = CU + L1 - L2 Else CD = CD + L2 - L1;
If L2 >= L3 then CU = CU + L2 - L3 Else CD = CD + L3 - L2;
If CU + CD <> 0 then RSI = CU / (CU + CD);
Plot1(RSI, "RSI"); Plot2(.8); Plot3(.2);
```
All histories start at 0 and bar 1 is computed (L-1). RSI holds its previous value when CU + CD = 0, initial 0 (L-2). No trig,
no `PI`, no D1 literal (gamma is an input; 0.5 is exact): **no NCL variant** (state this in the spec). Fig. 14.9 (EFS) agrees.
(b) Transfer functions: L0 = (1 - g)/(1 - g z^-1) (EMA); each later stage multiplies by the allpass A = (z^-1 - g)/(1 - g z^-1).
So L3 = L0 * A^3: **|L3| = |L0| at every frequency**, DC gain 1 for both; ramp lag L0 = g/(1 - g), L3 = g/(1 - g) + 3(1 + g)/(1 - g).

## Planning-chat numbers to reproduce (b)

Independent float64 model (`docs/harness/LAGUERRERSI_REVIEW_MODEL.py` + this list); inputs as MST: level 1.1, amplitude 0.01,
slope 1e-4, N = 3000, sines T = 5, 10, 20, 40, 100, alt = level + amp(-1)^n; rows >= 700 unless stated. Reproduce with
`reference.py`; report any difference > 1e-12 (tables) or > 1% relative (effects).

1. **L0 / L3 tables** (analytic H(e^jw); gain, phase rad, T = 5, 10, 20, 40, 100; alt gain / phase):
   - G05: gain 0.515441182073583, 0.752937760164676, 0.9144826257394167, 0.9762503597414621, 0.9960766670440261 (L3 equal to
     ~1e-15); L0 phase -0.5123349109077545, -0.4584578266589488, -0.286493792460628, -0.15331917019845434, -0.06258501979842945;
     L3 phase -1.073070253482447, 1.1890249284130687, -2.947934343301334, -1.5444730894276493, -0.6265906978043936;
     alt gain 0.3333333333333333 (both), alt phase L0 0, L3 pi (wrapped).
   - G07: gain 0.29174705961302644, 0.5018320986484869, 0.7534909167069183, 0.9161156395618575, 0.9849968569076663; L0 phase
     -0.7042011354674697, -0.7590908589631391, -0.5743590867142185, -0.34096299632055205, -0.14481875420461615; L3 phase
     -2.416133825400453, -0.9154062977162627, 1.3201939041031179, -2.857979872282333, -1.2022268386477006; alt gain
     0.17647058823529416.
   - G08: gain 0.18686099078895038, 0.3402202928517172, 0.5814602765397503, 0.8185547295323827, 0.9627270885276253; L0 phase
     -0.7907222675568412, -0.9271383721938123, -0.8019659985004615, -0.5377451535315523, -0.24422102259248527; L3 phase
     -3.021781750026053, -2.0917388903309746, -0.2730544784005824, 2.047730334420252, -1.8980427173627845; alt gain
     0.11111111111111109.
   - Ramp lag L0 / L3: G05 1 / 10, G07 2.333333333333333 / 19.33333333333333, G08 4 / 31 (measured, last 100 ramp rows:
     1.0000000000002451 / 9.999999999999586, 2.333333333333565 / 19.333333333332867, 4.000000000000736 / 31.00000000000109).
   - Flat: L0 = L3 = level (DC gain 1). Alt phase gate 0.05: alt gains >= 0.111, so alt phase is CHECKED (not SKIP) here.
2. **Floor.** No `PI`, no decimal literal in the corrected code, gamma built from integers: (c) Zorro vs model expected at rounding
   level (MST IMP <= 8.9e-16). The D2 floor is therefore the IMP residual; state it as such. Defaults: gain 3e-5, phase 3e-5 rad,
   ramp lag 1e-3, flat 1e-9, trace 3e-5 (D6 default), start-up 1e-6 (D4 default), bound tol_abs 1e-12, invariance 1e-9,
   imp 1e-9, x 1e-12. Check each against D2 rule 3 with the control effects below; if one fails, STOP and report.
3. **Gate margin** min (CU + CD)/amplitude, model, rows >= 200 (G05 / G07 / G08), T = 5, 10, 20, 40, 100:
   1.5444174181677983, 1.5613948955003787, 1.2521910177791584, 0.42901079963528765, 0.07555156262124552 /
   0.5261922807346053, 1.5640737397439874, 1.2212991432978937, 1.1313729412971263, 0.24451738161783698 /
   0.31807224827549163, 0.8264689338118414, 1.5603221435723125, 1.4936947619025975, 0.5505114253350429.
   **Gate g = 0.01** (D6 default); tightest margin 0.0756 (G05, T = 100). Expected gated rows: 0. Alt: min 2.0 / 1.0588 / 0.6667.
4. **Bound:** the FINAL output is in [0, 1] exactly, every row of every input (CU, CD >= 0; hold starts at 0). Two-sided bound on
   `out` (MST tooling), tol_abs 1e-12. (b) 0.0 and 1.0 are attained (pinning, finding 7).
5. **Invariance** (rows >= 700, 5 sines), scale10 (amp 0.1) / offset (level 2.2) max |dout|: G05 2.8621549574836536e-13 /
   1.0507150705052481e-12; G07 1.7408297026122455e-13 / 3.647082635893639e-13; G08 1.3777867735598193e-13 / 3.011202398539581e-13.
6. **Start-up is PASS/FAIL here** (L-1: the source defines it). Check `out` vs the model on rows < W for each sine, tolerance
   1e-6. G05, T = 20, rows 0-3: 0.7142857142857142, 0.7148014911433533, 0.8001802080788746, 1.0. Start-up memory: the price-seed
   difference is gone after row 61 / 120 / 196 (G05 / G07 / G08, review §3). **W = 700** (family default, 3.6x the largest).
7. **Pinning** (rows >= 200; share at exactly 0 or 1), T = 5..100: G05 0, 0, 0.50, 0.70, 0.88; G07 0, 0, 0.10, 0.45, 0.78;
   G08 0, 0, 0, 0.20, 0.66. Record as [observations] O_PIN (why short T and several gammas are in the spec).
8. **Ramp known answers (new check kind):** rising ramp, `out` = 1.0 exactly from row 3 / 6 / 10 (G05 / G07 / G08); falling ramp
   (level - slope*n, new input) `out` = 0.0 exactly after row 23 / 43 / 68. Checked on rows >= W, tol_abs 1e-12.
9. **Alt:** `out` alternates between exactly 1/3 and 2/3 (all three gammas, rows >= 700). Record as [observations] O_ALT (INFO).
10. **Flat:** G05 reaches CU + CD = 0 exactly at row 69 and holds 1.0; G07 / G08 never exactly 0 (normalised rounding noise).
    Flat `out` is INFO (D6 rule 2), never PASS/FAIL.

## Tooling (extensions only)

- **Real-valued parameter built from integers:** `params = [[1, 2]]` -> generator emits `var <prefix>_g = 1; <prefix>_g = <prefix>_g/2;`
  (gotchas 9d.1, 9d.8) and passes it. 0.7 = [7, 10], 0.8 = [4, 5]. Old integer params unchanged.
- **Four columns per call:** `LaguerreRSICore(S, g, &l0, &l3, &den)` returns `out`; raw columns `l0`, `l3`, `den`, `out` per
  variant (local-scalar out-parameter pattern, `62b4e97`). Linear checks run on BOTH `l0` and `l3` (each its own expected table);
  trace, invariance, bound, start-up and ramp-exact read `out`; `den` is exported for information (the gate uses the MODEL's).
- **Falling ramp input** `rampdn` (level - slope*n), behind a spec flag, placed after `ramp`; default off.
- **New check kinds on `out`:** `ramp_exact` (rows >= W of `ramp` = 1, of `rampdn` = 0, tol_abs) and `startup` on the normalised
  output (rows < W of each sine vs the model, tolerance 1e-6), both PASS/FAIL.
- **Trace gate on the model's CU + CD** (model exposes it per row); rows below g excluded and counted; all rows gated = ERROR.
- **Reference models** (restricted grammar, no eval): `lrsi_article(g, g_l0 = None, form = "book" | "tasc2025", seed = "zero" |
  "price", hold0 = 0.0)` and `lrsi_superseded(g)` (= the old file, incl. the FILE STATICS `lr_init` / `lr_prevRSI` shared by every
  call, in the generator's actual call order: use the RFX shared-state replay). `l0` / `l3` tables from the analytic transfer
  functions above; the simulated stages must agree with them to <= 1e-12 after W.
- `[zorro].include`: `LaguerreRSI_Superseded.c`, `LaguerreRSI.c` (written in stage 2; lint may report them missing — say so, do
  not create them).
- Existing specs (H1, SS2F, SS3F, HPF, RFF, USE, RFX, MST) must regenerate BYTE-IDENTICAL scripts; their checker outputs unchanged.

## Corrected code (pre-registered lines; `.c` written AFTER the spec is committed)

```c
var LaguerreRSICore(vars Close, var gamma, var* pL0, var* pL3, var* pDen)
{
    vars lr_L0 = series(0, 2);
    vars lr_L1 = series(0, 2);
    vars lr_L2 = series(0, 2);
    vars lr_L3 = series(0, 2);
    vars lr_R  = series(0, 2);
    var lr_k = 1;
    lr_k = lr_k - gamma;
    lr_L0[0] = lr_k*Close[0] + gamma*lr_L0[1];
    lr_L1[0] = lr_L0[1] - gamma*lr_L0[0] + gamma*lr_L1[1];
    lr_L2[0] = lr_L1[1] - gamma*lr_L1[0] + gamma*lr_L2[1];
    lr_L3[0] = lr_L2[1] - gamma*lr_L2[0] + gamma*lr_L3[1];
    var lr_CU = 0;
    var lr_CD = 0;
    if(lr_L0[0] >= lr_L1[0]) lr_CU = lr_L0[0] - lr_L1[0];
    else                     lr_CD = lr_L1[0] - lr_L0[0];
    if(lr_L1[0] >= lr_L2[0]) lr_CU = lr_CU + lr_L1[0] - lr_L2[0];
    else                     lr_CD = lr_CD + lr_L2[0] - lr_L1[0];
    if(lr_L2[0] >= lr_L3[0]) lr_CU = lr_CU + lr_L2[0] - lr_L3[0];
    else                     lr_CD = lr_CD + lr_L3[0] - lr_L2[0];
    lr_R[0] = lr_R[1];
    if(lr_CU + lr_CD != 0) lr_R[0] = lr_CU/(lr_CU + lr_CD);
    *pL0 = lr_L0[0];
    *pL3 = lr_L3[0];
    *pDen = lr_CU + lr_CD;
    return lr_R[0];
}

var LaguerreRSI(vars Close, var gamma)
{
    var lr_w0;
    var lr_w3;
    var lr_wd;
    return LaguerreRSICore(Close, gamma, &lr_w0, &lr_w3, &lr_wd);
}
```
L-1 zero start (each `series(0, 2)` starts its history at 0 on the instance's first call, gotchas 9d.6 — (c) to be confirmed by
the start-up checks); L-2 hold in a per-instance series, initial 0; L-3 no statics; all five `series()` calls unconditional and
first (3.1); every expression starts with a variable (9d.8). (b) The term order in L1..L3 differs from the book
(`L(k-1)[1] - g*L(k-1) + g*Lk[1]` vs `-g*L(k-1) + L(k-1)[1] + g*Lk[1]`): same value up to rounding; the model uses the book order,
IMP must pass at 1e-9. Superseded file (stage 2): current `LaguerreRSI.c` body verbatim as `LaguerreRSI_Superseded.c`, function
`LaguerreRSI_Superseded`, locals `lr_` -> `lro_` (flat namespace, 1.3). Pre-run (ii): record the current `LaguerreRSI.c` blob hash.
(c) If any line above cannot compile in Light-C, STOP and report.

## Spec draft: `analysis/harness/specs/LRSI_ArticleFidelity.toml`

Same structure as `MESA_ArticleFidelity.toml` (incl. [corrected_code], [floor], [detect], [imp], [observations], pass condition,
pre-run i–iv). id_prefix `LRS`. **Every number stored at full precision.**

Real variants (`LaguerreRSICore`, model `lrsi_article`): `G05` (0.5, the C2 default and the book's), `G07` (0.7), `G08` (0.8).
INFO variant: `NCH` hold initial 0.5 (L-2). (b) Invisible on every input here (the hold before a first defined value never fires:
x[0] != 0): reported, never PASS/FAIL; state this.

Negative controls (vs the G05 model; inline bodies, every expression starts with a variable, locals uniquely prefixed, 1/1000 from
a variable, 9d.8). Effects (b), T = 5, 10, 20, 40, 100:
- `NCG` gamma + 1/1000 in L0 only (third-digit copy error, D2 rule 4): trace 8.587296356932228e-05, 0.0006342174551938473,
  0.0007133515100741228, 0.0008146242189909225, 0.0008469690514941175 (max 28x); start-up 0.002158791270517657,
  0.0013738308618160833, 0.0048423698983621755, 0.0021575680392890706, 0.0008838074092193393; L0 / L3 gain max
  0.0011355290725825196 (38x), phase max 0.0013338316280936402 (44x); ramp lag L0 1.004008016031932 (4x tol).
- `NC25` L1..L3 in the TASC 2025 form (`-g*L(k-1)[1] + L(k-1)[1] + g*Lk[1]`, review L-6): trace 0.38513302852097764,
  0.3487701068339998, 0.30284144990303796, 0.2945505035341127, 0.2937768393508384; L0 unchanged; L3 gain max 0.44485552574684356,
  phase max 1.5370047327232406; ramp lag L3 7.000000000000228 (vs 10).
- `NCP` price seed alone (the old start-up, per instance, no statics): trace 0 (after W identical); start-up
  0.5979633949986088, 0.9392821926106899, 0.9233174011464185, 0.6160813372907071, 0.2142857142857142. Linear stages: start-up only.
- `NCS` the real superseded file, called as TWO instances per input (D6 rule 5): compute its effects with the shared-state replay
  **in the generator's actual call order** and report, per (instance, input), which rows differ from the G05 model and by how much.
  (c) Planning-chat prediction: only the FIRST superseded call of the run seeds (file static `lr_init`); if that call is on `flat`,
  the seed lands on an INFO input, every other call starts from zero history (= the source), and `lr_prevRSI` matters only on
  CU + CD = 0 rows (flat). Then NCS would differ from the model **only on flat rows** and no PASS/FAIL kind would catch it. If
  that is what you find, STOP and report — do not change the layout or add a check. The planning chat has options to put to the user.

[detect.required] = every kind >= 10x its tolerance; compare with the (b) values above. If any control (other than the NCS case
above) has NO kind >= 10x, STOP and report.
IMP must_pass: every variant (incl. NCH, and NCS with the `lrsi_superseded` model) on rows >= W; must_fail: G05 replayed with the
NCG model; NCS replayed with the G05 `lrsi_article` model only if NCS differs on rows >= W (else state why it cannot fire). Record
fire-test values at full precision.

Pass condition: real-check count = 3 variants x [l0: flat + 5 gains + alt gain + 5 phases + alt phase + ramp lag = 14;
l3: the same 14; out: 5 trace + 2 invariance + 1 bound + 2 ramp_exact + 5 startup = 15] = **129** expected — state the exact
number and explain any difference.

## Done when

- `bash analysis/harness/run_tests.sh` all PASS (report TOTAL before/after; 555 at `c5ad3b5`) incl. new tests for the real-valued
  parameter, four-column calls, linear checks on two outputs, `rampdn`, `ramp_exact` (fires on a 0.9999999 row), `startup` on the
  normalised output (fires on a seeded variant), gate on the model's CU + CD (with a gated row), `lrsi_article` vs findings 1–10,
  `lrsi_superseded` with shared statics, byte-identical regeneration of the 8 existing specs.
- `python analysis/harness/generator.py analysis/harness/specs/LRSI_ArticleFidelity.toml --lint-only` clean (except the stage-2
  files, reported).
- Report: real-check count, raw column count, the L0 / L3 tables, findings 1–10 reproduced (diff vs the (b) values above), floors,
  every control's effects and [detect.required], the NCS per-(instance, input) result, NCH INFO values, IMP fire-test values,
  anything that did not fit this prompt. Then STOP (no commit, no `.c` edit, no generated script run).

---

## Amendment 1 — 2026-11-19 (NCS call order; user decision A + C)

Stage 1 stopped at the NCS STOP condition (report 2026-11-19, Claude Code; planning-chat prediction confirmed). (b) With the
generator's variant-major order (flat, s5, s10, s20, s40, s100, alt, ramp, rampdn), the run's only seed lands on NCS instance 1's
`flat` call; every other call starts from zero history = the source, bit-identical to the G05 model; the shared hold acts only on
CU + CD = 0 rows (flat). No PASS/FAIL check could see the control. (c) Generated scripts return at INITRUN before any indicator
call, so the file's own INITRUN resets never run: a second [Test] press without restarting Zorro seeds nothing (as RFX A2.4).

**Decision (user, 2026-11-19): A + C.** Everything above stands except:

**A. Per-variant input subset.**
- Tooling: optional `skip_inputs = [...]` per variant (default: none; existing specs unchanged and byte-identical). The generator
  emits no call for a skipped input; the variant's remaining calls stay unconditional and in the standard order (3.1). The
  shared-state replay and IMP follow the ACTUAL call order of the generated script. Skipped (variant, input) pairs produce no raw
  column and no check; the results header lists them.
- NCS: both instances gamma 0.5, `skip_inputs = ["flat"]`. Its first call is then on `s5`. Expected (b): NCS instance 1, `s5`
  start-up differs from the G05 model with max 0.5979633949986088 (= NCP, T = 5; last differing row 60); every other
  (instance, input) bit-identical. [detect.required] for NCS: `startup` on `s5` (>= 10x tolerance 1e-6). Compute the effect
  with the checker's own functions in the actual call order and compare with this value; if it differs > 1% relative, STOP.
- IMP for NCS: must_pass with `lrsi_superseded` (actual call order). must_fail vs the G05 `lrsi_article` model cannot fire on
  rows >= W (bit-identical there): state this in the spec; no must_fail row for NCS.

**C. Structural check for L-3.**
- New pre-run lint item: the corrected `indicators/ehlers/LaguerreRSI.c` contains no `static` token (comments excluded). It must
  be seen to fire: a self-test runs it on a copy of the superseded body (2 hits: `lr_init`, `lr_prevRSI`). Recorded in the spec
  pre-run list and written to the results header (same place as the other pre-run records).
- Spec [observations] O_HOLD (b): the shared hold acts only on CU + CD = 0 rows, which occur only on flat (G05 from row 69); flat
  `out` is INFO (D6 rule 2), so no control can show it on these inputs. Covered by C, not by a control.

**Rerun rule (record in the spec run notes):** restart Zorro before any rerun of the generated script.

Unchanged: real variants, controls NCG / NC25 / NCP, NCH INFO, tolerances, W, gate, real-check count **129** (controls are not
counted). The scratch replay files need not be kept: `lrsi_superseded` + its tests replace them.
