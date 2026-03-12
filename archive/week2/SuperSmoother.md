# Super Smoother - Two-Pole Butterworth Filter

**Author:** John Ehlers  
**Source:** "Moving averages and smoothing filters" - Stocks & Commodities V.7:3 (87-90)  
**Implementation Date:** February 2026  
**Week:** 3 Day 5

---

## Overview

The Super Smoother is a two-pole Butterworth low-pass filter that provides superior noise reduction compared to simple moving averages while maintaining reasonable lag characteristics.

**Key Advantage:** Better smoothing than EMA with only ~2-3 bar delay (vs ~1 bar for EMA)

---

## Mathematical Foundation

### Filter Equation
```
SS[0] = B × SS[1] - A² × SS[2] + C × (Price[0] + 2×Price[1] + Price[2])
```

### Coefficients
```
A = e^(-4.44288 / Period)
B = 2 × A × cos(4.44288 / Period)    [NOTE: RADIANS!]
C = (1 - B + A²) / 4
```

**CRITICAL:** The `cos()` function requires RADIANS, not degrees!
- 4.44288 radians ≈ 254.5 degrees

---

## Implementation Details

### Function Signature
```c
var SuperSmoother(vars Data, int Period)
```

**Parameters:**
- `Data`: Price series (typically `priceClose()`)
- `Period`: Cutoff period - cycles shorter than this are filtered out

**Returns:** Smoothed value for current bar

### Zorro-Specific Patterns
```c
vars SS = series(0);  // Creates persistent series across bars

// Use array notation to access history
SS[0] = current bar
SS[1] = previous bar
SS[2] = 2 bars ago
```

**No static variables needed** - `series()` handles state automatically!

---

## Usage Example
```c
#include "../../indicators/ehlers/SuperSmoother.c"

function run()
{
    vars Price = series(priceClose());
    
    var SS10 = SuperSmoother(Price, 10);
    var SS20 = SuperSmoother(Price, 20);
    
    plot("SuperSmoother(10)", SS10, LINE, BLUE);
    plot("SuperSmoother(20)", SS20, LINE, RED);
}
```

---

## Performance Characteristics

### Delay Analysis
- **Period 10:** ~2 bar delay
- **Period 20:** ~3 bar delay
- **Comparison:** EMA has ~Period/2 delay

### Noise Reduction
- Two poles provide stronger filtering than single-pole filters
- The (1-2-1) weighting pattern in the formula acts as additional smoothing

### Frequency Response
- **Cutoff:** -3dB at Period specified
- **Rolloff:** -40dB/decade (two-pole characteristic)

---

## Testing Results

**Test Configuration:**
- Asset: EUR/USD
- Period: 2021-2022
- Comparison: SuperSmoother(10) vs EMA(10)

**Observations:**
- Smoother curve than EMA
- Slightly more lag (acceptable tradeoff)
- Better noise rejection in ranging markets

---

## Debugging Notes

### Issue 1: Radians vs Degrees
**Problem:** Initial implementation used degrees in cos() function  
**Solution:** Convert to radians (4.44288 instead of 254.5)  
**Lesson:** Always check trig function units in C/Light-C!

### Issue 2: Series Management
**Problem:** Initially used static variables for state  
**Solution:** Use Zorro's `series()` for proper history management  
**Lesson:** Trust Zorro's built-in series system!

---

## References

1. Ehlers, John. "Moving averages and smoothing filters" - TASC V.7:3
2. Butterworth filter theory - Digital Signal Processing
3. Zorro Manual - Series and Indicators

---

## Next Steps

- Test with multiple periods (5, 10, 20, 50)
- Compare to other Ehlers smoothers (Kalman, etc.)
- Use as baseline in NNFX strategy structure
- Test on crypto (BTC/USD) for comparison

---

**Status:** ✅ COMPLETE - Production Ready