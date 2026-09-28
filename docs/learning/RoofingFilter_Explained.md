# The Roofing Filter — In Plain Words

**Written:** 2026-09-28, Week 14 Session 1 part 4
**Run it:** `python docs/learning/roofing_playground.py` — every number below
that is not marked *(real CSV)* is printed by that script, and you can change the
parameters at the top. Manual: `RoofingFilter_Playground_Manual.md`.

**What this is.** My own explanation of the roofing filter, built by working
through it rather than reading it. I could not recall what a roofing filter was
at the start of the sitting; everything here was reconstructed from the two
pieces reviewed in part 3. The wrong turns are kept in. For status, evidence and
gaps, see `docs/indicators/HighPass_RoofingFilter_Notes.md`. Read
`HighPass_Explained.md` first — this builds on it.

> **One constant to know about.** `SuperSmoother2Pole.c` uses `sqrt(2)`; Ehlers'
> published code uses `1.414`. The sitting's live figures used 1.414, this file
> and the script use sqrt(2), so a few numbers differ from the chat in the 4th
> decimal (e.g. 0.890022 → 0.890038). Nothing else changes.

---

# Part 1 — What the filter does

## 1. What is it? — built from two pieces

> **What is a roofing filter, and why does the library need one?**

**What I said:** I don't remember. (Logged as GAP-1.29.)

So we built it. A made-up price made of three known ingredients:

| ingredient | what it is |
|---|---|
| **A** | slow drift, +0.05 per bar — effectively an infinite period |
| **B** | a clean 20-bar cycle, amplitude 2 |
| **C** | 2-bar jitter, +0.4, −0.4, +0.4, … |

Asked what survives each filter, I guessed:

| | high-pass (48) | SuperSmoother (10) |
|---|---|---|
| A drift | not sure | almost all |
| **B 20-bar** | **almost nothing** | **about half** |
| C jitter | almost all | almost nothing |

Then, asked what the two parameters *mean*, I said: HP(48) passes periods
shorter than ~48, SS(10) passes periods longer than ~10. **That rule is right,
and it contradicts both of my row-B guesses.** A 20-bar cycle is shorter than 48
and longer than 10, so it should get through both. I had the rule and did not
apply it.

Measured (section `ingredients`):

| | HP(48) | SS(10) |
|---|---|---|
| A drift | **0.0000** | 1.0000 |
| B 20-bar | **0.9213** | **0.9661** |
| C jitter | 1.0000 | **0.0000** |

Two of those are exact, not approximate:

- **A through HP = 0.** A straight line has zero second difference — the same
  fact that gives `UltimateSmootherE` its 0.0000 lag on a ramp.
- **C through SS = 0.** The SuperSmoother's input side is `(P + P[1]) / 2`. At
  period 2, consecutive bars are equal and opposite, so the average is zero
  before any feedback runs.

**B is the only thing that gets through both, nearly intact.** The drift dies in
the first filter, the jitter in the second.

## 2. Two filters in a row multiply

> **Run A + B + C through the high-pass, then feed that into the SuperSmoother.
> What comes out?**

**What I said:** A is rejected by the HP, C by the SS, about 90% of B is left.
And 0.9213 × 0.9661 ≈ 0.890. **Right.**

Checked (section `cascade`): predicted amplitude 2 × 0.890038 = **1.780076**,
measured **1.780076**. After removing the 20-bar sine, what is left is
1.9 × 10⁻¹³ — nothing.

So the whole filter's gain at each period is the **product** of the two:

| period | HP(48) | SS(10) | product |
|---|---|---|---|
| 2 | 1.0000 | 0.0000 | **0.0000** |
| 5 | 0.9960 | 0.2242 | 0.2233 |
| 10 | 0.9801 | 0.6951 | 0.6812 |
| 16 | 0.9486 | 0.9254 | 0.8778 |
| **20** | 0.9213 | 0.9661 | **0.8900** |
| 30 | 0.8374 | 0.9921 | 0.8308 |
| 48 | 0.6671 | 0.9983 | 0.6659 |
| 120 | 0.2423 | 0.9999 | 0.2423 |
| ∞ | 0.0000 | 1.0000 | **0.0000** |

Zero at both ends, a hump in the middle. Peak at **19.15 bars** (gain 0.8907).
Half-power band **10.40 to 43.57 bars**.

Neither filter does this alone. The high-pass rises forever toward the fast
end; the SuperSmoother rises forever toward the slow end. Multiplied, each one's
rising side is cut off by the other's falling side. **What is left is a window.**

Ehlers' own words for it (*Predictive And Successful Indicators*, TASC 2014):
it puts "a roof over the data spectrum" so the data is preprocessed for any
indicator that follows. His two design reasons: the fast side rejects
**aliasing noise**, and the second-order slow side removes **spectral
dilation** (bigger swings at longer periods).

> **The parameter is not the corner.** HPPeriod=48 puts the high-pass half-power
> point at **43.74** bars. SSPeriod=10 puts the SuperSmoother's at **10.17**, and
> its gain at exactly period 10 is 0.6951, not 0.7071.

## 3. The trap: reading gain off the output

> **A 2-bar average fed a period-4 sine of amplitude 1 outputs samples of
> +0.5, +0.5, −0.5, −0.5. Is its gain 0.5?**

**What I said:** yes.

**It is 0.707.** The inputs, `sin(πt/2)`:

| t | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| x | 0 | +1 | 0 | −1 | 0 |

    y[1] = (x[1] + x[0])/2 = (+1 + 0)/2 = +0.5
    y[2] = (x[2] + x[1])/2 = ( 0 + 1)/2 = +0.5
    y[3] = (x[3] + x[2])/2 = (−1 + 0)/2 = −0.5

Those samples are a sine of amplitude **0.707** whose peak falls at t = 1.5 —
between two bars. The filter shifted the wave half a bar (its lag) as well as
shrinking it, and no sample lands on the peak:

    half a bar out of a 4-bar period = 1/8 of a cycle = 45°
    sample = 0.707107 × cos(45°) = 0.707107 × 0.707107 = 0.5

**A filter changes size and timing together. A sample value mixes the two.**

Claude fell into this twice in the same sitting: a gain table measured by
driving sines and taking (max − min)/2 gave a nonsense high-pass curve and 0.0000
at period 2 (a period-2 *sine* is zero at every integer bar — it was fed
silence), and the cascade check first read 1.7775 instead of 1.780.

**The fix — compute gain from the coefficients, with no input at all.** Write
the filter as numerator and denominator lists, set `z = e^(−j·2π/P)`:

    gain(P) = |num[0] + num[1]·z + num[2]·z²| / |den[0] + den[1]·z + den[2]·z²|

For the 2-bar average at P = 4: z = −j, so |0.5 − 0.5j| = √0.5 = **0.707107**. ✓

## 4. The period-20 gains by hand

Section `byhand` prints every line below.

    ω = 2π/20 = 0.3141593
    z  = 0.9510565 − 0.3090170j
    z² = 0.8090170 − 0.5877853j

**High-pass, HPPeriod = 48.** `num = [c, −2c, c]`, `den = [1, −2b, b²]`,
alpha1 = 0.088513, c = 0.9134452, b = 0.911487, 2b = 1.822973, b² = 0.8308077.

    1 − 2z + z²   real: 1 − 1.9021130 + 0.8090170 = −0.0930960
                  imag:   + 0.6180340 − 0.5877853 = +0.0302487
                  size: √(0.0930960² + 0.0302487²) = 0.0978870
    |num| = 0.9134452 × 0.0978870 = 0.0894144

    1 − 2b·z + b²·z²   real: 1 − 1.7337504 + 0.6721375 = −0.0616129
                       imag:   + 0.5633298 − 0.4883367 = +0.0749931
                       |den| = 0.0970573

    gain = 0.0894144 / 0.0970573 = 0.921254

**SuperSmoother, Period = 10.** `num = [c1/2, c1/2]`, `den = [1, −c2, −c3]`,
c1/2 = 0.1265974, c2 = 1.158046, c3 = −0.411241.

    |1 + z| = 2·cos(ω/2) = 1.9753767          (shortcut)
    |num| = 0.1265974 × 1.9753767 = 0.2500776

    1 − c2·z − c3·z²   real = +0.2313336, imag = +0.1161346
                       |den| = 0.2588484

    gain = 0.2500776 / 0.2588484 = 0.966116

**Product:** 0.921254 × 0.966116 = **0.890038**.

> **Sign trap.** c3 is stored negative, and the denominator is `1 − c2·z −
> c3·z²`, so the c3 term comes out **positive**. Get it backwards and you get a
> plausible wrong number.

This is a check that runs from the `.c` file alone and would catch a wrong
coefficient. No test in the repo does that today.

## 5. Where do 48 and 10 come from?

> **What would you need to know about EUR/USD to justify SSPeriod = 10 over 6 or
> 16?**

**What I said:** 6 lets in more noise, 16 cuts slow periods that might be signal
— it's a trade-off. **Right, and incomplete:** a trade-off has an optimum only
*given something*. I did not know what.

The concrete case that got me there: suppose EUR/USD had **no energy at all**
between 10 and 48 bars. The roofing output would be nearly empty. **What I
said:** either the choice was not smart, or EUR/USD has no strong signal in that
band. **Exactly — and you cannot tell those apart from the output.** Only a
measurement of the *input* separates them: its **spectrum**, how much energy sits
at each period.

That measurement already exists. The Cycle Premise null test (Week 11) found **no
peak** on EUR/USD D1 — the real data sat at the 8th percentile for peak
prominence, flatter than noise. So on this asset, 48 and 10 **cannot** be
justified by matching a dominant cycle.

**What they are:** Ehlers' published values. The source is *Predictive And
Successful Indicators* (TASC V.32:1, 2014, code © 2013), which hard-codes 48 and
10. That is a citation, not a measurement.

- HPPeriod=48 → already logged as **GAP-1.24**.
- SSPeriod=10 → same position, never flagged → **GAP-1.30**.
- `RoofingFilter.c` cites "Optimal Detrending". The project's PDF is *Optimum
  Detrending* (1992), a different design. → **GAP-1.31**.

## 6. The header's four claims

`RoofingFilter.c` says:

1. HP removes trend (periods > HPPeriod)
2. SS removes noise (periods < SSPeriod)
3. Result: only dominant cycle survives
4. HPPeriod must be >> SSPeriod to avoid collapsing the passband to nothing

**What I said:** all four supported. **Three were wrong as written, one partly.**

**Claims 1 and 2 — "removes".** HP(48) at period 80 passes **0.4186**. SS(10) at
period 8 passes **0.5244**. Half the "removed" thing gets through. The honest
word is *attenuates, gradually*. Only at the very edge is "removes" fair: SS at
period 2 is exactly zero.

**Claim 3 — "only dominant cycle survives".** This is the important one. Next
section.

**Claim 4 — "collapses to nothing".** Before running it I said: not nothing, but
the band idea is lost. **Right.** Section `collapse`:

| HP/SS | peak gain | half-power band |
|---|---|---|
| 1.0 | 0.4778 | none |
| 1.5 | 0.6237 | none |
| 2.0 | 0.7131 | 12.99 to 15.65 |
| 3.0 | 0.8126 | 10.85 to 26.82 |
| 4.8 | 0.8907 | 10.40 to 43.57 |
| 8.0 | 0.9411 | 10.25 to 72.79 |

No cliff. The band shrinks and sinks smoothly, and first appears between ratio
1.5 and 2.

> **All four claims describe a slope as a wall.** "Removes", "only", "collapses
> to nothing". Same shape as the one-number-for-a-trade-off pattern the review
> keeps finding.

## 7. No cycle in, cycle out

> **Feed the roofing filter a coin-flip walk — each bar +1 or −1, nothing else.
> Is there a cycle in the recipe?**

**What I said:** no, every bar is independent. **Right.**

Section `coinflip` shows 60 bars of the output. It stays positive a while, then
negative, then positive — same-sign stretches of **5, 8, 13, 7, 18, 9** bars —
rising to crests and falling to troughs. Shown without a label, anyone would say
"a cycle of roughly 15–25 bars."

> **The input had none of it and the output is full of it. What made it?**

**What I said:** not sure — a mixture of perceived cycles from the +1s and −1s?

That was the right idea, unfinished. Narrowed: a coin-flip walk can be written as
a blend of wiggles of **every** length (Fourier). The filter keeps the 10–44 bar
slice and throws the rest away. Asked which of a 3-, 20- or 200-bar wiggle is
left: **the 20.** So the output **has to** swing on a ~20-bar rhythm, whatever
went in.

> **The filter does not find the cycle. It makes it**, by discarding everything
> outside the window. The uneven stretch lengths are the leftover randomness —
> the window is wide, so the rhythm wanders.

Claim 3 is therefore **contradicted**: output of this shape says nothing about
whether a cycle was in the input. This is Slutsky (1937), cited in the Cycle
Premise doc, rebuilt by hand.

**White versus red.** My picture was white light — every colour equal. A coin
flip's *steps* are white. The *walk* adds them up, which piles energy into long
periods: it is red (the roadmap measured f^−1.848 for a synthetic walk). Same
window, different input colour, different rhythm:

| input | output zero-crossing period |
|---|---|
| white (the steps) | 10.75 bars |
| red (the walk) | 23.24 bars |

Red input loads the slow side of the window, so the rhythm stretches. The
direction is explained; the exact numbers are not derived.

> **Claude's wrong turn.** Seeing the roofing peak at 19.15 bars next to the null
> test's "pipeline fingerprint" (19.51 EUR/USD, 19.81 BTC, 20.40 Brownian), Claude
> was about to call it a confirmation. The run above killed it: the **gain peak**
> belongs to the filter; the **zero-crossing period** belongs to filter × input.
> The null test's three numbers cluster because its three inputs share a spectral
> slope, not because the filter ignores its input. (And that test ran roofing →
> CyberCycle, a different chain, so the numbers are not directly comparable.)

---

# Part 2 — The code, the test, and the data

## 8. What the SuperSmoother is seeded with

`RoofingFilter.c` is three working lines:

    var* hp = series(HighPassFilter(Price, HPPeriod), 3);
    var roofed = SuperSmoother2Pole(hp, SSPeriod);
    return roofed;

`SuperSmoother2Pole` starts its memory at the **first value of whatever it is
given**. Here it is given `hp`.

> **What is the first value of `hp`?**

**What I said:** don't know. Built by hand — flat price 100, made-up b = 0.9,
memory seeded at price level as part 3 found:

| piece | value |
|---|---|
| second difference 100 − 200 + 100 | 0 |
| c × that | 0 |
| 2b · 100 | 180 |
| b² · 100 | 81 |
| **first HP output** | **99** |

Nearly the price, not zero. With the real b on EUR/USD at 1.10:

    2b·P0 − b²·P0 = 1.822973 × 1.10 − 0.830808 × 1.10 = 1.091382

So the roofing filter **also starts at ~1.09**, for an output whose normal size is
around 0.001.

## 9. Why a repeated pole fades so slowly

Section `seed`, flat price 1.10:

| bar | roofing | part 3's estimate `0.911487^bar × 1.10` |
|---|---|---|
| 0 | 1.09138 | 1.10000 |
| 10 | 0.85296 | 0.43541 |
| 30 | 0.26378 | 0.06822 |
| 50 | 0.06172 | 0.01069 |
| 75 | 0.00860 | 0.00105 |

Below 1% of the seed only at **bar 72**. Part 3 wrote that about 0.068 survives
at bar 30. The high-pass itself is at **0.2328** — **3.4× larger**. (GAP-1.32.)

> **Why would a repeated pole fade more slowly than a single one?**

**What I said:** not sure. Built from a smaller case. A repeated pole `(z − b)²`
is the same as **two one-pole filters in a row**. With b = 0.5 and one kick:

| bar | stage 1 = 0.5 × prev + input | stage 2 = 0.5 × prev + stage 1 | stage 2 ÷ stage 1 |
|---|---|---|---|
| 0 | 1 | 1 | 1 |
| 1 | 0.5 | 0.5 × 1 + 0.5 = **1** | 2 |
| 2 | 0.25 | 0.5 × 1 + 0.25 = **0.75** | 3 |
| 3 | 0.125 | 0.5 × 0.75 + 0.125 = **0.5** | 4 |
| 4 | 0.0625 | 0.5 × 0.5 + 0.0625 = **0.3125** | 5 |

**My first attempt was off by one row** — I fed stage 2 the stage 1 value from
the row above, counting the bar-0 kick twice (1.5, 1.25, 0.875, …). With rows
aligned, the ratio is **bar + 1**.

> **Single pole: `b^bar`. Repeated pole: `(bar + 1) × b^bar`.** Stage 2 drains
> at the same rate as stage 1, but keeps being **topped up** by stage 1, which is
> still draining. A bucket emptying while it is being refilled.

With the real b = 0.911487, `(bar + 1) × b^bar` peaks at **bar 10, height
4.3541** — the "grows for ~11 bars, peaks at ~4.4×" correction from part 3,
now derived rather than only observed. Part 3's `b^bar` ignored the refill.

## 10. The test file, and where the transient lands

`Test_RoofingFilter.c` claims to "validate RoofingFilter on EUR/USD D1."

> **Could it fail?**

**What I said:** don't know. Narrowed: the only way a script reacts to a wrong
answer is an `if`. It has one — `if(is(LOOKBACK)) return;` — which asks about
Zorro's warm-up phase, not the output. Everything else does `file_append`:
writes a CSV row. **Break the filter and it still runs and writes different
numbers. It is an exporter, not a test.** (GAP-1.33, same as GAP-1.19.)

> **Can it be reproduced from the repo?** It reads EUR/USD history from Zorro's
> folder and writes to `C:/Zorro/Data/` — neither is in the repo. No. (D-14.1.)

**The return comes before the filters.** Gotcha §4.1 says compute every
indicator *before* that line. Here the order is reversed.

> **During lookback, do the filters run? Where does the start-up transient end
> up?**

**What I said:** they don't run — so the transient is thrown away. **The first
half is right, the second doesn't follow.** The decay only happens when the
filter *runs*. Lookback bars with the filter switched off drain nothing. Its
first call is the first bar after lookback — which is also CSV row 1.

Prediction written before looking: row 1 HP = Roofing = 0.992 × Close.
**Real CSV:**

    row  1  Close 1.20248  HP 1.19306  Roofing 1.19306   (1.19306/1.20248 = 0.992166)
    row 30                 HP 0.28310  Roofing 0.31283
    row 72                 HP −0.00100 Roofing 0.00770

Row 1 matches to five decimals. Row 72's HP of −0.001 is the normal size; row 1
is ~1,000× that. The notebook drops 30 rows, so rows 31–72 of transient go into
its statistics. (GAP-1.34.)

## 11. The smoothing ratio: 2.6× or 10.9×?

> **What is a "smoothing ratio"?**

**My answers, in order:**

1. Roofing ÷ HP, row by row. **Fails** — both swing through zero. Row 72:
   0.00770 ÷ −0.00100 = −7.7. Dividing by almost nothing gives nonsense.
2. Average each column, then divide. **Fails** — both averages are ~0.
3. Square, average, square-root — the standard deviation. **Works**, and
   measures **size**.

**Size is not smoothness.** Toy: slow wave amplitude 10 + fast jitter amplitude 1.

    size (std):     slow 7.071, jitter 0.707
                    together √(7.071² + 0.707²) = √(50.0 + 0.5) = 7.106
                    jitter share 0.5 / 50.5 ≈ 1%   → removing it: ratio 1.005

    jaggedness (std of bar-to-bar change):
                    slow 1.4782, jitter 1.2247
                    together √(2.185 + 1.500) = 1.9196
                    jitter share 1.500 / 3.685 ≈ 41%  → removing it: ratio 1.299

Small but fast things barely register in size and dominate in jaggedness. On a
random walk: size ratio **1.12**, jaggedness ratio **2.27**. The notebook uses
jaggedness in both places (`diff().std()`), so the definition was not the cause.

**The input was.** Each step checked:

1. Cell 15's formula on the current Zorro CSV *(real CSV)*: **1.52** / **2.17**
   / **2.42** dropping 0 / 30 / 72 rows. Predicted ~1.6 / 2.2 / 2.4.
2. The notebook reads `data/fx/` (**4 May**), not `C:/Zorro/Data/` (**10 May**).
3. `data/fx/HP` rows 1–3 = 0.39169, 0.09814, 0.02575. Section `oldbug`: only
   `cos(360/48)` taken as radians, with no 0.707 (alpha **0.8211**), reproduces
   them. The Roofing file needs the matching SuperSmoother degrees bug.
4. The file has 5,192 rows — **two runs**. The second uses `cos(0.707·360/48)`
   and explodes to `-nan(ind)`.
5. Cell 15's formula on run 1 only *(real CSV)*: **10.88**. The notebook printed
   10.9.

> **Both numbers were computed correctly. They describe two different filters.**
> 10.9× is the pre-radians-fix filter. 2.6× is cell 19's Python recomputation
> (degrees bug absent, 0.707 missing), reproduced at 2.59. The current library
> gives ~2.2. Every EUR/USD figure in the Week 6 notebook describes a filter the
> library does not contain. (GAP-1.27e resolved; GAP-1.35.)

## 12. Why run 2 exploded

    b = 1 − alpha = 1 − (−2.2903) = 3.2903

Stable needs every pole below 1. This one is **3.29**. Each bar multiplies what
is left by more than that:

    46.66 / 5.10  = 9.1×
    251.72 / 46.66 = 5.4×
    1151.41 / 251.72 = 4.6×

— settling toward 3.29 as the (bar + 1) factor matters less. At ×3.29 per bar,
the largest number a computer stores (~10³⁰⁸) is passed in roughly 600 bars
(estimate, not located). Then infinity, then infinity − infinity = `nan`.

**One look at b predicts it before running anything.** A missing 0.707 or a
degrees/radians slip changes alpha, alpha sets b, and b alone decides whether the
filter settles or blows up.

---

# Part 3 — What to keep

- **Two filters in a row multiply their gains.** A roofing filter is a window
  made by two slopes, not a detector.
- **Compute gain from coefficients, not from output samples.** Samples mix size
  and timing.
- **A band-pass on random input produces a cycle.** Output shape says nothing
  about input cycles.
- **A repeated pole fades as (bar+1)·b^bar.** Estimate with b^bar and you
  undercount — by 3.4× at bar 30 here.
- **Seeding is visible in the data.** Row 1 = 0.992 × Close. Check first rows.
- **"Smoother" means less jagged, not smaller.** Say which one you measure.
- **A number is only as current as the file it was computed from.** The fix
  reached the code and the Zorro folder, not `data/fx/`.
- **Stability is readable off the coefficients.** b > 1 means it will explode.

---

# Part 4 — Playground

`python docs/learning/roofing_playground.py [section]` — sections `ingredients`,
`gain`, `cascade`, `twobar`, `byhand`, `coinflip`, `collapse`, `seed`, `ratio`,
`oldbug`. How to work in it, and five short experiments, are in
`RoofingFilter_Playground_Manual.md`.

---

# Part 5 — Still don't understand

- **Why is the corner not at the parameter?** HP(48) → 43.74, SS(10) → 10.17.
  Probably the 0.707 and the √2 again. Not derived.
- **What does the 0.707 compensate for?** Carried from part 3, still underived.
- **Why 10.75 and 23.24?** I can explain the direction (red input loads the slow
  side) but not the numbers.
- **The seed-case factor `b·(1 + alpha1·(bar + 1))`** was derived by Claude and
  checked against simulation; I have not worked through it myself.
- **What would justify 48 and 10 on EUR/USD?** No dominant cycle to tune to. The
  honest answer may be "whatever the downstream indicator needs", which is a
  Phase 2.5 question.
- **Is the roofing filter useful if it manufactures cycles?** Ehlers' case is
  that it prepares data for a following indicator, not that its output is a
  cycle. Whether that preparation helps is a strategy question.
- **Did the old SuperSmoother bug ring?** `cos(√2·180/10)` gives different poles.
  Not examined.
- **Are the Decycler and BTC files in `data/fx/`, `data/crypto/` also pre-fix?**
  Same date and oversized, so probably. Not checked.

**Closed from part 3's list:** "Why does the (A + B·n) form appear for a repeated
root?" — the two-stage table in §9 shows it. "Is the roofing smoothness 2.6× or
10.9×?" — both, for two different filters (§11).
