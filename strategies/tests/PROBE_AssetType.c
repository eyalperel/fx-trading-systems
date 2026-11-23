// PROBE_AssetType.c - which asset names does Zorro 3.11 identify as Forex? (P5, 2026-11-23)
//
// Why: TPL_Costs run 1 found assetType("EUR_A10_USD") = 0, so Zorro costed the synthetic assets per
// contract instead of per 10000 units (docs/preregistration/TPL_Costs_P5_Criteria.md, run 1).
// The manual (asset.htm): "If the name begins and ends with the 3-letter abbreviation of a currency,
// it is identified as Forex; if it ends with a number, it is identified as an index."
// This probe prints assetType() for candidate names. It loads no history and makes no trade.
// Output: Data/PROBE_AssetType.csv and the message window. 1 = FOREX, 2 = INDEX, 0 = unknown.

#include <default.c>

string pat_Out = "Data\\PROBE_AssetType.csv";

void pat_one(string pat_n)
{
	int pat_t = assetType(pat_n);
	printf("\n%s -> %i", pat_n, pat_t);
	file_append(pat_Out, strf("%s,%i\n", pat_n, pat_t));
}

void run()
{
	if(is(INITRUN)) {
		file_delete(pat_Out);
		file_append(pat_Out, "name,assetType\n");
		// real pairs (controls: expected 1)
		pat_one("EUR/USD");
		pat_one("EURUSD");
		// run 1 name shape and variants
		pat_one("EUR_A10_USD");
		pat_one("EUR_USD");
		pat_one("EURA10USD");
		// ISO 4217 test / no-currency codes
		pat_one("XTS/XXX");
		pat_one("XTSXXX");
		pat_one("XTS/USD");
		pat_one("EUR/XTS");
		// made-up codes
		pat_one("ABC/DEF");
		pat_one("SYA/SYB");
		pat_one("XTA/XTB");
		// index control (ends with a number: expected 2)
		pat_one("SYN_A2");
		pat_one("GER30");
		quit("assetType probe done");
	}
}
