# AGENTS.md — Quant / Sports-Betting Model Workspace

Standing instructions for any Antigravity agent working in this repo.
Applies to the Kenyan-sportsbook value-betting model and the forex quant model.

## Environment
- Python 3.11+, dependency management via `uv` or `pdm` (never bare pip in-repo).
- Keep the sports model and the forex model in separate top-level packages
  (`sports_model/`, `fx_model/`) sharing a common `core/` for odds math,
  backtesting utilities, and Kelly sizing — do not duplicate de-vig or
  EV logic between them.
- All third-party research repos referenced in
  `.agents/skills/quant-sports-toolkit/SKILL.md` get vendored under
  `reference/<repo-name>/` as **read-only reference material** — never
  imported directly into production code. Port only the specific
  function/idea you need into `core/`, cited with a source comment.

## Code standards
- Type hints required on every public function, especially anything
  touching odds, stakes, or probabilities (e.g. `float` vs `Decimal` matters —
  use `Decimal` for stake/bankroll math, `float` is fine for probabilities).
- No silent fallbacks: if a bookmaker feed or odds source fails, raise —
  never bet on stale or partial data.
- Every model change must be paired with a backtest run before merge.
  No PR that changes staking, EV threshholds, or model weights merges
  without a backtest diff attached.

## Data
- Never commit scraped odds data or API keys to git — `data/` and `.env` are
  gitignored.
- All backtests are walk-forward (train on past, test on strictly future
  data) — never k-fold shuffle on time series. This is non-negotiable for
  both the sports model and the forex model.
- Log every backtest run (date, git commit hash, dataset window, resulting
  Sharpe/ROI/CLV) to `experiments/log.csv` — don't overwrite prior runs.

## Betting/trading-specific conventions
- Every "edge" claim must report **closing-line value (CLV)**, not just
  raw ROI against a single soft book's opening price — see
  `.agents/skills/quant-sports-toolkit/SKILL.md` for the reference
  implementation pattern.
- Stake sizing goes through a fractional-Kelly function by default
  (configurable fraction, default 0.25) — no fixed-stake or arbitrary
  unit sizing in production code paths.
- Flag and log anything that looks like account-limiting risk (stake
  caps hit, odds suddenly worse only for your account, delayed bet
  acceptance) — this is operationally as important as the model's edge.

## When starting a task
Check `.agents/skills/quant-sports-toolkit/SKILL.md` before writing new
modeling, backtesting, or staking code — it catalogs vetted open-source
libraries for this exact use case. Prefer wiring in a maintained library
over hand-rolling backtesting, de-vig, or Kelly-sizing math from scratch.
