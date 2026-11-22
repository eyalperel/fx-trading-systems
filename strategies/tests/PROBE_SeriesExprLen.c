// PROBE_SeriesExprLen.c -- ATR stage 2, pre-run (vi): does series(0, L + 2), a length that is a parameter EXPRESSION, compile in
// Zorro 3.11 Light-C, and does every CALL of the same function get its own series slot?
// Pre-registration: analysis/harness/specs/ATR_MT4Fidelity.toml [prerun].cond_vi / pass_condition (vi); brief docs/harness/ATR_STAGE2_PROMPT.md section 2.
// Not an indicator test: a probe. The checker analysis/harness/tools/check_probe_series_len.py gives PASS / FAIL.
// Clock: EUR/USD D1, StartDate 20080101 / EndDate 20240101 as the generated script (Warning 047 expected, gotchas 9d.7). Inputs: per-script bar counter pse_bar (integer, from 1). Call 1: pse_f(14, bar); call 2: pse_f(20, 1000 + bar); unconditional, fixed order.
// pse_f writes x into slot 0 of series(0, L + 2) and returns the OLDEST slot [L + 1].
// Output: Data/PROBE_SeriesExprLen.csv: header "bar,r14,r20", one row per bar, 60 rows, %.15e; written before quit() (gotchas 9d.4).
//   The file is never overwritten: if it exists at INITRUN, the script refuses (prints REFUSED, writes nothing). Delete it by hand to rerun.
// Expected (b, by construction; pre-registered in the brief): r14 = bar - 15 for bar > 15; r20 = 1000 + bar - 21 for bar > 21;
//   earlier rows 0 (series(0, n) starts at 0, gotchas 9d.6). Padding other than 0 is a finding to report, not a failure.
// Run card: pick PROBE_SeriesExprLen in the Script dropdown (folder: repo strategies/tests/), restart Zorro first, ONE [Test] click.
//   Expect no line starting with `Error` in the Zorro window; the last message is "PROBE_SeriesExprLen: 60 rows written".
#include <default.c>

#define PSE_FILE "Data/PROBE_SeriesExprLen.csv"
#define PSE_NBARS 60

static int pse_bar = 0;
static int pse_done = 0;
static int pse_refuse = 0;

var pse_f(int L, var x)
{
    vars pse_s = series(0, L + 2);
    pse_s[0] = x;
    return pse_s[L + 1];
}

void run()
{
    BarPeriod = 1440;
    StartDate = 20080101;
    EndDate   = 20240101;
    LookBack  = 0;
    asset("EUR/USD");

    if(is(INITRUN)) {
        pse_bar = 0; pse_done = 0; pse_refuse = 0;      // declared initialisers (9b)
        if(file_length(PSE_FILE) > 0) {                 // no-overwrite guard
            pse_refuse = 1;
            printf("\nPROBE_SeriesExprLen REFUSED: %s exists; delete it to rerun", PSE_FILE);
        }
        return;
    }
    if(is(EXITRUN)) return;
    if(pse_refuse || pse_done) return;

    pse_bar = pse_bar + 1;
    var bar = pse_bar;                                  // integer-built (no literal)
    var r14 = pse_f(14, bar);                           // call 1
    var r20 = pse_f(20, 1000 + bar);                    // call 2
    if(pse_bar == 1)
        file_append(PSE_FILE, "bar,r14,r20\n", 0);
    file_append(PSE_FILE, strf("%d,%.15e,%.15e\n", pse_bar, r14, r20), 0);
    if(pse_bar >= PSE_NBARS) {
        pse_done = 1;
        printf("\nPROBE_SeriesExprLen: %d rows written", pse_bar);
        quit("PROBE_SeriesExprLen done");
    }
}
