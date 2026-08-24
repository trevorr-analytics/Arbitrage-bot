import requests

# Approximate coordinates for the major footballing capitals
LEAGUE_COORDS = {
    "EPL": {"lat": 51.5074, "lon": -0.1278},        # London, UK
    "LaLiga": {"lat": 40.4168, "lon": -3.7038},     # Madrid, Spain
    "Bundesliga": {"lat": 52.5200, "lon": 13.4050}, # Berlin, Germany
    "SerieA": {"lat": 41.9028, "lon": 12.4964},     # Rome, Italy
    "Ligue1": {"lat": 48.8566, "lon": 2.3522},      # Paris, France
    "Eredivisie": {"lat": 52.3676, "lon": 4.9041}   # Amsterdam, Netherlands
}

def get_league_weather(league: str) -> dict:
    """
    Fetches the current weather (precipitation, wind speed) from Open-Meteo for the given league's region.
    Open-Meteo requires no API key and is completely free.
    """
    coords = LEAGUE_COORDS.get(league)
    if not coords:
        return {"wind_speed_kmh": 0.0, "precipitation_mm": 0.0, "is_extreme": False}
        
    url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&current=precipitation,wind_speed_10m"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        current = data.get("current", {})
        wind_speed = current.get("wind_speed_10m", 0.0)
        precip = current.get("precipitation", 0.0)
        
        # Define extreme weather (e.g. wind > 25 km/h drastically reduces passing accuracy and goals)
        is_extreme = wind_speed >= 25.0 or precip >= 5.0
        
        return {
            "wind_speed_kmh": wind_speed,
            "precipitation_mm": precip,
            "is_extreme": is_extreme
        }
    except Exception as e:
        print(f"[Weather] Failed to fetch weather for {league}: {e}")
        return {"wind_speed_kmh": 0.0, "precipitation_mm": 0.0, "is_extreme": False}

if __name__ == "__main__":
    for lg in LEAGUE_COORDS.keys():
        print(f"{lg}: {get_league_weather(lg)}")
