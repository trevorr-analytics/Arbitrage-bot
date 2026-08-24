import os

path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\dashboard.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace tabs line to add Dreamer Parlay
old_tabs = 'tab1, tab_safe, tab2, tab3, tab4 = st.tabs(["🔥 Top Picks", "🛡️ Safe Plays", "⚽ Soccer", "🏀 Basketball", "📈 CLV Learning Log"])'
new_tabs = 'tab1, tab_safe, tab2, tab3, tab4, tab_dream = st.tabs(["🔥 Top Picks", "🛡️ Safe Plays", "⚽ Soccer", "🏀 Basketball", "📈 CLV Learning Log", "🦄 Dreamer Parlay"])'
content = content.replace(old_tabs, new_tabs)

# Add logic for rendering Dreamer tab at the end of the file
dreamer_render = """
with tab_dream:
    st.header("🦄 The Dreamer Parlay (500+ Odds)")
    st.write("A mathematically optimized mega-parlay purely for fun. High risk, astronomical reward.")
    
    dreamer_accas = [a for a in data if a.get("is_dreamer")]
    if dreamer_accas:
        render_acca(dreamer_accas[-1], "Mega Dreamer")
    else:
        st.info("Not enough positive-EV legs found this week to build a 500+ odds parlay.")
"""
if "🦄 The Dreamer Parlay" not in content:
    content += dreamer_render

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
