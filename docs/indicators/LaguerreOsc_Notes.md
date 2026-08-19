# Laguerre Oscillator — Notes

**Ehlers, "Laguerre Filters", TASC V.43:07 (2025)**
Implemented Week 13 Day 3. Article defaults: gamma 0.5, Length 30, RMS 100.

## What it computes

    L0  = UltimateSmoother(Close, Length)
    L1  = a delayed version of L0
    Osc = (L0 - L1) / RMS(L0 - L1, 100)

L1 is L0 pushed slightly later in time. Subtracting removes what the two have in
common — the trend — leaving what changed between them, which oscillates around
zero. Same principle as the Decycler (Week 6).

## The three parameters do three different jobs

| parameter | value | job |
|---|---|---|
| Length | 30 | how smooth L0 is |
| gamma | 0.5 | how far L1 trails L0 |
| RMSLen | 100 | what counts as a "typical" reading |

Length is the UltimateSmoother period. It does NOT set the L0-L1 gap — that is
gamma's job, and the two are easy to confuse.

## How gamma sets the delay

The recursion is

    L1 = -gamma*L0[1] + L0[1] + gamma*L1[1]

Collect the two L0[1] terms and it becomes a blend whose weights sum to 1:

    L1 = (1-gamma)*L0[1] + gamma*L1[1]

### Worked example, gamma = 0.8

    L1 = 0.2*(previous L0) + 0.8*(previous L1)

L0 jumps to 100 at bar 0 and stays. L1 starts at 0.

    Bar 1:  L1 = 0.2*100 + 0.8*0     = 20 + 0     = 20
    Bar 2:  L1 = 0.2*100 + 0.8*20    = 20 + 16    = 36
    Bar 3:  L1 = 0.2*100 + 0.8*36    = 20 + 28.8  = 48.8
    Bar 4:  L1 = 0.2*100 + 0.8*48.8  = 20 + 39.04 = 59.04

| bar | gap before | closes | % of gap closed | L1 after |
|---|---|---|---|---|
| 1 | 100 | 20 | 20% | 20 |
| 2 | 80 | 16 | 20% | 36 |
| 3 | 64 | 12.8 | 20% | 48.8 |
| 4 | 51.2 | 10.24 | 20% | 59.04 |

The percentage is 20% on every bar — it is always (1 - gamma), never changes.

### Same four bars, gamma = 0.5

    Bar 1:  L1 = 0.5*100 + 0.5*0     = 50
    Bar 2:  L1 = 0.5*100 + 0.5*50    = 75
    Bar 3:  L1 = 0.5*100 + 0.5*75    = 87.5
    Bar 4:  L1 = 0.5*100 + 0.5*87.5  = 93.75

| bar | gap before | closes | % of gap closed | L1 after |
|---|---|---|---|---|
| 1 | 100 | 50 | 50% | 50 |
| 2 | 50 | 25 | 50% | 75 |
| 3 | 25 | 12.5 | 50% | 87.5 |
| 4 | 12.5 | 6.25 | 50% | 93.75 |

After four bars: 93.75 at gamma 0.5, only 59.04 at gamma 0.8. Higher gamma leaves
L1 much further behind, so the gap L0-L1 is much larger — and that gap is what the
oscillator measures.

### Why a small gamma change makes a large delay change

The number that matters is what is LEFT each bar, which is gamma itself.

    gamma 0.5:   100 -> 50 -> 25      75% gone after two bars
    gamma 0.95:  100 -> 95 -> 90.25   only 10% gone after two bars

At 0.95 the gap barely shrinks, because you keep multiplying by something very
close to 1. Keeping almost everything takes a long time to fade.

The gap halves (or shrinks by whatever fraction) forever and never reaches zero,
so "how many bars behind" needs a convention: bars until the gap falls to 1/e,
about a third.

| gamma | % of gap closed per bar | effective delay |
|---|---|---|
| 0.20 | 80% | 0.6 bars |
| 0.50 | 50% | 1.4 bars |
| 0.80 | 20% | 4.5 bars |
| 0.90 | 10% | 9.5 bars |
| 0.95 | 5% | 19.5 bars |

At the article's gamma of 0.5, L1 trails L0 by about 1.4 bars.

## RMS vs standard deviation

RMS: square each value, average, take the root. It measures spread around ZERO.
A standard deviation measures spread around the data's own mean.

On values sitting away from zero they diverge sharply — (10,12,14,12,10) gives
sd 1.50 but rms 11.70. On values centred near zero they agree — the same shape
shifted to (-2,0,2,0,-2) gives sd 1.55 and rms 1.55.

L0-L1 is a difference between two similar quantities, so it hovers near zero and
the two should agree here. The article publishes an $RMS function and uses it; it
gives no reason and none is inferred. If L0-L1 ever develops a persistent offset,
RMS returns a larger number than sd would and the oscillator reads smaller than
its standard-deviation interpretation implies. Checkable on real data.

## Measured

| | EUR/USD D1 | BTC/USD H4 |
|---|---|---|
| n | 2,596 | 7,534 |
| mean | -0.049 | +0.078 |
| sd | 1.016 | 1.076 |
| p1 / p99 | -2.47 / +2.17 | -2.80 / +3.07 |
| min / max | -3.69 / +3.96 | -5.59 / +5.56 |
| % above zero | 49.2 | 52.3 |

**sd near 1 on both is close to automatic** — divide numbers by their own typical
size and you get numbers of typical size 1. It is not a discovery about markets.
What it does show is that the 100-bar window tracks the changing scale well on
both assets; a poorly chosen window would drift well away from 1.

**Zero-centred with a small drift offset.** Sign follows each asset's direction
over its sample (EUR/USD -13.9%, BTC +1212.5%). RSIH shows the same signature
from an independent construction.

**The tails do not match.** Both have typical size ~1, but BTC reaches +/-5.6
while EUR/USD stops near +/-3.9. So "scaled in standard deviations" transfers as
a SCALE but not as a PROBABILITY: reading +/-2 as "roughly the top 5%" holds on
EUR/USD (p5/p95 at +/-1.6-1.7) and understates how often BTC goes further. Same
distinction hit with NATR, in a different form.

Percentile asymmetry is mild but consistent with drift: EUR/USD's negative tail
reaches further (p1 -2.47 vs p99 +2.17), BTC's positive tail does (p99 +3.07 vs
p1 -2.80). The single most extreme readings carry no signal — each asset's two
extremes are near-symmetric, so which one happens to be larger is a coin flip.

## Article discrepancy — documented, not corrected

Ehlers writes that each term is "the allpass filter delay of the previous term".
An allpass filter passes every frequency at unchanged amplitude, shifting only
phase. The published code uses the PREVIOUS L0 in both terms, which collapses to
a lowpass. Measured amplitude at gamma 0.5: 0.45 at period 4, 0.75 at period 10,
0.91 at period 20, approaching 1.0 only asymptotically. A true allpass measures
1.0000 at every period. The book version (Cybernetic Analysis Fig 14.5, and our
Laguerre.c) uses the CURRENT L0 and is a genuine allpass.

**For this oscillator the difference is exactly nil.** The allpass form gives
exactly (1+gamma) times the published form, at every frequency — verified for
gamma 0.2/0.5/0.8/0.95, ratios 1.200000/1.500000/1.800000/1.950000. The RMS
division cancels a constant factor: it appears in numerator and denominator
alike. Max difference between the two oscillators: 8.9e-16.

Published code implemented as published.

**This does not carry over to the five-term Laguerre FILTER** in the same
article, which chains four such delays and combines them with binomial weights
1-4-6-4-1 and no normalisation. Constant factors do not cancel in a weighted sum.
Check before extending.
