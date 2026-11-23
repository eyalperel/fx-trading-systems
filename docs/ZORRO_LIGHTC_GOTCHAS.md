# Zorro Light-C — Standing Gotchas Reference

**Platform:** Zorro 3.11 (file version 3.1.1.2), Light-C. Sections 1–9c were found on
Zorro 2.70 and have **not** been re-verified on 3.11 (c). Section 9d was found on 3.11.
**Maintained since:** Week 1. Consolidated into this file Week 12 Day 6 (2026-08-06).
**Purpose:** Every one of these cost at least one debug cycle. Several were silent
failures that produced plausible-looking output. Consult before writing any new
indicator or test script.

> **Silent failures are marked 🔇.** These produce no error and no obvious symptom —
> the output simply looks fine and is wrong. They are the expensive ones.

---

## 1. Language subset limitations

Light-C is not full C. Constructs that compile elsewhere will fail here.

| # | Gotcha | Symptom | Fix |
|---|---|---|---|
| 1.1 | **No ternary operator `? :`** | `syntax error` at the line | Explicit `if`/`else` |
| 1.2 | `Period` is a reserved word | Compile error or unexpected behaviour | Use `BarPeriod`, or a prefixed local. (b, Zorro 3.11, H1 run 2) `int Period` as a function parameter compiles with no Error line. Not tested as a global or static name: keep avoiding it there (c). |
| 1.3 | 🔇 **Flat variable namespace across all included files** | Silent collision; one file overwrites another's local | Prefix every local: `rm_`, `rmo_`, `cc_`, `cyc_`, `ab_`, `mstc_`, `fi_` (FisherCore), `fto_` (FisherTransform_Superseded), `ift_` (Test_Fisher_IFT_COG), `ma_` (MAMACore), `maw_` (MAMA wrapper), `mao_` (MAMA_Superseded), `fr_` (FRAMACore), `frw_` (FRAMA wrapper), `fro_` (FRAMA_Superseded), `at_` (ATRMT4Core), `atw_` (ATRMT4 wrapper), `ats_` (ATR NCS body), `ax0_` / `axi_` / `axr_` / `axz_` (ATR control bodies NC0 / NCWi / NCR / NCZ), `pse_` (PROBE_SeriesExprLen), `xa_` (XCHK_ATRMT4_vs_ATRS), `tpc_` (TPL_Costs), `pat_` (PROBE_AssetType), `tsz_` (TPL_Sizing), `nxz_` (nx_size locals) |
| 1.4 | `void run()`, not `function run()` | Compile error | — |

**Prefixes in use (do not reuse):**
`cc_` CyberCycle · `cyc_` CorrelationCycle · `rm_`/`rmo_` RecursiveMedian ·
`ab_` AlphaBetaFilter · `mstc_` MESAStochastic · `fi_` FisherCore · `fto_` FisherTransform_Superseded · `ift_` Test_Fisher_IFT_COG ·
`ma_` MAMACore · `maw_` MAMA wrapper · `mao_` MAMA_Superseded · `fr_` FRAMACore · `frw_` FRAMA wrapper · `fro_` FRAMA_Superseded ·
`at_` ATRMT4Core · `atw_` ATRMT4 wrapper · `ats_` ATR NCS body · `ax0_`/`axi_`/`axr_`/`axz_` ATR control bodies NC0/NCWi/NCR/NCZ ·
`nx_` NNFX template config / state (`NNFX_Config.h`, `NNFX_Template.h`) · `nxs_` NNFX_Slots locals · `nxt_` NNFX_Template locals · `tp_` TPL_Probe · `tpe_` TPL_Equivalence · `tple_` its generated scenario include ·
`tpc_` TPL_Costs (its generated scenario include uses `tple_`) · `pat_` PROBE_AssetType ·
`tsz_` TPL_Sizing (include also `tple_`) · `nxz_` nx_size locals (NNFX_Template.h) ·
`pse_` PROBE_SeriesExprLen · `xa_` XCHK_ATRMT4_vs_ATRS

---

## 2. Trigonometry — RADIANS

> **Trig arguments are RADIANS.** Zorro Light-C uses the standard C math library.
> An earlier note in this project asserted degrees. **That was wrong** and caused a
> bug in Week 3, corrected May 2026 across four indicator files, with stale prose
> claims surviving until the Week 12 Day 6 sweep.

Ehlers publishes EasyLanguage in **degrees**. Every formula must be converted:

```
Ehlers (degrees)          Zorro Light-C (radians)
360 / Period       ->     2*PI / Period
1.414 * 180 / P    ->     1.414 * PI / P
0.707 * 360 / P    ->     0.707 * 2*PI / P
```

🔇 **The dangerous failure mode is a *mixed* file** — one coefficient converted and
another not. `exp(-1.414*PI/P)` alongside `cos(1.414*180/P)` yields plausible output
rather than obvious garbage. This defect was found in the roadmap's SuperSmoother
snippet on 2026-08-06.

**Legitimate degree usage:** converting `atan()` *output* to degrees (`*180/PI`) is
correct — e.g. MAMA's `Period = 360/arctan(Im/Re)` genuinely is a degree formula.
The rule is about trig *arguments*, not results.

### Verified reference values

Check any new implementation against these before trusting exported data:

| Filter | Formula | Value |
|---|---|---|
| One-pole, P=12, **no** 0.707 | `(cos(2π/P)+sin(2π/P)-1)/cos(2π/P)` | **0.422650** |
| Two-pole, P=30, **with** 0.707 | `(cos(0.707·2π/P)+sin(0.707·2π/P)-1)/cos(0.707·2π/P)` | **0.138102** |

🔇 **The 0.707 belongs only in two-pole cascades**, where it compensates for stacking
two identical poles. A single-pole filter must not have it. Two nearly identical alpha
formulas differing by one constant is a top-ranked bug source — print both on bar 1 and
compare against the table above.

---

## 3. Series, state, and call order

| # | Gotcha | Detail |
|---|---|---|
| 3.1 | 🔇 **`series()` allocates by CALL ORDER** | Two calls to the same function get two independent slots — correct — **but only if every call is unconditional and the sequence never varies between bars.** Never place a `series()`-using call inside an `if()`. |
| 3.2 | **IIR feedback state in included files needs `static`** | The `series()`-then-overwrite pattern is unreliable across file boundaries |
| 3.3 | 🔇 **Zero-initialised statics need explicit price seeding** | Otherwise the filter ramps from 0 to price level over the warmup, producing a huge startup transient. **See §9b.2** — seeding must be flag-based, not value-based, and **§9b.1**: a static that is never reset carries the previous run's state, which defeats the seed entirely |
| 3.4 | **Non-linear stages cannot use `series()` IIR patterns** | Medians, sorts, rank operations are order-dependent — needs explicit implementation |

**Worked example (Week 12):** `HighPassFilter` and `SuperSmoother2Pole` were each called
twice per bar — once inside `MESAStochastic` (via `RoofingFilter`), once inside
`RecursiveMedianOsc`. Correct, because both calls were unconditional and fixed in order.
One `if()` would have silently shuffled the slots.

---

## 4. Warmup and the LOOKBACK guard

| # | Gotcha | Detail |
|---|---|---|
| 4.1 | 🔇 **Compute ALL indicators BEFORE `if(is(LOOKBACK)) return;`** | Returning early starves IIR filters of warmup — they receive zero history |
| 4.2 | 🔇 **`LookBack` is auto-extended by Zorro** | Gating on `barCount == LookBack + 1` can never fire. Found Week 12: BTC/USD H4 extended 200 → 201 and the CSV header was silently omitted |
| 4.3 | `(int)Now` fails for bar dating | Use a `static int barCount` incremented each bar — **and reset it at `is(INITRUN)` (§9b.1)**. A stale counter means any warmup guard keyed to it never fires |

**Correct header pattern:**

```c
static int hdrWritten = 0;
if(!hdrWritten) {
    file_append("Data/output.csv", "col1,col2,col3\n", 0);
    hdrWritten = 1;
}
```

---

## 5. Includes and file structure

| # | Gotcha | Detail |
|---|---|---|
| 5.1 | `#include <default.c>` must be **first** | — |
| 5.2 | **Relative `#include` paths inside indicator files don't resolve** from strategy subfolders | Put all includes in the test script, in dependency order |
| 5.3 | **Light-C is single-pass** — dependency order matters | A function must be included before anything that calls it |
| 5.4 | Set `Asset =` explicitly in test scripts | Do not rely on inheritance. **A wrong name does not fail (§9b.3)** — guard on price magnitude instead |

**Worked dependency chain (Week 12):**

```
MESAStochastic -> RoofingFilter -> HighPassFilter + SuperSmoother2Pole
RecursiveMedian -> HighPassFilter

Required include order:
  HighPassFilter.c -> SuperSmoother2Pole.c -> RoofingFilter.c
  -> MESAStochastic.c -> RecursiveMedian.c
```

---

## 6. Price access and file output

| # | Gotcha | Detail |
|---|---|---|
| 6.1 | `High[]` / `Low[]` not directly accessible in included files | Use `series(priceHigh())` / `series(priceLow())` |
| 6.2 | Use `file_append(...)`, not `file_write` | `file_append("Data/f.csv", strf(...), 0)` |
| 6.3 | ⚠️ **`file_append` appends — delete the CSV before re-running** | Otherwise a second header lands mid-file and row counts are wrong |
| 6.4 | CSV exports go to `C:/zorro/Data/` | Path is relative to the Zorro install, not the repo |

---

## 7. Multiple-return-value pattern

Light-C has no tuples or structs in the usual sense. For an indicator returning several
values, use pointer out-parameters:

```c
void CorrelationCycle(vars Price, int Period,
                      var* pReal, var* pImag, var* pAngle)
{
    /* ... */
    *pReal = cyc_Real;
    *pImag = cyc_Imag;
    *pAngle = cyc_angle;
}

// Call site:
var ccReal, ccImag, ccAngle;
CorrelationCycle(Price, 20, &ccReal, &ccImag, &ccAngle);
```

Advantage: one pass, no recomputation, no shared state between outputs.

---

## 8. Debugging checklist

Before trusting any exported data from a new indicator:

1. **Print alpha values on bar 1** and compare against §2's reference table
2. **Check for NaN / inf** in the export before analysing
3. **Verify bounded outputs are bounded** (Pearson correlations in [−1,1], stochastics in [0,100])
4. **Verify a known analytic property** — for filters, ramp steady-state lag against theory
5. **Check the first and last rows** for startup transients (§3.3)
6. **Row count** — does it match expected bars minus lookback?

### Verify measurement instruments too

🔇 A method that fails on a case with a known answer will fail silently on the unknown
case. Week 12: first-difference cross-correlation reported **0.00 bars lag for an EMA
with analytic lag 1.50** — it would have produced confident nonsense.

**Standing rule: validate any measurement instrument against a known ground truth before
applying it to the quantity of interest.**

| Lag method | Pure 3-bar delay | EMA α=0.40 (true 1.50) | Verdict |
|---|---|---|---|
| First-difference cross-correlation | — | 0.00 | ⛔ Invalid |
| MSE-minimising shift | 3.00 ✅ | 0.94 | ⚠️ ~0.65× biased for smoothers |
| **Ramp steady-state** | 3.00 ✅ | 1.500 ✅ | ✅ Exact |

---

## 9. Non-platform algorithmic traps

Not Zorro-specific, but encountered in this project and worth the same vigilance.

**🔇 Sorting networks are order-dependent.** A 5-element median network with the
comparators in the wrong sequence returned a non-median on **12 of 120 permutations** —
~10% of bars silently corrupted, with a chart that looked entirely plausible.

Verified-correct 5-element network (Knuth, 9 comparators, optimal):

```
(a,b) (d,e) (c,e) (c,d) (b,e) (a,d) (a,c) (b,d) (b,c)   -> median is c
```

**Verification method — the 0-1 principle:** a comparator network that correctly sorts
all 2⁵ = 32 binary inputs provably sorts *all* inputs over any ordered type. 32 test
cases is a complete proof, not a sample.

---

## 9b. Run-scoped state, asset resolution, and quit()

Four defects found Week 13 Day 2 (2026-08-12). All four produced
plausible output and no error.

| # | Gotcha | Detail |
|---|---|---|
| 9b.1 | 🔇 **Statics persist for the lifetime of the LOADED script** | Not the run. Editing a source forces a recompile and zeroes them — so edit-and-rerun is safe, but a repeat [Test] press or Train→Test is not. Output depends on whether a recompile happened, which is not observable from the CSV. Reset every static on `is(INITRUN)`. |
| 9b.2 | 🔇 **Value-based seed guards cannot fire on stale state** | `if(prev == 0) prev = price;` tests "is state zero", not "is this a fresh run". Those coincide only by accident. Use an explicit `init` flag cleared at INITRUN. |
| 9b.3 | 🔇 **`asset()` is not a validity guard** | Zorro 2.70 emits `Warning 034: <name> not in asset list`, then runs anyway with an auto-created dummy asset and returns non-zero. Guard on the data instead — a price-range assertion catches a wrong instrument by magnitude. |
| 9b.4 | 🔇 **`quit()` completes the current bar before stopping** | It does not abort at the point of call. A bare `quit()` in a validation check still let one mislabelled row reach the CSV. Latch a flag and gate the write on it. |

Asset naming is inconsistent in `AssetsFix.csv`: FX uses a slash
(`EUR/USD`), crypto does not (`BTCUSD`). Writing `BTC/USD` by analogy
silently produced EUR/USD data under a BTC filename for five months.
History resolution strips the slash, so an unknown slashed name may
still load the right `.t6` file — making the failure even harder to
see once `AssetList` is pinned.

Reset to the DECLARED INITIALISER, not to zero. `Peak = 0.1` and
`SmoothCycle = 20` are chosen values; zeroing them changes behaviour
rather than preserving it. Reset only what genuinely persists — state
that is write-before-read every bar does not leak.

Standing rule: a guard that has never been seen to fire is not a
guard. Both guards added this session were tested by deliberately
breaking the input first. The `asset()` check failed that test.

---

## 9c. Measuring lag — which quantity, and with what input

Found Week 13 Day 3 (2026-08-13) while measuring Laguerre RSI for C-4.

| # | Gotcha | Detail |
|---|---|---|
| 9c.1 | ⚠️ **"Lag" means two different things** | A **ramp** input measures GROUP delay at DC. A **sine** cross-correlation measures PHASE delay at that sine's frequency. They converge at DC and diverge elsewhere. SuperSmoother P=20 is 4.039 by ramp and 4.3505 by sine at period 40 — both correct. Comparing across methods made a working harness look 7% in error. **Use the same method for candidate and reference.** |
| 9c.2 | 🔇 **The ramp method fails silently on bounded and rescaling indicators** | A stochastic asks where today sits between its own recent high and low; on a rising line today IS the high, so it reads 100 forever. Laguerre RSI pins at 1.0 for the same reason — all four stages stay ordered. The output is constant, no lag can be read, and nothing errors. Use a sine. |
| 9c.3 | ⚠️ **Search both lead and lag** | Oscillators respond to rate of change, which leads price by a quarter cycle. If the shift search starts at 0, a leading indicator reports a peak at exactly 0 — the boundary of the range, not the true peak. A peak at the edge of the search window is a signal the window is wrong. |
| 9c.4 | ⚠️ **A single-frequency lag does not predict the market-data relationship** | Sine at period 40 implied Laguerre RSI lags MESA Stochastic by 1.14 bars; market data shows it leads by 0.55-0.85. Opposite sign. A sine is one frequency, markets contain many, and filters behave differently across the range (Ehlers plots this for the Laguerre allpass elements, Cybernetic Analysis Fig 14.3). |

**Sine parameters.** Period 40 was used. Two failure modes it avoids: a cycle short
enough that the lag approaches half a cycle makes lead and lag indistinguishable,
and too few samples per cycle makes the peak location imprecise. Longer cycles are
safer still but yield fewer cycles per run.

**Sub-bar results are within measurement resolution.** Shifts come in whole bars;
the decimal comes from fitting a parabola through the peak and its two neighbours:

    offset = 0.5 * (y1 - y3) / (y1 - 2*y2 + y3)

A refined value below 1.0 bar should not be reported as a precise lead or lag.

**Read the peak's sharpness, not only its location.** A broad flat profile means
"essentially in phase" even when the maximum sits at a non-zero shift.

**Standing rule, extending section 8:** validate the harness against a known answer
before trusting it. SuperSmoother's analytic phase delay served here.

---

## 9d. Zorro 3.11 findings (H1, 2026-11-05)

Found building harness H1 for `SuperSmoother2Pole.c`. Runs: H1 run 1 (FAIL, input guards;
`analysis/harness/results/H1_SuperSmoother2Pole_20261105.csv`), H1 run 2 (PASS;
`..._20261105_run2.csv`), include probe (`strategies/tests/H1_IncludeProbe_BAD.c`).

| # | Gotcha | Evidence and fix |
|---|---|---|
| 9d.1 | 🔇 **Decimal literals are float32** | (b) run 1: `X[0] = 1.1` was exported as `1.100000023841858` (= float32(1.1)); the ramp slope `0.0001` fitted float32(1e-4) to 12 digits. **Fix:** build exact constants at run time from integers: `var c = 11; c = c / 10;`. (c) Compile-time folding of `11.0/10.0` may also be float32, hence the run-time form. Run 2 used this and passed the 1e-12 input guard (b). |
| 9d.2 | 🔇 **`PI` macro = 3.14159** | (b) `C:/Zorro/Include/trading.h:25` `#define PI 3.14159`. (b) The value actually used is float32(3.14159) = 3.141590118…, i.e. the filter behaves as if the period were larger by a factor 1 + 8.07e-7 (the decimal macro alone would give 8.4e-7). (b) Run 2 ramp-lag offsets from the exact-π value, full precision: +1.76e-6 / +2.50e-6 / +3.60e-6 / +5.43e-6 bars for P = 10 / 14 / 20 / 30. A Python recursion using P/(1−8.07e-7) reproduces them to the digits printed. The simpler estimate lag × 8.4e-7 (1.5e-6 / 2.3e-6 / 3.4e-6 / 5.3e-6) is within about 15% (b); lag is not exactly proportional to P. Every indicator using `PI` is affected; the effect is tiny (~1e-6 bars; ~1e-8 in filter output). Exact π: `var p = 4; p = p * atan(1);`. |
| 9d.3 | 🔇 **A missing `#include` is not fatal** | (b) Probe: `Error in line 11: Include file ... not found`, and the script **still ran**. **Rule:** every run, check the message window for any line starting with `Error`. A clean compile of a script that includes a file also shows that the relative path resolved (b, H1 run 2). |
| 9d.4 | ⚠️ **After `quit()` the EXITRUN branch did not visibly run** | (b) H1 runs 1 and 2: the EXITRUN `printf` never appeared; in run 2 the EXITRUN `file_append` marker file was never created. (c) Cause not proven: EXITRUN may not be called after `quit()`, or output at exit may be unavailable. **Rule:** write anything important BEFORE `quit()`. (b) Re-confirmed 2026-11-12, SS2F run 1: no EXIT `printf`, no marker file; no marker file from any run exists under `C:/Zorro` or the repo. The generator's EXITRUN printf + marker are dead code (PROJECT_STATE §4). |
| 9d.5 | ⚠️ **`Init` is `is(INITRUN)`** | (b) `C:/Zorro/include/variables.h:182` `#define Init is(INITRUN)`. An indicator's `if(Init)` branch runs only in the INITRUN call, never on the first bar. The "First bar" comments in `SuperSmoother2Pole.c` are misleading (comment only; the output is unaffected, H1 run 2). |
| 9d.6 | `series(x, n)` seeds with the first value | (b) Run 2 observations O1–O3: with `series(Price[0], 3)` the flat-input error was 0 from n = 0 for all 6 variants, and the ramp output starts at exactly x[0]. So no startup transient on a flat input. **Shown for these inputs only** (synthetic, `LookBack = 0`, INITRUN returning before any `series()` call) (c for other cases). (b) Addendum, FSH run 1 (2026-11-20): `series()` also pads with the first value for a caller-built input series read by `MaxVal` / `MinVal` (the Fisher window): the start-up rows of `FisherCore` equal the padded-window model to <= 8.9e-16, and `series(0, 2)` starts Value1 and Fish at 0. Same conditions as above (harness, `LookBack = 0`). |
| 9d.7 | `Warning 047: EUR/USD first bar on 2008-01-07` is harmless here | (b) Seen 2026-11-07 in the Zorro window of the generated H1 run (`GEN_H1_SuperSmoother2Pole`, StartDate 20080101, EndDate 20240101); the run completed with 3000 rows, no `Error` line, and 28/28 PASS. EUR/USD D1 history starts 2008-01-07, after StartDate. The harness exports the first 3000 bars fed, so the start date does not matter for it. (c) H1 run 2 likely showed the same warning: its raw file is byte-identical to the GEN run (sha256 e8ffc043…5a6f) and its StartDate is the same, but its message window was not recorded. Still check every run for lines starting with `Error`. |
| 9d.8 | 🔇 **A product of literals is folded at compile time to an unpredictable float32** | (b) Probe `strategies/tests/PROBE_LiteralEval_20261117.c` (commit ba54022, output `analysis/harness/results/PROBE_LiteralEval_20261117.csv`): `0.707*2.0*PI` (all literals; `PI` is a macro) compiles to the float32 value 4.44221019744873047, 3-4 float32 ulps from every standard rounding rule (float32 factors, double product then float32, exact pi). The same factors through a variable (`var k = 0.707; k*2.0*PI`) give 4.442208535 = float32(0.707) x float32(PI) in double, as modelled. Trig, division and the recursion are plain double. Effect: the old HighPassFilter.c alpha was 3.6e-7 (relative) off the model, which failed HP_ArticleFidelity run 1 on one IMP row (2.2e-7; a361e4b); fixed by measuring the constant (Amendment 2, e29febd), run 2 PASS (512781c). (b) `2.0*PI` folds to exactly 2 x float32(PI) (probe L16): predictable. (c) Rule of the fold unknown. **Rule:** never start an expression with two or more literals multiplied or divided together; start it with a variable (`var hp_k = sqrt(2.0)/2.0; hp_k*2.0*PI/P`), which keeps every step at run time and modellable. **Audit 2026-11-17** (grep, `indicators/ehlers/`): folded literal products remain in UltimateSmootherE.c:47-48 (`1.414 * PI`; **fixed 2026-11-18**, `ad8eae5`), DominantCycle.c:24,25,46,47 (`1.414 * PI`, `1.414 * 180`), InstantTrendline.c:63 (`360.0 / 10.0 * PI / 180.0`). Each spec replaces them (D1 rule 1 turns 1.414 into sqrt(2) anyway); a probe value is needed only if the old file is kept as a control. **Addendum 2026-11-17 (RFF run 1; inference (c), not probed):** control bodies containing `1.0 / 1000` replayed at 7.4e-13 / 3.5e-12 (NCA / NCB) vs ~1e-15 for every other variant, consistent with `1.0 / 1000` folded to float32(0.001) (4.7e-11 relative): a literal *division* likely folds too. Build such constants from a variable (`var k = 1; k = k / 1000;`). |
| 9d.9 | 🔇 **`Bar` is a global bar count, not a per-call count** | (a) EasyLanguage start-up rules (`If CurrentBar < 4 Then X = Price`) count calls of THAT function instance from 1. (b, UltimateSmootherE review 2026-11-18) The old `if(Bar < 4)` was off by one if `Bar` is 0-based (its comment said "4 bars"; the source seeds 3), and for any instance first called after bar 0 (a later-starting input, a second instance) it seeds the wrong bars. **Fix:** a per-instance counter, called unconditionally before any early return: `vars xx_n = series(0, 2); xx_n[0] = xx_n[1] + 1;` then `if(xx_n[0] < 4)`. (b) USE run 1 (`41c8d76`): it starts at 1 on each instance's first call — real start-up rows match the 3-bar rule within 1.5e-8; a 4-bar seed differs by 8.3e-4 on a sine. (b) A 3- vs 4-bar seed is invisible on flat and ramp inputs: test start-up on a sine. Shown for harness conditions (LookBack = 0, INITRUN returning before any `series()` call). |
| 9d.10 | ⚠️ **OPEN: length of a `series()` without a length under `LookBack = 0`** | (c) Unprobed. The generated harness scripts run with `LookBack = 0`, where the default length of `series(x)` is not known here, and `MAMA_Superseded.c` / `FRAMA_Superseded.c` call it without a length. (b) With explicit lengths (`series(x, 7)` in `MAMA_Superseded.c`, A1.2) the NCS / NCS2 replays agree with Zorro to <= 4.5e-14 (MAMA) and <= 1.0e-13 (FRAMA), MAF run 1. **Rule until probed:** always give a length in harness-run code, larger than the largest index read. |
| 9d.11 | 🔇 **Trade fields `TradeStopLimit`, `TradeProfitLimit`, `TradeProfit` are 4-byte `float`; printed with `%f` in `strf` they come out as garbage** | (b) TPL_Probe run 3 (2026-11-22): stop 0.0084375 and profit 0 printed for open and closed trades. (a) `include/trading.h`: `float fStopLimit; float fProfitLimit;`; `variables.h`: `#define TradeStopLimit g->tr->fStopLimit`. | Cast every float trade field: `strf("%.15f", (var)TradeStopLimit)`. `TradePriceOpen` / `TradePriceClose` printed correctly. |
| 9d.12 | 🔇 **Without the `TICKS` flag a trade cannot exit on its entry bar** | (a) mode.htm: without TICKS "an intra-bar approximation is used ... a stop loss is always triggered earlier than a profit target ... TICKS should be used when trades enter and exit at the same bar". (b) TPL_Probe run 3: Fill = 3 entries filled on the 03-08 bar whose low went through the stop and high through the target; neither fired. | `set(TICKS)` in INITRUN when entry-bar exits matter (NNFX template: `nx_TicksOn`, T5 amendment). |
| 9d.13 | **Synthetic history: one unsplit `.t6` file per asset loads; a year-split file of daily records is rejected; do not mix with year-split M1 assets** | (b) TPL_Probe runs 1-2 (2026-11-22): unsplit `SYN_A2.t6` loaded; `SYN_A2_2024.t6` gave `Error 047: SYN_A2 no 2024 history`; year-split M1 EUR/USD gave the same error after an unsplit synthetic asset. (a) errors.htm, Error 047: "Don't use ... a part of the data split into years and another part not". (c) cause of the year-split rejection not established. | Synthetic assets: unsplit file, never in the same script as real year-split history. |
| 9d.14 | **The first bar of a test is a partial bar ending at the first record** | (b) TPL_Probe runs 1 and 3: bar 0 stamped one minute before the first record; with no warm-up the first records fell into it and a scenario signal was lost. | Synthetic scenarios get neutral warm-up bars (`tools/make_scenarios.py`, PAD_BARS = 5). |
| 9d.15 | **Open trades are closed at the first tick of the asset's last day of history** | (b) TPL_Probe runs 3-6 (2026-11-22): every trade still open when an asset's history ended was sold on the first tick of its final history day (A3 12 s after entry; A2 / P1 on the first Monday tick); with 5 trailing bars the scenarios completed as predicted (run 6). (c) Zorro closes the asset's trades at the start of its final history bar. | Synthetic scenarios carry trailing bars; trades closed this way (reason "end") are compared on entry only. |
| 9d.16 | 🔇 **The trading week is counted in the BarZone: with `BarZone = EST` the default week starts Sunday 23:00 New York** | (a) `StartWeek` default 72300 = Sunday 23:00 local BarZone time; `BR_WEEKEND` (default) stops trading between EndWeek and StartWeek "even when they contain price quotes" (date.htm, barmode.htm). (b) S4 run 1 (2026-11-23): every Monday-open fill at Monday 03:00 UTC (the synthetic day's low / high), 10 scenarios failed; real EUR/USD opens Sunday 17:01-17:09 New York. | `StartWeek = 71700` before the first asset call (M-D6, `nx_StartWeek`). |
| 9d.17 | 🔇 **Bars are created only where the first asset has prices** | (a) "If that flag [BR_FLAT] is not set, bars are only created where the first asset has valid prices" (barmode.htm). (b) S4 run 1: all 64 synthetic assets stopped at the first asset's last day (2024-03-18); longer scenarios lost their last bars, no error. | Multi-asset synthetic batches: one common last day for every asset (`make_scenarios.py` refuses otherwise). Real portfolios: put the asset with the fullest history first, or decide on BR_FLAT. |
| 9d.18 | 🔇 **Only real currency-pair names are Forex for `assetType()`; other assets are costed per contract** | (a) asset.htm: Forex if the name "begins and ends with the 3-letter abbreviation of a currency"; spread.htm: commission and rollover per 10000 units for currencies, per contract otherwise. (b) PROBE_AssetType (2026-11-23): EUR/USD, EURUSD = 1; EUR_A10_USD, EUR_USD, XTS/XXX, EUR/XTS, ABC/DEF = 0; GER30 = 2, SYN_A2 = 0. P5 run 1: names like EUR_A10_USD got commission 1000 instead of 0.1 per half, no error. | Synthetic cost tests use real pair names with a separate file suffix (`History = "*syn.t6"`), never the real files; log `assetType()` as a guard. |
| 9d.19 | **Spread: every half pays one spread against its own recorded fill; a long's take-profit triggers at about bid = level; rollover day = bar day** | (b) P5 run 2 (2026-11-23, M-D7 wording correction): the cost identity holds for every half, long TP1 included (32 halves, within 5.5e-7): each pays exactly one spread against its recorded fill. What differs is the trigger: a long's take-profit fills at about bid = level, so its recorded (ask) exit is one spread above the level and its result equals the TP distance. (b) P5 run 1, costs off vs on on identical paths: long stop / breakeven / trail / market exits and all short exits lost exactly one spread vs the cost-free run; long TP1 halves lost none (same trigger effect); short levels measured from the ask entry; rollover charged per bar day (17:00 New York with M-D1), Saturday and Sunday included, after 12 h open. (a) stop.htm says every limit is checked against the ask; the long-TP trigger contradicts that wording. | Accepted (M-D7). Check costs against each half's own fill, not against the level. Count long TP1 halves in every real-data run. |

---

## 10. Change log

| Date | Change |
|---|---|
| 2026-08-06 | File created; gotchas consolidated from scattered notes across `docs/` |
| 2026-08-06 | Added §1.1 no ternary operator (Week 12 Day 5) |
| 2026-08-06 | Added §4.2 LookBack auto-extension (Week 12 Day 3) |
| 2026-08-06 | Added §8 instrument-validation rule (Week 12 Day 3) |
| 2026-08-06 | Added §9 sorting network verification (Week 12 Day 3) |
| 2026-05 | Radians correction applied to four indicator files; prose lagged until 2026-08-06 |
| 2026-08-12 | Added §9b: static run-scope, seed guards, asset() unreliability, quit() timing (Week 13 Day 2) |
| 2026-08-13 | Added §9c: group vs phase delay, ramp failure on bounded indicators, lead/lag search (Week 13 Day 3) |
| 2026-11-05 | Added §9d: Zorro 3.11 findings from H1 (float32 literals, PI macro, missing include not fatal, EXITRUN after quit, Init, series seeding); platform line updated to 3.11, §1–9c not re-verified on 3.11 |
| 2026-11-07 | Added §9d.7: Warning 047 (EUR/USD D1 history starts 2008-01-07, after StartDate) is harmless for the harness (stage 4 run) |
| 2026-11-17 | Added §9d.8: compile-time folding of literal products to an unpredictable float32 (probe ba54022; HP run 1 FAIL / run 2 PASS); library audit of remaining literal products |
| 2026-11-17 | §9d.8 addendum: literal division `1.0 / 1000` likely folded too (RFF run 1 IMP residuals; inference, not probed) |
| 2026-11-18 | Added §9d.9: `Bar` is global — a per-instance CurrentBar counter for EasyLanguage start-up rules (USE run 1) |
| 2026-11-20 | §9d.6 addendum (b): FSH run 1 confirms `series()` first-value padding for a caller-built input series read by MaxVal / MinVal (start-up <= 8.9e-16) |
| 2026-11-20 | §1.3: prefixes `fi_` (FisherCore), `fto_` (FisherTransform_Superseded), `ift_` (Test_Fisher_IFT_COG) added to those in use |
| 2026-11-20 | §1.3: prefixes `ma_` (MAMACore), `maw_` (MAMA wrapper), `mao_` (MAMA_Superseded), `fr_` (FRAMACore), `frw_` (FRAMA wrapper), `fro_` (FRAMA_Superseded) added to those in use (MAF stage 2) |
| 2026-11-21 | §9d.10 (open): length of a `series()` without a length under `LookBack = 0` unprobed; give explicit lengths in harness-run code (MAF run 1) |
| 2026-11-22 | §1.3: prefixes `at_` (ATRMT4Core), `atw_` (ATRMT4 wrapper), `ats_` (ATR NCS body), `ax0_` / `axi_` / `axr_` / `axz_` (ATR control bodies), `pse_` (PROBE_SeriesExprLen), `xa_` (XCHK_ATRMT4_vs_ATRS) added to those in use (ATR stage 2) |
| 2026-11-22 | Added §9d.11-9d.14 (TPL_Probe runs 1-3: float trade fields in strf, TICKS and entry-bar exits, synthetic history naming, partial first bar); §1.3 prefixes `nx_`, `tp_` |
| 2026-11-22 | Added §9d.15: open trades closed at the first tick of the asset's last history day (TPL_Probe runs 3-6) |
| 2026-11-22 | §9d.12 addendum: with TICKS, the fill is the price of the record that crosses the level (run 4: 0.98450 for a 0.98500 stop); on fine paths the fill lands on the level (run 6). `assetAdd(..., Spread 0, ...)` left a 0.0100 spread; set `Spread = 0;` after `asset()` (run 4-5) |
| 2026-11-22 | §1.4 note (b): on Zorro 3.11 `function run()` compiled and ran (TPL_Probe runs 1-6, no Error line); the §1.4 rule dates from 2.70. `void run()` remains the project convention |
| 2026-11-23 | §1.3: prefixes `nxs_`, `nxt_`, `tpe_`, `tple_` (template S3 / S4). Reason seen in the first draft: a local `g` shadows Zorro's global `g` used by every trade macro (`TradeInt` = `g->tr->...`) |
| 2026-11-23 | Added §9d.16 (trading week in BarZone; StartWeek) and §9d.17 (bars follow the first asset) from S4 run 1 |
| 2026-11-23 | Added §9d.18 (assetType: only real pair names are Forex) and §9d.19 (spread on long TP exits, rollover day) from P5 run 1 and PROBE_AssetType |
| 2026-11-23 | §1.3: prefixes `tpc_` (TPL_Costs), `pat_` (PROBE_AssetType). §9d.19 reworded to the M-D7 correction (P5 run 2): every half pays one spread against its own fill; a long TP triggers at about bid = level |
| 2026-11-23 | §1.3: prefixes `tsz_` (TPL_Sizing), `nxz_` (nx_size locals in NNFX_Template.h), P6 |
