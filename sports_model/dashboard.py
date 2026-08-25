import sys
import os

# Insert paths to allow importing from core/ and sports_model/
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'core')))

import json
from datetime import datetime, timedelta, timezone
import pandas as pd
import streamlit as st

st.set_page_config(page_title="AutoQuant Betting Dashboard", layout="wide", initial_sidebar_state="collapsed")

# Load CSS
css_path = os.path.join(os.path.dirname(__file__), "style.css")
if os.path.exists(css_path):
    with open(css_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ----------------- SIMULATION HELPERS -----------------
@st.cache_resource
def get_soccer_model(league):
    from dixon_coles import DixonColesModel, load_league_data
    model = DixonColesModel()
    try:
        data = load_league_data(league, min_seasons=2)
        model.fit(data)
        return model
    except Exception as e:
        print(f"Failed to load soccer model for {league}: {e}")
        return None

@st.cache_resource
def get_basketball_model(league):
    from basketball_model import BasketballModel
    model = BasketballModel()
    try:
        model.fit(None, league_name=league)
        return model
    except Exception as e:
        print(f"Failed to load bb model for {league}: {e}")
        return None

@st.cache_data
def get_soccer_sim_data(league, home, away):
    model = get_soccer_model(league)
    if not model: return None
    try:
        home_xg, away_xg = model._get_lam_mu(home, away)
        rho = model.params_[-1] if model.params_ is not None else None
        from simulation import simulate_match
        res = simulate_match(home_xg, away_xg, n_sims=10000, dixon_coles_rho=rho, seed=42)
        table = res.scoreline_table(max_goals=5)
        top_scores = sorted(table.items(), key=lambda kv: kv[1], reverse=True)[:3]
        return {
            "win_prob": res.home_win_pct,
            "draw_prob": res.draw_pct,
            "loss_prob": res.away_win_pct,
            "top_scores": top_scores,
            "ov15": res.over_under(1.5)["over_1.5"],
            "ov25": res.over_under(2.5)["over_2.5"],
            "btts_yes": res.btts()["btts_yes"]
        }
    except Exception:
        return None

@st.cache_data
def get_basketball_sim_data(league, home, away, line):
    model = get_basketball_model(league)
    if not model: return None
    try:
        res = model.predict(home, away, over_under_line=line, league=league)
        return {
            "win_prob": res["home_win"],
            "loss_prob": res["away_win"],
            "over": res["over_total"],
            "under": res["under_total"],
            "line": line
        }
    except Exception:
        return None

# ----------------- DATA LOADING -----------------
@st.cache_data(ttl=60)
def load_data():
    try:
        path = os.path.join(os.path.dirname(__file__), os.path.join(os.path.dirname(__file__), "acca_tracker.json"))
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return []

data = load_data()

now = datetime.now(timezone.utc)
end_of_week = now + timedelta(days=7)

def parse_date(date_str):
    if not date_str:
        return None
    try:
        if date_str.endswith("Z"):
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
    except Exception:
        return None

if data:
    valid_accas = []
    raw_all_legs = []
    for acca in reversed(data):
        for leg in acca.get("legs", []):
            dt = parse_date(leg.get("date", ""))
            if dt is None or (now <= dt <= end_of_week):
                leg_sig = f"{leg.get('home')}-{leg.get('away')}-{leg.get('market')}"
                if not any(f"{l.get('home')}-{l.get('away')}-{l.get('market')}" == leg_sig for l in raw_all_legs):
                    raw_all_legs.append(leg)
                    
        has_past_leg = False
        out_of_week = False
        for leg in acca.get("legs", []):
            dt = parse_date(leg.get("date", ""))
            if dt is not None:
                if dt < now:
                    has_past_leg = True
                elif dt > end_of_week:
                    out_of_week = True
        
        if not has_past_leg and not out_of_week:
            valid_accas.append(acca)
    data = valid_accas

if not data:
    st.warning("No accumulators found. The daily bot may not have run yet.")
    st.stop()

soccer_accas = []
nba_accas = []
all_legs = raw_all_legs

for acca in data:
    is_nba = False
    for leg in acca.get("legs", []):
        if leg.get("league") in ["NBA", "EuroLeague", "NCAAB", "WNBA"]:
            is_nba = True

    if is_nba:
        nba_accas.append(acca)
    else:
        soccer_accas.append(acca)

soccer_accas = sorted(soccer_accas, key=lambda x: x.get("combined_edge", x.get("edge", 0)), reverse=True)
nba_accas = sorted(nba_accas, key=lambda x: x.get("combined_edge", x.get("edge", 0)), reverse=True)
all_legs = sorted(all_legs, key=lambda x: x.get("edge", 0), reverse=True)

tab1, tab_safe, tab2, tab3, tab4, tab_dream = st.tabs(["🔥 Top Picks", "🎯 Safe Plays", "⚽ Soccer", "🏀 Basketball", "📈 CLV Learning Log", "🤑 Dreamer Parlay"])

def render_leg_details(leg, date_str):
    league = leg.get('league', 'Unknown')
    home = leg.get('home', 'Unknown')
    away = leg.get('away', 'Unknown')
    market = leg.get('market', 'Unknown')
    odds = leg.get('odds', 0)
    edge = leg.get('edge', 0) * 100

    html = f"""
<div class="leg-row">
<b>[{league}]</b> {home} vs {away} <i>({date_str})</i><br>
🎯 {market} @ {odds:.2f} <i>(+{edge:.1f}%)</i>
"""
    
    if league not in ["NBA", "EuroLeague", "NCAAB", "WNBA"]:
        sim = get_soccer_sim_data(league, home, away)
        if sim:
            scores_str = ", ".join([f"{h}-{a} ({p*100:.1f}%)" for (h,a), p in sim['top_scores']])
            html += f"""
<div style="font-size:0.85em; color:#a0a0a0; padding: 5px 0px 0px 15px; border-left: 2px solid #333; margin-top:5px;">
    <b>MC Sim:</b> W: {sim['win_prob']*100:.1f}% | D: {sim['draw_prob']*100:.1f}% | L: {sim['loss_prob']*100:.1f}% <br>
    <b>Most Likely Scores:</b> {scores_str} <br>
    <b>Totals:</b> O1.5: {sim['ov15']*100:.1f}% | O2.5: {sim['ov25']*100:.1f}% | BTTS: {sim['btts_yes']*100:.1f}%
</div>
"""
    else:
        import re
        line_match = re.search(r"(\d+\.?\d*)", market)
        line = float(line_match.group(1)) if line_match else 225.5
        sim = get_basketball_sim_data(league, home, away, line)
        if sim:
            html += f"""
<div style="font-size:0.85em; color:#a0a0a0; padding: 5px 0px 0px 15px; border-left: 2px solid #333; margin-top:5px;">
    <b>Model:</b> {home} Win: {sim['win_prob']*100:.1f}% | {away} Win: {sim['loss_prob']*100:.1f}% <br>
    <b>Totals (Line {sim['line']}):</b> Over: {sim['over']*100:.1f}% | Under: {sim['under']*100:.1f}%
</div>
"""
            
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def render_acca(acca, title):
    combined_odds = acca.get('combined_odds', acca.get('odds', 0))
    combined_edge = acca.get('combined_edge', acca.get('edge', 0))
    
    combined_prob = 1.0
    has_prob = True
    for leg in acca.get('legs', []):
        p = leg.get('model_prob', 0)
        if p == 0:
            has_prob = False
            break
        combined_prob *= p
        
    prob_str = f" | **Win Prob:** {combined_prob*100:.1f}%" if has_prob else ""
    
    st.markdown(f'<div class="acca-card">', unsafe_allow_html=True)
    st.subheader(f"{title} | Odds: {combined_odds:.2f}")
    st.write(f"**Edge:** <span class='edge-text'>+{combined_edge*100:.2f}%</span> | **Stake:** KES {acca.get('stake', 0):.0f}{prob_str}", unsafe_allow_html=True)
    
    for leg in acca.get('legs', []):
        dt = parse_date(leg.get('date', ''))
        date_str = (dt + timedelta(hours=3)).strftime("%A, %b %d @ %H:%M EAT") if dt else "Time TBD" 
        render_leg_details(leg, date_str)
        
    st.markdown('</div>', unsafe_allow_html=True)

with tab1:
    st.header("🔥 The 3 Best Accumulators")
    top_3_overall = sorted(data, key=lambda x: x.get("combined_edge", x.get("edge", 0)), reverse=True)[:3]
    for i, acca in enumerate(top_3_overall):
        render_acca(acca, f"Ultimate Acca #{i+1}")
        
    st.header("🔥 The 3 Best +EV Singles")
    for i, leg in enumerate(all_legs[:3]):
        st.markdown(f'<div class="acca-card">', unsafe_allow_html=True)
        dt = parse_date(leg.get('date', ''))
        date_str = (dt + timedelta(hours=3)).strftime("%A, %b %d @ %H:%M EAT") if dt else "Time TBD" 
        render_leg_details(leg, date_str)
        st.markdown('</div>', unsafe_allow_html=True)

with tab_safe:
    st.header("🎯 Safe & Steady Plays (>65% Win Probability)")
    st.write("These are the mathematically safest single bets across all sports, prioritizing high likelihood of hitting with a positive mathematical edge.")
    
    safe_legs = [leg for leg in all_legs if leg.get('model_prob', 0) >= 0.65 and leg.get('edge', 0) > 0]
    safe_legs = sorted(safe_legs, key=lambda x: x.get('model_prob', 0), reverse=True)
    
    if not safe_legs:
        st.info("No plays with >65% probability and +EV found today.")
    else:
        for i, leg in enumerate(safe_legs):
            st.markdown(f'<div class="acca-card"><h4>#{i+1} [{leg.get("league")}] {leg.get("home")} vs {leg.get("away")}</h4>', unsafe_allow_html=True)
            dt = parse_date(leg.get('date', ''))
            date_str = (dt + timedelta(hours=3)).strftime("%A, %b %d @ %H:%M EAT") if dt else "Time TBD" 
            render_leg_details(leg, date_str)
            st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.header("⚽ All Soccer Accumulators")
    for i, acca in enumerate(soccer_accas):
        render_acca(acca, f"Soccer Acca #{i+1}")

with tab3:
    st.header("🏀 All Basketball Accumulators")
    for i, acca in enumerate(nba_accas):
        render_acca(acca, f"Basketball Acca #{i+1}")

with tab4:
    st.header("📈 CLV Resolution & Self-Learning Log")
    st.info("The automated self-learning system resolves matches every Monday morning. The results and CLV deltas are logged here for the AI to analyze.")
    clv_path = os.path.join(os.path.dirname(__file__), "clv_history.csv")
    if os.path.exists(clv_path):
        df = pd.read_csv(clv_path)
        st.dataframe(df, width='stretch')
    else:
        st.write("No historical CLV data available yet. Waiting for Monday resolution cycle.")

with tab_dream:
    st.header("🤑 The Dreamer Parlay (500+ Odds)")
    st.write("A mathematically optimized mega-parlay purely for fun. High risk, astronomical reward.")
    dreamer_accas = [a for a in data if a.get("is_dreamer")]
    if dreamer_accas:
        render_acca(dreamer_accas[-1], "Mega Dreamer")
    else:
        st.info("Not enough positive-EV legs found this week to build a 500+ odds parlay.")
