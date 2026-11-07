#!/usr/bin/env bash
# Runs the harness test suite and prints one summary line plus every skip with its reason.
#   bash analysis/harness/run_tests.sh
# Optional: HARNESS_TEST_DIR=<dir> runs another suite (used by test_generator G9 on a fixture).
# Last lines:  TOTAL n  PASS p  FAIL f  ERROR e  SKIP s
# Exit code: that of unittest (0 = all ran OK, skips allowed).
set -u
cd "$(dirname "$0")/../.." || exit 1
dir="${HARNESS_TEST_DIR:-analysis/harness/tests}"

out=$(python -u -m unittest discover -s "$dir" -v 2>&1)
rc=$?
printf '%s\n' "$out"

total=$(printf '%s\n' "$out" | sed -n 's/^Ran \([0-9][0-9]*\) test.*/\1/p' | tail -1)
last=$(printf '%s\n' "$out" | grep -E '^(OK|FAILED)' | tail -1)
getn() { printf '%s\n' "$last" | grep -o "$1=[0-9]*" | head -1 | cut -d= -f2; }
f=$(getn failures); e=$(getn errors); s=$(getn skipped)
f=${f:-0}; e=${e:-0}; s=${s:-0}
if [ -z "${total:-}" ]; then
    echo "TOTAL ?  PASS ?  FAIL ?  ERROR ?  SKIP ?   (no 'Ran N tests' line: the suite did not run)"
    exit 1
fi
p=$((total - f - e - s))

echo
printf '%s\n' "$out" | awk '
    /^test[A-Za-z0-9_]* \(/ { name = $1 }
    /\.\.\. skipped / { sub(/^.*\.\.\. skipped /, ""); print "SKIP  " name ": " $0 }
'
echo "TOTAL $total  PASS $p  FAIL $f  ERROR $e  SKIP $s"
exit $rc
