import os
import re

path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\dashboard.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace the title dynamically using regex
content = re.sub(r'st\.title\(.*?AutoQuant Live Dashboard.*?\)', 
                 'st.markdown(\'<span class="eyebrow">model vs market · calibration in public</span>\', unsafe_allow_html=True)\nst.markdown(\'<h1>AutoQuant · <span class="grass">Sports</span></h1>\', unsafe_allow_html=True)\nst.write("every day, a new game, and a new machine learning prediction by AutoQuant.")', 
                 content)

# Add hide Streamlit header and footer via CSS
content = content.replace("    .stApp, .main", "    #MainMenu {visibility: hidden;}\n    footer {visibility: hidden;}\n    header {visibility: hidden;}\n    .stApp, .main")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
