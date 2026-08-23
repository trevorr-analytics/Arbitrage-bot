import streamlit as st
import json
import pandas as pd
from datetime import datetime, timezone, timedelta
import os

st.set_page_config(page_title="Quant Betting Dashboard", page_icon="📈", layout="wide")

# Custom CSS for a mobile-friendly dark theme
st.markdown("""
    <style>
    /* Athena-inspired theme */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp, .main {background-color: #0d1110;}
    .stApp > header {background-color: transparent;}
    h1, h2, h3 {color: #ffffff; font-weight: 800; letter-spacing: -0.02em;}
    h1 {font-size: 3.5rem !important; line-height: 1.1 !important;}
    .grass {color: #2f8f56;}
    .eyebrow {
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.1em;
        color: #8c9b93;
        font-weight: 600;
        margin-bottom: -15px;
        display: block;
    }
    .acca-card {
        background-color: #141a18;
        border: 1px solid #1f2924;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .acca-card:hover {
        border-color: #2f8f56;
        transform: translateY(-2px);
    }
    .acca-card h4 {
        color: #ffffff;
        margin-top: 0;
        border-bottom: 1px solid #1f2924;
        padding-bottom: 12px;
        font-size: 1.25rem;
    }
    .leg-row {
        font-size: 0.95em;
        color: #a4b3ac;
        padding-top: 12px;
        padding-bottom: 12px;
        border-bottom: 1px solid #1f2924;
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    .leg-row:last-child {
        border-bottom: none;
    }
    .leg-row b {
        color: #eef4ef;
    }
    .edge-text {
        color: #2f8f56;
        font-weight: 700;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<span class="eyebrow">model vs market &middot; calibration in public</span>', unsafe_allow_html=True)
st.markdown('<h1>AutoQuant &middot; <span class="grass">Sports</span></h1>', unsafe_allow_html=True)
st.write("every day, a new game, and a new machine learning prediction by AutoQuant.")
st.write(f"**Last Updated:** {(datetime.now(timezone.utc) + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M EAT')}")

@st.cache_data(ttl=60)
def load_data():
    try:
        path = os.path.join(os.path.dirname(__file__), "acca_tracker.json")
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
    
    # First, collect all unique future legs regardless of acca validity
    for acca in reversed(data):
        for leg in acca.get("legs", []):
            dt = parse_date(leg.get("date", ""))
            if dt is None or (now <= dt <= end_of_week):
                leg_sig = f"{leg.get('home')}-{leg.get('away')}-{leg.get('market')}"
                if not any(f"{l.get('home')}-{l.get('away')}-{l.get('market')}" == leg_sig for l in raw_all_legs):
                    raw_all_legs.append(leg)
                    
        # Now validate the acca itself (must not contain past games)
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
            
    # Overwrite data with only valid future accas (so the Acca tabs don't show past games)
    data = valid_accas

if not data:
    st.warning("No accumulators found. The daily bot may not have run yet.")
    st.stop()

# Classify data
soccer_accas = []
nba_accas = []
all_legs = []

all_legs = raw_all_legs

for acca in data: # We already reversed earlier if we needed, but data is now just valid_accas
    is_nba = False
    for leg in acca.get("legs", []):
        if leg.get("league") in ["NBA", "EuroLeague", "NCAAB", "WNBA"]:
            is_nba = True

    if is_nba:
        nba_accas.append(acca)
    else:
        soccer_accas.append(acca)

# Sort strictly by Edge (using safe .get() to prevent KeyError on old schemas)
soccer_accas = sorted(soccer_accas, key=lambda x: x.get("combined_edge", x.get("edge", 0)), reverse=True)
nba_accas = sorted(nba_accas, key=lambda x: x.get("combined_edge", x.get("edge", 0)), reverse=True)
all_legs = sorted(all_legs, key=lambda x: x.get("edge", 0), reverse=True)

tab1, tab_safe, tab2, tab3, tab4 = st.tabs(["🔥 Top Picks", "🛡️ Safe Plays", "⚽ Soccer", "🏀 Basketball", "🧠 CLV Learning Log"])

def render_acca(acca, title):
    combined_odds = acca.get('combined_odds', acca.get('odds', 0))
    combined_edge = acca.get('combined_edge', acca.get('edge', 0))
    
    # Calculate combined probability
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
        st.markdown(f"""
        <div class="leg-row">
            <b>[{leg.get('league', 'Unknown')}]</b> {leg.get('home', 'Unknown')} vs {leg.get('away', 'Unknown')} <i>({date_str})</i><br>
            👉 {leg.get('market', 'Unknown')} @ {leg.get('odds', 0):.2f} <i>(+{leg.get('edge', 0)*100:.1f}%)</i>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with tab1:
    st.header("🏆 The 3 Best Accumulators")
    top_3_overall = sorted(data, key=lambda x: x.get("combined_edge", x.get("edge", 0)), reverse=True)[:3]
    for i, acca in enumerate(top_3_overall):
        render_acca(acca, f"Ultimate Acca #{i+1}")
        
    st.header("🎯 The 3 Best +EV Singles")
    for i, leg in enumerate(all_legs[:3]):
        st.markdown(f'<div class="acca-card">', unsafe_allow_html=True)
        dt = parse_date(leg.get('date', ''))
        date_str = (dt + timedelta(hours=3)).strftime("%A, %b %d @ %H:%M EAT") if dt else "Time TBD" 
        st.write(f"**[{leg.get('league', 'Unknown')}]** {leg.get('home', 'Unknown')} vs {leg.get('away', 'Unknown')} <i>({date_str})</i>", unsafe_allow_html=True)
        st.write(f"👉 **{leg.get('market', 'Unknown')} @ {leg.get('odds', 0):.2f}**")
        st.write(f"**Edge:** <span class='edge-text'>+{leg.get('edge', 0)*100:.2f}%</span>", unsafe_allow_html=True)
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
            dt = parse_date(leg.get('date', ''))
            date_str = (dt + timedelta(hours=3)).strftime("%A, %b %d @ %H:%M EAT") if dt else "Time TBD" 
            edge_pct = leg.get('edge', 0) * 100
            prob_pct = leg.get('model_prob', 0) * 100
            st.markdown(f'''
            <div class="acca-card">
                <h4>#{i+1} [{leg.get('league')}] {leg.get('home')} vs {leg.get('away')}</h4>
                <div class="leg-row" style="border:none;">
                    <b>Date & Time:</b> {date_str} <br>
                    <b>Market:</b> {leg.get('market')} <br>
                    <b>Offered Odds:</b> {leg.get('odds', 0):.2f} <br>
                    <b>True Probability:</b> <span class='edge-text'>{prob_pct:.1f}%</span> <br>
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
