///////////////////////////////////////////////////////
// Recursive Median Filter (RM) + Recursive Median
// Oscillator (RMO) - John Ehlers
//
// From:    "Recursive Median Filters" - TASC V.36:03 (2018)
// Theory:  docs/indicators/RecursiveMedian_Theory.md
//
// Purpose: RM  - outlier-robust smoothing. Non-linear
//                median stage gates spikes BEFORE they
//                reach the recursive EMA state.
//          RMO - detrended momentum oscillator.
//                Strategy 2 C2 candidate (Week 12).
//
// Inputs:  Price     - price series (vars)
//          LPPeriod  - RM low-pass critical period (default 12)
//          HPPeriod  - RMO high-pass critical period (default 30)
//
// Output:  RM  - smoothed price LEVEL (same units as price)
//          RMO - zero-centred oscillator (price curvature units)
//
// KEY PROPERTY (breakdown point):
//   5-bar median tolerates 2 of 5 corrupted bars (40%).
//   Linear filters have a 0% breakdown point - one bad bar
//   moves the output arbitrarily far. Protection is bounded:
//   3+ CONSECUTIVE bad bars pass through and enter EMA state.
//
// ALPHA HAZARD - the most likely bug in this file:
//   alpha1 (RM low-pass)  = SINGLE pole -> NO 0.707
//   alpha2 (RMO high-pass) = TWO poles  -> 0.707 REQUIRED
//   Verified reference values:
//     alpha1(LPPeriod=12) = 0.422650
//     alpha2(HPPeriod=30) = 0.138102   (computed in HighPassFilter)
//
// Notes:   Trig args are RADIANS. Ehlers publishes in DEGREES:
//          360/P -> 2*PI/P.
//          Median stage is NON-LINEAR - no transfer function,
//          no analytic lag. Predicted lag ~3.4 bars (2.0 median
//          + 1.37 EMA at P=12); MEASURE it, do not assume it.
//          Uses series() for IIR state: callers must invoke
//          unconditionally every bar (allocation is by call order).
//          Locals prefixed rm_ / rmo_ - Zorro Light-C has a flat
//          namespace across included files.
///////////////////////////////////////////////////////

///////////////////////////////////////////////////////
// Median5 - median of 5 values via sorting network
//
// Nine compare-exchange operations, fixed sequence, no
// loops and no data-dependent branching. Only the middle
// element is guaranteed correct on exit - that is all we
// need, and it is why this is cheaper than a full sort.
//
// A median cannot be written as a weighted sum, which is
// precisely why it resists outliers: the spike's VALUE is
// discarded and only its RANK is used.
///////////////////////////////////////////////////////
var Median5(var a, var b, var c, var d, var e)
{
    var rm_t;
    // Sort pairs into ascending order within each comparison
    #define RM_SWAP(x,y) if((x) > (y)) { rm_t = (x); (x) = (y); (y) = rm_t; }

    // Knuth's optimal 9-comparator network for n=5.
    // Order is load-bearing: each comparator assumes invariants
    // established by the ones before it. Verified exhaustively
    // via the 0-1 principle (a network sorting all 2^5 binary
    // inputs provably sorts ALL inputs, over any ordered type).
    RM_SWAP(a, b)
    RM_SWAP(d, e)
    RM_SWAP(c, e)
    RM_SWAP(c, d)
    RM_SWAP(b, e)
    RM_SWAP(a, d)
    RM_SWAP(a, c)
    RM_SWAP(b, d)
    RM_SWAP(b, c)

    #undef RM_SWAP
    return c;   // middle element = median
}

///////////////////////////////////////////////////////
// RecursiveMedian - median gate followed by a one-pole EMA
//
// RM[0] = alpha1 * Median(Price,5) + (1-alpha1) * RM[1]
//
// The asymmetry is the whole design: the median is MEMORYLESS
// (5 bars in, 1 number out, no state) and operates on RAW price.
// The EMA is the only recursive element and never sees raw price.
// A spike the median rejects therefore never enters filter state.
//
// Contrast a plain EMA of price: the spike enters state, is
// scaled by alpha, and decays over ~1/alpha bars (~2.4 at P=12),
// with magnitude proportional to the spike size.
///////////////////////////////////////////////////////
var RecursiveMedian(vars Price, int LPPeriod)
{
    // One-pole critical-period constant. Places the EMA's -3dB
    // point at LPPeriod (asymptotically exact; ~0.7dB error at P=8).
    // NO 0.707 HERE - single pole. See ALPHA HAZARD above.
    var rm_alpha1 = (cos(2.0*PI / LPPeriod) + sin(2.0*PI / LPPeriod) - 1.0)
                  / cos(2.0*PI / LPPeriod);

    // Median of the last 5 bars - non-linear, no state
    var rm_med = Median5(Price[0], Price[1], Price[2], Price[3], Price[4]);

    // IIR state. Seeded at Price[0] to avoid a startup transient
    // (zero-initialised statics would ramp from 0 to price level).
    var* rm_RM = series(Price[0], 2);

    rm_RM[0] = rm_alpha1 * rm_med + (1.0 - rm_alpha1) * rm_RM[1];

    return rm_RM[0];
}

///////////////////////////////////////////////////////
// RecursiveMedianOsc - RM passed through a 2-pole high-pass
//
// The high-pass stage is structurally identical to the existing
// HighPassFilter, so it is reused rather than duplicated. Its
// alpha carries the 0.707 two-pole cascade compensation.
//
// Second difference (P[0] - 2*P[1] + P[2]) removes BOTH constants
// and linear trends -> output is zero-centred regardless of price
// level, which is what makes a zero-crossing signal meaningful.
//
// WARNING - NO AGC. Unlike MESA Stochastic (rolling min/max
// normalisation), amplitude scales with volatility. BTC/USD H4
// shows ~10x regime amplitude variation. Day 4 must check whether
// a normalisation wrapper is required before C2 use.
//
// PERMITTED USE:  sign of RMO, zero crossings.
// FORBIDDEN USE:  RMO period or phase for timing/projection.
// The 12-30 bar passband overlaps the ~20-bar resonance that the
// Week 11 null test found in PURE BROWNIAN MOTION. RMO will
// oscillate at roughly that period on random data too. That is
// expected and is not a defect - provided the claim stays
// "sign of filtered momentum" and never "the market's cycle".
// See docs/research/Cycle_Premise_Conclusions_and_Impact.md
///////////////////////////////////////////////////////
var RecursiveMedianOsc(vars Price, int LPPeriod, int HPPeriod)
{
    // Stage 1: outlier-robust smoothing
    var rmo_rm = RecursiveMedian(Price, LPPeriod);

    // Promote the scalar to a series so the high-pass can index
    // back 2 bars. Allocated by call order - never call this
    // function conditionally.
    var* rmo_RMseries = series(rmo_rm, 3);

    // Stage 2: 2-pole high-pass (alpha2 with 0.707 lives in there)
    return HighPassFilter(rmo_RMseries, HPPeriod);
}