# /simulate-match

Runs a Monte Carlo simulation on one or more upcoming matches using
`core/simulation.py`, sized appropriately to the market being checked, and
reports the resulting probabilities against the sportsbook price.

## When to use this
Run automatically whenever a match has passed the value-bet screen (local
book price vs. de-vigged sharp reference, per the quant-sports-toolkit
skill) and needs a full outcome distribution before staking — not just a
single win-probability number.

## Steps

1. **Get expected goals, don't estimate them here.**
   Pull `home_xg` / `away_xg` from the existing Poisson/Dixon-Coles model
   output for the match. This workflow simulates outcomes from those
   numbers — it never invents or adjusts xG itself. If the model hasn't
   produced xG for this match yet, stop and run the model first.

2. **Pick simulation count by market, not a fixed default:**
   - Match-winner, over/under, BTTS → `n_sims = 50_000`
   - Correct-score or any market pulling a specific low-frequency
     scoreline → `n_sims = 200_000` (rare scorelines need a larger pool
     to keep standard error low)
   - If checking many matches in a batch/backtest run rather than
     previewing one live match → keep `n_sims = 50_000` per match; more
     matches beats over-simulating any single one.

3. **Always pass a seed** (e.g. the match ID or a fixed integer) when the
   result will be used in a backtest or logged for validation — the
   validation-gate requires reproducible results run to run.

4. **Apply the Dixon-Coles adjustment** (`dixon_coles_rho`) whenever the
   model has already fit a rho parameter — do not leave it out silently;
   note explicitly in output if rho is unavailable and independent
   Poisson was used instead, since that under-corrects low-scoring
   markets.

5. **Compute the market being checked:**
   - Match-winner → `home_win_pct` / `draw_pct` / `away_win_pct`
   - Totals → `over_under(line)`
   - BTTS → `btts()`
   - Exact score → `scoreline_table()`, report the specific scoreline's
     probability plus its standard error (`sqrt(p*(1-p)/n_sims)`), not
     just the probability alone.

6. **Convert to EV against the market price**, not just report the raw
   simulated probability:
   ```
   EV = (sim_probability * (decimal_odds - 1)) - (1 - sim_probability)
   ```
   using the local sportsbook's decimal odds for that specific market.

7. **Report using this format — never just a probability on its own:**
   ```
   MATCH: <teams, date>
   MARKET: <e.g. "Match winner", "Over/Under 2.5", "Correct score 1-0">
   n_sims: <int>          seed: <int>
   Simulated probability: <value>  (SE: ±<value>)
   Market odds: <decimal>          Implied probability: <value>
   EV: <value>
   Dixon-Coles rho applied: <yes/no>
   ```

8. **Do not stake off this output directly.** A simulation result feeding
   into a real bet still has to clear `.agents/skills/validation-gate/SKILL.md`
   (§1-4) before being called a validated edge — this workflow produces
   the probability/EV inputs the gate checks, not a final go/no-go itself.
