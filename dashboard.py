import streamlit as st
import json
import pandas as pd
from datetime import datetime
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
st.write(f"**Last Updated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

@st.cache_data(ttl=3600)
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

for acca in data:
    is_nba = any(leg["league"] in ["NBA", "EuroLeague", "NCAAB", "WNBA"] for leg in acca["legs"])
    if is_nba:
        nba_accas.append(acca)
    else:
        soccer_accas.append(acca)
        
    for leg in acca["legs"]:
        # deduplicate legs
        if leg not in all_legs:
            all_legs.append(leg)

# Sort strictly by Edge
soccer_accas = sorted(soccer_accas, key=lambda x: x["edge"], reverse=True)
nba_accas = sorted(nba_accas, key=lambda x: x["edge"], reverse=True)
all_legs = sorted(all_legs, key=lambda x: x["edge"], reverse=True)

tab1, tab2, tab3, tab4 = st.tabs(["🔥 Top Picks", "⚽ Soccer", "🏀 Basketball", "🧠 CLV Learning Log"])

def render_acca(acca, title):
    st.markdown(f'<div class="acca-card">', unsafe_allow_html=True)
    st.subheader(f"{title} | Odds: {acca['odds']:.2f}")
    st.write(f"**Edge:** <span style='color:#00ffa3;'>+{acca['edge']*100:.2f}%</span> | **Stake:** KES {acca['stake']:.0f}", unsafe_allow_html=True)
    
    for leg in acca['legs']:
        date_str = leg.get('date', 'Unknown')[:16].replace('T', ' ')
        st.markdown(f"""
        <div class="leg-row">
            <b>[{leg['league']}]</b> {leg['home']} vs {leg['away']} <i>({date_str})</i><br>
            👉 {leg['market']} @ {leg['odds']:.2f} <i>(+{leg['edge']*100:.1f}%)</i>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tab1:
    st.header("🏆 The 3 Best Accumulators")
    top_3_overall = sorted(data, key=lambda x: x["edge"], reverse=True)[:3]
    for i, acca in enumerate(top_3_overall):
        render_acca(acca, f"Ultimate Acca #{i+1}")
        
    st.header("🎯 The 3 Best +EV Singles")
    for i, leg in enumerate(all_legs[:3]):
        st.markdown(f'<div class="acca-card">', unsafe_allow_html=True)
        date_str = leg.get('date', 'Unknown')[:16].replace('T', ' ')
        st.write(f"**[{leg['league']}]** {leg['home']} vs {leg['away']} <i>({date_str})</i>", unsafe_allow_html=True)
        st.write(f"👉 **{leg['market']} @ {leg['odds']:.2f}**")
        st.write(f"**Edge:** <span style='color:#00ffa3;'>+{leg['edge']*100:.2f}%</span>", unsafe_allow_html=True)
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
    st.header("🧠 CLV Resolution & Self-Learning Log")
    st.info("The automated self-learning system resolves matches every Monday morning. The results and CLV deltas are logged here for the AI to analyze.")
    
    clv_path = os.path.join(os.path.dirname(__file__), "clv_history.csv")
    if os.path.exists(clv_path):
        df = pd.read_csv(clv_path)
        st.dataframe(df, use_container_width=True)
    else:
        st.write("No historical CLV data available yet. Waiting for Monday resolution cycle.")
