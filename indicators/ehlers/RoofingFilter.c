///////////////////////////////////////////////////////
// Roofing Filter - John Ehlers
// Source (a): "Predictive And Successful Indicators", TASC
//          (S&C V.32:1, Jan 2014), sidebar "EasyLanguage Code To
//          Compute The Roofing Filter": the 2-pole high-pass
//          (HP-A, 48) followed by the 2-pole SuperSmoother (10)
//          applied to (HP + HP[1]) / 2. In the source both the HP
//          and the Filt histories start at 0 (Vars: HP(0), Filt(0)).
//          The article fixes 48 and 10; HPPeriod / SSPeriod are
//          this library's parameters (generalisation).
//          Fixes GAP-1.31 (the earlier source note "Optimal
//          Detrending" was wrong).
// Purpose: Band-pass: HighPassFilter -> SuperSmoother2Pole
// Inputs:  Price    - price series (vars)
//          HPPeriod - high-pass cutoff (article: 48)
//          SSPeriod - SuperSmoother cutoff (article: 10)
// Output:  Filtered series, oscillates around zero
// Seeding: (b) HP's first output is 0 (input history = Price[0]
//          by series seeding, HP history 0) and SuperSmoother2Pole
//          seeds at its first input, so the output starts as the
//          source's Filt(0) (spec [observations].O_SEED).
// Gain:    (b) article RoofingFilter(48, 10): T = 20 0.8900165495219391;
//          T = 2 ~0 (spec [known_answer_T20]).
// Call rules: callers invoke unconditionally every bar (series()
//          allocates by call order, gotchas 3.1). Include order:
//          HighPassFilter.c, SuperSmoother2Pole.c, RoofingFilter.c
//          (gotchas 5.3).
// Verification: analysis/harness/specs/RFF_ArticleFidelity.toml
//          (pre-registered b6b5c5d). Not verified until that run
//          passes.
///////////////////////////////////////////////////////


var RoofingFilter(vars Price, int HPPeriod, int SSPeriod)
{
    var* rf_hp = series(HighPassFilter(Price, HPPeriod), 3);
    var rf_out = SuperSmoother2Pole(rf_hp, SSPeriod);
    return rf_out;
}
