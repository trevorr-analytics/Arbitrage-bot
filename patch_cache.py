import os

path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\dashboard.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("@st.cache_data(ttl=3600)", "@st.cache_data(ttl=60)")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
