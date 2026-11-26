// NNFX_Strategy2_Config.h - every number used by Strategy 2's slot source (T11; T3 amendment 1; PERF2 slot table).
// Config mode of tools/lint_literals.py: each line holding a number carries a source label; non-integers are
// built from integers (gotchas 9d.1). Changing a value is a named, counted variant (T11). Prefix s2_.

int s2_FramaN;         // FRAMA full window N (even)
var s2_MidWeight;      // weight of High and Low in the (H+L)/2 input
int s2_MesaLen;        // MESA Stochastic window (Length)
int s2_MesaHP;         // MESA Stochastic roofing high-pass period (fixed in the source)
int s2_MesaSS;         // MESA Stochastic SuperSmoother period (fixed in the source)
int s2_C1SmaLen;       // SMA of the MESA output: C1's second line (two-lines cross)
var s2_LrsiGamma;      // Laguerre RSI gamma
var s2_LrsiMid;        // Laguerre RSI midline (C2 state)
int s2_LookBackBars;   // bars before StartDate that only warm the indicators
int s2_SeriesExtra;    // input series length beyond the longest window read
int s2_CountLen;       // length of the MESA-output counter series (current and previous value)

void s2_config_init()
{
	s2_FramaN = 32;                          // (a) TASC V.23:10 window N (default 16); 32 = slot choice, PROJECT_STATE 1.2
	s2_MidWeight = 1; s2_MidWeight /= 2;     // Price = (H+L)/2 (a) TASC V.23:10 Inputs
	s2_MesaLen = 20;                         // (a) TASC V.32:1 Inputs Length(20)
	s2_MesaHP = 48;                          // (a) TASC V.32:1 sidebar, fixed 48
	s2_MesaSS = 10;                          // (a) TASC V.32:1 sidebar, fixed 10
	s2_C1SmaLen = 10;                        // (a) [V18] "just leave it on ten"; T3 amendment 1 (other lengths: T11 levels)
	s2_LrsiGamma = 1; s2_LrsiGamma /= 2;     // 0.5 (a) Cybernetic Analysis p. 221 default; T3.2
	s2_LrsiMid = 1; s2_LrsiMid /= 2;         // 0.5 midline (c) T3.2, our adaptation
	s2_LookBackBars = 520;                   // (c) same bars as PERF1 (R-D4, PERF2 Range); FRAMA residual 5.2e-3 worst case
	s2_SeriesExtra = 2;                      // (c) margin over the longest index read
	s2_CountLen = 2;                         // (c) the counter reads [0] and [1] only
}
