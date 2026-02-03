function run()
{
    set(LOGFILE);
    Verbose = 2;

    BarPeriod = 1440;
    LookBack  = 50;
    StartDate = 20240101;
    EndDate   = 20240131;

    asset("EUR/USD");

    // DAILY series every bar
    TimeFrame = 1;
    vars D = series(priceClose());

    // WEEKLY (7-bar frame) series every bar
    TimeFrame = 7;
    vars W = series(priceClose());

    // Back to daily (hygiene)
    TimeFrame = 1;

    // Detect a new weekly frame by change in W[0] vs W[1]
    // (When a new frame starts, the last frame’s close becomes W[1])
    if(W[0] != W[1]) {
        var LastDailyClose = D[0];     // close of current daily bar
        var LastWeeklyClose = W[1];    // close of the just-finished weekly frame
        printf("\nNew weekly frame started at Bar %d",Bar);
        printf("\nLast weekly close = %.5f",LastWeeklyClose);
        printf("\nLast daily close  = %.5f",LastDailyClose);
    }
}
