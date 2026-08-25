import os
import re

path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\sports_model\dashboard.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix the st.tabs line
# Match tab1, tab_safe, tab2, tab3, tab4 = st.tabs([...])
content = re.sub(
    r'tab1,\s*tab_safe,\s*tab2,\s*tab3,\s*tab4\s*=\s*st\.tabs\(\[.*?\]\)',
    'tab1, tab_safe, tab2, tab3, tab4, tab_dream = st.tabs(["🔥 Top Picks", "🛡️ Safe Plays", "⚽ Soccer", "🏀 Basketball", "📈 CLV Learning Log", "🦄 Dreamer Parlay"])',
    content,
    flags=re.DOTALL
)

# Fix the Streamlit deprecation warning
content = content.replace('use_container_width=True', "width='stretch'")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
