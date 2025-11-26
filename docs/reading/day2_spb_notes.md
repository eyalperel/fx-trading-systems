# Day 2 Reading Notes — Super Passband Prep

## 1) Laguerre recap (gamma ↔ lag)
- key ideas:
- half-life formula:
- warm-up/guard notes:
- what gamma range seems reasonable for FX D1 (your words):

## 2) Super Passband (SPB)
- what it passes / what it rejects:
- how to choose center_period and bandwidth (your rule-of-thumb):
- implementation cues (FIR vs IIR; Ehlers intent):
- entry/exit cues from SPB (zero-cross, slope, phase):

## 3) Hilbert / Instantaneous Frequency & Phasor
- what "instantaneous period" means:
- how we might estimate dominant period:
- caveats (edge effects / phase wrap):

## 4) Measuring cycle periods
- methods mentioned (Hilbert, MESA, others):
- practical defaults for FX D1:
- pitfalls (aliasing, nonstationarity):

## 5) Aliasing & Windowing
- aliasing: when it bites us in FX:
- windowing: what it fixes / why we care:

## 6) Noise control & gating
- why RMS/energy gate helps:
- initial gate rule for EURUSD D1 (your proposal):

## 7) Bandy (mini-read)
- 3 sentences on overfitting & walk-forward:
- 2 sentences on parameter robustness:

## 8) Questions you want answered before coding SPB
- Q1:
- Q2:

