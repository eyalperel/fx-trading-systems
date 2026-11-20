# MAF stage 1 — D7 tooling + reference models + two spec drafts (MAMA / FAMA, FRAMA)

Planning chat, 2026-11-20. Decisions accepted by the user: review `docs/harness/MAMA_FRAMA_SOURCE_REVIEW.md` (`b7bdd69`, MA-1..MA-9,
FR-1..FR-8) **plus its appended section "Correction and spec-level decisions"** (C-1..C-3, S1..S5); HARNESS_DESIGN **D7** (adaptive-smoother
family, first two indicators). Build mode, speed over polish; the validation gate is unchanged (CLAUDE.md). Labels: (a) source states,
(b) measured / computed, (c) inference. Run on **Opus, effort High**.

**Git:** branch `harness-mama-frama` (at `b7bdd69`, created by the user; the review appendix, the updated review model and
`MAMA_FRAMA_STAGE1_NUMBERS.py` are uncommitted in the working tree, commit them with the tooling). Do NOT commit. At the end print the
`git add` / `git commit` commands you suggest (one commit for tooling + tests + review appendix + this brief, one for the two spec drafts), and
STOP. No `.c` edit, no Zorro run.

Read first: the review (all of it, incl. the appendix), `docs/harness/MAMA_FRAMA_REVIEW_MODEL.py`, `docs/harness/MAMA_FRAMA_STAGE1_NUMBERS.py`
(the source of every number below; run it and diff), HARNESS_DESIGN D6, the four "D6 applied to ..." notes and D7,
`analysis/harness/specs/FSH_ArticleFidelity.toml` (structure to follow), gotchas 1.3, 3.1, 9d.1, 9d.2, 9d.6, 9d.8, 9d.9.

**Lessons applied (from the Fisher session):** (1) the planning chat's post-run back-check replays IMP and must_fail over ALL exported inputs
(base, band, sc, of), so the spec must list every input on which IMP runs; (2) callers use their own local prefix (gotchas 1.3): the
corrected files, the superseded copies, the wrappers and the generated script must not share any local name.

## Sources (a) — verbatim in the review §1

- MAMA / FAMA: Ehlers, TASC V.19:9 (2001), Sidebar Fig. 1, PDF p. 5. Start-up: every var 0; body only if CurrentBar > 5; a var not assigned on
  a bar keeps its value (EasyLanguage). `ArcTangent` returns degrees.
- FRAMA: Ehlers, TASC V.23:10 (2005), sidebar, PDF p. 3. N = full window (even). Dimen only if N1 > 0 and N2 > 0 and N3 > 0, else held
  (initial 0). `Filt = Price` while CurrentBar < N + 1.
- D1: every literal taken at its decimal value (rule 2; none equals a named constant to every digit), built from integers at run time. No NCL.
  **S1:** MAMA's degree conversion uses exact pi built at run time (`4*atan(1)`), a D3 exception under D3's own rule (review appendix).

## Planning-chat numbers to reproduce (b)

Run `python docs/harness/MAMA_FRAMA_STAGE1_NUMBERS.py` and reproduce with `reference.py`. Inputs: level 1.1, amplitude 0.01, slope 1e-4,
N = 3000, flat, ramp, sines T = 5, 10, 20, 40, 100. FRAMA band bars: H = x + h, L = x - h, h = 0.002 (suffix B). Equivariance copies: `sc` =
10 x - 9.9 (amplitude 0.1; band H / L mapped the same way), `of` = x + 1.1 (level 2.2). History before the first bar padded with the first
value (gotchas 9d.6), in the model and in Zorro. **Your reference models mirror the corrected code's operation order** (e.g. `deg = 180/pi`
then `atan(.)*deg`); the planning-chat script uses `atan(.)*180/pi`. So report a difference as a finding only if it exceeds 10x that column's
rule-3 conditioning value (table 1) or 1e-12, whichever is larger; effects within 1% relative.

1. **Conditioning (D7 rule 3), all rows, 5 perturbations x(1 + 2^-52 u), u in {-1, 0, 1}, seed 20261120.** Bound = tolerance / 10 (S2):
   MAMA 1e-10 (mama, fama, alpha, period), 1e-9 (phase); FRAMA 1e-11 (out, dim, alpha).
   - MAMA, both variants: **checked s10, s20, s40, s100**; INFO flat, ramp, s5. Largest checked values: MA05 s100 phase 1.453e-10, alpha
     2.318e-11, fama 2.351e-13; MA03 s100 phase 1.538e-10, alpha 1.624e-11, fama 6.678e-13. INFO examples: MA05 ramp alpha 4.5e-01, fama
     2.788e-04; flat fama 3.244e-02; s5 fama 1.686e-02.
   - FRAMA, both variants: out checked on all 13 inputs (point flat, ramp, s5..s100; band rampB, s5B..s100B), max 5.773e-15; dim and alpha
     checked on 12 (all but point flat: dim 2.0, alpha 0.9899 = INFO), max dim 5.178e-13 (FR16 s100), alpha 1.285e-12 (FR16 s100).
   - The tooling recomputes this classification (same seed and draw order) and the spec lists it; a mismatch is a pre-run STOP.
2. **MAMA facts** (corrected model, MA05 / MA03 identical where alpha is clamped): alpha in [SL, FL] on rows >= 6 (rows 1-5: alpha = 0, the
   var's initial value); Period <= 50 every row; Period rows >= 1000: s10 [10.046866000871653, 10.138692660663777], s20 [19.955554535888744,
   20.051537545020732], s40 [39.807136333604554, 40.18200281308779], s100 50.0 exactly. MA05 FAMA rows >= 1000: s20 [1.099446341089458,
   1.1005536589105402], s100 [1.0920658491664514, 1.1079341508335487].
3. **MAMA equivariance** (C-2): holds only after start-up; last row off > 1e-9 (> 1e-8 for phase) <= 516 on s20 / s40, both variants. Rows
   >= 1000 maxima: mama 1.6e-14, fama 1.6e-14, alpha 3.7e-13, period 6.2e-12, phase 5.3e-11. **W_eq = 1000.**
4. **IMP estimate** (model fed the %.15f-rounded x vs exact x), MA05: phase up to 1.124e-10, alpha 1.737e-11, fama 2.596e-13 (s100); FRAMA:
   alpha up to 1.933e-12 (FR16 s100), out <= 5.1e-15.
5. **FRAMA known answers.** Point ramp: alpha = 1, out = x exactly (0.0) on every row (FR16 / FR32), D = log2(4(N/2 - 1)/(N - 1)) =
   0.9004643264490856 / 0.9526942852216433. Band ramp: D = log2(4 r1 / r3), r1 = s(N/2 - 1) + 2h, r3 = s(N - 1) + 2h: FR16 D
   1.773229138152978, alpha 0.028528433125587088, **lag (1 - alpha)/alpha = 34.05274879969143** (model over the last 100 rows
   34.05274879967843; converged to 1e-9 from row 854); FR32 D 1.6316125940199773, alpha 0.054725914083758966, **lag 17.27287888639891**
   (row 450). Point flat: out = 1.1 exactly, Dimen held at 0 (never computed: N3 = 0).
6. **FRAMA bounds** (C-3): alpha in [exp(-4.6), 1] = [0.010051835744633586, 1]; observed min 0.010051835744633504 (band, Dimen
   2.0000000000000018): use the D6 relative allowance 1e-12 on both alpha and Dimen <= 2. out within the running [min x, max x] every row.
7. **FRAMA equivariance** s40B, from row 1: sc out 7.994e-15, dim 1.532e-14, alpha 2.787e-14; of out 1.776e-15, dim 5.773e-14, alpha 6.384e-14.

## Tolerances (pre-registered; check each against D2 rule 3)

- MAMA trace **1e-9** (mama, fama, alpha, period), **1e-8** (phase, degrees). FRAMA trace **1e-10** (out, dim, alpha). If a measured floor
  x 10 exceeds its tolerance, STOP and report.
- bound: D6 relative allowance 1e-12 (alpha both sides, Period <= 50, Dimen <= 2, FRAMA hull with absolute 1e-15).
- equivariance: MAMA 1e-9 (1e-8 phase), rows >= W_eq = 1000; FRAMA 1e-10, rows >= 1.
- ramp_exact (FRAMA point ramp out = x) 1e-12. ramp lag (FRAMA band ramp vs the item-5 value) 1e-6 bars (floor 1.3e-11). flat (FRAMA point
  out = 1.1) 1e-12. imp 1e-9 (MAMA phase 1e-8). x 1e-12.

## Tooling (extensions only)

- **Bars input family:** each input carries x plus High / Low series. Point: H = L = x. Band: H = x + h, L = x - h, h built from integers
  (2/1000). Band inputs are a separate input list (`rampB`, `s5B` ... `s100B`); equivariance copies map x, H and L together. The generator
  passes `series(x)`, `series(H)`, `series(L)` built per input, unconditionally, in fixed order (3.1). `series_len` >= 33 (FR32 + control NCN
  window 34: make it 34).
- **Multi-column calls:** `MAMACore` -> 5 columns (`mama` = return, `fama`, `period`, `alpha`, `phase`); `FRAMACore` -> 3 (`out`, `dim`,
  `alpha`). Local-scalar out-parameters (`62b4e97` pattern).
- **Trace from row 1** (W = 1) with the per-(input, column) checked / INFO classification of rule 3; INFO traces reported, never PASS/FAIL.
- **New kinds:** `equivariance` (affine: out_copy = k out + c on level columns, = out on adaptation columns; rows >= W_eq); `hull` (out within
  running [min x, max x]); `bound` generalised to per-column one- / two-sided limits with relative allowance and a first row (MAMA alpha from
  row 6). Reuse `ramp_exact`, ramp lag (DC gain 1 holds: an EMA), flat.
- **Conditioning classifier** (pre-run, deterministic, seed in the spec): perturbation ensemble on the MODEL; output written into the pre-run
  record and compared with the spec's list.
- **Real-valued parameters** FastLimit / SlowLimit built from integers (`real_params`, LRS): .5 = 1/2, .05 = 1/20, .3 = 3/10, .1 = 1/10.
- **Reference models** (restricted grammar, rationals as integer pairs, no eval):
  `mama_article(FL, SL, w1 = [962,10000], w2 = [5769,10000], ka = [75,1000], kb = [54,100], a2 = [2,10], a8 = [8,10], up = [15,10],
  dn = [67,100], fama_k = [1,2], pi = "exact" | "zorro", literals = "exact" | "float32")` (dn and the SmoothPeriod .67 are separate parameters);
  `frama_article(N, k = [46,10], lo = [1,100], literals = "exact" | "float32", startup = "source" | "old")` (`old` = the current file's start-up
  and guard: seed on the first call, EMA from the second, return without update when N3 <= 0, no N1 / N2 condition, `log(0)` = -inf);
  `mama_superseded(FL, SL)` and `frama_superseded(T)` = the old files incl. FILE STATICS (`barCount`; `frama_prev`, `frama_init`) shared by
  every call in the generator's ACTUAL call order (RFX / LRS / FSH shared-state replay), with float32 literals and Zorro `PI`.
- `[zorro].include`: `MAMA_Superseded.c`, `MAMA.c` / `FRAMA_Superseded.c`, `FRAMA.c` (stage 2; lint may report them missing: say so, do not
  create them). `[lint].no_static` on both corrected files (must fire on the superseded bodies: MAMA 1 hit `barCount`; FRAMA 2 hits).
- Existing specs (H1, SS2F, SS3F, HPF, RFF, USE, RFX, MST, LRSI, FSH) must regenerate BYTE-IDENTICAL scripts; checker outputs unchanged.

## Corrected code (pre-registered; `.c` written in stage 2, AFTER the specs are committed)

```c
var MAMACore(vars Price, var FastLimit, var SlowLimit,
             var* pFama, var* pPeriod, var* pAlpha, var* pPhase)
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
Notes: every `series()` call unconditional and first (3.1); zero start = the sources' var initial values; every constant built from integers
(MA-4, FR-6); every expression starts with a variable or a single integer literal times a variable (9d.8); MAMA's degree conversion is
`atan(.)*deg` with `deg = 180/pi` (your model mirrors it). (c) If any line cannot compile in Light-C (declarations inside the function body,
`&&`, unary minus on a variable, `int` division `N/2`), STOP and report. FRAMA's caller series must hold >= N values (header note, stage 2).
Prefixes `ma_`, `maw_`, `fr_`, `frw_`: grep the repo for collisions (1.3) and add them to gotchas 1.3 in stage 2.
**Callers (FR-2, MA):** grep for `MAMA(`, `FRAMA(`; list file:line in the report (expected: `Test_FRAMA_Laguerre_DSMA.c:87`,
`Test_FRAMA_vs_MAMA.c:38-39`, `Test_MAMA.c:32`, `Test_UltimateChannelBands.c:83`). Do not edit them (stage 2: FRAMA callers pass
`series((priceHigh() + priceLow())/2)`, `series(priceHigh())`, `series(priceLow())` and **N = 32** (FR-1); MAMA callers build .5 / .05 from integers).
**Superseded files (stage 2):** current bodies as `MAMA_Superseded.c` (`MAMA_Superseded(vars Price, var FastLimit, var SlowLimit, var* outFAMA)`,
every local / static prefixed `mao_`; NO behavioural edit) and `FRAMA_Superseded.c` (`FRAMA_Superseded(vars Price, vars High, vars Low, int T)`,
the ONLY behavioural edit is the input: `priceHigh()` / `priceLow()` -> `High[0]` / `Low[0]` series reads and `frama_price` -> `Price[0]`;
prefix `frama_` -> `fro_`). Pre-run (ii): record both current blob hashes.

## Spec drafts

Two specs, same structure as `FSH_ArticleFidelity.toml` (incl. [corrected_code], [floor], [detect], [imp], [observations], pass condition,
pre-run i-iv, the restart-Zorro rerun rule: the superseded statics are reset only by a recompile). **Every number stored at full precision.**
State in each spec what is checked by code review only (S4: MA-2; FRAMA's `log(0)` branch, unreachable on band bars).

### `analysis/harness/specs/MAMA_ArticleFidelity.toml` (id_prefix `MAM`)

Real variants (`MAMACore`, model `mama_article`): `MA05` (.5, .05, the slot), `MA03` (.3, .1). INFO variant: `NCB` (dn .67 -> .68): zero effect
on every checked input (S4), reported only.
Negative controls (vs MA05; inline bodies, variable-first, own prefixes). Effects (b), max over all rows, checked inputs s10 / s20 / s40 / s100:
- `NCH` every .0962 -> .0963: phase 1.261940e-01 / 3.312006e-02 / 1.753128e-02 / 1.753819e-02; period 2.281164e-03 / 4.196015e-04 /
  2.857445e-03 / 9.631416e-04; fama 0 / 2.268373e-05 / 3.229289e-05 / 6.721418e-06.
- `NCF` FAMA factor .5 -> .51: fama 8.369000e-03 / 8.473840e-03 / 8.499630e-03 / 8.464515e-03; other columns 0.
- `NC32` the current file's float32 literals, exact pi: period 5.943743e-06 (all four); phase 7.297708e-06 / 7.543313e-06 / 8.784561e-06 /
  5.679194e-06; alpha 0 / 5.859257e-09 / 6.192775e-08 / 5.140390e-07. This is what makes MA-4 a checked fix.
- `NCP` Zorro `PI` (float32 3.14159) in place of exact pi: phase 7.182130e-05 / 7.244585e-05 / 7.259361e-05 / 7.262519e-05; period
  2.042073e-05 / 2.313917e-05 / 3.805698e-05 / 4.327885e-05. This is what makes S1 a checked change.
- `NCS` the real superseded file, TWO instances per input, both (.5, .05) (D7 rule 7; columns mama, fama only). Compute with the shared-state
  replay in the generator's actual call order and report per (instance, input). (b) One instance alone vs the model: mama / fama up to
  1.109511e+00 (price seed vs zero start), alpha 4.5e-01, period 20; the shared `barCount` adds a start-up shift (review §3).
MA03 effects for NCH / NC32 / NCP are in `MAMA_FRAMA_STAGE1_NUMBERS.py` §3 (NCH: alpha 0 on s10 / s20 at MA03; detection is on phase).
Pass condition (real checks per variant): trace 5 columns x 4 checked inputs = 20; bound 2 (alpha in [SL, FL] rows >= 6; Period <= 50),
every input; equivariance on s40, copies sc and of: level columns mama, fama (4) + adaptation columns alpha, period, phase (6) = 10, rows >= 1000.
**32 per variant, 64 total** expected: state the exact number and explain any difference. INFO: traces on flat, ramp, s5; NCB.
IMP must_pass: MA05, MA03, NCB, NCH, NCF, NC32, NCP with their models, NCS with `mama_superseded`, on every checked AND INFO input of the
spec (sc, of included); report INFO-input IMP values separately (expected large where conditioning fails). must_fail: MA05 replayed with the
NCH model; NCS replayed with the MA05 model.

### `analysis/harness/specs/FRAMA_ArticleFidelity.toml` (id_prefix `FRA`)

Real variants (`FRAMACore`, model `frama_article`): `FR16` (N = 16, source default), `FR32` (N = 32, the slot configuration, FR-1).
Negative controls (vs FR16; inline bodies). Effects (b), max over all rows, point | band, T = 5 / 10 / 20 / 40 / 100 (ramp where non-zero):
- `NCE` 4.6 -> 4.61: alpha 3.955914e-04 / 6.492834e-04 / 6.711281e-04 / 7.934269e-04 / 7.988544e-04 | 7.972850e-04 / 7.972850e-04 /
  7.986411e-04 / 7.971924e-04 / 7.208465e-04; band ramp out 2.720886e-05, alpha 2.197395e-04 (and the band ramp lag).
- `NCN` window N + 2 (= 18): out 9.414967e-03 / 9.301115e-03 / 9.288646e-03 / 6.191439e-03 / 1.201051e-03 | 9.414967e-03 / 9.314053e-03 /
  6.379796e-03 / 2.554497e-03 / 5.032419e-04; dim up to 1.58 (point), 0.44 (band).
- `NC32` float32 4.6 / .01: alpha 3.783699e-09 / 6.204084e-09 / 6.412279e-09 / 7.575926e-09 / 7.626796e-09 | 7.612292e-09 / 7.612292e-09 /
  7.624908e-09 / 7.610535e-09 / 6.885912e-09 (37.8x .. 76x at 1e-10). The .01 floor never binds (D <= 2): the effect is 4.6 alone.
- `NCT` the old start-up and guard, per instance (`frama_article(startup = "old")`): out 1.492164e-02 / 1.438820e-02 / 1.007774e-02 /
  6.866947e-04 / 0 | 9.663821e-03 / 1.285909e-02 / 1.273796e-02 / 5.287610e-03 / 3.543947e-03; band ramp 1.257889e-03.
- `NCS` the real superseded file, TWO instances per input, both T = 8 (N = 16); shared `frama_prev` / `frama_init`. Replay in actual call order,
  report per (instance, input). (b) review §3: two instances (N16, N32) on one input, rows >= 200: up to 9.9e-3 (s40), 3.3e-2 (random walk);
  (c) with every call of the run chained through one state the effect should be large on every non-flat input. If NCS differs from the model
  only on flat or only at start-up, STOP and report.
Pass condition (real checks per variant): trace out 13 + dim 12 + alpha 12 = 37; bound 3 (alpha, Dimen, hull; every input); known answers 3
(point ramp ramp_exact, band ramp lag, point flat); equivariance on s40B, copies sc and of: out (2) + dim, alpha (4) = 6.
**49 per variant, 98 total** expected: state the exact number and explain any difference. INFO: dim and alpha traces on point flat.
IMP must_pass: FR16, FR32, NCE, NCN, NC32, NCT with their models, NCS with `frama_superseded`, on every input (point, band, sc, of); must_fail:
FR16 replayed with the NCE model; NCS replayed with the FR16 model.

[detect.required] in both specs = every kind >= 10x its tolerance; compare with the (b) values above. If any control has NO kind >= 10x, STOP.

## Done when

- `bash analysis/harness/run_tests.sh` all PASS (report TOTAL before / after; 740 at `2f3b596`) incl. new tests for: bars inputs (point / band,
  affine copies map H and L), five- and three-column calls, trace from row 1 with per-(input, column) INFO classification, the conditioning
  classifier (fixed seed, reproduces table 1), `equivariance` (fires on a 1e-8 affine error and respects W_eq), `hull` (fires on one row out
  by 1e-12), per-column bounds with first row, `mama_article` / `frama_article` vs items 1-7, `startup = "old"`, both superseded models with
  shared statics, the no-static lint on both superseded bodies (1 and 2 hits), byte-identical regeneration of the 10 existing specs.
- `python analysis/harness/generator.py <spec> --lint-only` clean for both specs (except the stage-2 files, reported).
- Report (write it as `docs/harness/MAF_STAGE1_REPORT.md`): real-check counts, raw column counts, items 1-7 reproduced (diff vs the values
  above), the conditioning table, floors and the tolerance window per quantity, every control's effects and [detect.required], the NCS
  per-(instance, input) results, NCB INFO values, IMP fire-test values at full precision (all inputs), the caller list, the prefix grep,
  anything that did not fit this prompt. Then STOP (no commit, no `.c` edit, no generated script run).
