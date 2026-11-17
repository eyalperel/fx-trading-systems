// PROBE_LiteralEval_20261117.c -- how Zorro 3.11 evaluates the literal expression 0.707*2.0*PI / HPPeriod
// Why: HP_ArticleFidelity run 1 (a361e4b) failed only HPF-NCH-imp-pass (2.244e-7). The old HighPassFilter.c
// alpha, written with the literal 0.707, differs from the float32 model by 3.6e-7 relative (b, back-check).
// This probe prints each evaluation step at full precision so the NCH model can be fixed from measurement (c->b).
// Output: Data/PROBE_LiteralEval.csv, lines "label,value" with %.17e. One [Test] click; quits after one bar.
// Not a harness test: it has no pass condition. It measures; the planning chat interprets.
#include <default.c>

var probe_alpha_nch(vars Dummy, int HPPeriod)     // identical expression to the old .c / NCH body
{
    var alpha1 = (cos(0.707*2.0*PI / HPPeriod) + sin(0.707*2.0*PI / HPPeriod) - 1.0)
           / cos(0.707*2.0*PI / HPPeriod);
    return alpha1;
}

var probe_alpha_corr(vars Dummy, int HPPeriod)    // corrected .c expression
{
    var hp_k = sqrt(2.0) / 2.0;
    var alpha1 = (cos(hp_k*2.0*PI / HPPeriod) + sin(hp_k*2.0*PI / HPPeriod) - 1.0)
           / cos(hp_k*2.0*PI / HPPeriod);
    return alpha1;
}

void pr(string label, var v)
{
    file_append("Data/PROBE_LiteralEval.csv", strf("%s,%.17e\n", label, v), 0);
}

void run()
{
    BarPeriod = 1440;
    LookBack = 0;
    StartDate = 20200106;
    EndDate = 20200201;
    asset("EUR/USD");
    static int pd_done;
    if(is(INITRUN)) {
        pd_done = 0;
        file_delete("Data/PROBE_LiteralEval.csv");
        return;
    }
    vars pd_dummy = series(priceClose(), 3);
    if(pd_done) return;
    pd_done = 1;
    int P = 48;
    var v01 = PI;                         pr("L01_PI", v01);
    var v02 = 0.707;                      pr("L02_lit0707", v02);
    var v03 = 0.707*2.0;                  pr("L03_lit0707x2", v03);
    var v04 = 0.707*2.0*PI;               pr("L04_lit0707x2xPI", v04);
    var v05 = 0.707*2.0*PI / P;           pr("L05_theta_lit_divP", v05);
    var v06 = cos(0.707*2.0*PI / P);      pr("L06_cos_inline", v06);
    var v07 = sin(0.707*2.0*PI / P);      pr("L07_sin_inline", v07);
    var v08 = cos(v05);                   pr("L08_cos_of_var_theta", v08);
    var v09 = sin(v05);                   pr("L09_sin_of_var_theta", v09);
    var v10 = probe_alpha_nch(pd_dummy, 48);   pr("L10_alpha_nch_function", v10);
    var v11 = (cos(0.707*2.0*PI / P) + sin(0.707*2.0*PI / P) - 1.0) / cos(0.707*2.0*PI / P);
                                          pr("L11_alpha_inline_localP", v11);
    var v12 = (v08 + v09 - 1.0) / v08;    pr("L12_alpha_from_var_trig", v12);
    var k = 0.707;
    var v13 = k*2.0*PI / P;               pr("L13_theta_var_k", v13);
    var v14 = (cos(v13) + sin(v13) - 1.0) / cos(v13);  pr("L14_alpha_var_k", v14);
    var v15 = probe_alpha_corr(pd_dummy, 48);  pr("L15_alpha_corrected_function", v15);
    var v16 = 2.0*PI;                     pr("L16_2xPI", v16);
    var v17 = 0.707*(2.0*PI);             pr("L17_lit0707_x_paren2PI", v17);
    quit("PROBE done: 17 lines");
}
