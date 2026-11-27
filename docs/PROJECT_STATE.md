# Project State — fx-trading-systems

**As of:** 2026-11-27 (**C1S3 read 1: 0 survivors** (five C1S1 readings pooled over AUD/USD + EUR/JPY, bar +0.034): the D1-FX
C1-only line closes; **DIAG1 read 1: Strategy 2's slot-set loss at zero cost is not distinguishable from path noise**
(pooled -0.0105, z -0.87; NULL1's "x0" included rollover, NULL1 Amendment 2); next: Decision N4; before that: **FINDINGS1** (`docs/research/FINDINGS1_C1_Timing_D1FX.md`): no C1 timing edge found on the D1 FX dev pairs. **C1S2 read 1: MAF fails on AUD/USD and EUR/JPY = STOP** ("passes on EUR/USD only"); C1S1 read 1: 1 of 6 C1s (MAF) shortlisted on EUR/USD; NULL1 read 1: both PERF STOPs are ordinary random-timing draws; confirmation set untouched; next: Decision N3 (next research question); before that: 2026-11-25 **PERF2 read 1: Strategy 2 v0 on EUR/USD = STOP** (x2: mean -0.048 signal-R, t -1.18; project-wide strategy variants tested: 2); before that: **PERF1 read 1: Strategy 1 v0 on EUR/USD = STOP** (x2: mean -0.030 signal-R, t -0.87; 1 strategy variant tested); before that: Phase 1 step 4: Light-C NNFX template built; **S4 engine equivalence PASS** (60/60 + 4/4 controls) and **P5 costs PASS** (run 3) and **P6 sizing PASS**; merged `1e8c189`; **R1 EUR/USD real data PASS** (merged `d487fc7`); **Phase 1 step 5 PASS** (10 real trades + 1 refused signal, rules and prices checked); next: Strategy 2 variant 0 on EUR/USD)
**Replaces:** `FX_Roadmap_v2026.08.10.md` (v4.4), `Week14_Review_Plan.md`,
`Week5-14_Indicator_Plan.md`, all Week 14 handoffs, `ROADMAP_UPDATE_PROTOCOL.md`.
Those stay in git history as the record; this file is the current state.

Compiled from: project knowledge docs, the README, the Week 14 Session 1 handoffs
(parts 1–4), and summaries of 25 project chats (Nov 2025 – Sep 2026).
Items not re-verified against the repo this sitting are marked *(unverified)*.

---

## 1. What exists

### 1.1 Indicator library (Light-C, `indicators/ehlers/`)

~32 files. "Validated" was applied with different methods in different weeks, so
it does **not** mean the same thing across the library (Week 13/14 finding).

| Group | Indicators | Week 14 review status |
|---|---|---|
| Smoothers | SuperSmoother 2-pole | **Implementation verified** (H1 run 2 PASS, f59f6e4) **and source fidelity verified** (SS2F run 1 PASS, 763601e, 2026-11-12): Zorro output matches Ehlers' TASC V.42:04 formula (√2 and π exact per D1) within gain 5.7e-7 / lag 5.4e-6 bars, which is the Zorro `PI` gap (D3); tolerances 3e-5 / 1e-3; 4 negative controls detected; 8 variants. Not tested: start-up seeding (article: output = Price for the first 3 bars; excluded by warmup) |
| Smoothers | SuperSmoother 3-pole | **Corrected and verified 2026-11-16.** The previous file was a hybrid matching neither cited source (real pole a1 instead of a1², 2-pole input average); it had been listed as "Validated". Kept as `SuperSmoother3Pole_Hybrid_Superseded.c`. Corrected to *Cybernetic Analysis* (2004) Fig. 13.11 with √3 (D1 Amendment 1: the printed 1.738 is a typo, the book's Table 13.4 uses 1.732). SS3F run 1 PASS (`09c05ad`): 28/28, 6 controls detected, IMP replay ≤ 3.4e-14, Zorro vs book = `PI` gap (gain 9.0e-7, lag 7.7e-6); 10 variants. Passband overshoot to gain 1.0046 (P = 10) |
| Smoothers | UltimateSmootherE | **Corrected and verified 2026-11-18.** Source: Ehlers, "The Ultimate Smoother", TASC V.42:04 (2024): US = input − HP, with the V.42:04 $HighPass (a third HP, not HP-A of `HighPassFilter.c`). Two deviations corrected (`ad8eae5`): D-1 folded literal `1.414 * PI` (gotchas 9d.8) → `us_k*PI`, `us_k = sqrt(2.0)` (D1 rule 1); D-2 global `Bar < 4` (comment said 4 bars; source seeds 3) → per-instance counter `us_n` = EasyLanguage CurrentBar (gotchas 9d.9). Spec `USE_ArticleFidelity.toml` (`ca4454b` + Amendments 1–2). **Run 1 PASS** (`41c8d76`): 64/64 (flat, 5 gains, alt gain, 5 phases, ramp lag, 3 start-ups) × P = 10/14/20/30; 6 controls (incl. NCS = 4-bar seed, detected by start-up only, 834×; NCX = x − HP-A); IMP ≤ 8.0e-15; Zorro vs article = `PI` gap (gain 6.5e-7, phase 7.6e-7 rad). (b) DC gain 1, Nyquist gain 0, ramp lag 0; but passband gain up to ~1.27 (T ≈ 1.3P) and phase at T = P ≈ −0.62 rad: the article's "zero lag" holds at DC only |
| Superseded | `UltimateSmoother_W5_Superseded.c` — does not implement its cited article | Reviewed, retired |
| High-pass family | HighPassFilter | **Corrected and verified 2026-11-17.** Source: HP-A, TASC V.32:1 (2014), same lines in V.33:09 / V.36:03 (Ehlers published three different HPs; HARNESS_DESIGN D4 note). Two deviations corrected (`d22ef57`): `0.707` → √2/2 (D1 rule 1) and price-level seed → zero seed (GAP-1.26). Spec `HP_ArticleFidelity.toml` (`2069d86` + Amendments 1–2). **Run 1 FAIL** (`a361e4b`, one control-model row: Zorro literal fold, gotchas 9d.8) → **run 2 PASS** (`512781c`): 56/56 (flat, gain, **phase**, ramp residual, start-up), 8 controls, IMP ≤ 6.7e-15 on the real variants; Zorro vs article = `PI` gap (gain 4.0e-7, phase 8.1e-7 rad). Leads price: 1.81 bars at T = 20, P = 48 (INFO) |
| High-pass family | RoofingFilter | **Verified 2026-11-17.** Source: TASC V.32:1 Roofing sidebar (HP-A(48) → SuperSmoother(10) on `(HP + HP[1])/2`, both histories start at 0). Code already matched; header corrected (GAP-1.31) and locals prefixed (`b249142`). Spec `RFF_ArticleFidelity.toml` (`b6b5c5d` + Amendments 1–2). **Run 1 PASS** (`d1395d3`): 64/64 (flat, 5 gains, Nyquist gain via a new alternating input, 5 phases, ramp residual, 3 start-ups) × (48,10), (30,10), (125,10), (48,20); 7 controls; IMP ≤ 3.5e-12; Zorro vs article = `PI` gap (gain 5.6e-7, phase 1.6e-6 rad). Start-up equals the source's zero start (HP's first output is 0). Gain at T = 20: 0.8900165 (§5 corrected) |
| High-pass family | Decycler | Not reviewed. (c) Probably not the same filter as UltimateSmootherE: same construction (price − HP) but the *Decyclers* article (V.33:09) uses HP-A, while UltimateSmootherE uses the V.42:04 HP; unchecked until Decycler.c is read |
| Baselines | MAMA / FAMA | **Corrected and verified 2026-11-21.** Source: Ehlers, "MESA Adaptive Moving Averages", TASC V.19:9 (2001), pp. 30-35, sidebar Fig. 1 "TradeStation code for MAMA and FAMA" (the article cites *Rocket Science for Traders*, not in `C:/books`; *Cybernetic Analysis* does not contain it). Review `docs/harness/MAMA_FRAMA_SOURCE_REVIEW.md` (`b7bdd69`, appendix C-1..C-3 / S1..S5 `7713f5b`): MA-1 start-up price seeds and a 5-call pass-through (source: every var starts at 0, computed from CurrentBar > 5) -> zero start; MA-2 Period / Phase held on a zero denominator (was 20 / 0); MA-3 `static int barCount` shared by every call -> per-instance counter; MA-4 float32 literals -> built from integers; MA-5 `PI` fallback never applies (record); MA-6 SmoothPeriod unused as the source (record); MA-7 `MAMACore(Price, FastLimit, SlowLimit, &fama, &period, &alpha, &phase)` exports, `MAMA()` wrapper; MA-8 header (unsourced claims removed); MA-9 phase-wrap / Re-sign discontinuities (conditioning classification). **S1: exact pi** built at run time (`4 * atan(1)`), the one D3 exception, because the `PI` gap on the checked sines (Phase 7.26e-5 degrees) is not a negligible floor here. Tooling and specs `7713f5b` (D7: bars inputs, equivariance, hull, conditioning classifier); corrected `MAMA.c` + `MAMA_Superseded.c` (control NCS / NCS2, explicit series lengths) + callers + Amendment 1 `d0c9a23`; prediction `8c1e648`. Spec `MAMA_ArticleFidelity.toml` + Amendment 2. **Run 1 PASS** (`MAMA_ArticleFidelity_20261121.csv`): 66/66 real checks (MA05 = (.5, .05) the slot, MA03 = (.3, .1)), 7/7 controls detected (71 FAIL rows: NCB 1, NCH 18, NCF 4, NC32 15, NCP 17, NCS 8, NCS2 8), IMP 11/11 (<= 1.124e-10) + must_fail, floor 8/8; 9 variants. Zorro vs the source model <= 8.2e-14 start-up included: no `PI` gap (S1 confirmed in a run). Read twice, agreed with the prediction (ulp-level differences only, Amendment 2 A2.2). (b) From a zero start MAMA / FAMA are unusable for ~500 bars; alpha is bimodal (FastLimit or SlowLimit) on short cycles; Period tracks T = 10-40 within ~0.5%; the output is ill-conditioned on flat, ramp and T < 6 (s5: 1.05e-3 per input ulp, a phase wrap flips 180 degrees), so those inputs are INFO only |
| Baselines | FRAMA | **Corrected and verified 2026-11-21.** Source: Ehlers, "Fractal Adaptive Moving Averages", TASC V.23:10 (2005), pp. 81-82, "FRAMA EasyLanguage code" sidebar. Review `docs/harness/MAMA_FRAMA_SOURCE_REVIEW.md` (`b7bdd69`): FR-1 parameter was half window T, source `N` is the full window (default 16); callers now pass N = 32 (the configuration the slot was chosen on); FR-2 inputs fixed inside the function -> `FRAMA(vars Price, vars High, vars Low, int N)`; FR-3 `static frama_prev` / `frama_init` shared by every call (up to 3.3e-2, permanent) -> per-instance series; FR-4 start-up: seed on first call, EMA from the second -> the source's `Filt = Price` while CurrentBar < N + 1; FR-5 guard on N3 only -> Dimen held when any of N1, N2, N3 is 0; FR-6 float32 literals 4.6 / .01 -> integers; FR-7 `FRAMACore(Price, High, Low, N, &dim, &alpha)` exports, `FRAMA()` wrapper; FR-8 header. Tooling / specs `7713f5b`; corrected `FRAMA.c` + `FRAMA_Superseded.c` (control NCS / NCS2) + callers + Amendment 1 `d0c9a23`; prediction `8c1e648`. Spec `FRAMA_ArticleFidelity.toml` + Amendment 2. **Run 1 PASS** (`FRAMA_ArticleFidelity_20261121.csv`): 98/98 real checks (FR16 = source default, FR32 = slot), 6/6 controls detected (129 FAIL rows: NCE 24, NCN 35, NC32 17, NCT 23, NCS 15, NCS2 15; NC32 the thinnest required margin, 76.3 x), IMP 10/10 (<= 1.934e-12) + must_fail, floor 10/10; 8 variants. Zorro vs the source model <= 2.2e-15; both known answers exact (point ramp out = x; band-ramp lag (1 - alpha) / alpha = 34.05274880 / 17.27287889). Read twice, agreed with the prediction (ulp-level differences on FR32 only, Amendment 2 A2.2). (b) The .01 alpha floor never binds (D <= 2, alpha >= exp(-4.6) = 0.0100518); D < 1 is reachable with close-only (point) bars; start-up memory up to ~2750 bars; the old shared statics gave wrong output by up to 3.3e-2; the library's old window was 32 = the source's N = 32 |
| Baselines | Laguerre Filter, DSMA | Not reviewed; Week 9 (Laguerre / DSMA) not reproducible from repo |
| Oscillators | Reflex | **Corrected and verified 2026-11-18.** Source: Ehlers, "Reflex: A New Zero-Lag Indicator", TASC V.38:02 (2020). Review `docs/harness/REFLEX_SOURCE_REVIEW.md` (`05be788`): R-1 file-static MS shared by every call (silent wrong output with two instances or an asset loop) → per-instance series; R-2 int `Length/2` → real `.5*Length`, SuperSmoother computed in-file; R-3 float32 weights → built from integers; R-4 start-up undefined in the source (INFO); R-5 header. New `ReflexCore(Price, Length, &sum, &ms)` exports the linear stage; `Reflex()` wrapper unchanged for callers (`5840f20`). Old file kept as `Reflex_Superseded.c` (control NCS/NCT). Spec `RFX_ArticleFidelity.toml` (`960ae09` + Amendment 1). **Run 1 PASS** (`ad487b7`): 84/84 (Sum: flat, 5 gains, alt gain, 5 phases, ramp residual; Reflex: 5 trace, bound, 2 invariance) × L = 14/20/21/30; 8 controls (incl. the real superseded file, 76 FAIL rows); IMP ≤ 2.8e-12; Zorro vs article = `PI` gap (trace 1.57e-6). Read twice, agreed on every row. (b) **Not zero-lag at its own design period:** Sum has phase 0 at T = L but the SuperSmoother(L/2) adds −0.62 rad (≈ 2 bars at L = 20). (b) On flat/ramp input Reflex is rounding noise / rounding noise (|r| up to 2.86 in the article model): never read it there. \|Reflex\| ≤ 5 exactly |
| Oscillators | MESA Stochastic | **Corrected and verified 2026-11-19.** Source: TASC V.32:1 (2014) sidebar. Review `docs/harness/MESASTOCHASTIC_SOURCE_REVIEW.md` (`3f0de96`): M-1 window `StochPeriod + 1` → `StochPeriod`; M-2 scale 0–100 → 0–1 (exports before `0332395` are ×100); M-6 fallback 50 → 0.5; M-9 `MESAStochasticCore` exports Roof and raw Stoc; M-8 header; M-4 HP seeding fixed upstream (GAP-1.26); M-5 final seed kept (start-up INFO). Old file kept as `MESAStochastic_Superseded.c` (control NCS). Spec `MESA_ArticleFidelity.toml` (`0fd34ee` + Amendment 1 `4843ee2` + Amendment 2). **Run 1 PASS** (`17a8604`): 84/84 real checks, 5/5 controls detected (29 FAIL rows), IMP ≤ 8.9e-16, floor 20/20; Zorro vs article = `PI` gap (trace 3.9e-6). Read twice, agreed with the pre-run prediction (`57b1abf`). (b) A window-length error (21 vs 20 bars) is invisible on sines with T ≤ L (≤ 7.6e-14) and shows only at T > L (6.2e-2 / 8.1e-2 at T = 40 / 100). (b) The final output is not bounded to [0, 1] (−0.0295 to 1.0295 at T = 100); only the raw Stoc is exactly bounded, so the source's .2 / .8 thresholds act on a signal that can exceed [0, 1] |
| Oscillators | Laguerre RSI | **Corrected and verified 2026-11-19.** Source: Ehlers, *Cybernetic Analysis for Stocks and Futures* (Wiley 2004), ch. 14, Fig. 14.8, p. 221 (Fig. 14.9 EFS agrees). Review `docs/harness/LAGUERRERSI_SOURCE_REVIEW.md` (`6382607`, on main): L-1 zero start as the source (was: price seed, first bar skipped, 0.5 returned); L-2 per-instance hold when CU + CD = 0, initial 0 (was a static starting at 0.5); L-3 no statics (the old `lr_init` / `lr_prevRSI` were shared by every call); L-4 gamma 0.7 / 0.8 are not float32-exact (build from integers); L-5 `LaguerreRSICore(Close, gamma, &l0, &l3, &den)` exports the stages, `LaguerreRSI()` wrapper unchanged for callers; L-6 header; L-7 record only (input Close matches; `Laguerre.c` findings logged for its own review, §4). Old file kept as `LaguerreRSI_Superseded.c` (control NCS / NCT). Spec `LRSI_ArticleFidelity.toml` (`824a3cc` + Amendment 1 `b85cfd9` + Amendment 2); tooling `c2fcd44`; corrected .c + test `a8955d1`. **Run 1 PASS** (`15ae118`): 129/129 real checks (3 gammas x 43), 4/4 controls detected (60 FAIL rows: NCG 32, NC25 22, NCP 5, NCS 1), IMP 9/9 (<= 8.539e-13) + must_fail, floor 21/21; Zorro vs the source model about 5e-16 (no `PI` gap: no trig, no literal). Read twice, agreed with the pre-run prediction (`63d1c21`). (b) The output is exactly bounded to [0, 1] on every row; a rising ramp gives exactly 1 and a falling ramp exactly 0 (ramp_exact, diff 0). (b) Pinning at 0 or 1 grows with the cycle length and depends on gamma (spec O_PIN: G05 0 / 0 / 0.5 / 0.7 / 0.88 at T = 5 / 10 / 20 / 40 / 100): in a trend it says THAT price trends, not how strongly. (b) Outputs before `a8955d1` differ from the corrected file only in the first ~60 / 120 / 196 bars (gamma 0.5 / 0.7 / 0.8); after that they are identical |
| Oscillators | Fisher Transform | **Corrected and verified 2026-11-20.** Source: Ehlers, TASC V.20:11 (2002) Fig. 5 p. 41 (source A; the book's Fig. 1.7 is the INFO variant NCB: EMA 1/2, clamp .9999, log gain 1/4). Review `docs/harness/FISHER_SOURCE_REVIEW.md` (`bdc83da`): F-1 file statics `ft_Value1` / `ft_Fish` and global `ft_Trigger` shared by every call (now per-instance `series`, trigger as an out-parameter); F-2 input fixed inside the function (now `Price` is a parameter); F-3 float32 literals .33 / .67 / .99 / .999 (built from integers); F-4 zero-range guard is ours, kept and labelled; F-5 start-up not defined by the source (INFO only); F-6 EFS window includes the bar's real High / Low (record only); F-7 exports `FisherCore(Price, Len, &raw, &v1, &rng, &trig)`, `FisherTransform(Price, Len)` a wrapper; F-8 header text corrected (date, unsourced +-2.5 claim, 'second EMA'); F-9 INITRUN resets of statics never run in generated scripts (gone with F-1). Tooling `c1c222e`; spec `FSH_ArticleFidelity.toml` (`258b24a` + Amendment 1 `cb93b65` + Amendment 2); corrected .c + `FisherTransform_Superseded.c` (controls NCS / NCT) + callers + test `800c797`; prediction `6e79c16`. **Run 1 PASS** (`a6debe0`, `FSH_ArticleFidelity_20261120.csv`; merged to main `a9e2ea4`): 56/56 real checks (FR10, FR20), 7/7 controls detected (66 FAIL rows: NCW 10, NCC 8, NCK 7, NCL 9, NC32 16, NCS 8, NCT 8), IMP 10/10 (<= 5.748e-12) + 2/2 must_fail, floor 10/10, 0 gated rows; 10 variants. Zorro vs the source model <= 8.9e-16 on every stage, start-up included (no `PI` gap). Read twice; agreed with the prediction except two differences, both one prediction-side omission (the back-check's IMP and must_fail loops covered the base inputs only), see Amendment 2. (b) Saturation: at T = 100 about 2/3 of bars are clamped and Fish reaches +-7.6; +-2.5 is routine at T >= 20 with Len 10, so the header's +-2.5 'statistically meaningful' claim is not a threshold. (b) A window-length error is invisible at T <= L (NCL detected at T = 20 / 40 / 100 only). (b) |Fish| <= ln(1999) is reached on a trend (exactly, in float64). (b) The shared statics corrupted a second instance by up to 2.7; the old float32 literals moved Fish by up to 1.29e-5 |
| Oscillators | CyberCycle, Elegant Oscillator, Inverse Fisher, COG, RSIH, Laguerre Osc | Not reviewed |
| Zero-lag / noise | InstantTrendline, DominantCycle, Recursive Median, RMO, Alpha-Beta, Correlation Cycle | Not reviewed |
| Failed | ELI | Documented FAIL |
| Volatility | ATR(14), MT4 definition (`indicators/nnfx/ATR.c`, `ATRMT4Core` / `ATRMT4`; not Ehlers, new folder) | **Verified 2026-11-22.** Source: MetaQuotes `ATR.mq4`, installed copy (sha256 `134da529…` / `c5c680c4…`, year-only difference), NNFX "ATR 14, default settings" (NNFX_Sources A §2.1, B §1.4; the MT4 identification is (c), review §2): TR = max(H, C[1]) - min(L, C[1]); ATR = simple Length-bar mean of TR as a running sum; 0 on the instance's rows 0..Length-1, row Length = mean TR[1..Length]. Zorro's `ATR()` is Wilder's form (manual) and is NOT this; `ATRS()` is. Review `docs/harness/ATR_SOURCE_REVIEW.md` (`e11270a`, AT-1..AT-7); tooling `2957476`; spec `ATR_MT4Fidelity.toml` (`bd62493`) + Amendment 1 (`5c5d700`, pre-run probe `PROBE_SeriesExprLen` PASS: `series(0, Length + 2)` compiles and allocates per call) + Amendments 2-3. **Run 1 PASS** (`5250bfb`): 90/90 real checks (AT14 the template, AT20), 7/7 controls detected (142 FAIL rows: NCW 21, NC0 21, NCWi 11, NCR 26, NCZ 15, NCS 24, NCS2 24), IMP 9/9 (<= 2.694e-15) + must_fail, floor 6/6; 9 variants. Zorro vs the source model <= 5.0e-16, start-up included; known answers exact. Read twice, AGREE on every item (prediction `348838b`; one prediction-side error disclosed and fixed before it was committed). **Real-data cross-check vs Zorro `ATRS(14)`, EUR/USD D1 2009-2023: PASS**, max relative 1.724e-14 over 3633 bars (pre-registered <= 1e-9; Amendment 3). (b) A 14- vs 15-bar window differs by 2-8% of the ATR level; Wilder vs this up to 2-4% on band sines (0 when TR is constant); the first Length bars are 0: a strategy's LookBack must cover Length + 1 bars (c) |
| Volatility | NATR, Ultimate Channel/Bands, VolatilityRegime | Not reviewed. **Deferred 2026-11-21, off the first template's critical path:** no channel / band stop in NNFX_Sources; NATR here is `100 * UltimateSmootherE(TR, 20) / Close` (`UltimateChannelBands.c` out-parameter), not ATR(14); possible volume / volatility slot candidates later (ATR review §1) |

### 1.2 Previous slot decisions — made on indicator-level evidence only

No strategy has ever been backtested. These were chosen by lag, signal count and
correlation, not by trading results.

**Decision 2026-10-20: all slots unlocked.** These are starting candidates — the first
indicators through the new test harness — not settled answers.

| Slot | Strategy 1 | Strategy 2 | Basis |
|---|---|---|---|
| Baseline | FAMA (MAMA's second output, (.5, .05)) — verified 2026-11-21 | FRAMA (N = 32; source default 16) — verified 2026-11-21 | Crossover counts, 10y EUR/USD D1 |
| C1 | Fisher (10) — verified 2026-11-20 (source A; saturates on long cycles) | MESA Stochastic (20,48,10) — verified 2026-11-19 (0–1 scale; source lines .2 / .8) | Indicator metrics |
| C2 | Reflex — flagged; verified 2026-11-18 (not zero-lag at T = L, §1.1) | Laguerre RSI (gamma 0.5) — verified 2026-11-19 (0–1 scale; source lines .2 / .8) | C-3b (backtest) never run |
| Stops / vol | ATR(14), MT4 definition (stop 1.5 x ATR) — verified 2026-11-22 (run 1 PASS + ATRS cross-check) | same | NNFX_Sources (A §4, B §2); decided 2026-11-21 (was Ultimate Channel, NATR from Week 13: deferred) |
| Exit | None: opposite C1 signal [V12] (template decision T1, variant 0) | same | Decided 2026-11-22 (`docs/template/NNFX_TEMPLATE_DECISIONS.md`) |

Both strategies' C1 indicators are now verified (Fisher 2026-11-20, MESA Stochastic 2026-11-19). Strategy 1's C2 (Reflex) was verified 2026-11-18, so Strategy 1's entry pair is fully verified too, as Strategy 2's (MESA Stochastic + Laguerre RSI). The baselines are verified too (FAMA and FRAMA, 2026-11-21), so **every slot indicator of both strategies except the exit (none defined) is now verified (ATR(14) for the stops verified 2026-11-22)**.

### 1.3 Infrastructure

- Repo: `eyalperel/fx-trading-systems` (public), local
  `C:/Users/eyalp/Documents/fx-trading-systems/`
- Zorro 3.11 (file version 3.1.1.2, (b) H1 session 2026-11-05), Git Bash, VS Code, Python/Jupyter (`python`, not `python3`)
- Data: EUR/USD D1, BTC/USD H4 (Zorro native); EUR/JPY D1, AUD/USD D1 (Darwinex MT4)
- `docs/ZORRO_LIGHTC_GOTCHAS.md` — platform reference, keep
- `analysis/null_tests/` — seeded surrogate harness (bootstrap, fGn, IAAFT, stoch-vol)
- Sources: 102 Ehlers TASC articles; *Cybernetic Analysis* (2004); 24 PDFs in project

### 1.4 Does not exist yet

- Any strategy that passed a performance read (Strategy 1 v0 on EUR/USD: STOP, PERF1 2026-11-24; Strategy 2 v0 on EUR/USD: STOP, PERF2 2026-11-25); a defined exit indicator
- Walk-forward, Monte Carlo, or strategy-level surrogate test
- Historical (time-varying) swap / spread model (asset-list costs only, T7)
- Confirmation-set pass condition

---

## 2. Validation discipline — carried forward unchanged

1. **Dev / confirmation split.** Dev: EUR/USD D1, BTC/USD H4, EUR/JPY D1, AUD/USD D1.
   Confirmation: other majors and crosses, XAU, XAG, WTI (minors excluded). Selection
   on dev only; confirmation set untouched until a system is frozen.
2. **Pre-registration.** Criteria written and committed before the test runs.
   Amendments dated and appended, never in place.
3. **Count every variant tested** and report it with the result. *(new, Oct 2026)*
4. **A guard never seen to fire is not a guard.** Test with deliberately broken input.
5. **Test the measuring tool on a known answer first** (EMA lag = 1.50 bars).
6. **Same parameters across assets.** Per-asset retuning = overfitting.
7. **Judge an indicator by what it does**, not by what its article claims.
8. **Combinations decide.** Indicator metrics screen; backtests select (C-3b).
9. **Failures stay documented.**

---

## 3. Research results (bounded)

- **Cycle premise null test.** 64 tests, EUR/USD D1 + BTC/USD H4, one
  parameterisation, 10–48 bar band: no null rejected, min p = 0.070. Positive
  control: cycles >~4–5% of return variance would have been detected. Bounded
  result, not a general finding.
- **Slutsky–Yule.** ~20-bar zero-crossing period appears in EUR/USD, BTC and pure
  Brownian motion alike. A filter's output rhythm belongs to filter × input.
- **Volatility persists, direction doesn't.** H(returns) ≈ 0.50 on both assets;
  H(|returns|) = 0.658 (EUR/USD D1), 0.766 (BTC/USD H4).
- **Strategy 1 v0 on EUR/USD D1 (PERF1, 2026-11-24): STOP.** 2007-2026, 325 signals, mean -0.030 signal-R at spread x2
  (t -0.87): no evidence of an edge; roughly flat before costs (c). One feed, one asset, one variant.
- **Strategy 2 v0 on EUR/USD D1 (PERF2, 2026-11-25): STOP.** Same bars, 282 signals, mean -0.048 signal-R at spread x2
  (t -1.18), total -13.5 R, -16.0 R without the best year (2008): no evidence of an edge; about -0.02 R per signal before
  costs (c). (c) Two different indicator sets in the same template both read roughly flat before costs on EUR/USD D1.
  Project-wide strategy variants tested: 2.
- **NULL1 (2026-11-25): random-timing null of the template.** C1 states circularly shifted (1,000 offsets), spread x2 +
  rollover: null medians -0.025 (Strategy 1 slots) / -0.046 (Strategy 2 slots) signal-R; PERF1 at the 42.7th, PERF2 at the
  47.5th percentile: both STOPs are ordinary draws from random C1 timing. Detection limit of one read: about +0.013 to
  +0.032 R per signal. Strategy 2 slots lose about -0.028 R per signal without spread (not investigated). **Corrected 2026-11-26 (NULL1
  Amendment 2): NULL1's x0 rows include rollover**; true zero cost is measured by DIAG1.
- **C1S1 (2026-11-25): C1-only screen, 6 readings, EUR/USD.** Best-of-six null bar +0.074: 1 pass, MAF (MAMA vs FAMA; 205
  signals, mean +0.101, t +1.48, 98.6th percentile); FSH, MSS, RFX, ROF, LRS fail.
- **C1S2 (2026-11-26): MAF unchanged on AUD/USD and EUR/JPY: STOP.** Means -0.064 / -0.064 (25th / 34th percentile of own
  nulls), negative even at zero cost. Recorded "passes on EUR/USD only". (c) The EUR/USD pass is best read as a best-of-six
  selection effect. Summary of all five studies: `docs/research/FINDINGS1_C1_Timing_D1FX.md`.
- **C1S3 (2026-11-26/27): FSH, MSS, RFX, ROF, LRS C1-only, pooled AUD/USD + EUR/JPY: 0 survivors.** Pooled best-of-5 bar
  +0.034; pooled means -0.046 .. -0.003, every one inside its own null's 5-95% (Q1-Q5 met). Recorded "no verified-library C1
  reading (6) beats random timing on the three D1 FX dev pairs" (O-a): the D1-FX C1-only line closes.
- **DIAG1 (2026-11-27): Strategy 2 slot set, random C1, true zero cost, 5 arms x 3 pairs, calendar-year jackknife.** Pooled
  A0 -0.0105 (z -0.87), EUR/JPY positive; no component (baseline, bridge-too-far, C2) meets z <= -2; random C1 alone -0.0015
  (z -0.33). NULL1's EUR/USD -0.028 = about -0.008 rollover + -0.021 one-path noise. Not distinguishable from path noise (R1-R5 met).
- **Ehlers' 2015 "pink noise"** measurement is brown noise (f⁻²).

---

## 4. Known defects — open

| Ref | Defect | Impact |
|---|---|---|
| GAP-1.35 | `data/fx/` CSVs are pre-radians-fix output; one run diverges to NaN | Week 6 notebook figures describe a filter not in the library. Decycler and BTC files unchecked |
| GAP-1.33/34 | `Test_RoofingFilter.c` has no pass criterion; returns before filters run | Test cannot fail; transient in export rows 1–72. Likely pattern across all test scripts *(unverified)* |
| GAP-1.26 | HP seeding — first output starts far from steady state | **Fixed in HighPassFilter.c 2026-11-17** (`d22ef57`, zero seed as the source). RoofingFilter re-verified 2026-11-17 (RFF run 1 PASS). MESAStochastic re-verified 2026-11-19 (MST run 1 PASS). Not yet re-verified: Decycler, RMO |
| — | MESA Stochastic exports made before `0332395` (e.g. `Test_MESAStochastic.c`, `Test_C2_LaguerreRSI.c`, `Test_LagSine.c`, `Test_RecursiveMedian.c` outputs, any notebook reading them) are on 0–100 and used the 21-bar window. `Test_C2_LaguerreRSI.c` / `Test_LagSine.c` outputs also predate the LaguerreRSI fix (`a8955d1`: price seed, shared statics) | Not comparable with the verified indicators |
| — | `Laguerre.c` (baseline filter, Fig. 14.5): file statics `lag_L0..L3` / `lag_init` shared by every call (R-1 class), reads `priceHigh` / `priceLow` itself | Not reviewed |
| — | Week 9 validation not reproducible (no tracked file reads its CSVs) | FRAMA: superseded by the 2026-11-21 verification (§1.1). Laguerre, DSMA status unsupported |
| — | `CyberCycle.c` statics may lack `cc_` prefix | Unconfirmed after four sittings |
| — | Decycler vs UltimateSmootherE — possibly the same filter | (c) 2026-11-18: probably different HPs (V.33:09 HP-A vs V.42:04 HP); USE run 1 control NCX (= x − HP-A(20)) differs from UltimateSmootherE(20) by gain 0.22. Confirm when Decycler is reviewed |
| — | `SuperSmoother2Pole.c` "First bar" comments are misleading: `Init` is `is(INITRUN)`, not the first bar (b, `include/variables.h:182`; gotchas 9d.5) | Comment only; output unaffected (H1 run 2) |
| — | Generated scripts' EXITRUN `printf` + marker file never fire (gotchas 9d.4; no marker from any run, re-confirmed SS2F run 1) | Dead code presented as a check; run cards must not rely on it. Remove or replace with a check written before `quit()` |
| — | Harness ramp-lag check assumes DC gain 1: a DC-gain error reads as lag ((x − y)/s = (1 − G)·x/s + G·τ; NC-B 35 bars) | **Resolved 2026-11-16:** HARNESS_DESIGN D4 (`032d766`): sine phase + ramp residual; ramp lag only at DC gain 1; `m_flat` generalised |
| — | Literal products folded at compile time to an unpredictable float32 (gotchas 9d.8, probe `ba54022`) | UltimateSmootherE.c fixed 2026-11-18 (`ad8eae5`). Remaining in DominantCycle.c:24–25/46–47, InstantTrendline.c:63; each spec replaces them |
| — | `L_FLOAT32` exemption is not written to the results header (lint output only) | Run records should carry every pre-registered exception; small tooling task |
| — | `.gitignore` line 13 `Results/` (meant for Zorro's folder) also matches every lowercase `results/` folder, because git runs with `core.ignorecase = true` (b, found 2026-11-24): template checker outputs (S4, P5, P6, R1a-d) were never committed; harness results were force-added | Records cited by the criteria docs existed only on disk. Force-added 2026-11-24 (PERF1 report + template results). Fix the pattern later (separate commit) |
| — | Intermittent test errors (`test_cli` MemoryError in Claude Code's shell, ×2; once 4/144 ERRORs in Git Bash, cause not captured) | CLAUDE.md §8 now requires tracebacks + rerun; watch |
| — | `docs/indicators/SuperSmoother_Notes.md`: SS3 sections dated before 2026-11-16 describe the superseded hybrid (Key Finding 2, coefficients, SS3 table rows, SS3 Period column) | Flagged by a notice in the file; not re-measured for the corrected SS3 |
| — | The `PI` macro is 3.14159 in Zorro 3.11 (b, `Include/trading.h:25`); used library-wide | Tiny: ~1e-6 bars of lag, ~1e-8 in filter output (gotchas 9d.2). **Decided 2026-11-06 (HARNESS_DESIGN D3): keep `PI`**; each spec records the gap in its tolerance floor |

**Inference:** given that every test script reviewed so far could not fail, the
practical status of the unreviewed library is "implemented, not verified". The
Phase 1 test harness should establish verification automatically rather than
continuing the manual review.

---

## 5. Carried forward from retired docs

Kept here because the source docs leave project knowledge (they remain in the repo).

**Known answers for the indicator harness** (computed from coefficients; matched by
simulation):

| Filter | Input | Expected | Source |
|---|---|---|---|
| SuperSmoother2Pole(20) | Flat line | Output = input (DC gain 1) | Session 2026-10-20 |
| SuperSmoother2Pole(20) | Unit sine, period 5 / 20 / 100 | Amplitude 0.0577 / 0.7042 / 0.9990 | Session 2026-10-20 |
| SuperSmoother2Pole(20) | Ramp | Lag 4.0387 bars | Session 2026-10-20 |
| RoofingFilter(48, 10) | Unit sine, period 20 / alternating (period 2) | Gain 0.8900165495219391 (phase −0.05338683922280379 rad) / ~6e-18 | RFF spec `[known_answer_T20]`, 2026-11-17. **Corrected:** the earlier 0.890038 (Week 14 Handoff 4 §8) was computed from the old code (0.707 HP), not the article; it differs by 2.1e-5. A period-2 sine cannot be built (sin(πn) = 0), hence the alternating input |
| EMA (lag reference) | Ramp | Lag 1.50 bars | README, measuring-tool check |

**D-14.1 — test data design.** Correctness tests use synthetic inputs. Real-data
checks use three small committed EUR/USD D1 slices, each named by the event it
covers, never stitched together: a splice creates an artificial bend the filter
treats as signal.

**Strategy-level validation (from roadmap v4.4, Phase 2.5).**
- Walk-forward over a 3×3 grid of training/testing window lengths; stability across
  the grid is the signal, not any single window's result.
- Surrogate test on a strategy's Sharpe: run it on ~1,000 surrogate price series
  (`analysis/null_tests/`), locate the real Sharpe in that distribution, with a
  positive control (injected known edge) so a null result has a detection bound.
- Confirmation-set pass condition is written and committed before the first
  confirmation run.

**Recurring error to avoid: one number in place of a trade-off.** Seen 5+ times in
Week 14 (SNR, "more attenuation = better", mean absolute difference as lag, mid-band
attenuation as quality). Harness and backtest reports show the trade-off as a table,
not a single score.

**Debugging method (found GAP-1.35).** Predict a value from first principles, check
it against the actual file; on a miss, find which coefficient version reproduces the
file's first rows exactly.

---

## 6. Phase 0 — complete

- [x] Step 1: project instructions rewritten (two modes, validation gate)
- [x] Step 2: this document committed as `docs/PROJECT_STATE.md` (`e151871`)
- [x] Step 3: superseded docs removed from project knowledge (21 docs; all remain in
  the repo, verified 2026-10-20). Repo reorganisation deferred to the README rewrite.
- [x] Step 4: `docs/sources/NNFX_Sources.md` — VP rules + Stonehill tests from 143 videos
  (transcripts fetched by `tools/fetch_transcripts.sh`, kept outside the repo). Numbers are
  configurable defaults; risk 0.3%–2%; dead-market mode optional, off. Stonehill numeric
  results are on their blog — fetch only for shortlisted indicators.

## 7. Phase 1 — build pipeline (decided 2026-11-03)

**Platform decision:** free Zorro, **batch scripts, one click per batch**. Move to Zorro S
(€35/month, cancel anytime) only if clicking becomes the bottleneck.
- Reason: Zorro's command-line automation (`-run`, `-train`, `-h`, `-quiet`, `-a`, `-d`, `-i`)
  is **Zorro S only** (Zorro manual, "Automatization with the command line"). Free Zorro can
  only *select* a script from the command line; [Test] must be clicked.
- Workflow: Claude Code (VS Code extension) writes a batch script that loops internally over
  indicators / assets / parameter sets and writes all results to file → user clicks [Test]
  once → Claude Code reads results and writes the next batch.
- Considered and not chosen now: Python research platform with own backtest engine (free, fully
  automatic, but leaves Zorro's built-in WFO/MC/cost model). Revisit if Light-C keeps causing
  silent bugs.
- Roles: claude.ai project chat = planning, decisions, research, review.
  Claude Code in VS Code = building and testing.

**Phase 1 steps**
1. [x] Check Claude Code in VS Code works in the repo (`git status`). Done.
2. [x] Write `CLAUDE.md` (rules Claude Code reads: validation gate, gotchas, paths, batch
   workflow). Done, `176fe70`.
3. [ ] **In progress.** Indicator harness as a batch script: known-answer checks (flat line,
   waves, ramp — §5) for SuperSmoother first, then the rest of the library, PASS/FAIL to one
   results file. H1 SuperSmoother2Pole: **run 2 PASS** (28/28 checks, NC1 + NC2 fail as
   required, 6 variants; `analysis/harness/results/H1_SuperSmoother2Pole_20261105_run2.csv`,
   `f59f6e4`). **Run 1 FAIL** (7 input guards: harness input precision — float32 literals and
   the `PI` macro) is kept in the record
   (`H1_SuperSmoother2Pole_20261105.csv`, `fd40b37`). Criteria:
   `docs/preregistration/H1_SuperSmoother2Pole_Criteria.md` (+ Amendment 1). Findings:
   gotchas §9d. Reusable harness design: `docs/harness/HARNESS_DESIGN.md`; its open points
   **D1–D3 decided 2026-11-06** (§6 there): exact √2/π under a literal-constant rule;
   per-quantity tolerances inside a floor×10 / ceiling÷10 window; keep Zorro `PI`.
   **Reusable harness built and accepted 2026-11-07** (`417da02`, branch `harness-step2`):
   reference model, checker, generator + TOML spec format, 27/27 self-tests; tool acceptance run
   reproduced H1 byte-identically (HARNESS_DESIGN §7). Run tests: `bash analysis/harness/run_tests.sh`.
   **SS2 source fidelity: run 1 PASS, 2026-11-12** (`763601e`, branch `harness-ss2f`). Spec
   `analysis/harness/specs/SS2_ArticleFidelity.toml` (`eaba250` + Amendment 1 `b941c06` + Amendment 2
   `02a6fca`); gain tol 3e-5, lag 1e-3. 28/28 real checks; NC-A, NC-B, NC1, NC2 detected on their required
   kinds; OX: 37/37 raw columns identical to H1 run 2 raw; 8 variants. Tooling 40/40 tests (checker CLI:
   `python analysis/harness/checker.py <spec.toml> <raw.csv>`). Raw sha256 `39c9ce95…a89e` (copy kept
   locally, `*_raw_run*.csv` is gitignored).
   **SS3 source fidelity + implementation: run 1 PASS, 2026-11-16** (`09c05ad`, branch `harness-ss3f`). Source
   *Cybernetic Analysis* Fig. 13.11; D1 Amendment 1 (rule 4, `9789fb5`): printed `1.738` → √3, justified by the
   book's own Table 13.4. The existing `SuperSmoother3Pole.c` was a hybrid matching neither cited source; corrected
   (`172fb4e`), hybrid kept as `SuperSmoother3Pole_Hybrid_Superseded.c` and used as negative control NCH. Spec
   `analysis/harness/specs/SS3_ArticleFidelity.toml` (`867f952` + Amendment 1 `a1dbce5`); gain tol 3e-5, lag 1e-3.
   New in this spec: IMP replay check (implementation question answered in the same run, no H1-style run needed)
   and floor guard (pass item 7). 28/28; NCA, NCB, NCL, NCH, NC1, NC2 detected on required kinds; IMP ≤ 3.4e-14;
   10 variants. Tooling 65/65 tests. Raw sha256 `eacb27cc…88f5` (local copy).
   **Order C decided 2026-11-16:** verify the indicators on the shortlisted slot path first (§1.2): MESAStochastic (C1) →
   RoofingFilter → HighPassFilter; UltimateChannelBands (stops) → UltimateSmootherE; Reflex (C2) → SuperSmoother2Pole
   (verified). Decycler deferred (used only by `Test_Decycler.c`). Steps 4–5 may be built in parallel; **no backtest
   result is read until every slot indicator in it has passed.**
   **HighPassFilter: run 2 PASS 2026-11-17** (`512781c`, branch `harness-hpf`; details §1.1 and HARNESS_DESIGN §7). New in
   this spec: D4 checks (phase, ramp residual, start-up), IMP own-model replay for every control, D5 amendment corrections.
   Workflow from now on: every run is read twice (planning-chat back-check + prediction, then checker; HARNESS_DESIGN §4).
   Tooling 198/198 tests. Raw sha256 `40dec81a…4898` (runs 1 and 2 byte-identical).
   **RoofingFilter: run 1 PASS 2026-11-17** (`d1395d3`, branch `harness-rff`; details §1.1 and HARNESS_DESIGN §7). New in
   this spec: two-parameter variants, include lists, alternating (Nyquist) input, phase gate binding (alt phase SKIP), cascade
   reference models. Read twice: planning-chat back-check agreed on every verdict row. Tooling 286/286. Raw sha256
   `edb3400f…c810`.
   **UltimateSmootherE: run 1 PASS 2026-11-18** (`41c8d76`, branch `harness-use`; details §1.1 and HARNESS_DESIGN §7). New in
   this spec: start-up seed mode `pass<n>` (the source's first-n-bars = Price rule), complement model `one_minus`, variant role `info`
   (NCL, article as printed, reported never PASS/FAIL), per-instance CurrentBar counter in the corrected .c (gotchas 9d.9). Read twice:
   planning-chat back-check agreed on every verdict and FAIL count. Tooling 361/361. Raw sha256 `b47897d9…4745c74`.
   **Decided 2026-11-18: oscillator family first (option B), Reflex before MESAStochastic.** Reason: C1/C2 are the entry signals
   (the template cannot trade without C1), their dependencies were already verified, and Reflex.c carried a live shared-state bug.
   UltimateChannelBands deferred: it reads High/Low itself (`series(priceHigh())`), so it needs a High/Low/Close signature change
   before the harness can test true range; (c) possibly off the first template's critical path if NNFX_Sources gives ATR stops
   (to check from the source, not memory).
   **Reflex: run 1 PASS 2026-11-18** (`ad487b7`, branch `harness-rfx`; details §1.1). New: HARNESS_DESIGN **D6** (oscillator check
   set: export the linear stage, trace replay with a model-MS gate, exact bound, invariance, multi-instance control, start-up INFO;
   `5087c39`); tooling `853dc20` (multi-output calls, trace/bound/invariance, shared-state replay) + `62b4e97` (out-parameters via
   local scalars, `&Y[k]` never compiled). Planning-chat prediction committed before the checker (`901b3a0`); the checker agreed on
   every verdict and all 76 control FAIL rows. Tooling 460/460. Raw sha256 `f1ab5494…1d75` (local copy).
   **MESAStochastic: run 1 PASS 2026-11-19** (branch `harness-mesa`; details §1.1). Review `3f0de96`, tooling `85b7431`, spec `0fd34ee`,
   corrected .c + superseded control + test `0332395`, Amendment 1 + script `4843ee2`, prediction `57b1abf`, results `17a8604`. New in
   this spec: three-output calls (out, Roof, raw Stoc), two-sided bound on the raw Stoc (the final output has no exact bound), gate
   on the model's HH − LL range, trace tolerance 5e-5 chosen by D2 rule 3 (the 3e-5 default failed the window). Resumed after an
   interrupted session (stash backup). Read twice: the checker agreed with the pre-run prediction on verdict, counts and compared
   values. Tooling 555/555. Raw sha256 `0c53641a…efddefda` (local copy).
   **LaguerreRSI: run 1 PASS 2026-11-19** (branch `harness-lrsi`; details §1.1). Review `6382607`, tooling `c2fcd44`, spec `824a3cc`,
   corrected .c + superseded control + test `a8955d1`, Amendment 1 + script `b85cfd9`, prediction `63d1c21`, results `15ae118`. New in this
   spec: real-valued call parameters built from integers, four columns per call (l0 / l3 / den / out) with linear checks on two outputs,
   the falling ramp, the kinds ramp_exact and startup (the source defines the start-up), the gate on the model's CU + CD, per-variant
   `skip_inputs` and the no-static pre-run lint (the shared-static control needs its seeded call on a checked input). Read twice: the
   checker agreed with the prediction on verdict, counts and every FAIL row; the prediction's ~1e-12 trace / start-up maxima came from
   its model being fed the exported %.15f x (corrected in Amendment 2). Tooling 657/657 (Claude Code shell). Raw sha256 `97125fec…2e3d`
   (local copy). Strategy 2's entry pair (MESA C1 + Laguerre RSI C2) is now fully verified.
   **Fisher Transform: run 1 PASS 2026-11-20** (branch `harness-fisher`; details §1.1). Review `bdc83da`, tooling `c1c222e`, spec `258b24a`, corrected .c + superseded control + callers + test `800c797`, Amendment 1 + script `cb93b65`, prediction `6e79c16`, results + Amendment 2 `a6debe0`; merged to main `a9e2ea4` (pushed). New in this spec: no linear stage (the normalisation divides by the range), three exported stages (raw, v1, out) each with an exact bound, a second gate on the clamp distance, kinds trigger and flat_zero, series_len 21, the shared statics are the IIR state so NCT is a real control. Read twice: the checker agreed with the prediction on verdict, counts and every FAIL row; two differences, both explained in Amendment 2 by one prediction-side omission (the back-check's IMP and must_fail loops left out the offset / scale inputs: FR20 IMP 5.262e-12, not 1.474e-12; FR10 must_fail 1.3044958329186862 at of100, not 1.304495832918544 at s100). Raw sha256 `8b8b61a0…9857a` (local copy). Both strategies' C1 indicators are now verified (Fisher, MESA Stochastic); Strategy 1's C2 (Reflex) was verified 2026-11-18, so Strategy 1's entry pair (Fisher C1 + Reflex C2) is fully verified too, as Strategy 2's.
   **MAMA / FAMA and FRAMA: run 1 PASS 2026-11-21** (branch `harness-mama-frama`; details §1.1). Review `b7bdd69`, tooling + specs `7713f5b`, corrected .c + superseded controls + callers + Amendment 1 `d0c9a23`, prediction `8c1e648`, results + Amendment 2 `3f7832f`; merged to main `ddcf11d` (pushed). New in these specs: the D7 family (adaptation variables exported next to the outputs, trace from row 1 with no warm-up cut, equivariance out(kx + c) = k out(x) + c, the hull bound, a conditioning classifier that sets which inputs are INFO), bars inputs for FRAMA (point bars and band bars x +- h), exact pi under D3 (MAMA, S1), explicit `series()` lengths for length-less series under `LookBack = 0` (gotchas 9d.10, open). MAMA: 66/66, 7/7 controls (71 FAIL rows), IMP 11/11 (<= 1.124e-10), floor 8/8, 9 variants. FRAMA: 98/98, 6/6 controls (129 FAIL rows), IMP 10/10 (<= 1.934e-12), floor 10/10, 8 variants. Read twice: the checker agreed with the prediction on verdict, counts, detections and IMP values; only ulp-level trace-maximum differences (<= 4e-15 absolute, MAMA phase / fama, FRAMA FR32 out / alpha), explained in each Amendment 2 A2.2. Raw sha256 MAMA `7c86c370…471e`, FRAMA `12c0e3bf…1d27` (local copies).
   **Stops re-scoped to ATR(14), 2026-11-21** (planning chat, user: as recommended). `NNFX_Sources.md` gives ATR-based stops (1.5 x ATR(14), A §4 / B §2.1) and five more
   ATR rules (TP1, trailing activation and distance, sizing, 1 x ATR baseline distance); no channel / band stop. UltimateChannelBands and NATR are deferred, off the
   critical path (NATR as coded = 100 x UltimateSmootherE(TR, 20) / Close, not ATR(14)). The averaging behind "ATR 14, default settings" was settled from MetaQuotes'
   installed `ATR.mq4` (simple 14-bar mean of TR, defined start-up), not from memory; Zorro's `ATR()` is Wilder's form, `ATRS()` the MT4 SMA. Review
   `docs/harness/ATR_SOURCE_REVIEW.md` + `ATR_REVIEW_MODEL.py` (AT-1..AT-7). (b) Spec-relevant: band bars with h above every per-bar move make TR constant and
   blind the averaging (s100: SMA = Wilder exactly); a 14- vs 15-bar window differs by 2-8% of the ATR level at every tested period.
   **ATR(14): run 1 PASS 2026-11-22** (branch `harness-atr`; details §1.1, HARNESS_DESIGN "D7 applied to ATR"). Review `e11270a`, tooling `2957476`, spec `bd62493`,
   ATR.c + probe + cross-check scripts + Amendment 1 `5c5d700`, prediction `348838b`, results + Amendment 2 `5250bfb`, cross-check record Amendment 3. New in this spec:
   D7 on a price-scale output (column role `scale`, `window_hull`, `known_value`, `range_bound`), a planted shared-state control (no superseded file), a pre-run
   probe for a condition only Zorro can answer, and a pre-registered real-data cross-check against a platform built-in (`ATRS(14)`: PASS, 1.7e-14 relative).
   Read twice: AGREE on every item. Tooling 950/950 (Git Bash). Raw sha256 `4f22e7c1…a441`, cross-check `8db8141c…16f4` (local copies).
   **Every slot indicator of both strategies is now verified except the exit, which has never been defined.**
   **Next: Phase 1 step 4, the generic NNFX template.** Open decisions before building (to take from the sources, not memory): (a) the exit slot (NNFX_Sources
   A §2.6: with no exit indicator, use an opposite C1 signal [V12]); the volume / volatility slot (none chosen; NATR and VolatilityRegime are unreviewed
   candidates, §1.1); the source gaps that affect coding (one-candle rule, fill model, TP1 touch vs close: NNFX_Sources "Open gaps" and A §10 / B §11).
4. [ ] **In progress.** Generic NNFX template with swappable slots and configurable defaults from `NNFX_Sources.md`.
   **Decisions T1-T11 taken 2026-11-22** (planning chat, one at a time): `docs/template/NNFX_TEMPLATE_DECISIONS.md` (`e1c0cb8`);
   plain-language summary `docs/template/NNFX_Template_Rules_Plain.md` + printable PDF (`0fad653`). Variant 0: exit slot NONE (opposite
   C1 [V12]); volume ALWAYS_YES (+ ALWAYS_NO guard stub); next-open fill; stop / TP1 intrabar, same-bar stop first; strict same-candle
   agreement; costs from the asset list at spread x1 and x2; 2% in two 1% halves, results in R; continuation with C2; catch-up with no
   day limit; T11 no magic numbers (one-at-a-time pre-registered sensitivity, every level counted). Open: NNFX Podcast Ep 39
   (one-candle rule) not among the 336 fetched videos, to fetch (T6); Strategy 2's C1 / C2 are both midline crosses, against V20 (T3).
   **Stages done 2026-11-22** (branch `template-decisions`, last commit `7018d5d`, not yet merged):
   - S0 Zorro 3.11 trade mechanics from the bundled manual (`C:/Zorro/zorro.chm`, unpacked to `C:/Zorro/manual_311/`; the older
     `zorro_help` copy is 2.70): `docs/template/ZORRO_TRADE_MECHANICS.md`; decisions M-D1 (bars close 17:00 New York: BarZone EST,
     BarOffset 1020), M-D2 (Slippage 0, 5 s as sensitivity), M-D3 (breakeven due with the close beyond entry: runner exits at the
     next open), M-D4 (project asset list `config/assets/AssetsNNFX_FX.csv` = AssetsForex.csv, account EUR, 100,000 start).
   - S1 `strategies/template/NNFX_Config.h` (every number named, source-labelled, integer-built) + `tools/lint_literals.py` (23 tests;
     planted label / decimal guards fire).
   - S2 `analysis/template/reference_engine.py` (independent Python implementation of T1-T11): 31 hand-calculated scenario tests incl.
     short mirror and config agreement; mutation check 7/7 real bugs caught, 2 equivalent mutants (`analysis/template/README.md`).
   - S3 probe `strategies/tests/TPL_Probe.c` + `tools/make_scenarios.py` (synthetic scenarios as `.t6` intraday paths + states CSV +
     expected trades): **run 6 PASS, all predictions** after 5 recorded runs and 5 amendments (`docs/template/TPL_Probe_Prediction.md`).
     Confirmed: next-open fill (Fill 3), entry-bar exits need TICKS (**T5 amendment: `nx_TicksOn = 1`**; the engine keeps T5.2, scenario
     A3HF documents the TICKS-order difference), stop / TP at the level, breakeven via `TradeStopLimit`, 17:00 NY bars across DST.
     Gotchas 9d.11-9d.15 (float trade fields in `strf`, TICKS, synthetic history naming, partial first bar, end-of-history close).
   **S3 template + S4 equivalence, 2026-11-23** (branch `template-decisions`; commits `356315a`, `b3f31f9`):
   - Decisions in this sitting (planning chat, one at a time): layout + event-order mapping (architecture A:
     Zorro executes, `nx_bar()` decides at each close, a statement-by-statement port of the engine's step 3);
     **M-D5** `Hedge = 2` (Zorro never closes a trade itself, so a missing exit shows); scenario set d (30 long
     + 30 short mirrors, new reversal scenario R1); planted-bug controls inside the same click; **M-D6**
     `StartWeek = 71700` (Sunday 17:00 New York).
   - Code: `strategies/template/NNFX_Slots.h` (slot states per closed bar, SCRIPTED source, volume / exit modes),
     `NNFX_Template.h` (per-asset arrays, no statics; halves matched by `TradeInt` tags because `TradeID` is 0
     while pending; exit reasons from Zorro's trade flags); config codes and switches in `NNFX_Config.h`
     (lint clean); `strategies/tests/TPL_Equivalence.c` (64 assets, compile-only switch);
     `tools/make_scenarios.py` (D/E/R1 scenarios, mirrors with explicit intraday order, padding guard,
     common last day, generated include); `tools/compare_equivalence.py` + 18 tests (each planted defect seen
     to flip the verdict). Engine tests 32/32 (R1 catches a bug no earlier test caught).
   - Criteria `docs/preregistration/TPL_Equivalence_Criteria.md` (committed before run 1; Amendment 1 before run 2).
     **Run 1 FAIL** (setup): Zorro's week starts Sunday 23:00 in the BarZone (gotchas 9d.16) and bars follow the
     first asset (9d.17). **Run 2 PASS, all predictions met:** 60/60 real scenarios, 4 DOC (A3HF / A3HFM TICKS
     order), 40 entry-only, 4/4 controls detected, largest fill difference 1.4e-8 (tolerance 1e-5).
     Confirmed (b): close-sent exits fill at the next open (Fill 3); a stop set beyond the price fills at the
     next tick (= the M-D3 exit price); real EUR/USD 2024 opens Sunday 17:01-17:09 New York.
   **P5 costs, 2026-11-23** (commits `4c10fec`, `8f5d947`, `4156cf6`): `strategies/tests/TPL_Costs.c` (8 scenarios x
   costs off / on, one click), `tools/check_costs.py` + 8 tests; template HALF rows carry profit / rollover /
   commission / spread / units, `nx_costs_apply()` applies the T7 multiplier from a stored base. Criteria
   `docs/preregistration/TPL_Costs_P5_Criteria.md` (+ Amendments 1-2). Run 1 FAIL (Q1 guard: synthetic names not
   Forex, costs per contract; `PROBE_AssetType`: only real pair names are Forex, gotchas 9d.18), run 2 FAIL (criteria
   tolerance), **run 3 PASS** (byte-identical to run 2). Found (b): every half pays one spread against its recorded
   fill; a long TP1 triggers at about bid = level (M-D7, accepted); short levels from the ask entry; rollover per bar
   day (17:00 New York), weekend days included, after 12 h (gotchas 9d.19). Cost assets: real pair names with a
   `syn` history suffix (`History = "*syn.t6"`), so no real run can load them.
   **P6 sizing, 2026-11-23** (commits `1cc7f3e`, `f315f77`, `2b22994`): decisions M-D8 (template computes lots:
   floor(Equity x 1% / (1.5 x ATR pips x PIPCost)) per half; refuse below 1 lot, risk above 1%, margin above Equity;
   `Capital` 100,000; fixed asset-list PIPCost = 2025-07-28 rates, per-bar conversion later; MarginCost from
   leverage 20 at entry). `nx_size()`, SIZE / ACCT log rows; probe `strategies/tests/TPL_Sizing.c` (15 synthetic
   assets, `History = "*sz.t6"`), `tools/check_sizing.py` + 8 tests; criteria `docs/preregistration/TPL_Sizing_Criteria.md`.
   **Run 1 PASS**: hand-calculated lots 66 / 77 / 11474, all 3 guards fired, mutant detected; Equity at a decision
   holds every asset's state at this bar's close (timing TA). Open (b): `MarginTotal` fits neither MarginCost model
   (<= 0.2% off). Regressions after P6: TPL_Equivalence run 4 and TPL_Costs run 4 byte-identical to run 3.
   Housekeeping: S4 run 3 regression after P5 PASS; gotchas §1.3 prefixes `tpc_`, `pat_`, `tsz_`, `nxz_`; 9d.19
   reworded to M-D7; P5 run-1 files moved to `History/_to_delete/`.
   **R1 EUR/USD real data, 2026-11-23/24** (branch `eurusd-r1`; decisions R-D1..R-D7 in NNFX_TEMPLATE_DECISIONS; criteria
   `docs/preregistration/TPL_R1_Criteria.md` + Amendments 1-2): mechanics only, no performance read (R-D1). Strategy 1 variant 0
   (`NNFX_Strategy1.h`: FAMA (.5, .05), Fisher 10, Reflex 20, ATR 14), EUR/USD M1 2005-2026, trades 2007-04-01..2026-05-29,
   TR_FRC on. Python side `tools/r1_data.py` (17:00 NY bars, dedup of repeated M1 records, holiday folding), `r1_replay.py`
   (engine + M1 layer), `check_r1.py` + 21 tests. **R1a run 1 FAIL** (bar rule, holidays, INITRUN series state, Error 047),
   **R1a run 2 PASS** under Amendment 2 (Error 047 "no 2004 history" accepted only with every bar matched): 650/650 halves equal
   the independent replay, indicators equal the models (<= 5.6e-16), sizing / Equity / profit exact. **R1b run 1 PASS** (cost
   identity and whole-day rollover on 650 halves). Regressions: S4 run 5, P6 run 2 byte-identical; P5 run 5 PASS with 2 long-TP
   fills moved 7e-7 (Zorro rounded fills to 0.1 pip before TR_FRC). Gotchas 9d.20-9d.23.
   **Step 5, 2026-11-24** (`docs/preregistration/STEP5_HandChecked_Trades.md`): 10 R1a trades (one per exit combination,
   both same-bar days; seed 20261124) + one bridge-too-far refusal, every rule checked, decisive highs / lows confirmed against
   exchangerates.org.uk / poundsterlinglive.com within 0.4 pip: **PASS**. Pullback entries never occurred (S4 covers them).
   Observation: several outcomes hang on < 4-pip margins: test sensitivity to a second EUR/USD data feed later.
   **PERF1, 2026-11-24** (branch `perf1-strategy1`; criteria `docs/preregistration/PERF1_Strategy1_EURUSD_Criteria.md` `8c28490`
   + Amendments 1-3): first performance read of Strategy 1 variant 0 on EUR/USD, decided before looking (what is reported, data,
   verdict rule at spread x2, one-feed note). `tools/perf_report.py` (51 tests: hand-calculated items, planted target-risk
   defect, four verdict guards). Logging-only template change (REFUSED rows, INFO Tp1Atr; `d49c581`); regressions S4 run 6,
   P5 run 6, P6 run 3 PASS (P6: 3 REFUSED rows = 3 ERROR rows); **R1d** (x1) PASS with K7 650/650 HALF rows = R1b;
   **R1c** (x2) PASS. **Read 1: STOP** (b): 325 signals, mean signal-R -0.030 at x2 (t -0.87), total -9.87 R, -12.87 R without
   the best year (2007); x1 mean -0.024. (c) No evidence of an edge; roughly flat before costs (approximate). Report
   `analysis/template/r1/results/PERF1_read1_report.md`. Disclosures: step-5 trades, 3 R1b rows + row counts, Zorro's summary
   seen after R1d (A3.1). **Strategy variants tested: 1.** Strategy 1 is not tuned on EUR/USD (P-3).
   **PERF2, 2026-11-24/25** (branch `perf2-strategy2`; criteria `docs/preregistration/PERF2_Strategy2_EURUSD_Criteria.md`
   `6eade39` + Amendments 1-6). **T3 amendment 1** (decided 2026-11-24, option B): Strategy 2 C1 = MESA Stochastic vs SMA(10) of
   its own output, two-lines cross [V18, V20]; C2 Laguerre RSI 0.5 midline unchanged; bridge-too-far on (V34). SMA computed by
   our own code, Zorro `SMA()` as cross-check X1 (decision 2a); mechanics gate = R1 pattern (decision 2b). Built:
   `NNFX_Strategy2.h` + config, `TPL_R2_EURUSD.c`, `tools/r2_replay.py`, `tools/check_r2.py` (+ IND column-count guard),
   engine records bridge-too-far refusals, `perf_report.py --read perf2`. **R2a run 1 FAIL** (IND format miscount, holiday
   market fills: gotchas 9d.24 corrected, 9d.25; `r1_replay.open_fill` skips holiday-dated records, R1a run 2 re-checked
   PASS), run 2 checks PASS with a stray IND column, **run 3 PASS** (gate run); **R2b (x1) PASS**, **R2c (x2) PASS**: 564
   halves = the independent replay, 158 bridge-too-far refusals equal, X1 exact. **Read 1: STOP** (b): 282 signals, mean
   -0.048 at x2 (t -1.18), total -13.52 R, -16.01 R without 2008. Report `analysis/template/r2/results/PERF2_read1_report.md`.
   Disclosures: dry-run entry-kind / refusal counts (A2), Zorro's costs-off summary of R2a (A3.1). **Strategy variants
   tested: 2.**
   **Decision N1 (2026-11-25, user: as recommended): C -> B, with D alongside.** C: the template's null distribution first
   (verified Python engine, random C1 states, costs, many runs, positive control: what "no edge" looks like under this money
   management, and what edge a ~300-signal read can detect). B: then VP's slot-by-slot method (C1 alone with the ATR money
   management across dev pairs, then C2 by C-3b of `C2_Selection_Criteria_PreRegistered.md`, then the rest; (a) A §5.1).
   D: EUR/JPY and AUD/USD M1 into Zorro. Options not taken: A (re-run both stopped strategies on other pairs: a search over
   pairs, C2 criteria A1.4). C's pre-registration is decided one point at a time.
   **NULL1, 2026-11-25** (`docs/preregistration/NULL1_TemplateNull_Criteria.md`, decisions C1-C6): Python engine with costs
   (V1 PASS vs Zorro), C1-only mode (`baseline_mode = "off"`, V3 tests), circular-shift null, drift-injection positive
   control, fast vectorised M1 resolver (Amendment 1, proven identical). **Read 1** in §3. Tools `tools/null1.py`,
   `null1_report.py`.
   **C1S1, 2026-11-25** (`C1S1_C1Screen_EURUSD_Criteria.md`, K = 6, rule R-b, max-statistic null): **read 1: 1 survivor, MAF.**
   Tools `tools/c1s1.py`.
   **Step D data, 2026-11-26:** AUD/USD (2002-2026) and EUR/JPY (2010-2026-01-15, quote hole 2017-12-11..2018-01-01) M1 from
   Zorro's free history packages into `C:/Zorro/History`; EUR/USD files unchanged.
   **C1S2, 2026-11-26** (`C1S2_MAF_OtherPairs_Criteria.md`, decisions P1-P4): `TPL_BARS_PAIR.c` (bars + MAMA / FAMA / ATR, no
   trades), `tools/check_bars_pair.py`, `tools/c1s2.py`. VB checks: AUD/USD PASS; EUR/JPY FAIL (Zorro's 3 flat filler bars in
   the quote hole, gotcha 9d.26) -> Amendment 1 (Python takes Zorro's filler bars as logged, `r1_data.insert_fillers`) -> PASS.
   Offsets and null runs committed before the read. **Read 1: MAF STOP** (§3).
   **FINDINGS1, 2026-11-26** (decision N2: A): write-up of PERF1, PERF2, NULL1, C1S1, C1S2
   (`docs/research/FINDINGS1_C1_Timing_D1FX.md`). Counts: full-strategy variants 2; C1-only readings 6 on EUR/USD + MAF on 2
   more pairs.
   **C1S3 + DIAG1, 2026-11-26/27** (decision N3: B + D; branch `c1s3-pooled-c1-screen`; criteria
   `C1S3_FiveC1_Pooled_Criteria.md` (P-a, V-a, O-a, Q1-Q5), `DIAG1_S2Slots_ZeroCost_Criteria.md` (G-a, J-a, R1-R5, Amendments
   1-2)): `TPL_IND_PAIR.c` + `tools/check_ind_pair.py` (VW2 PASS both pairs), `tools/c1s3.py`, `tools/diag1.py`; tools tests
   193. NULL1 Amendment 2 (x0 rows include rollover). Reads in §3.
   **Next:** Decision N4 (after C1S3: the D1-FX C1-only line is closed; open: BTC/USD H4, a different slot, or a rethink of the
   template). **Earlier:** Decision N3, the next research question, one decision at a time. Open options (FINDINGS1): the five other C1
   readings on AUD/USD + EUR/JPY with a pooled max-statistic null; another slot or market (exits / trailing, baseline as a
   filter, BTC/USD H4); why the Strategy 2 slot set loses R without spread (rollover in: NULL1 Amendment 2). Not to be done: tuning MAF or any stopped strategy, or
   choosing variants from subgroups.
   **Earlier next (before N1, done):** decide the next step after two STOPs, one decision at a time (planning chat). Not to be done: tuning either
   strategy on EUR/USD or choosing variants from the PERF1 / PERF2 subgroups. Phase 2 items (T11 sensitivity, other dev pairs,
   walk-forward, surrogates, second data feed) apply only to a system that passes a read. Small open items: stale comment
   `NNFX_Config.h:156` "(Strategy 2: 0)" (value 1 is right; fix with the next template change); PERF1 header start date
   "2007-02-01" vs the 2007-04-01 its runs used (noted in PERF2).
   **Open:** `MarginTotal` mechanism (P6 run 1 observation).  dev-set history: `C:/Zorro/History` holds EUR/USD (2005-2026), AUD/USD (2002-2026), EUR/JPY (2010-2026-01-15) M1; BTC/USD to locate. `C:/Zorro/history_*.zip` and `_unpack/` can be deleted by the user. `.gitignore` `Results/` also matches `results/` (needs `git add -f`). NNFX Podcast
   Ep 39 (one-candle rule) to fetch. Delete `C:/Zorro/History/_to_delete/` (old synthetic files; deletion is off from the session).
5. Backtest engine checks on hand-calculated trades (stop, 1×ATR half exit, breakeven,
   trailing after 2×ATR) before any strategy result is trusted.

---

## Appendix — chat inventory (for archiving)

Done 2026-10-20. Chats are renamed rather than archived (claude.ai has no archive).
A `[ARCHIVED]` chat is history; where it conflicts with this document, this document wins.

| Prefix | Chats |
|---|---|
| `[REF]` | Ehlers price decomposition premise (null-test design); Claim Audit (CV and interview gaps) |
| `[ARCHIVED]` | Roadmap review; Unified FX/crypto roadmap; Integrating FX and crypto plans; Weeks 5, 6, 7 (MAMA), 8, 9, 10, 12, 13 (NATR/Channels/RSIH/Laguerre) |
| Deleted | Weeks 1, 2, 3-4, 4 Day 3-6, 7 part b, 13 Volatility & Bands; Cross-asset validation spec; rehaul_10_08_2026; Week 14 Session 1 parts 1–5 |
