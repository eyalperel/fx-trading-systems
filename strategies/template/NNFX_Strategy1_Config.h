// NNFX_Strategy1_Config.h - every number used by Strategy 1's slot source (T11; decisions R-D3, R-D4).
// Config mode of tools/lint_literals.py: each line holding a number carries a source label; non-integers are
// built from integers (gotchas 9d.1). Changing a value is a named, counted variant (T11). Prefix s1_.

var s1_FastLimit;      // MAMA FastLimit
var s1_SlowLimit;      // MAMA SlowLimit
var s1_MidWeight;      // weight of High and Low in the (H+L)/2 input
int s1_FisherLen;      // Fisher window
int s1_ReflexLen;      // Reflex assumed cycle period
int s1_LookBackBars;   // bars before StartDate that only warm the indicators
int s1_SeriesExtra;    // input series length beyond the longest window read

void s1_config_init()
{
	s1_FastLimit = 1; s1_FastLimit /= 2;     // 0.5 (a) TASC V.19:9 Inputs; R-D3
	s1_SlowLimit = 1; s1_SlowLimit /= 20;    // 0.05 (a) TASC V.19:9 Inputs; R-D3
	s1_MidWeight = 1; s1_MidWeight /= 2;     // Price = (H+L)/2 (a) TASC V.19:9, V.20:11 Inputs
	s1_FisherLen = 10;                       // (a) TASC V.20:11 Inputs; R-D3
	s1_ReflexLen = 20;                       // (a) TASC V.38:02 default; R-D3 (50 = T11 level, [C12])
	s1_LookBackBars = 520;                   // (c) covers FAMA's ~500-bar start-up (MAMA review MA-1); R-D4
	s1_SeriesExtra = 2;                      // (c) margin over the longest index read
}
