// =============================================================================
// FisherTransform.c  (corrected; replaces the version of blob 259954ed, see below)
//
// Source (a): Ehlers, "Using The Fisher Transform", Technical Analysis of Stocks &
//   Commodities V.20:11 (2002), pp. 40-42, Fig. 5 (EasyLanguage), p. 41.
// Formula in Light-C terms (a): Price input (default (H+L)/2), Len (default 10);
//   raw   = 2*((Price - MinL)/(MaxH - MinL) - .5), MinL / MaxH over the last Len values
//           of Price including the current one;
//   Value1 = .33*raw + .67*Value1[1];
//   if Value1 > .99 then Value1 = .999; if Value1 < -.99 then Value1 = -.999
//           (the trigger and the set value differ, as printed);
//   Fish  = .5*ln((1 + Value1)/(1 - Value1)) + .5*Fish[1];
//   trigger = Fish[1].
// (a) The book version (Cybernetic Analysis, 2004, Fig. 1.7, p. 7: .5 / .5, .9999,
//   .25*ln) is a DIFFERENT indicator; it is not implemented here (review section 1).
//
// Deviations fixed (b), review docs/harness/FISHER_SOURCE_REVIEW.md (bdc83da):
//   F-1 per-instance state: the old static ft_Value1, static ft_Fish and the global
//       ft_Trigger were shared by every call, so a second instance or an asset loop
//       silently corrupted every instance (up to 2.7 in Fish; review section 3).
//   F-2 Price is a parameter (the old file read priceHigh() / priceLow() itself).
//   F-3 the constants are built from integers (the old float32 literals moved Fish
//       by up to 1.29e-5).
//   F-7 FisherCore exports raw, Value1, the range and the trigger.
//   F-8 this header.
// Outputs after the first ~100 bars of a single instance on one asset differ from the
// old file only by the F-3 rounding (<= 1.3e-5 on these test inputs); any second
// instance or asset loop was wrong.
//
// Our guard (b, F-4): when MaxH - MinL is not > 0 (flat window), raw = 0
//   (mid-channel). Not in the source (it divides by zero).
//
// Caller requirements:
//   - pass a series of at least Len values (MaxVal / MinVal read Price[0..Len-1]);
//     the default series() length is LookBack (c).
//   - for the source's input use  vars mid = series((priceHigh() + priceLow())/2);
//   - use the caller's own prefix for its locals, never fi_ (FisherCore's prefix; flat namespace, gotchas 1.3).
//   - call unconditionally every bar, before any LOOKBACK return (gotchas 3.1).
//   - trigger: FisherCore(..., &trig) or the caller's own Fish[1].
//
// Start-up: the source defines none (review F-5). Value1 and Fish start at 0 on the
//   instance's first call; the window is padded with the first value until Len values
//   exist (gotchas 9d.6). Treat the first ~100 bars as warm-up (the harness uses W = 700).
//
// Behaviour (b, review section 3 and the spec observations): raw in [-1, 1];
//   |Value1| <= .999; |Fish| <= ln(1999) = 7.6004 (reached on a steady trend).
//   Fisher SATURATES on long cycles: at T = 100 about two thirds of bars sit at the
//   clamp and Fish at about +-7.6; at T = 40, Len 10, 20% of bars. Readings beyond
//   +-2.5 are routine on any cycle with T >= 20 (Len 10). The Fish feedback is not an
//   EMA: the gain from arctanh(Value1) to Fish is 1/(1 - .5) = 2.
//
// Use stated by the source (a): Fish crossing its one-bar-delayed trigger identifies
//   cyclic turning points. Not implemented here.
//
// STATE: no statics; both series() calls are unconditional and first; each instance
//   has its own state. No includes needed.
//
// Verification: analysis/harness/specs/FSH_ArticleFidelity.toml (pre-registered 258b24a).
//   NOT VERIFIED until that run passes.
// =============================================================================

var FisherCore(vars Price, int Len, var* pRaw, var* pV1, var* pRng, var* pTrig) {
    vars fi_V = series(0, 2);
    vars fi_F = series(0, 2);
    var fi_a = 33;   fi_a = fi_a/100;
    var fi_b = 67;   fi_b = fi_b/100;
    var fi_t = 99;   fi_t = fi_t/100;
    var fi_c = 999;  fi_c = fi_c/1000;
    var fi_h = 1;    fi_h = fi_h/2;
    var fi_hi = MaxVal(Price, Len);
    var fi_lo = MinVal(Price, Len);
    var fi_rng = fi_hi - fi_lo;
    var fi_raw = 0;
    if(fi_rng > 0) {
        fi_raw = Price[0] - fi_lo;
        fi_raw = fi_raw/fi_rng;
        fi_raw = fi_raw - fi_h;
        fi_raw = fi_raw*2;
    }
    fi_V[0] = fi_a*fi_raw + fi_b*fi_V[1];
    var fi_nt = 0;   fi_nt = fi_nt - fi_t;
    var fi_nc = 0;   fi_nc = fi_nc - fi_c;
    if(fi_V[0] > fi_t)  fi_V[0] = fi_c;
    if(fi_V[0] < fi_nt) fi_V[0] = fi_nc;
    var fi_u = 1;
    var fi_num = fi_u + fi_V[0];
    var fi_den = fi_u - fi_V[0];
    fi_F[0] = fi_h*log(fi_num/fi_den) + fi_h*fi_F[1];
    *pRaw  = fi_raw;
    *pV1   = fi_V[0];
    *pRng  = fi_rng;
    *pTrig = fi_F[1];
    return fi_F[0];
}

var FisherTransform(vars Price, int Len) {
    var fi_w1;
    var fi_w2;
    var fi_w3;
    var fi_w4;
    return FisherCore(Price, Len, &fi_w1, &fi_w2, &fi_w3, &fi_w4);
}
