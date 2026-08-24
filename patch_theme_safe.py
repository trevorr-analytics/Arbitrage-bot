import os
import re

path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\dashboard.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace CSS
old_css = """<style>
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
    </style>"""

new_css = """<style>
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
    </style>"""

content = content.replace(old_css, new_css)

# Update color codes in render_acca and Safe Tab
content = content.replace("#00ffa3", "#2f8f56")
content = content.replace("<span style=\"color:#2f8f56;\">", "<span class=\"edge-text\">")
content = content.replace("<span style='color:#2f8f56;'>", "<span class=\"edge-text\">")

# Replace Title using robust regex
# We look for st.title(...) and replace it along with the subtitle
content = re.sub(r'st\.title\(.*?\)', 
                 'st.markdown(\'<span class="eyebrow">model vs market &middot; calibration in public</span>\', unsafe_allow_html=True)\nst.markdown(\'<h1>AutoQuant &middot; <span class="grass">Sports</span></h1>\', unsafe_allow_html=True)\nst.write("every day, a new game, and a new machine learning prediction by AutoQuant.")', 
                 content)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
