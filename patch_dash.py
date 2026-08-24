import os

path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\dashboard.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old_tabs = 'tab1, tab2, tab3, tab4 = st.tabs(["🔥 Top Picks", "⚽ Soccer", "🏀 Basketball", "🧠 CLV Learning Log"])'
new_tabs = 'tab1, tab_safe, tab2, tab3, tab4 = st.tabs(["🔥 Top Picks", "🛡️ Safe Plays", "⚽ Soccer", "🏀 Basketball", "🧠 CLV Learning Log"])'
content = content.replace(old_tabs, new_tabs)

safe_tab_code = """
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
"""

# We can append it just before `with tab2:`
content = content.replace("with tab2:", safe_tab_code + "\nwith tab2:")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
