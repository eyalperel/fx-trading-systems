// XCHK_ATRMT4_vs_ATRS.c -- ATR stage 2, real-data cross-check S8 / AT-5: ATRMT4 (indicators/nnfx/ATR.c) against Zorro's ATRS(14).
// Pre-registration: analysis/harness/specs/ATR_MT4Fidelity.toml [cross_check] (criterion: on rows >= 100, max relative |diff| <= 1e-9, (c));
//   brief docs/harness/ATR_STAGE2_PROMPT.md section 3.
// Inputs: EUR/USD D1 (dev set), Zorro history, StartDate 20100101, EndDate 20240101, LookBack = 100 (c: >= 100 per the spec).
// Per bar, unconditionally and BEFORE the lookback return (gotchas 4.1): series(priceHigh/Low/Close(), 16), ATRMT4(.., 14), ATRS(14).
// Output: Data/XCHK_ATR_raw.csv: every bar incl. lookback bars (flag): date,bar,lookback,atrmt4,atrs,absdiff,reldiff,close ; %.15e.
//   reldiff = absdiff / atrs, 0 when atrs = 0. `close` is the (b) magnitude guard column for the checker (wrong asset): 0.8 .. 1.7.
//   Never overwritten: if the file exists at INITRUN the script refuses (prints REFUSED, writes nothing). Rows are written bar by bar.
// Checker: analysis/harness/tools/check_xchk_atr.py. Not run in stage 2.
// Run card: after the main run (GEN_ATR_MT4); pick XCHK_ATRMT4_vs_ATRS (folder: repo strategies/tests/), restart Zorro first, ONE [Test] click.
//   Expect no line starting with `Error` in the Zorro window.
#include <default.c>
#include "../../indicators/nnfx/ATR.c"

#define XA_FILE "Data/XCHK_ATR_raw.csv"

static int xa_bar = 0;
static int xa_hdr = 0;
static int xa_refuse = 0;

void run()
{
    BarPeriod = 1440;
    StartDate = 20100101;
    EndDate   = 20240101;
    LookBack  = 100;
    asset("EUR/USD");

    if(is(INITRUN)) {
        xa_bar = 0; xa_hdr = 0; xa_refuse = 0;          // declared initialisers (9b)
        if(file_length(XA_FILE) > 0) {                  // no-overwrite guard
            xa_refuse = 1;
            printf("\nXCHK_ATR REFUSED: %s exists; move or delete it to rerun", XA_FILE);
        }
        return;
    }
    if(is(EXITRUN)) return;
    if(xa_refuse) return;

    vars xa_h = series(priceHigh(), 16);
    vars xa_l = series(priceLow(), 16);
    vars xa_c = series(priceClose(), 16);
    var xa_m = ATRMT4(xa_h, xa_l, xa_c, 14);
    var xa_z = ATRS(14);

    int xa_lb = 0;
    if(is(LOOKBACK)) xa_lb = 1;
    var xa_d = abs(xa_m - xa_z);
    var xa_r = 0;
    if(xa_z != 0) xa_r = xa_d / xa_z;

    if(!xa_hdr) {
        file_append(XA_FILE, "date,bar,lookback,atrmt4,atrs,absdiff,reldiff,close\n", 0);
        xa_hdr = 1;
    }
    file_append(XA_FILE, strf("%d,%d,%d,%.15e,%.15e,%.15e,%.15e,%.15e\n",
        ymd(wdate()), xa_bar, xa_lb, xa_m, xa_z, xa_d, xa_r, xa_c[0]), 0);
    xa_bar = xa_bar + 1;
}
