import os
import requests
api_key = os.environ.get("ODDS_API_KEY", "017cbc1f3724942ba358b77a4b1095fe")
url = f"https://api.the-odds-api.com/v4/sports/soccer_epl/scores/?daysFrom=3&apiKey={api_key}"
resp = requests.get(url)
print(resp.status_code)
print(resp.json()[:2] if isinstance(resp.json(), list) else resp.json())
