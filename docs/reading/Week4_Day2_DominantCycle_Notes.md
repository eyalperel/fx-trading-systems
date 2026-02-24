# Week 4 Day 2: Dominant Cycle Measurement

**Date:** February 24, 2026  
**Article:** "Linear Predictive Filters And Instantaneous Frequency"  
**Author:** John F. Ehlers, Stocks & Commodities V.43:01 (January 2025)

## Overview

Implemented Griffiths method for adaptive dominant cycle measurement to replace the fixed dc=20 parameter in InstantTrendline, making it fully adaptive to changing market conditions.

## Key Concepts Learned

### 1. The Problem
- Indicators with static parameters fail when market cycle shifts
- EUR/USD dominant cycle varies: 18-40 bars over time
- Fixed dc=20 works sometimes but is suboptimal when cycle changes

### 2. Griffiths Method vs MESA
- **MESA:** Computationally intensive (30+ min on old hardware)
- **Griffiths:** Adaptive, continuous updates, much faster
- **Key advantage:** Updates with each new bar (real-time trading friendly)

### 3. How It Works (Simplified)

**Think of it like a music equalizer:**
- We test each "frequency" (cycle period from 18-40 bars)
- Measure the "volume" (power) at each frequency
- The loudest frequency = dominant cycle

**Technical process:**
1. Band-limit data (remove very long trends and short noise)
2. Normalize to [-1, +1] using AGC
3. Compute adaptive linear predictive filter coefficients
4. Extract spectrum by testing each period
5. Find period with maximum power
6. Smooth result to prevent jumps

### 4. The Math (Frequency Domain Analysis)

For each period from 18 to 40:
```
Real = Σ(coef[i] * cos(2π * i / Period))
Imag = Σ(coef[i] * sin(2π * i / Period))
Power = 1 / [(1-Real)² + Imag²]
```

**Why this works:**
- Filter coefficients capture the spectrum information
- cos/sin are complex frequency probes
- High power at a period = strong cycle at that frequency

## Implementation

### Files Created
- `indicators/ehlers/DominantCycle.c` - Standalone dominant cycle indicator
- `indicators/ehlers/InstantTrendline.c` - Updated to use adaptive DC
- `strategies/tests/DominantCycle_Test.c` - Test showing DC changes over time
- `strategies/tests/InstantTrendline_Test.c` - Test comparing adaptive vs EMA

### Results
- Dominant cycle successfully measures: ranges 18-40 bars
- InstantTrendline now fully adaptive
- Smoother than EMA(20) with less lag
- Adapts to market regime changes automatically

## Critical Lesson: Zorro/Lite-C Include System

**Discovered important compilation rules:**

1. **Always include `<default.c>` first** in test scripts
2. **Include order matters** - dependencies must come before usage
3. **Don't nest includes** - control order in main script
4. **Compile order = include order** - top to bottom

**Correct pattern:**
```c
#include <default.c>
#include "../../indicators/ehlers/DominantCycle.c"
#include "../../indicators/ehlers/InstantTrendline.c"

function run() {
    // test code
}
```

## Comparison: Fixed vs Adaptive

**Fixed DC=20 (Yesterday):**
- Always uses 20-bar cycle assumption
- Works okay when market is near 20-bar cycle
- Fails when cycle shifts to 30+ or drops to 18

**Adaptive DC (Today):**
- Measures actual cycle: 18, 23, 30, 40, etc.
- InstantTrendline adjusts Stage 3 notch filter accordingly
- Better trend following across different market regimes

## Next Steps

**Week 4 Day 3+:**
- Compare fixed vs adaptive performance quantitatively
- Test on different pairs and timeframes
- Consider using DC for other indicators
- Explore using DC for regime detection

## References
- Ehlers, J.F. (2025). "Linear Predictive Filters And Instantaneous Frequency", TASC V.43:01
- Griffiths, L.J. "Rapid Measurement of Digital Instantaneous Frequency", IEEE ASSP-23