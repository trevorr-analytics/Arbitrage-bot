import os
import json
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sports_model'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from dixon_coles import DixonColesModel, load_league_data
from simulation import simulate_match
from basketball_model import BasketballModel

tracker_path = os.path.join(os.path.dirname(__file__), 'sports_model', 'acca_tracker.json')

with open(tracker_path, 'r') as f:
    data = json.load(f)

soccer_models = {}
bb_models = {}

updated_count = 0

for acca in data:
    for leg in acca.get('legs', []):
        league = leg.get('league')
        home = leg.get('home')
        away = leg.get('away')
        market = leg.get('market')
        
        if league not in ["NBA", "EuroLeague", "NCAAB", "WNBA"]:
            if "mc_stats" not in leg:
                if league not in soccer_models:
                    model = DixonColesModel()
                    try:
                        ldata = load_league_data(league, min_seasons=2)
                        model.fit(ldata)
                        soccer_models[league] = model
                    except Exception:
                        soccer_models[league] = None
                
                model = soccer_models[league]
                if model:
                    try:
                        home_xg, away_xg = model._get_lam_mu(home, away)
                        rho = model.params_[-1] if model.params_ is not None else None
                        res = simulate_match(home_xg, away_xg, n_sims=5000, dixon_coles_rho=rho, seed=42)
                        table = res.scoreline_table(max_goals=5)
                        top_scores = sorted(table.items(), key=lambda kv: kv[1], reverse=True)[:3]
                        leg["mc_stats"] = {
                            "win_prob": res.home_win_pct,
                            "draw_prob": res.draw_pct,
                            "loss_prob": res.away_win_pct,
                            "top_scores": top_scores,
                            "ov15": res.over_under(1.5)["over_1.5"],
                            "ov25": res.over_under(2.5)["over_2.5"],
                            "btts_yes": res.btts()["btts_yes"]
                        }
                        updated_count += 1
                    except Exception as e:
                        pass
        else:
            if "bb_stats" not in leg:
                if league not in bb_models:
                    model = BasketballModel()
                    try:
                        model.fit(None, league_name=league)
                        bb_models[league] = model
                    except Exception:
                        bb_models[league] = None
                
                model = bb_models[league]
                if model:
                    try:
                        import re
                        line_match = re.search(r"(\d+\.?\d*)", market)
                        line = float(line_match.group(1)) if line_match else 225.5
                        res = model.predict(home, away, over_under_line=line, league=league)
                        leg["bb_stats"] = {
                            "win_prob": res["home_win"],
                            "loss_prob": res["away_win"],
                            "over": res["over_total"],
                            "under": res["under_total"],
                            "line": line
                        }
                        updated_count += 1
                    except Exception:
                        pass

if updated_count > 0:
    with open(tracker_path, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Enriched {updated_count} legs with MC/BB stats.")
else:
    print("No legs needed enrichment.")
