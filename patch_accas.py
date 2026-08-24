import os
import re

path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\dashboard.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Fix sorting for Accumulators
content = content.replace('soccer_accas = sorted(soccer_accas, key=lambda x: x.get("edge", 0), reverse=True)', 'soccer_accas = sorted(soccer_accas, key=lambda x: x.get("combined_edge", x.get("edge", 0)), reverse=True)')
content = content.replace('nba_accas = sorted(nba_accas, key=lambda x: x.get("edge", 0), reverse=True)', 'nba_accas = sorted(nba_accas, key=lambda x: x.get("combined_edge", x.get("edge", 0)), reverse=True)')
content = content.replace('top_3_overall = sorted(data, key=lambda x: x.get("edge", 0), reverse=True)[:3]', 'top_3_overall = sorted(data, key=lambda x: x.get("combined_edge", x.get("edge", 0)), reverse=True)[:3]')

# 2. Fix render_acca function
old_render = """def render_acca(acca, title):
    st.markdown(f'<div class="acca-card">', unsafe_allow_html=True)
    st.subheader(f"{title} | Odds: {acca.get('odds', 0):.2f}")
    st.write(f"**Edge:** <span class='edge-text'>+{acca.get('edge', 0)*100:.2f}%</span> | **Stake:** KES {acca.get('stake', 0):.0f}", unsafe_allow_html=True)"""

new_render = """def render_acca(acca, title):
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
    st.write(f"**Edge:** <span class='edge-text'>+{combined_edge*100:.2f}%</span> | **Stake:** KES {acca.get('stake', 0):.0f}{prob_str}", unsafe_allow_html=True)"""

content = content.replace(old_render, new_render)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
