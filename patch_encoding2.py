import os
import re

path = r"C:\Users\hp\Desktop\AutoQuant_Betting_Bot\dashboard.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

content = re.sub(r'model vs market .*? calibration in public', 'model vs market - calibration in public', content)
content = re.sub(r'<h1>AutoQuant .*? <span', '<h1>AutoQuant - <span', content)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
