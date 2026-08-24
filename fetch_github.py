import pandas as pd
import urllib.request
import os

os.makedirs("basketball_data", exist_ok=True)
url = "https://raw.githubusercontent.com/josedv82/EuroLeagueData/master/EuroLeague_BoxScores_2019-2020.csv"
print("Downloading EuroLeague dataset from GitHub...")
try:
    urllib.request.urlretrieve(url, "basketball_data/euroleague_2019_boxscore.csv")
    df = pd.read_csv("basketball_data/euroleague_2019_boxscore.csv")
    print(f"Downloaded shape: {df.shape}")
except Exception as e:
    print(f"Failed to download: {e}")
