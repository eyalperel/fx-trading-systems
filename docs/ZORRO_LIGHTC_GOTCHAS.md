# Zorro Light-C — Standing Gotchas Reference

**Platform:** Zorro 2.70, Light-C
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
| 1.2 | `Period` is a reserved word | Compile error or unexpected behaviour | Use `BarPeriod`, or a prefixed local |
| 1.3 | 🔇 **Flat variable namespace across all included files** | Silent collision; one file overwrites another's local | Prefix every local: `rm_`, `rmo_`, `cc_`, `cyc_`, `ab_`, `mstc_` |
| 1.4 | `void run()`, not `function run()` | Compile error | — |

**Prefixes in use (do not reuse):**
`cc_` CyberCycle · `cyc_` CorrelationCycle · `rm_`/`rmo_` RecursiveMedian ·
`ab_` AlphaBetaFilter · `mstc_` MESAStochastic

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
