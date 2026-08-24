# /upgrade-quant-stack

Fetches and integrates the vetted repos from
`.agents/skills/quant-sports-toolkit/SKILL.md` into this workspace, then
upgrades the sports-betting model and the forex model to use them at full
strength. Run this once to bootstrap, and re-run anytime after adding a
new repo to the skill file.

## Steps

1. **Read the skill file first.**
   Load `.agents/skills/quant-sports-toolkit/SKILL.md` in full — it is the
   source of truth for which repos to fetch and why. Do not clone anything
   not listed there without asking first.

2. **Set up the reference workspace.**
   Create `reference/` at repo root if it doesn't exist, and add it to
   `.gitignore` (these are read-only research clones, not our code).

3. **Clone the core toolkit.**
   ```bash
   mkdir -p reference && cd reference
   git clone --depth 1 https://github.com/georgedouzas/sports-betting.git
   git clone --depth 1 https://github.com/hudson-and-thames/mlfinlab.git
   git clone --depth 1 https://github.com/polakowo/vectorbt.git
   git clone --depth 1 https://github.com/robcarver17/pysystemtrade.git
   cd ..
   ```
   If any clone fails (renamed/archived repo), search GitHub for the
   current name/fork before skipping it — note the replacement in the
   skill file.

4. **Install the sports-betting toolkit into our environment.**
   ```bash
   uv add sports-betting  # or: pdm add sports-betting
   uv add 'sports-betting[mcp]'
   ```

5. **Wire the sports model.**
   - In `sports_model/`, create a `KenyanBookDataLoader` that follows the
     `sportsbet.datasets.SoccerDataLoader` interface from
     `reference/sports-betting`, pulling from our existing scraped-odds
     source as one leg and a sharp reference book (Bet365/Pinnacle) as the
     other.
   - Wrap our current classifier in `sportsbet.evaluation.ClassifierBettor`
     and run its walk-forward `backtest()` against our historical match
     data — do not hand-roll a new backtest loop for this.
   - Port the purged/embargoed cross-validation split from
     `reference/mlfinlab` into `core/validation.py` and use it inside the
     backtest instead of a plain `TimeSeriesSplit`, so adjacent-day leakage
     doesn't inflate results.
   - Add a `core/clv.py` if it doesn't exist: for every settled bet, store
     the closing sharp-book line alongside our bet price, and compute CLV
     — this becomes the primary "is this edge real" metric, per AGENTS.md.
   - Replace any fixed-stake logic with fractional-Kelly sizing (default
     0.25), reading bankroll and edge from the backtest output.

6. **Wire the forex model.**
   - Stand up (or migrate our existing signal logic into) a `vectorbt`- or
     `backtrader`-based backtest in `fx_model/`, following the module
     layout in `reference/pysystemtrade` for separating signal generation,
     position sizing, and risk scaling.
   - Reuse the same `core/validation.py` purged walk-forward split so both
     models are validated identically.

7. **Run and report.**
   - Run both backtests. Append results (date, commit hash, dataset
     window, Sharpe/ROI/CLV) to `experiments/log.csv` per AGENTS.md.
   - Summarize: did wiring in the maintained libraries change backtest
     results materially versus our hand-rolled version? Flag anything
     that looks like previously-hidden leakage or an inflated edge.

8. **Do not proceed to live/production staking changes automatically.**
   Stop after reporting backtest deltas and ask before changing any
   real-money staking config — this workflow is for research/model
   infrastructure only.
