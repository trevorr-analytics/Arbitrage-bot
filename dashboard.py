import os
import sys

# Ensure sports_model is in the path
sports_model_path = os.path.join(os.path.dirname(__file__), "sports_model")
sys.path.insert(0, sports_model_path)

file_path = os.path.join(sports_model_path, "dashboard.py")
with open(file_path, "r", encoding="utf-8") as f:
    code = f.read()

# Execute with the correct __file__ so relative paths inside the dashboard resolve correctly
g = globals().copy()
g["__file__"] = file_path
exec(code, g)
