# ATR(14) — source review (definition for the NNFX template)

**Date:** 2026-11-21 (planning chat). **Status:** review complete; decisions taken (user, 2026-11-21: as recommended). No spec, no code yet.
**Replaces in the step-3 plan:** "stops (UltimateChannelBands, NATR)" (PROJECT_STATE §7). Reason in §1.
**Files reviewed:** none to correct. (b) The library has **no ATR indicator**: `grep -i natr` over `*.c` finds only `UltimateChannelBands.c`
(NATR is its out-parameter `pNATR`), `VolatilityRegime.c` (takes NATR as input) and `LaguerreOsc.c` (comment). A new file is written.
**Model:** every (b) number below is reproduced by `docs/harness/ATR_REVIEW_MODEL.py` (float64, independent of the harness tooling;
inputs level 1.1, sine amplitude 0.01, ramp slope 1e-4, 3000 bars; point bars H = L = C = x, band bars H = x + h, L = x - h, C = x, h = 1e-3).

Labels: (a) source states · (b) read or computed here · (c) inference.

---

## 1. What the template needs, from the NNFX sources (a)

`docs/sources/NNFX_Sources.md` (repo copy read 2026-11-21; same sections as the project copy):
- **ATR period 14, default settings**, read from completed candles; the entry-candle value is frozen for the whole trade
  (Part A §2.1 [V03, V11, V16]; Part B §1.4, §2.10 [M3, M13]).
- **Stop 1.5 x ATR** from entry (A §4 [V25]; B §2.1 [M3]; spot-checked against the transcripts, file line 8). 1.25 x ATR for gold and BTC is
  Dan's optional testing choice (V139, conflict K4).
- The same frozen ATR sets **TP1 (half at 1 x ATR)**, **trailing activation (close >= 2 x ATR)**, **trailing distance (1.5 x ATR)**,
  **position size (risk / 1.5 x ATR)** and the **1 x ATR baseline-distance entry rule** (A §3.2-3.3 [V28]; B §1.3, §2.5-2.11).
- **No channel or band stop** anywhere in the corpus. The one mention: Stonehill removes GChannel's stop lines "and uses NNFX stops" (C1 §3).

(c) So ATR(14) is on the first template's critical path (six rules), and UltimateChannelBands / NATR are not. NATR as coded is not ATR(14)
either: (b) `UltimateChannelBands.c` lines 115-130 compute `100 * UltimateSmootherE(TR, STRLength) / Close` (article STRLength 20), a percent
of a recursive smoother of TR. NATR / VolatilityRegime may matter later only as a volume / volatility slot candidate (step 4; that slot has no
candidate in §1.2 yet). **Decision (user, 2026-11-21):** UCB and NATR deferred, off the critical path.

## 2. Which ATR is "default settings" (a)

The sources fix the period, not the averaging. VP's indicator demos are MT4 (A §2.3 [V18], "Apply to: First Indicator's Data").

**MetaQuotes `ATR.mq4`, installed copy** (read 2026-11-21 from all four MT4 data folders on this machine,
`%APPDATA%/MetaQuotes/Terminal/{70CA…, A9D0…, BADF…, F952…}/MQL4/Indicators/ATR.mq4`; 3900 bytes each; sha256 prefixes
`134da529e0382b89` (two copies, "2000-2026") and `c5c680c466e7d87f` (two copies, "2000-2025"); the two differ only in the copyright year (b, diff)):

```
input int InpAtrPeriod=14;                                                      // line 16
ExtTRBuffer[0]=0.0;  ExtATRBuffer[0]=0.0;                                       // lines 76-77
for(i=1; i<rates_total; i++)
   ExtTRBuffer[i]=MathMax(high[i],close[i-1])-MathMin(low[i],close[i-1]);       // lines 79-80
for(i=1; i<=InpAtrPeriod; i++) { ExtATRBuffer[i]=0.0; firstValue+=ExtTRBuffer[i]; }   // lines 83-87
firstValue/=InpAtrPeriod;  ExtATRBuffer[InpAtrPeriod]=firstValue;                // lines 89-90
for(i=limit; i<rates_total; i++)                                                // limit = InpAtrPeriod+1
   ExtATRBuffer[i]=ExtATRBuffer[i-1]+(ExtTRBuffer[i]-ExtTRBuffer[i-InpAtrPeriod])/InpAtrPeriod;  // line 99
```

So: **TR = max(H, C[1]) - min(L, C[1])**; **ATR = simple 14-bar mean of TR**, kept as a running sum; **start-up:** output 0 on rows 0..13,
row 14 = mean of TR[1..14]; TR[0] (= 0, no previous close) never enters. Same code as quoted in an MQL5 forum thread (mql5.com/zh/forum/154784).
MetaQuotes' code-base page (mql5.com/en/code/7807) states only "a moving average of values of the true range".

**Zorro manual** (zorro-project.com/manual/en/ta.htm, read 2026-11-21): `ATR(n)` = (ATR1*(n-1) + TR)/n, recursive (Wilder's form);
`ATRS(n)` = "SMA of the TrueRange over the TimePeriod, using the current asset price series" (= MT4's definition); `TrueRange()` =
max(High[0],Close[1]) - min(Low[0],Close[1]) (= MT4's TR); `NATR(n)` = 100*ATR(n)/Close. ATR / ATRS read the current asset's prices.

**Caveat (c).** The installed file is MetaQuotes' published indicator source. It does not by itself prove that the terminal's compiled
built-in ATR (`iATR`, the Navigator's ATR) computes identically; only a value comparison on an MT4 chart would. Recorded, not blocking.

**Decision (user, 2026-11-21): template default = MT4 ATR(14)** (simple 14-bar mean of TR, MT4 start-up). Wilder's ATR is not the default;
if ever used it is a named, counted, pre-registered variant.

## 3. Behaviour — computed (b)

`ATR_REVIEW_MODEL.py`, items 1-6:

| # | Finding |
|---|---|
| 1 | Known answers, rows >= 14, all exact to float64 rounding (<= 2.2e-16): flat point bars 0; flat band bars 2h; point ramp up / down = slope; band ramp up / down = h + max(h, slope) (= 2h here). Rows 1..13 are 0 on every input |
| 2 | Start-up: ATR[14] = mean TR[1..14] = 2.107897511639391e-03 (s20, point); including TR[0] = 0 would give 2.006440710267819e-03 (4.8% lower): a start-up check sees an off-by-one window |
| 3 | Running-sum update vs direct 14-bar mean: <= 5.6e-17 over 3000 rows (ATR scale 4e-4..9e-3): rounding does not accumulate visibly here |
| 4 | SMA (MT4) vs Wilder (Zorro `ATR` form), rows >= 200, max relative difference: 1.9e-2 (s5) to 8.6e-1 (s100) on point bars; 1.7e-2..4.2e-2 on band bars, and **0 on s100 band**: there every per-bar move (<= 6.3e-4) is below h, so TR = 2h on every bar and the input cannot tell any average from another |
| 5 | Window-length error (14 vs 15), point bars, rows >= 200: 1.8e-5 (s100) to 3.0e-4 (s5) absolute, i.e. 2-8% of the ATR level: visible at every tested period |
| 6 | TR form max(H,C1) - min(L,C1) equals max(H-L, \|H-C1\|, \|L-C1\|) exactly on all inputs (band bars) |

(c) Consequences for the spec: band bars need h below the per-bar moves on at least some inputs (or point bars), or TR is constant and the
averaging is untested (finding 4); start-up is PASS/FAIL (the source defines it, as LRS / D7); no trig and no literal (only the integer
period), so no `PI` gap and no float32-literal risk in a correct file (gotchas 9d.1, 9d.8).

## 4. Deviations and decisions

| # | Item | Decision (user, 2026-11-21) |
|---|---|---|
| **AT-1** | No ATR file exists; NNFX needs ATR(14) | **New file** `indicators/ATR.c` or `indicators/ehlers/` sibling (location: stage 1 decides; it is not an Ehlers indicator): `ATR(vars High, vars Low, vars Close, int Length)` returning the MT4 ATR, plus `ATRCore(..., &tr)` exporting TR (D6 rule 1 style); inputs as parameters, never `priceHigh()` inside (lesson from FR-2, UCB) |
| **AT-2** | Averaging: MT4 SMA vs Zorro `ATR` (Wilder) | **MT4 SMA** (§2) |
| **AT-3** | Start-up | **Follow the source:** 0 on the instance's rows 0..Length-1, mean TR[1..Length] at row Length, running update after; per-instance call counter (gotchas 9d.9), no statics |
| **AT-4** | Running-sum form vs direct mean | **Running sum, as the source** (line 99); difference measured <= 5.6e-17 (finding 3) |
| **AT-5** | Zorro's own `ATRS(14)` | **Cross-check only, on real EUR/USD D1** (it reads the asset's prices, so the harness cannot feed it synthetic bars); its start-up is not stated in the manual, so compare after warm-up (c) |
| **AT-6** | UltimateChannelBands, NATR | **Deferred, off critical path** (§1); their own review later if a slot needs them |
| **AT-7** | iATR caveat (§2) | **Record only** |

## 5. Harness family

(c) ATR is a price-scale level with a moving-window average of a nonlinear input (TR). The nearest family is **D7** (adaptive smoothers): trace
from row 1 against the source model (start-up included), equivariance in scale (ATR(kx + c) = k ATR(x)), known answers (§3 item 1), every
exported column (TR, ATR). Bars inputs (point, band) exist from FRAMA. No adaptation variables, no conditioning issue expected (no division by a
data-dependent quantity; to confirm on the model per D7 rule 3). Whether this is "D7 applied" or a small D8 is a spec decision.

## 6. For the spec (not decided here)

- Variants: Length 14 (template); one other (e.g. 20) to show the window is a parameter, not a constant.
- Inputs: flat, ramp, rampdn, sines T = 5..100; point bars and band bars with h chosen so TR varies (finding 4); possibly bars with gaps
  (C[1] outside [L, H]) so all three TR branches are exercised.
- Controls (candidates): window 15 (finding 5); TR[0] included in the first mean (finding 2); Wilder averaging (finding 4); TR = H - L
  (no previous close); a shared static running sum (two instances); start-up seed = first TR instead of zeros.
- Floor: IMP residual only (no trig, no literal).
- Real-data cross-check (AT-5): our ATR vs Zorro `ATRS(14)` on EUR/USD D1, rows after warm-up; tolerance and row range pre-registered.
