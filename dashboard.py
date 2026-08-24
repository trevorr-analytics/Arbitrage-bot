import os
import sys

# Add the sports_model directory to the path so we can import from it
sports_model_path = os.path.join(os.path.dirname(__file__), "sports_model")
sys.path.insert(0, sports_model_path)

# Importing the module will execute all its Streamlit commands
import dashboard
