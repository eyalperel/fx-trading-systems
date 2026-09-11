# The High-Pass Filter — In Plain Words

**Written:** 2026-09-10, Week 14 Session 1 part 3
**Run it:** `python docs/learning/highpass_playground.py` — every number below is
in there and you can change them.

**What this is.** My own explanation of how the high-pass filter works, built by
working through it rather than reading it. It keeps the wrong turns in, because
those are the parts worth rereading. For status, evidence and gaps, see
`docs/indicators/HighPass_RoofingFilter_Notes.md`. Revise this file freely — that
is what it is for.

---

# Part 1 — How the filter works

## 1. The question that started it

> **What is a high-pass filter, and why does the library need one?**

**What I said:** it blocks slow movement and lets fast movement through — the
noise. And we use it by subtracting it from price, which gives us the slow part,
smoothed, with less lag than a moving average.

The subtraction half was right and is the whole design. The word **noise** was
the problem.

## 2. The question that broke it

> **Here is a price series with no noise in it at all. Does the filter output
> zero?**

    100  101  102  103  104  105  104  103  102  101  100

Straight up at +1 a bar, then straight down at −1 a bar. A tent. Peak at bar 5.

**What I said:** yes — it kills straight lines, and this is two straight lines.

**What was wrong:** the join between them. Two straight lines have a corner, and
the corner is not a straight line.

The core of the filter is the weights `1, −2, 1`:

    d[t] = P[t] − 2·P[t−1] + P[t−2]

| t | window | d[t] |
|---|---|---|
| 2 | 100, 101, 102 | 0 |
| 3 | 101, 102, 103 | 0 |
| 4 | 102, 103, 104 | 0 |
| 5 | 103, 104, 105 | 0 |
| 6 | **104, 105, 104** | **−2** |
| 7 | 105, 104, 103 | 0 |
| 8 | 104, 103, 102 | 0 |
| 9 | 103, 102, 101 | 0 |
| 10 | 102, 101, 100 | 0 |

Ten zeros and one −2. By hand at bar 6: 104 − 2(105) + 104 = 104 − 210 + 104 = −2.

**What the −2 is.** Slope into the peak: 105 − 104 = **+1**. Slope out: 104 − 105
= **−1**. Change in slope: −1 − (+1) = **−2**. That is exactly d[6].

So the output is the size of the direction change, in price units, reported one
bar **after** the turn.

> **The correction I needed.** A high-pass does not detect noise. It detects
> **bend**. Noise gets through because random jitter bends the series at nearly
> every bar — not because the filter knows what noise is. A clean, deliberate,
> noiseless turn gets through just as easily. The filter only ever sees shape.
>
> "Noise" is a claim about where movement came from. "Bend" is a claim about its
> shape. Only the second is something a filter can see.

## 3. Smoothing by subtraction

`UltimateSmoother = Price − HighPass(Price)`. Same for `Decycler`. Take price,
throw away the bendy part, keep the rest.

> **What happens at the corner? Is the smoother above price, below it, or on it?**

Say the filter multiplies that −2 by some positive number, giving −0.6:

| bar | 4 | 5 | 6 |
|---|---|---|---|
| price | 104 | **105** | 104 |
| HP | 0 | 0 | −0.6 |
| US = P − HP | 104 | 105 | **104.6** |

**Where I tripped:** I reasoned "HP is negative, so US is below price." Wrong —
subtracting a negative **adds**. `104 − (−0.6) = 104.6`. Write it out rather than
doing it in your head.

So at bar 6 price has already turned down, and the smoother is sitting **above**
it, between price and the peak it just left.

Flip the shape and the same thing happens the other way. Valley `100 99 98 97 98
99`, trough at bar 3. At bar 4: d = 98 − 2(97) + 98 = **+2**, positive, so US
sits **below** price.

> **The whole design in one line:** follows price exactly while price is
> straight, and resists price wherever price bends. It pulls toward where price
> came *from*.

**Why that matters.** Both halves are the same mechanism — you cannot keep one
without the other. On a perfectly straight ramp there are no bends, the filter
does nothing at all, and US = price exactly.

**That is what "zero lag on a ramp" means.** It is not a very good lag result. It
is the case where the filter is switched off.

## 4. What happens on the bars after the bend

The `1, −2, 1` part is only the input side. The filter also feeds its own past
output back in:

    HP[t] = c0·d[t] + c1·HP[t−1] + c2·HP[t−2]

> **After the corner the input side feeds nothing but zeros. Does the output snap
> back to zero?**

**What I said:** no — the old values are still in memory, so there is a residue
that decays away, probably exponentially, and at some point it is small enough to
treat as zero.

Right that it does not snap back. **Wrong that it is always a plain exponential.**

### Poles — the thing that decides everything

Write the feedback coefficients as a quadratic. Its roots are the **poles**.

- **Real roots** → the disturbance never changes sign
- **Complex roots** → the disturbance **rings**: swings positive, negative,
  positive, each swing smaller

To tell which, compute the discriminant `B² − 4AC`. Negative → complex.

### Ringing, on made-up coefficients

`HP[t] = 0.5·d[t] + 1.0·HP[t−1] − 0.5·HP[t−2]`, single kick of −2:

    −1, −1, −0.5, 0, +0.25, +0.25, +0.125, 0, −1/16, −1/16, −1/32, 0, ...

Same block every 4 bars, sign flipped, size quartered. Poles are (1±i)/2:
magnitude √0.5 ≈ 0.707, angle 45° a bar.

**"Full swing = 8 bars"** means: negative stretch → positive stretch → back to
negative takes 8 bars. Three ways to count it, all agreeing — first negative at
bar 6, next at bar 14 (8 apart); zeros at 9, 13, 17 (4 apart, two crossings per
cycle → 8); or 360° ÷ 45° = 8.

**These are teaching numbers, not the real filter's.** I picked them for clean
arithmetic and they happen to ring. The real one does not.

### What the real filter does

`HighPassFilter.c` feedback, with `b = 1 − alpha1`:

    z² − 2b·z + b²    which is    (z − b)²

**The discriminant is zero at every HPPeriod.** One repeated real root at b. The
filter is **critically damped** — the fastest settling you can get with no
oscillation. Ehlers built the perfect square in deliberately.

**How easily it breaks.** Drop one `(1 − alpha1)` and you get `z² − 1.8z + 0.9` at
b = 0.9. Discriminant = 3.24 − 3.6 = **−0.36**. Complex. It rings. One missing
factor, completely different filter.

## 5. The thing I got wrong and only caught by running it

> **I wrote in two repo documents that after a bend the output "decays
> monotonically." It does not.**

Critically damped means **no sign changes**. It does not mean shrinking from the
start. A repeated root gives a response shaped like `(A + B·n)·b^n` — the `n`
pushes it up early, and it only comes down once `b^n` wins.

Run the tent through the real filter at HPPeriod=48:

| bar | 6 | 10 | 16 | 20 | 30 | 40 | 60 | 80 |
|---|---|---|---|---|---|---|---|---|
| output | −1.83 | −6.30 | **−7.95** | −7.49 | −4.94 | −2.74 | −0.67 | −0.14 |

The kick at bar 6 is −1.83. It **grows to −7.95 at bar 16** — about **4.4× bigger**
— and only then decays. The turning point is at `1/(−ln b)` ≈ 10.8 bars.

Sign changes across 126 bars: **zero**. It never crosses the axis.

> **So: not monotonic, but never oscillating. Those are different properties and
> I collapsed them.** The distinction from the broken ringing version still holds
> completely. What changes is that the disturbance is **worst about ten bars
> after the bend that caused it**, not at the moment of the bend.
>
> Nothing in an hour of reasoning caught this. Running the filter caught it in
> one line. That is why `highpass_playground.py` exists.

## 6. How long the disturbance lasts

At HPPeriod = 48: alpha1 = 0.088513, so b = 0.911487.

| residue | bars |
|---|---|
| 10% | 25 |
| **1%** | **50** |
| 0.1% | 75 |

**~25 bars per factor of ten.** Constant bars-per-decade is what exponential
decay looks like — there is no point where it "ends," you pick a threshold and
count.

Rule of thumb at two periods (48 → 49.7 bars, 20 → 20.6 bars): **1% settling ≈
HPPeriod**. Two points, not a proof.

**Measured from the peak, not from the bend** — add the ~11 bars it takes to get
there.

Whether 50-odd bars is "damped enough" is not a maths question. On D1 that is ten
weeks. It gets settled by parameter sensitivity once strategies exist.

## 7. Superposition — why one value tells you nothing

The filter is **linear**. Feed it A, get response A. Feed it B, get response B.
Feed it A+B, get exactly response A + response B. No interaction. That property
is **superposition**, and it means the output is *literally* the sum of the
responses to every past bend.

Two bends, b = 0.9. Bend A kicks it to 1.0 at bar 0; bend B kicks it to 0.5 at
bar 3:

| bar | from A | from B | total |
|---|---|---|---|
| 0 | 1.000 | — | 1.000 |
| 1 | 0.900 | — | 0.900 |
| 2 | 0.810 | — | 0.810 |
| 3 | 0.729 | 0.500 | **1.229** |
| 4 | 0.656 | 0.450 | **1.106** |

At bar 4 the output is 1.106. Nothing in the filter records that 0.656 came from
bar 0 and 0.450 from bar 3. It is one number.

**So what?** Real price bends constantly. With bends every few bars and a 50-plus
bar memory, any single output value is a pile of dozens of past bends. You cannot
read it as a statement about now, and nothing downstream can unpick it either.

This is the heart of the open question about `UltimateSmootherE`. Its 0.0000-bar
result was measured on input with no bends, so nothing accumulated and nothing
was subtracted. On real price, `Price − HighPass` subtracts a running sum of
fifty-odd bars of accumulated bend.

---

# Part 2 — How to think about validation

The more transferable half, and it applies to every indicator, not just this one.

## 8. The question to ask about any test

> **Not "did it pass?" but "could it have failed?"**

Take the correct filter and the broken ringing one. Completely different
behaviour. Run both on ten years of EUR/USD and plot them.

**Both produce a squiggly line around zero.** The correct one squiggles because
price bends constantly; the broken one squiggles because price bends *and*
because it oscillates by itself. A chart cannot separate those.

So "validated on EUR/USD D1" carries no information about which one you have.

What *would* separate them: the tent. Eleven bars, one kink, no market data.
Correct filter never changes sign; broken filter crosses zero eleven times. Or
compute the discriminant — one line of algebra, no data at all.

## 9. Three metrics that cannot fail

**Mean of the output.** The gate was `|mean| < 0.0001`. But second differences
**telescope** — the middle terms cancel:

    (P2 − 2P1 + P0) + (P3 − 2P2 + P1) = P3 − P2 − P1 + P0

Check with P = 100, 103, 101, 106: d[2] = −5, d[3] = +7, sum = **+2**. And
106 − 101 − 103 + 100 = **+2**. ✓

The sum over N bars collapses to a few endpoint terms and stays bounded however
long the series. The **mean** is that bounded sum ÷ N, so it goes to zero as 1/N
for *any* coefficients. At 2,566 bars it lands near 1e-6 against a 1e-4 gate.
Passes for the correct filter, the ringing filter, anything.

It tests the algebra of `1, −2, 1` and is blind to every feedback term — which is
where all the parameters and all the plausible typos live.

**Distance from price, used as a lag measure.** Price 100, 102, 99, 103. Filter A
is the identity (outputs price unchanged). Filter B smooths heavily: 100.0,
100.5, 100.2, 100.9.

| | distances | mean |
|---|---|---|
| A (does nothing) | 0, 0, 0, 0 | **0.000** |
| B (smooths) | 0, 1.5, 1.2, 2.1 | **1.200** |

A wins. A is the do-nothing filter. **Mean distance is minimised by the filter
with zero lag *and* zero smoothing.** It is not a lag measurement.

Worse for the Decycler: `Decycler = Price − HP`, and HP outputs nothing on
straight input, so on straight stretches Decycler *is* price. It beats
SuperSmoother by construction, not by measurement.

This exact metric produced the false "UltimateSmoother has zero lag" claim in
Week 5. Week 13 measured the real figure at 3.87 bars.

**Signal-to-noise as Week 5 defined it** — `var(indicator) / var(price −
indicator)`. The reference is the candidate's own output, so a filter that
smooths less scores higher, and a do-nothing filter scores infinity. Same
degenerate answer, different formula.

## 10. The pattern underneath all three

**One number standing in for a trade-off.** Every time: a quantity that only
moves one way gets read as a quality score, when the honest answer needs two
columns — behaviour at the fast end *and* at the slow end.

> **The rule I want to keep.** Before accepting a metric, ask what its *perfect*
> score would be, and check whether the thing that achieves it is any good. For
> SNR and for mean distance, the perfect score belongs to a filter that does
> nothing.

## 11. What a validation needs

1. The reference must be fixed across candidates, or you are not comparing them.
2. The candidate's output must enter the score, or you are describing the data.
3. There must be a result a wrong implementation would produce and a correct one
   would not. **If you cannot describe what failure looks like, passing means
   nothing.**

Synthetic inputs satisfy all three for free, because signal and noise are known
by construction: a ramp for lag, a tent for damping, a fast wiggle for rejection,
a slow wave for signal preservation. They also need no data files, which is why
validation from a fresh clone is possible at all.

---

# Part 3 — Still don't understand

Honest residue. Pick one up rather than rediscovering it was never closed.

- **What does the 0.707 actually compensate for?** It is called two-pole cascade
  compensation, and dropping it costs 39% on alpha. I verified the number and
  never derived where it comes from or what "cascade" means here. Probably
  related to how two single-pole stages combine, but that is a guess and should
  be treated as one.

- **Why does the SS2 SNR column dip at Period=20?** 17.53, 19.86, **14.18**,
  18.99 across periods 10, 14, 20, 30. A smoothing parameter should not produce a
  hole in the middle. The 14.18 also matches another table exactly, so it may
  just be a copied cell. Unresolved, and Period=20 is used everywhere.

- **Is the roofing smoothness 2.6× or 10.9×?** Two tables in the same document
  disagree by 4× at SSPeriod=10. Not settled.

- **Why does the `(A + B·n)` form appear for a repeated root?** I can see it in
  the numbers and I trust the result, but I have not derived it. The standard
  answer involves what happens to the two-solution form when the two roots
  collide.

- **How much lag does `UltimateSmootherE` actually have on a curve?** The whole
  open question. We now know the mechanism — resist the bend, worst about ten
  bars later — but no number exists.

- **What is a reasonable damping tolerance?** Fifty bars of memory on D1 is ten
  weeks. Whether that is fine or terrible depends on the strategy, and no
  strategy exists yet.
