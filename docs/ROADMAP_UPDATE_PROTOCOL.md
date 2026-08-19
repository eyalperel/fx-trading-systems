# Roadmap Update Protocol

**Status:** Dormant. Written for a phase the project is not yet in.
**Moved out of project instructions:** 2026-08-13, Week 13 Day 3.

## Why it is dormant

The protocol below screens external research on whether it "improves Sharpe ratio
or reduces drawdown". The project has not run a backtest. There is no Sharpe
ratio yet, so nothing can pass that test. Its search topics (reinforcement
learning, ML strategy development) also do not match current work, which is
measuring filter frequency response, lag and bandwidth.

It went 13 weeks without being triggered. That is a fit problem, not neglect.

## TRIGGER CONDITIONS — Claude must raise this when any of these occur

1. Before the first walk-forward optimization run (Phase 2.5, Week 15+)
2. Before Phase 2.5 pre-registration criteria are written
3. Whenever the roadmap file itself is being edited
4. When the user says "Time for roadmap update"

On 1-3, Claude does not run the protocol — it says the protocol exists, is
written for the wrong phase, and asks whether to rewrite it for the decision
actually being made.

## Rewrite needed before use

If revived for Phase 2.5, the search topics should target the decisions being
made then, not the current list:

- Walk-forward optimization methodology and window selection
- Overfitting detection in systematic strategies
- Multiple-testing correction for parameter sweeps
- Backtest statistics: deflated Sharpe, minimum track record length
- Regime-aware validation design

## Original protocol, unmodified

**Trigger:** User will message "Time for bi-weekly roadmap update" every 2 weeks

**When Triggered, Claude Must:**

1. **Search for latest developments:**
   - Machine learning trading strategies [current month/year]
   - Algorithmic trading new techniques [current month/year]
   - Reinforcement learning trading advances [current month/year]
   - Time series forecasting AI methods [current month/year]
   - Systematic trading technology trends [current month/year]

2. **Assess Impact & Categorize:**
   - HIGH PRIORITY: Integrate immediately into current phase
   - MEDIUM PRIORITY: Add to backlog for later phases
   - LOW PRIORITY: Monitor only, don't add yet
   - IGNORE: Not relevant to systematic trading goals

3. **Integration Rules - Only Add If:**
   - Aligns with NNFX methodology
   - Implementable in Zorro/Python
   - Has proven backtesting evidence
   - Improves Sharpe ratio or reduces drawdown
   - Doesn't require unavailable data sources

4. **What to IGNORE:**
   - HFT-specific techniques (wrong timeframe)
   - Crypto hype without systematic basis
   - Overly complex methods that can't be validated
   - Techniques requiring expensive data access

5. **Deliver Results As:**
   - Summary of significant developments
   - Recommended changes (Add/Replace/Defer/Ignore)
   - Updated roadmap section if changes approved
   - Changelog entry documenting what changed and why

**User's Role:** Review recommendations and approve/reject changes

**Version Control:** Save as FX_Roadmap_v[YYYY.MM.DD].md after each update
