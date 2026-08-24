---
name: quant-sports-toolkit
description: Curated open-source libraries and reference repos for building, backtesting, and hardening sports-betting value models and forex/quant trading models. Load this whenever the task involves odds modeling, de-vig math, value-bet detection, Kelly staking, backtesting engines, or algorithmic/forex trading infrastructure.
---

# Quant + Sports-Betting Toolkit

Reference catalog of vetted repos. Don't reinvent backtesting engines,
de-vig math, or staking logic — wire in one of these, then customize.
Clone into `reference/<name>/` (read-only), never import directly into
`core/` — port the specific logic you need with a source comment.

## 1. Sports betting — closest fit to our use case

**georgedouzas/sports-betting** — https://github.com/georgedouzas/sports-betting
The centerpiece. A scikit-learn-compatible toolkit purpose-built for this
exact workflow: `dataloaders` fetch historical results + real bookmaker
odds across 27+ leagues back to 1994; `bettors` wrap any sklearn estimator,
backtest it walk-forward, and surface value bets on upcoming fixtures. Has
a CLI, a GUI, and an MCP server (`sports_betting[mcp]`) so an agent can
drive it directly. **Start here for the Kenyan-sportsbook model** — swap in
your local odds feed as the second `DataLoader` source and it gives you
walk-forward backtesting and value-bet scoring for free.

**GitHub topic pages (browse for maintained, narrower repos):**
- https://github.com/topics/sports-betting
- https://github.com/topics/betting-models
- https://github.com/topics/sport-betting
- https://github.com/topics/poisson

Look specifically for repos tagged `dixon-coles`, `closing-line-value`,
`kelly-criterion`, and `devig` — several small, focused repos exist for
each (e.g. standalone devig + Kelly sizer utilities, CLV tracking with
sqlite, Dixon-Coles + lineup-aware soccer models walk-forward tested
against closing odds). Vet stars/last-commit date before vendoring.

**maxantcliff/football_basic_poisson** — https://github.com/maxantcliff/football_basic_poisson
Minimal, readable baseline Poisson goals model for football. Good as a
teaching reference for the math, not for production (author's own notes
say predictive power is weak) — use it to understand the mechanics, then
move to Dixon-Coles.

## 2. General backtesting engines (reusable for both models)

- **vectorbt** — https://github.com/polakowo/vectorbt — vectorized,
  very fast backtesting; good if you want to sweep thousands of parameter
  combinations (e.g. EV-threshold, Kelly fraction) quickly.
- **backtrader** (maintained fork) — https://github.com/cloudQuant/backtrader —
  event-driven backtesting/live-trading framework, mature ecosystem.
- **QSTrader** — https://github.com/mhallsmoore/qstrader — modular,
  schedule-driven backtesting engine, good architectural reference for
  separating signal generation from execution/risk.
- **pysystemtrade** — https://github.com/robcarver17/pysystemtrade —
  Rob Carver's production-grade systematic trading framework; excellent
  reference for position sizing and risk-scaling logic even if you don't
  use it directly.
- **zipline-reloaded** — https://github.com/stefan-jansen/zipline-reloaded —
  the maintained fork of Quantopian's Zipline, full backtest + paper/live
  loop.

## 3. Financial ML methodology

- **mlfinlab** (Hudson & Thames) — https://github.com/hudson-and-thames/mlfinlab —
  implements López de Prado's "Advances in Financial Machine Learning":
  proper time-series labeling (triple-barrier method), purged/embargoed
  cross-validation (critical — prevents the data leakage that inflates
  backtest results on both sports and forex models), sample weighting.
  **Use this specifically to fix walk-forward validation correctness.**
- **FinRL** (AI4Finance Foundation) — https://github.com/AI4Finance-Foundation/FinRL —
  reinforcement-learning trading framework; relevant only if you want to
  explore RL-based position sizing later, not a v1 priority.

## 4. Forex / algo trading specific

- **Getting-Started-with-Forex-Trading-Using-Python** (Packt) —
  https://github.com/PacktPublishing/Getting-Started-with-Forex-Trading-Using-Python —
  code companion for FX-specific data handling, indicator construction,
  and strategy scaffolding.
- **QuantConnect Lean** — https://github.com/QuantConnect/Lean —
  production-grade, broker-agnostic algo trading engine (equities, FX,
  crypto, futures) with a huge strategy library — heavier weight, but
  the reference implementation for going from backtest to live execution
  cleanly.
- **awesome-systematic-trading** — https://github.com/wangzhe3224/awesome-systematic-trading —
  curated index of trading libraries/data sources across asset classes;
  use as a directory when you need something not already listed here.
- **best-of-algorithmic-trading** — https://github.com/merovinh/best-of-algorithmic-trading —
  ranked list of algo trading libraries, updated weekly; good for
  discovering newly-maintained tools.

## 5. Aggregators to re-check periodically

Re-run a repo search against these topic/list pages every few months —
this space moves fast and better-maintained tools appear regularly:
- https://github.com/topics/algorithmic-trading-quantitative
- https://github.com/topics/forex
- https://github.com/EliteQuant/EliteQuant (long-running curated list)

## How to apply this to our two models

**Sports model (Kenyan sportsbook value betting):**
1. Fork the `sportsbet.datasets` pattern from georgedouzas/sports-betting —
   build a custom `DataLoader` for the local book's odds feed as one source
   and Bet365/Pinnacle as the "sharp reference" source.
   Wrap our existing classifier in `ClassifierBettor` to get walk-forward
   backtesting and value-bet output for free instead of hand-rolling it.
2. Pull the purged cross-validation approach from mlfinlab so backtest
   results aren't inflated by leakage between adjacent match-days.
3. Use the devig + Kelly patterns from the betting-models topic repos
   for stake sizing, per the fractional-Kelly rule in AGENTS.md.

**Forex model:**
1. Use vectorbt or backtrader as the backtesting core (vectorbt if we
   want to sweep many parameter sets fast; backtrader if we want closer
   parity with eventual live execution).
   pysystemtrade is worth reading (not necessarily running) for its
   position-sizing and risk-scaling design.
2. Apply the same mlfinlab-based purged walk-forward validation as the
   sports model, so both models share one validation methodology.
3. If/when we move toward live execution, QuantConnect Lean is the
   reference for broker-agnostic order routing.
