// ===== DEBUGGING TOOLKIT =====

// 1. Watch variables in real-time
watch("Variable name", variableName);

// 2. Print with prefixes
printf("\n[FunctionName] Message: value=%.5f", value);

// 3. Conditional breakpoint
if(Bar == 100 && condition) {
    printf("\n=== BREAKPOINT HIT ===");
    quit("Debug stop");
}

// 4. Visual debugging
plot("Indicator", value, LINE, BLUE);

// 5. Full logging
Verbose = 2;
set(LOGFILE);

// 6. Series inspection
printf("\n[0]=%.5f [1]=%.5f [2]=%.5f", Series[0], Series[1], Series[2]);