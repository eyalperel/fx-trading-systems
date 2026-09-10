# The High-Pass Filter — In Plain Words

**Written:** 2026-09-10, Week 14 Session 1 part 3
**What this is:** my own explanation of how the high-pass filter works, built by
working through it rather than reading it. Pedagogical, not a status record.
For status, evidence and gaps see `docs/indicators/HighPass_RoofingFilter_Notes.md`.
Revised whenever my understanding improves — that is what it is for.

---

## 1. What it does — the short version

A high-pass filter lets fast movement through and blocks slow movement.

That is the standard description and it is not wrong, but it hides the important
part. What the filter actually reacts to is **bend** — anywhere the price series
stops being a straight line.

## 2. Why "it passes noise" is the wrong way to think about it

Here is a price series with **no noise in it at all**. Every number is exact:

    100  101  102  103  104  105  104  103  102  101  100

Straight up at +1 per bar, then straight down at −1 per bar. A tent, peak at bar 5.

The core of a 2-pole high-pass is the weights `1, −2, 1`:

    d[t] = P[t] − 2·P[t−1] + P[t−2]

Run it across every bar:

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

Ten zeros and one −2. Check bar 6 by hand: 104 − 2(105) + 104 = 104 − 210 + 104 = −2.

**Every window that sits inside one straight leg gives zero.** The only window
that gives anything is the one straddling the corner.

**What the −2 is.** The slope going into the peak is 105 − 104 = **+1**. The slope
coming out is 104 − 105 = **−1**. The change in slope is −1 − (+1) = **−2**. Exactly
d[6].

So the output is the size of the direction change, in price units, reported on
the bar **after** the turn.

**The lesson.** A high-pass does not detect noise. It detects **curvature**. Noise
gets through because random jitter bends the series at nearly every bar — not
because the filter knows what noise is. A clean, deliberate, noiseless turn in
trend gets through just as easily. The filter only ever sees shape.

## 3. The design: smoothing by subtraction

`UltimateSmoother = Price − HighPass(Price)` and `Decycler = Price − HighPass(Price)`
are the same idea: take price, throw away the fast part, keep the rest.

Watch what that does at the tent's corner. Say the real filter multiplies that
−2 by some positive number k, and take k = 0.3 so the kick is −0.6:

| bar | 4 | 5 | 6 | 7 |
|---|---|---|---|---|
| price | 104 | **105** | 104 | 103 |
| HP | 0 | 0 | −0.6 | ... |
| US = P − HP | 104 | 105 | **104.6** | ... |

Price has already turned down at bar 6. US is at 104.6 — **above price**, sitting
between price and the peak it just left.

Note the sign carefully: HP is negative, and subtracting a negative **adds**.
`104 − (−0.6) = 104.6`.

**Flip it upside down and the same thing happens the other way.** Valley:
`100 99 98 97 98 99`, trough at bar 3. At bar 4: d = 98 − 2(97) + 98 = **+2**,
positive, so US sits **below** price.

**The one-line description of the whole design:**

> A filter that follows price exactly while price is straight, and resists price
> wherever price bends. It pulls toward where price came *from*.

**Why this matters.** Both halves of that sentence are the same mechanism — you
cannot have the first without the second. On a perfectly straight ramp there are
no bends, so the filter does nothing at all and US = price exactly. That is what
"zero lag on a ramp" means. It is not a very good lag result; it is the case
where the filter is switched off.

Every bar on which the filter actually *does* something is a bar where price
bent, and on those bars it moves against the new direction. Resisting a jitter is
what you want. Resisting a real turn is lag arriving through a different door.

## 4. Feedback: what happens on the bars after the bend

The `1, −2, 1` part is only the input side. A real filter also feeds its own past
output back in:

    HP[t] = c0·d[t] + c1·HP[t−1] + c2·HP[t−2]

So after the kink at bar 6, the input side goes back to feeding zeros — but the
filter keeps producing output from memory. It does not snap back.

### Poles — the thing that decides the behaviour

Take the feedback coefficients and write them as a quadratic. Its roots are
called the **poles**, and they tell you two things: whether the filter is stable,
and whether it swings.

- **Real roots** → the disturbance just fades away
- **Complex roots** → the disturbance **rings**: swings positive, negative,
  positive, each swing smaller

To tell which, compute the discriminant `B² − 4AC`. Negative means complex.

### What ringing looks like (general theory — NOT this filter)

Made-up coefficients `HP[t] = 0.5·d[t] + 1.0·HP[t−1] − 0.5·HP[t−2]`, single kick
of −2 at bar 6:

    −1, −1, −0.5, 0, +0.25, +0.25, +0.125, 0, −1/16, −1/16, −1/32, 0, ...

Same block shape every 4 bars, sign flipped, size quartered. Poles are (1±i)/2:
magnitude √0.5 ≈ 0.707, angle 45° per bar.

**"Full swing = 8 bars"** means: negative stretch → positive stretch → back to
negative takes 8 bars. Count it three ways and they agree — first negative at bar
6, next at bar 14 (8 apart); zeros at bars 9, 13, 17 (4 apart, and there are two
zero crossings per cycle → 8); or 360° ÷ 45°/bar = 8.

The ring period is **how wide the contaminated region is** after a single bend.

### What the real filter actually does

`HighPassFilter.c` feedback, with `b = 1 − alpha1`:

    z² − 2b·z + b²

That is `(z − b)²` identically. **The discriminant is zero at every HPPeriod**, so
there is one repeated real pole at b.

**This filter is critically damped. It does not ring.** Ehlers built the perfect
square in on purpose: critical damping is the fastest settling you can get with
no oscillation at all.

**How easily this breaks.** Drop one factor of `(1 − alpha1)` — a plausible typo —
and you get `z² − 1.8z + 0.9` at b = 0.9. Discriminant = 3.24 − 3.6 = **−0.36**.
Complex. The filter now rings. One missing factor turns a fading filter into an
oscillating one.

## 5. How long the disturbance lasts

At HPPeriod = 48: alpha1 = 0.088513, so b = 0.911487. Ask how many bars for
`b^n` to shrink to a given fraction:

| residue | bars |
|---|---|
| 10% | 25 |
| **1%** | **50** |
| 0.1% | 75 |

**~25 bars per factor of ten.** Constant bars-per-decade is the signature of
exponential decay — there is no point at which it "ends," you pick a threshold
and count.

Rule of thumb, checked at two periods (48 → 49.7 bars, 20 → 20.6 bars):
**1% settling ≈ HPPeriod**. Two data points, not a proof.

Whether 50 bars is "damped enough" is not a mathematical question. On D1 that is
ten weeks. It gets settled by parameter sensitivity once strategies exist
(GAP-1.17).

## 6. Superposition — why a single value tells you nothing

The filter is **linear**: feed it A, get response A; feed it B, get response B;
feed it A+B, get exactly response A + response B. No interaction, no cross-terms.
That property is called **superposition**, and it means the output is *literally*
the sum of the responses to every past bend.

Two bends, b = 0.9. Bend A kicks the filter to 1.0 at bar 0; bend B kicks it to
0.5 at bar 3:

| bar | from A | from B | total |
|---|---|---|---|
| 0 | 1.000 | — | 1.000 |
| 1 | 0.900 | — | 0.900 |
| 2 | 0.810 | — | 0.810 |
| 3 | 0.729 | 0.500 | **1.229** |
| 4 | 0.656 | 0.450 | **1.106** |

At bar 4 the output is 1.106. Nothing in the filter's state records that 0.656 of
it came from bar 0 and 0.450 from bar 3. It is one number.

**The consequence.** Real price bends constantly. With bends every few bars and a
~50-bar memory, any single value of the output is an accumulation of dozens of
past bends. You cannot read it as a statement about current conditions, and
nothing downstream can unpick it either.

This is the heart of **GAP-1.16**. The 0.0000-bar ramp result was measured on
input with no bends at all, so nothing accumulated and nothing was subtracted.
On real price, `Price − HighPass` subtracts a running sum of ~50 bars of
accumulated bend.

---

# What I learned about validation

Separate from the filter itself, and the more transferable half.

## 7. "Validated on EUR/USD D1" can be worth nothing

Two filters: the correct one (fades) and the broken one (rings). Utterly
different behaviour.

Run both on ten years of EUR/USD and plot them. **Both produce a squiggly line
around zero.** The correct one squiggles because price bends constantly; the
broken one squiggles because price bends *and* because it oscillates by itself.
Looking at a chart cannot separate those.

**The test question is not "did it pass?" but "could it have failed?"** If a wrong
implementation would have produced the same result, passing carries no
information.

What *would* catch it: the tent. Eleven bars, one kink, no market data. Correct
filter fades monotonically; broken filter flips sign. Unmistakable. Or compute
the discriminant, which needs no data at all.

## 8. Three metrics that cannot fail

**Mean of the high-pass output.** The gate was `|mean| < 0.0001`. But second
differences **telescope** — the middle terms cancel:

    (P2 − 2P1 + P0) + (P3 − 2P2 + P1) = P3 − P2 − P1 + P0

Check with P = 100, 103, 101, 106: d[2] = −5, d[3] = +7, sum = +2. And
106 − 101 − 103 + 100 = +2. ✓

So the sum over N bars collapses to a few endpoint terms and stays bounded no
matter how long the series is. The **mean** is that bounded sum ÷ N, so it goes
to zero as 1/N for *any* coefficients. At 2,566 bars it lands around 1e-6 against
a 1e-4 gate. Passes for the correct filter, the ringing filter, anything.

It tests the algebra of `1, −2, 1`. It is blind to every feedback term — which is
where all the parameters and all the plausible typos live.

**Mean absolute distance from price, used as a lag measure.** Price 100, 102, 99,
103. Filter A is the identity (outputs price). Filter B is a heavy smoother:
100.0, 100.5, 100.2, 100.9.

| | distances | mean |
|---|---|---|
| A (does nothing) | 0, 0, 0, 0 | **0.000** |
| B (smooths) | 0, 1.5, 1.2, 2.1 | **1.200** |

A wins. A is the do-nothing filter. **MAD is minimised by the filter that has zero
lag *and* zero smoothing** — it is not a lag measurement.

Worse for the Decycler specifically: `Decycler = Price − HP`, and HP outputs
nothing on unbent input, so Decycler *is* price on straight stretches. It beats
SuperSmoother by construction, not by measurement.

This exact metric produced the false "UltimateSmoother has zero lag" claim in
Week 5. Week 13 measured it at 3.87 bars.

**Signal-to-noise ratio as Week 5 defined it** — `var(indicator) / var(price −
indicator)`. The reference is the candidate's own output, so a filter that smooths
less scores higher, and the do-nothing filter scores infinity. Same degenerate
answer, different formula.

## 9. The recurring pattern

**One number standing in for a trade-off.** Every time, a quantity that only moves
in one direction gets read as a quality score, when the honest answer needs two
columns — behaviour at the fast end *and* at the slow end.

Instances found so far across this review: SNR, "SS3 is better" defined as more
attenuation, MAD read as lag, coefficient sum used as a stability test, HP mean
as a correctness gate.

**The general rule I want to keep:** before accepting a metric, ask what its
*perfect* score would be, and check whether the thing achieving it is any good.
For SNR and MAD, the perfect score belongs to a filter that does nothing.

## 10. What a validation needs

1. The reference must be fixed across candidates, or you are not comparing them.
2. The candidate's output must enter the score, or you are describing the data.
3. There must be a result a wrong implementation would produce and a correct one
   would not. **If you cannot describe what failure looks like, passing means
   nothing.**

Synthetic inputs satisfy all three for free, because signal and noise are known
by construction: a ramp for lag, a tent for damping, a single-period wiggle for
rejection, a slow wave for signal preservation. They also need no data files,
which is why validation from a fresh clone is possible at all (decision D-14.1).
