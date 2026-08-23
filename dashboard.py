import streamlit as st
import json
import pandas as pd
from datetime import datetime, timezone
import os

st.set_page_config(page_title="Quant Betting Dashboard", page_icon="📈", layout="wide")

# Custom CSS for a mobile-friendly dark theme
st.markdown("""
    <style>
    .main {background-color: #0e1117;}
    h1, h2, h3 {color: #00ffa3;}
    .acca-card {
        background-color: #1a1c24;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        border-left: 4px solid #00ffa3;
    }
    .leg-row {
        font-size: 0.9em;
        color: #d1d5db;
        border-bottom: 1px solid #374151;
        padding-bottom: 5px;
        margin-bottom: 5px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📈 AutoQuant Live Dashboard")
st.write(f"**Last Updated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

@st.cache_data(ttl=60)
def load_data():
    try:
        path = os.path.join(os.path.dirname(__file__), "acca_tracker.json")
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return []

data = load_data()

if not data:
    st.warning("No accumulators found. The daily bot may not have run yet.")
    st.stop()

# Classify data
soccer_accas = []
nba_accas = []
all_legs = []

for acca in reversed(data):
    is_nba = False
    for leg in acca.get("legs", []):
        if leg.get("league") in ["NBA", "EuroLeague", "NCAAB", "WNBA"]:
            is_nba = True
        
        # deduplicate legs
        # Check by match signature to avoid referencing issues
        leg_sig = f"{leg.get('home')}-{leg.get('away')}-{leg.get('market')}"
        if not any(f"{l.get('home')}-{l.get('away')}-{l.get('market')}" == leg_sig for l in all_legs):
            all_legs.append(leg)

    if is_nba:
        nba_accas.append(acca)
    else:
        soccer_accas.append(acca)

# Sort strictly by Edge (using safe .get() to prevent KeyError on old schemas)
soccer_accas = sorted(soccer_accas, key=lambda x: x.get("edge", 0), reverse=True)
nba_accas = sorted(nba_accas, key=lambda x: x.get("edge", 0), reverse=True)
all_legs = sorted(all_legs, key=lambda x: x.get("edge", 0), reverse=True)

tab1, tab_safe, tab2, tab3, tab4 = st.tabs(["🔥 Top Picks", "🛡️ Safe Plays", "⚽ Soccer", "🏀 Basketball", "🧠 CLV Learning Log"])

def render_acca(acca, title):
    st.markdown(f'<div class="acca-card">', unsafe_allow_html=True)
    st.subheader(f"{title} | Odds: {acca.get('odds', 0):.2f}")
    st.write(f"**Edge:** <span style='color:#00ffa3;'>+{acca.get('edge', 0)*100:.2f}%</span> | **Stake:** KES {acca.get('stake', 0):.0f}", unsafe_allow_html=True)
    
    for leg in acca.get('legs', []):
        date_str = leg.get('date', 'Unknown')[:16].replace('T', ' ')
        st.markdown(f"""
        <div class="leg-row">
            <b>[{leg.get('league', 'Unknown')}]</b> {leg.get('home', 'Unknown')} vs {leg.get('away', 'Unknown')} <i>({date_str})</i><br>
            👉 {leg.get('market', 'Unknown')} @ {leg.get('odds', 0):.2f} <i>(+{leg.get('edge', 0)*100:.1f}%)</i>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tab1:
    st.header("🏆 The 3 Best Accumulators")
    top_3_overall = sorted(data, key=lambda x: x.get("edge", 0), reverse=True)[:3]
    for i, acca in enumerate(top_3_overall):
        render_acca(acca, f"Ultimate Acca #{i+1}")
        
    st.header("🎯 The 3 Best +EV Singles")
    for i, leg in enumerate(all_legs[:3]):
        st.markdown(f'<div class="acca-card">', unsafe_allow_html=True)
        date_str = leg.get('date', 'Unknown')[:16].replace('T', ' ')
        st.write(f"**[{leg.get('league', 'Unknown')}]** {leg.get('home', 'Unknown')} vs {leg.get('away', 'Unknown')} <i>({date_str})</i>", unsafe_allow_html=True)
        st.write(f"👉 **{leg.get('market', 'Unknown')} @ {leg.get('odds', 0):.2f}**")
        st.write(f"**Edge:** <span style='color:#00ffa3;'>+{leg.get('edge', 0)*100:.2f}%</span>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)


with tab_safe:
    st.header("🛡️ Safe & Steady Plays (>65% Win Probability)")
    st.write("These are the mathematically safest single bets across all sports, prioritizing high likelihood of hitting with a positive mathematical edge.")
    
    # Filter and sort by model_prob instead of edge
    safe_legs = [leg for leg in all_legs if leg.get('model_prob', 0) >= 0.65 and leg.get('edge', 0) > 0]
    safe_legs = sorted(safe_legs, key=lambda x: x.get('model_prob', 0), reverse=True)
    
    if not safe_legs:
        st.info("No plays with >65% probability and +EV found today.")
    else:
        for i, leg in enumerate(safe_legs):
            date_str = leg.get('date', 'Unknown')[:16].replace('T', ' ')
            edge_pct = leg.get('edge', 0) * 100
            prob_pct = leg.get('model_prob', 0) * 100
            st.markdown(f'''
            <div class="acca-card">
                <h4>#{i+1} [{leg.get('league')}] {leg.get('home')} vs {leg.get('away')}</h4>
                <div class="leg-row" style="border:none;">
                    <b>Market:</b> {leg.get('market')} <br>
                    <b>Offered Odds:</b> {leg.get('odds', 0):.2f} <br>
                    <b>True Probability:</b> <span style="color:#00ffa3;">{prob_pct:.1f}%</span> <br>
                    <b>Edge:</b> +{edge_pct:.1f}%
                </div>
            </div>
            ''', unsafe_allow_html=True)

with tab2:
    st.header("⚽ All Soccer Accumulators")
    for i, acca in enumerate(soccer_accas):
        render_acca(acca, f"Soccer Acca #{i+1}")

with tab3:
    st.header("🏀 All Basketball Accumulators")
    for i, acca in enumerate(nba_accas):
        render_acca(acca, f"Basketball Acca #{i+1}")

with tab4:
    st.header("🧠 CLV Resolution & Self-Learning Log")
    st.info("The automated self-learning system resolves matches every Monday morning. The results and CLV deltas are logged here for the AI to analyze.")
    
    clv_path = os.path.join(os.path.dirname(__file__), "clv_history.csv")
    if os.path.exists(clv_path):
        df = pd.read_csv(clv_path)
        st.dataframe(df, use_container_width=True)
    else:
        st.write("No historical CLV data available yet. Waiting for Monday resolution cycle.")
