# MAMA / FAMA and FRAMA — source review (code vs article)

**Date:** 2026-11-20 (planning chat). **Status:** review complete, decisions taken (user, 2026-11-20: all as recommended). No spec yet.
**Files reviewed:** `indicators/ehlers/MAMA.c` (181 lines, last commit `2a5eca5`), `indicators/ehlers/FRAMA.c` (95 lines, last commit `2a5eca5`).
No dependencies (MAMA takes `Price` as a parameter; FRAMA reads `priceHigh()` / `priceLow()` itself, FR-2).
**Sources (both read from the page images, not only the text layer; one source each):**
- **MAMA / FAMA:** Ehlers, J.F., "MESA Adaptive Moving Averages", *Technical Analysis of Stocks & Commodities* **V.19:9 (2001)**, pp. 30-35;
  **Sidebar Figure 1 "TradeStation code for MAMA and FAMA"** (project knowledge `MESA Adaptive Moving Averages.pdf`, PDF page 5). (a) The
  article states it was adapted from *Rocket Science for Traders* (Wiley 2001), which is not in `C:/books`.
- **FRAMA:** Ehlers, J.F., "Fractal Adaptive Moving Averages", *TASC* **V.23:10 (2005)**, pp. 81-82; **"FRAMA EasyLanguage code" sidebar**
  (project knowledge `Fractal Adaptive Moving Averages.pdf`, PDF page 3).
- (b) *Cybernetic Analysis* (2004, `C:/books`) contains neither indicator (text search: no MAMA, no fractal / FRAMA).
**Context:** PROJECT_STATE §7 step 3; baselines of both strategies (§1.2: FAMA for Strategy 1, FRAMA for Strategy 2), decided 2026-11-19.
First indicators of a new harness family, **D7 (adaptive smoothers)**, §6 below.
**Model:** every (b) number below is reproduced by `docs/harness/MAMA_FRAMA_REVIEW_MODEL.py` (first pass) and
`docs/harness/MAMA_FRAMA_REVIEW_MODEL_2.py` (conditioning, shared state, hold rule, bounds, equivariance), float64, independent of the
harness tooling. Inputs as before: level 1.1, sine amplitude 0.01, ramp slope 1e-4, 3000 bars. FRAMA inputs use H = L = x (point bars) unless
stated. "Source model" = EasyLanguage semantics: every var starts at its declared initial value and keeps its previous value on a bar where
it is not assigned.

Labels: (a) source states · (b) read or computed here · (c) inference.

---

## 1. Source formulas (a)

**MAMA — TASC V.19:9, Sidebar Fig. 1:**

```
Inputs: Price((H+L)/2), FastLimit(.5), SlowLimit(.05);
Vars:   Smooth(0), Detrender(0), I1(0), Q1(0), jI(0), jQ(0), I2(0), Q2(0), Re(0), Im(0),
        Period(0), SmoothPeriod(0), Phase(0), DeltaPhase(0), alpha(0), MAMA(0), FAMA(0);

If CurrentBar > 5 then begin
  Smooth = (4*Price + 3*Price[1] + 2*Price[2] + Price[3]) / 10;
  Detrender = (.0962*Smooth + .5769*Smooth[2] - .5769*Smooth[4] - .0962*Smooth[6])*(.075*Period[1] + .54);
  Q1 = (.0962*Detrender + .5769*Detrender[2] - .5769*Detrender[4] - .0962*Detrender[6])*(.075*Period[1] + .54);
  I1 = Detrender[3];
  jI = (.0962*I1 + .5769*I1[2] - .5769*I1[4] - .0962*I1[6])*(.075*Period[1] + .54);
  jQ = (.0962*Q1 + .5769*Q1[2] - .5769*Q1[4] - .0962*Q1[6])*(.075*Period[1] + .54);
  I2 = I1 - jQ;            Q2 = Q1 + jI;
  I2 = .2*I2 + .8*I2[1];   Q2 = .2*Q2 + .8*Q2[1];
  Re = I2*I2[1] + Q2*Q2[1];
  Im = I2*Q2[1] - Q2*I2[1];
  Re = .2*Re + .8*Re[1];   Im = .2*Im + .8*Im[1];
  If Im <> 0 and Re <> 0 then Period = 360/ArcTangent(Im/Re);
  If Period > 1.5*Period[1] then Period = 1.5*Period[1];
  If Period < .67*Period[1] then Period = .67*Period[1];
  If Period < 6 then Period = 6;
  If Period > 50 then Period = 50;
  Period = .2*Period + .8*Period[1];
  SmoothPeriod = .33*Period + .67*SmoothPeriod[1];
  If I1 <> 0 then Phase = (ArcTangent(Q1 / I1));
  DeltaPhase = Phase[1] - Phase;
  If DeltaPhase < 1 then DeltaPhase = 1;
  alpha = FastLimit / DeltaPhase;
  If alpha < SlowLimit then alpha = SlowLimit;
  If alpha > FastLimit then alpha = FastLimit;
  MAMA = alpha*Price + (1 - alpha)*MAMA[1];
  FAMA = .5*alpha*MAMA + (1 - .5*alpha)*FAMA[1];
  Plot1(MAMA, "MAMA"); Plot2(FAMA, "FAMA");
End;
```

(a) Text: FastLimit .5 and SlowLimit .05 are the suggested limits; "these limits are simple boundaries to keep a computer program from
hanging up or crashing". The arctangent measures phase over -90..+90 degrees and snaps back every half cycle; a negative rate of change is
limited to 1 so alpha = FastLimit at the snapback. FAMA uses half of MAMA's alpha. The crossover of MAMA and FAMA is the suggested signal.
(a) `ArcTangent` returns degrees (EasyLanguage). (a) Start-up: every var starts at 0 and nothing is computed while `CurrentBar <= 5`.
(a) SmoothPeriod is computed and never used.

**FRAMA — TASC V.23:10, sidebar:**

```
Inputs: Price((H+L)/2), N(16);   {N must be an even number}
Vars:   count(0), N1(0), N2(0), N3(0), HH(0), LL(0), Dimen(0), alpha(0), Filt(0);

N3 = (Highest(High, N) - Lowest(Low, N)) / N;
HH = High; LL = Low;
For count = 0 to N/2 - 1 begin  If High[count] > HH then HH = High[count];  If Low[count] < LL then LL = Low[count];  End;
N1 = (HH - LL) / (N / 2);
HH = High[N/2]; LL = Low[N/2];
For count = N/2 to N - 1 begin  If High[count] > HH then HH = High[count];  If Low[count] < LL then LL = Low[count];  End;
N2 = (HH - LL) / (N / 2);
If N1 > 0 and N2 > 0 and N3 > 0 then Dimen = (Log(N1 + N2) - Log(N3)) / Log(2);
alpha = ExpValue(-4.6*(Dimen - 1));
If alpha < .01 then alpha = .01;
If alpha > 1 then alpha = 1;
Filt = alpha*Price + (1 - alpha)*Filt[1];
If CurrentBar < N + 1 then Filt = Price;
Plot1(Filt);
```

(a) Text: "The length input is the entire period to compute N3 ... divided into two equal segments for N1 and N2, the length must be an even
number." D varies from 1 to 2; alpha = exp(-4.6(D - 1)): 1 at D = 1, "0.01 when D = 2". (a) The dimension uses **High and Low**, the filter
uses **Price** ((H+L)/2 by default). (a) Start-up: `Filt = Price` for the first N bars. (a) When N1, N2 or N3 is 0, Dimen keeps its previous
value (initial 0, so alpha = 1) and Filt still updates.

## 2. Line-by-line comparison

**MAMA.c vs Sidebar Fig. 1**

| Stage | Source (a) | `.c` (b) | Verdict |
|---|---|---|---|
| Input | `Price` input | `vars Price` parameter (line 65) | Matches |
| Start-up | all vars 0; body only if `CurrentBar > 5` | `series(Price[0])` for Smooth, MAMA, FAMA; `series(20.0)` for Period, SmoothPeriod; returns `Price[0]` (and FAMA = Price) while `barCount <= 5` (lines 74-96) | **MA-1** |
| Counter | `CurrentBar` (per indicator instance) | `static int barCount`, reset in INITRUN (lines 68-70) | **MA-3** |
| Smooth | `(4P + 3P[1] + 2P[2] + P[3]) / 10` | line 100, same | Matches |
| Detrender, Q1, I1, jI, jQ | HT FIR .0962 / .5769 at lags 0, 2, 4, 6, x (.075 Period[1] + .54); I1 = Detrender[3] | lines 105-124, same | Matches; literals **MA-4** |
| Phasor addition, smoothing | I2 = I1 - jQ, Q2 = Q1 + jI; .2 / .8 | lines 128-132, same | Matches; literals **MA-4** |
| Homodyne | Re, Im, .2 / .8 | lines 137-141, same | Matches |
| Period | `If Im <> 0 and Re <> 0 then Period = 360/ArcTangent(Im/Re)` (degrees); otherwise **keeps Period[1]** | line 146-147: `360/(atan(Im/Re)*180/PI)`; otherwise Period[0] = **20** (the `series(20.0)` default set every bar) | Conversion matches; hold **MA-2** |
| Period bounds | 1.5x, .67x, 6, 50, then .2 / .8 blend; order as listed | lines 150-154, same order | Matches; literals **MA-4** |
| SmoothPeriod | .33 / .67, unused | line 155, unused | Matches (**MA-6** record) |
| Phase | `If I1 <> 0 then Phase = ArcTangent(Q1/I1)`; otherwise **keeps Phase[1]** | lines 159-160: degrees via `*180/PI`; otherwise Phase[0] = **0** (series default) | Conversion matches; hold **MA-2** |
| DeltaPhase, alpha | `Phase[1] - Phase`, floor 1; FL / DeltaPhase clamped to [SL, FL] | lines 164-170, same | Matches |
| MAMA, FAMA | EMA alpha; FAMA EMA .5 alpha of MAMA | lines 173-177, same | Matches |
| `PI` | — | `#ifndef PI` fallback 3.14159265358979 never applies: `trading.h:25` defines PI 3.14159 (gotchas 9d.2) | **MA-5** |
| Literal products | — | none at the start of an expression (`atan(...)*180.0/PI` starts with a call) | OK (gotchas 9d.8) |
| Exports | — | FAMA via `outFAMA` only | **MA-7** |
| Header | — | "APPROVED Week 7", "Lag FX=0 bars", SNR, "51.3% win rate", "92.5% clamp", "Low sensitivity confirmed Day 5", "published code initializes to 0 which causes 1.5*0=0 trap" | **MA-8** |

**FRAMA.c vs the sidebar**

| Stage | Source (a) | `.c` (b) | Verdict |
|---|---|---|---|
| Parameter | `N` = full window, even, default 16 | `int T` = half window (header: "full window = 2T bars, default T=16"); every caller passes 16 (32-bar window) | **FR-1** |
| Inputs | `Price` input; High, Low read by the indicator | `priceHigh()` / `priceLow()` inside the function (lines 38-42); Price fixed to (H+L)/2 | **FR-2** |
| N1 (bars 0..N/2-1) | HH / LL loop, / (N/2) | lines 45-52, same with T = N/2 | Matches |
| N2 (bars N/2..N-1) | HH = High[N/2] ..., / (N/2) | lines 55-61, same | Matches |
| N3 (bars 0..N-1) | `(Highest(High,N) - Lowest(Low,N)) / N` | lines 64-70: max / min of the two boxes, / (2T) | Matches |
| Guard | `If N1 > 0 and N2 > 0 and N3 > 0 then Dimen = ...`; otherwise Dimen held, Filt still updated | line 81: `if(N3 <= 0) return prev` (no update); no N1 / N2 condition: N1 + N2 = 0 with N3 > 0 gives `log(0)` = -inf, alpha -> .01 | **FR-5** |
| Dimen, alpha | `(Log(N1+N2) - Log(N3)) / Log(2)`; `ExpValue(-4.6*(Dimen-1))`; clamps .01, 1 | lines 84-89, same (clamp order reversed, equivalent) | Matches; literals **FR-6** |
| Filter | `alpha*Price + (1-alpha)*Filt[1]` | line 92, same | Matches |
| Start-up | `Filt = Price` while `CurrentBar < N + 1` | seed `frama_prev = price` on the first call, EMA from the second call over windows padded with the first value (gotchas 9d.6) | **FR-4** |
| State scope | per instance | `static frama_prev`, `static frama_init` **shared by every call** | **FR-3** |
| Exports | — | none | **FR-7** |
| Header | — | "default T=16", "alpha -> 0.01 (D -> 2)", "Implementation: Week 9" (Week 9 validation not reproducible, PROJECT_STATE §4) | **FR-8** |

## 3. Behaviour — measured (b)

**MAMA / FAMA (FastLimit .5, SlowLimit .05), source model unless stated:**

| Input | FAMA range rows >= 1000 | Period rows >= 1000 | alpha: FL / SL / interior | 1-ulp input change: max \|dFAMA\| all rows / rows >= 1000 |
|---|---|---|---|---|
| flat | 1.1 exactly | 50 (driven by rounding noise in Detrender) | 1.000 / 0 / 0 | **3.2e-2** / 6.7e-16 |
| ramp | trace | 36.27..47.66 (wanders) | 0.490 / 0 / 0.510 | 6.7e-14 / 6.7e-14 |
| s5 | 1.099523..1.101657 | 6 (floor; T = 5 < 6) | 0.400 / 0.600 / 0 | **8.6e-3** / **1.05e-3** (alpha differs on 56 rows >= 1000) |
| s10 | 1.099901..1.100099 | 10.05..10.14 | 0.200 / 0.800 / 0 | 6.7e-16 / 4.4e-16 |
| s20 | 1.099446..1.100554 | 19.96..20.05 | 0.100 / 0.900 / 0 | 6.0e-15 / 6.7e-16 |
| s40 | 1.098878..1.101122 | 39.81..40.18 | 0.050 / 0 / 0.950 | 1.3e-14 / 1.6e-15 |
| s100 | 1.092066..1.107934 | 50 (ceiling) | 0.020 / 0 / 0.980 | 6.7e-14 / 4.7e-14 |

- (b) **The discriminator measures the cycle** on T = 10 / 20 / 40 (within 0.5%); T = 5 and T = 100 sit on the 6 / 50 bounds.
- (b) **Discontinuities.** alpha is continuous in DeltaPhase (FL/1 = FL and FL/10 = SL at the clamp edges), but the phase **wrap** at
  ±90 degrees (I1 near 0) changes DeltaPhase by 180 degrees, flipping alpha between FL and SL, and the Period formula changes sign with Re.
  A flip moves the EMA state, which then decays over hundreds of bars. **s5 is ill-conditioned:** one ulp of input moves FAMA by 1.05e-3 at
  rows >= 1000 (phase steps of +63 / -117 degrees at the flipped rows). **Flat is ill-conditioned during start-up:** from the zero start,
  rounding noise in Detrender drives the phase, so one ulp moves FAMA by 3.2e-2 over all rows (6.7e-16 at rows >= 1000). Every other input
  moves by <= 6.7e-14 over all rows.
- (b) **Ramp is not a known answer for MAMA:** Period wanders 36..48 and the lags (rows >= 1000) are 2.222245814077 bars (MAMA) and
  6.963521413259 bars (FAMA), not the 1 / 4 bars a constant alpha .5 would give. It is well conditioned (6.7e-14), but its start-up memory
  never ends: source vs current code still differ by 9.6e-5 at row 2999. A ramp trace is valid only if the start-up matches the source.
- (b) **Start-up memory on the sines:** current code vs source (MA-1) differs by up to 1.11 (the level), last row > 1e-12 at 216 (MAMA) /
  521 (FAMA) on s20, 155 / 277 on s100. The Period init alone (20 vs 0): up to 1.3e-2, last row 441 (s20) / 304 (s100).
- (b) **Shared `barCount` (MA-3):** a second instance seeing the counter one ahead differs by 1.24e-3 (s20) / 5.7e-4 (s100) / 1.36e-4 (ramp),
  last row > 1e-12 at 399 / 215 / 109: start-up only, not permanent.
- (b) **float32 literals (MA-4):** max \|dFAMA\| rows >= 1000: 0 (s10, s20), 4.1e-11 (s40), 5.7e-10 (s100), 3.1e-4 (ramp, long memory),
  1.48e-3 (s5, a wrap flip at row 18 that never washes out).
- (b) **`PI` gap (D3):** <= 4.8e-9 in FAMA (s100), 2.2e-10 (ramp), 0 where alpha is clamped every row.
- (b) **Exact bounds:** alpha in [SL, FL] on every computed row; Period <= 50 always; Period >= 6 only asymptotically from the zero start
  (the 1.5x bound acts before the 6 floor, so Period climbs 0 -> 1.2 -> ...).
- (b) **Equivariance:** MAMA(3x + .5) = 3 MAMA(x) + .5 within 7.1e-15 (FAMA 4.0e-15) and alpha unchanged within 2.9e-13 (s40, rows >= 1000).

**FRAMA (H = L = x), source model N = 16:**

| Input | out range rows >= 200 | mean alpha rows >= 200 | Dimen range rows >= 200 | current code (T = 16, i.e. N = 32) vs source N = 16 |
|---|---|---|---|---|
| flat | 1.1 exactly | 1 | 0 (never computed: N3 = 0; held initial) | 0 |
| ramp | out = x exactly | 1 | 0.900464326449 = log2(28/15) | 0 |
| s5 | 1.099930..1.100096 | 0.0101 | 2.0000 | 1.27e-3 |
| s10 | 1.099773..1.100213 | 0.0139 | 1.8552..2.0000 | 8.5e-4 |
| s20 | 1.090489..1.109511 | 0.4494 | 0.7579..1.8880 | 9.46e-3 |
| s40 | 1.090000..1.110000 | 0.7441 | 0.8720..1.8257 | 9.92e-3 |
| s100 | 1.090000..1.110000 | 0.8999 | 0.8966..1.8102 | 3.46e-3 |

- (b) **The window convention matters (FR-1):** the library's 32-bar window vs the source default 16 differs by up to 9.9e-3, about the whole
  sine amplitude (0.01).
- (b) **D <= 2 always, so alpha >= exp(-4.6) = 0.010051835744633586 and the .01 floor never binds:** N1 + N2 <= 2 range / (N/2) = 4 N3.
  The article's "0.01 when D = 2" is rounded. **The 1.0 ceiling binds whenever D < 1**, which point bars allow (the two halves do not
  overlap: ramp D = log2(4(N/2 - 1)/(N - 1)) = 0.9005 at N = 16). (c) With real bars (H > L, overlapping ranges) D >= 1 always.
- (b) **Ramp known answer (H = L):** alpha = 1, out = x exactly (lag 0) on every row past start-up.
- (b) **Start-up (FR-4):** current code vs source differ by up to 1.49e-2 (s5) / 1.44e-2 (s10); because alpha sits near .01 when D is near 2,
  the memory is long: .99^n < 1e-12 from n = **2750** bars; s5 still differs by 8.2e-4 at rows >= 200.
- (b) **Hold rule (FR-5):** on a step, a stair (16-bar flats) and a random walk (sigma .005), code and source differ only at start-up
  (random walk: 1.6e-3, last row 15); 0 / 2.2e-16 at rows >= 200. The `log(0)` branch is reachable with point bars (both halves flat, N3 > 0).
- (b) **Shared statics (FR-3):** two instances (N = 16 then N = 32) sharing `frama_prev` differ from their own instances by up to 3.5e-4 /
  9.5e-3 (s20), 3.9e-3 / 9.9e-3 (s40), **1.4e-2 / 3.3e-2 (random walk)**, rows >= 200: permanent, silent.
- (b) **float32 literals (FR-6):** <= 1.6e-10.
- (b) **Well conditioned on every input:** one ulp of input moves the output by <= 4.4e-15 (5 random perturbations per input).
- (b) **Bounds:** out within the running [min x, max x] on every row (convex combination); alpha in [exp(-4.6), 1].
- (b) **Equivariance:** FRAMA(3x + .5) = 3 FRAMA(x) + .5 within 2.2e-15 (s40, every row).

## 4. Deviations and decisions (user, 2026-11-20: all as recommended)

**MAMA.c**

| # | Deviation | Impact (b) | Decision |
|---|---|---|---|
| **MA-1** | Start-up: price seeds, `Price` returned for the first 5 calls, Period / SmoothPeriod start at 20; source starts every var at 0 and computes only when CurrentBar > 5 | Up to 1.11 for ~220-520 rows on sines; never ends on the ramp | **Fix: follow the source** (as GAP-1.26, LRS L-1). Start-up becomes a PASS/FAIL check and the ramp a valid trace. (c) Cost: MAMA / FAMA are unusable for ~500 bars from a zero start; the NNFX template's LookBack must cover it (step 4) |
| **MA-2** | Period = 20 when Im or Re = 0; Phase = 0 when I1 = 0 (series defaults); the source keeps the previous value | Fires only on exact zeros (flat) | **Fix:** `Period[0] = Period[1]`, `Phase[0] = Phase[1]` before each conditional |
| **MA-3** | `static int barCount` shared by every call; INITRUN reset never runs in generated scripts (they return at INITRUN) | Up to 1.24e-3 on a second instance, start-up only | **Fix:** per-instance counter `series(0, 2)` (gotchas 9d.9), called before any early return. Old file kept as `MAMA_Superseded.c`, two instances = shared-state control |
| **MA-4** | float32 literals .0962, .5769, .075, .54, .2, .8, .33, .67 | <= 5.7e-10 on well-conditioned sines; 3.1e-4 ramp; 1.5e-3 s5 | **Fix:** build from integers (D1 rule 2: taken literally at the decimal value) |
| **MA-5** | `#ifndef PI` fallback (3.14159265358979) never applies | `PI` gap <= 4.8e-9 | **Keep `PI`** (D3); correct the comment; the spec records the gap in its floor |
| **MA-6** | SmoothPeriod computed, unused (as the source) | — | **Record only;** kept for fidelity |
| **MA-7** | Only FAMA exported | — | **Fix:** `MAMACore(Price, FastLimit, SlowLimit, &fama, &period, &alpha, &phase)` returning MAMA; `MAMA()` a thin wrapper, callers unchanged (exact list set by stage 1 tooling) |
| **MA-8** | Header: unsourced / unreproducible claims ("APPROVED Week 7", lag 0, SNR, win rate, 92.5% clamp, sensitivity), and the "1.5*0 = 0 trap" (b: does not occur, the 6 floor acts) | Wrong text read later as fact | **Fix header:** source and page, formula, deviations fixed, this review's path, claims labelled or removed |
| **MA-9** | (record) Phase-wrap and Re-sign discontinuities | s5 ill-conditioned (1.05e-3 per ulp) | **Spec:** per-input conditioning classification (D7 rule 3) |

**FRAMA.c**

| # | Deviation | Impact (b) | Decision |
|---|---|---|---|
| **FR-1** | Parameter `T` = half window; source `N` = full window, default 16; callers pass T = 16 (N = 32) | Up to 9.9e-3 between N = 16 and N = 32 | **Fix: source convention `N`** (full, even). **Callers pass N = 32**, keeping the configuration Week 9 and the §1.2 slot choice were measured on. The spec tests N = 16 (source default) and N = 32 (slot). Which trades better is a backtest question |
| **FR-2** | Inputs fixed inside the function | Harness cannot feed synthetic inputs | **Fix:** `FRAMA(vars Price, vars High, vars Low, int N)`; callers pass `series((priceHigh() + priceLow())/2)`, `series(priceHigh())`, `series(priceLow())`. Clean signature change, no alias; stage 1 greps and updates callers (test scripts only: `Test_FRAMA_Laguerre_DSMA.c`, `Test_FRAMA_vs_MAMA.c`, `Test_UltimateChannelBands.c`) |
| **FR-3** | `static frama_prev`, `frama_init` shared by every call | Up to 3.3e-2, permanent | **Fix:** per-instance `series` state (Filt, Dimen, counter). Old file kept as `FRAMA_Superseded.c`, two instances = shared-state control |
| **FR-4** | Start-up: seed on first call, EMA from the second; source `Filt = Price` while CurrentBar < N + 1 | Up to 1.5e-2, memory up to 2750 bars | **Fix: follow the source** (per-instance counter); start-up is PASS/FAIL |
| **FR-5** | Guard: N3 <= 0 returns without update; no N1 / N2 condition (`log(0)` reachable) | Start-up only on step / stair / random walk; (c) never with real bars | **Fix: follow the source** (Dimen per-instance and held when any of N1, N2, N3 is 0; Filt always updated). Removes an untested branch |
| **FR-6** | float32 literals 4.6, .01 | <= 1.6e-10 | **Fix:** build from integers |
| **FR-7** | No exports | — | **Fix:** `FRAMACore(Price, High, Low, N, &dim, &alpha)` returning Filt; `FRAMA()` a thin wrapper |
| **FR-8** | Header: "default T=16", "alpha -> 0.01", Week 9 status | Wrong text | **Fix header;** record D <= 2 (the .01 floor never binds) and the D < 1 case for point bars |

**Locals prefixes (gotchas 1.3; proposal for stage 1, not decided here):** the current MAMA locals are unprefixed (`Smooth`, `Period`, ...)
and FRAMA uses `frama_`. Corrected and superseded files must be includable together in one generated script, so each needs its own prefix
(e.g. `ma_` / `mao_`, `fr_` / `fro_`); stage 1 checks them against gotchas 1.3 and adds them there. Callers use their own local prefix.

## 5. Dependencies

None for either file. FAMA is an output of MAMA, not a separate indicator: the Strategy 1 baseline (§1.2 "FAMA") is reviewed and tested as
MAMA's second output. (c) Whether the NNFX baseline signal is price vs FAMA or the MAMA / FAMA cross is a template decision (step 4),
from NNFX_Sources, not from this review.

## 6. Harness check family — D7, adaptive smoothers (decided 2026-11-20, user: as recommended)

Why D6 does not fit as is (b): the output is a price level (not normalised), so "invariance" becomes **equivariance**; there is no useful
linear stage (MAMA's 4-bar Smooth is the only one, and the trace covers it); both sources define the start-up but its memory is long
(FRAMA 2750 bars), so a warm-up cut W leaves too little; and MAMA's discontinuities have memory, so a per-row gate cannot contain a flip.

Rules (each spec states how they map to its indicator):
1. **Export the adaptation variables** (MAMA: alpha, Period, Phase; FRAMA: Dimen, alpha) and the outputs (MAMA, FAMA; FRAMA).
2. **Trace from row 1** against the source model, every exported column, on well-conditioned inputs; no W cut. Start-up is part of the trace
   and PASS/FAIL, because both sources define it (as LRS, D6 rule 6 refined).
3. **Conditioning per input, classified before the run** on the model: an input is checked only if a pre-registered 1-ulp perturbation set
   moves no exported column by more than a pre-registered bound over ALL rows; otherwise its trace is INFO. (b) MAMA (FAMA, all rows): flat
   fails (3.2e-2, start-up transient) and s5 fails (8.6e-3); ramp, s10-s100 pass (<= 6.7e-14). FRAMA: all pass (<= 4.4e-15).
   Classification is per exported column in the spec (only FAMA measured here).
4. **Exact bounds** on every row of every input: MAMA alpha in [SL, FL], Period <= 50; FRAMA alpha in [exp(-4.6), 1], Dimen <= 2, out within
   the running [min x, max x].
5. **Equivariance:** out(k x + c) = k out(x) + c and adaptation variables unchanged (scale and offset copies of a sine; Zorro-internal, no model).
6. **Known answers** where the source gives one: flat -> level (MAMA: rows >= 1000 only, (b) 4.4e-16; its trace is INFO under rule 3); FRAMA ramp with point bars -> out = x exactly. The MAMA ramp is a trace only.
7. **Multi-instance control:** each superseded file called as two instances must fail trace.
8. **No v1 linear checks** (gain / phase / ramp lag) for this family.
D2 (tolerance window, per-control detection), D5 (amendments) unchanged. The H / L inputs FRAMA needs (point bars H = L = x, and a band
x +- h) are a spec decision.

## 7. For the spec (not decided here)

- MAMA variants: (FL, SL) = (.5, .05) (slot); one other pair, e.g. (.3, .1), per the old header's sensitivity claim (to measure, not to trust).
- FRAMA variants: N = 16 and N = 32; H / L construction.
- Inputs: flat, ramp, sines T = 5, 10, 20, 40, 100; conditioning classification per rule 3; rows: all 3000.
- Controls (candidates): the superseded files as two instances (MA-3, FR-3); HT coefficient off in its third digit (.0962 -> .0963); FAMA
  alpha factor .5 -> .6; Period bound .67 -> .68; FRAMA exponent 4.6 -> 4.7; FRAMA window N vs N + 2 (needs T > N); FRAMA price-seed
  start-up (FR-4 old); MAMA price-seed start-up (MA-1 old); MA-2 series-default hold (needs a flat stretch to show).
- Floor: `PI` gap (MAMA, <= 4.8e-9 on checked inputs) plus IMP residual; FRAMA has no trig.

---

## Correction and spec-level decisions — 2026-11-20 (after `b7bdd69`, before any spec)

**C-1 (correction, b).** §3 states the MAMA ramp is well conditioned (6.7e-14 per ulp) and lists the flat value at rows >= 1000 only.
Both came from ONE perturbation draw. With five draws (`MAMA_FRAMA_STAGE1_NUMBERS.py`, seed 20261120, all rows) the ramp is
**ill-conditioned**: one ulp moves alpha by 0.45, Period by 9.2, Phase by 30.6 degrees, FAMA by 2.8e-4 (exact pi: FAMA 3.1e-4, alpha 0.45).
Flat: FAMA 3.2e-2, alpha 0.45 (zero-start transient). s5: FAMA 1.7e-2. s10-s100: every column <= 1.5e-10 (Phase, degrees), <= 2.3e-11
(alpha), <= 6.7e-13 (FAMA). Under D7 rule 3 the MAMA checked inputs are **s10, s20, s40, s100**; flat, ramp and s5 are INFO. §6 rule 6's
"flat -> level" for MAMA is therefore INFO as well. FRAMA: output well conditioned on every input (<= 5.8e-15); Dimen and alpha are
ill-conditioned on point-bar **flat** only (Dimen 2.0, alpha 0.99: rounding noise decides whether N3 > 0), INFO there.
**C-2 (b).** MAMA equivariance holds only after the start-up: the zero start does not map under x -> kx + c (last row off > 1e-9: <= 516 on
s20 / s40, both variants); from row 1000 the residual is <= 5.3e-11 (Phase) / 1.6e-14 (FAMA). FRAMA equivariance holds from row 1 (<= 8e-15).
**C-3 (b).** FRAMA Dimen can exceed 2 by rounding (2.0000000000000018 on band sines), so alpha can fall one ulp below exp(-4.6): bound
checks need the D6 relative allowance.

**Spec-level decisions (user, 2026-11-20: all as recommended):**
- **S1 — exact pi in MAMA (D3 exception, under D3's own rule).** With Zorro `PI` the floor on the checked sines is Phase 7.26e-5 deg,
  Period 4.33e-5, alpha 3.27e-6, larger than the float32-literal effect (Phase 8.8e-6, Period 5.9e-6), so MA-4 could never be seen by a run.
  Corrected MAMA builds pi at run time (`4*atan(1)`, D3's prescribed form); the old `PI` becomes control NCP. Output change <= 4.6e-8.
- **S2 — tolerances.** MAMA trace 1e-9 (MAMA, FAMA, alpha, Period), 1e-8 (Phase, degrees); FRAMA trace 1e-10 (out, Dimen, alpha).
  Rule-3 conditioning bound = tolerance / 10 per column.
- **S3 — MAMA variants** (FL, SL) = (.5, .05) (slot) and (.3, .1).
- **S4 — recorded, not invented:** the Period-bound control (.67 -> .68) has zero effect on every checked input (binds on the ramp only):
  INFO. MA-2 (hold on exact zeros) fires only on flat (INFO): verified by code review only, stated in the spec.
- **S5 — FRAMA bars:** point bars (H = L = x) AND band bars (H = x + h, L = x - h, h = 0.002, built from integers). Band ramp is a new known
  answer: D = log2(4 r1 / r3) constant, alpha constant, lag (1 - alpha)/alpha = 34.05274879969143 (N = 16) / 17.27287888639891 (N = 32).
