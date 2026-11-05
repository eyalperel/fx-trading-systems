// H1_IncludeProbe_BAD.c
//
// PURPOSE:  Criteria S8 (observation, not a pass condition): confirm that Zorro resolves
//           #include "../../..." relative to the script's own folder, by showing that a
//           deliberately WRONG include path fails to compile.
// EXPECTED: COMPILE ERROR naming the include file below. The script must NOT run.
//           If it compiles and runs, report that: it means include errors are not caught.
// OUTPUT:   none.

#include <default.c>
#include "../../indicators/ehlers/H1_PROBE_DOES_NOT_EXIST.c"

void run()
{
	printf("\nH1 probe: compiled although the include does not exist - REPORT THIS");
	quit("H1 probe compiled (unexpected)");
}
