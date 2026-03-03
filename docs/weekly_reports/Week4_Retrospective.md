# Week 4 Retrospective
**Date:** Week 4 Day 6

---

## What Was Planned
- Build analysis framework (Jupyter template + metrics module)
- Validate InstantTrendline fixed vs adaptive
- Test on crypto
- Select 20-25 indicators for Weeks 5-14

## What Was Delivered
- ✅ indicator_metrics.py — 4 functions: lag, SNR, cross-asset, validation report
- ✅ Indicator_Analysis_Template.ipynb — 8-section reusable notebook
- ✅ InstantTrendline validated on EUR/USD D1 (fixed vs adaptive)
- ✅ InstantTrendline validated on BTC/USD H4
- ✅ BTC/USD H4 data pipeline established
- ✅ 26 indicators selected for Weeks 5-14
- ✅ Repo cleaned and organized

## Key Findings
1. Fixed period InstantTrendline outperforms adaptive on both EUR/USD D1
   and BTC/USD H4 — DominantCycle instability costs more than it gains
2. Both versions pass validation and are approved for library
3. Same period (DC=20) works on both asset classes
4. BTC shows higher absolute SNR due to stronger sustained trends

## What Was Harder Than Expected
- Zorro CSV export path resolution (absolute path required)
- Jupyter notebook setup in VS Code (ipykernel installation)
- Warmup period filtering (threshold approach unreliable,
  date-based filtering more robust)

## What Was Easier Than Expected
- BTC/USD H4 data was already available in Zorro natively
- The analysis framework generalized cleanly to crypto without changes

## Lessons Learned
- Validate the framework on known data before using it on new indicators
- Fixed paths in Zorro scripts are a maintenance issue — consider a
  config approach in later weeks
- The SNR metric reveals things the eye misses (Fixed vs Adaptive gap)

## Going Into Week 5
- Analysis framework is ready and tested
- Indicator library methodology is locked in
- Week 5 starts with SuperSmoother — read article before touching code