"""
Download historical match + odds data from Football-Data.co.uk
Covers: EPL, Bundesliga, La Liga, Serie A, Ligue 1, Eredivisie
Seasons: 2018-19 through 2023-24 (6 seasons of training data)
"""
import urllib.request
import os
import time

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "football_data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

LEAGUES = {
    "EPL":        "E0",
    "Bundesliga": "D1",
    "LaLiga":     "SP1",
    "SerieA":     "I1",
    "Ligue1":     "F1",
    "Eredivisie": "N1",
}

# Seasons in football-data.co.uk format (e.g. 2018-19 = "1819")
SEASONS = ["1819", "1920", "2021", "2122", "2223", "2324"]

BASE_URL = "https://www.football-data.co.uk/mmz4281/{season}/{league_code}.csv"

def download():
    total = 0
    skipped = 0
    failed = 0
    for league_name, code in LEAGUES.items():
        league_dir = os.path.join(OUTPUT_DIR, league_name)
        os.makedirs(league_dir, exist_ok=True)
        for season in SEASONS:
            url = BASE_URL.format(season=season, league_code=code)
            out_path = os.path.join(league_dir, f"{season}.csv")
            if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
                skipped += 1
                continue
            try:
                print(f"  Downloading {league_name} {season}...", end=" ", flush=True)
                urllib.request.urlretrieve(url, out_path)
                size = os.path.getsize(out_path)
                print(f"OK ({size:,} bytes)")
                total += 1
                time.sleep(0.3)
            except Exception as e:
                print(f"FAILED: {e}")
                failed += 1

    print(f"\nDone. Downloaded: {total}, Skipped (cached): {skipped}, Failed: {failed}")

if __name__ == "__main__":
    download()
