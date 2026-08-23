import os
import sys
import math
import itertools
import pandas as pd
from typing import List, Dict

sys.path.insert(0, os.path.dirname(__file__))
from dixon_coles import DixonColesModel, load_league_data
from odds_api import fetch_live_odds
from devig import shin_devig

from basketball_model import BasketballModel
from telegram_notifier import send_telegram_message

BANKROLL_KES = 5000.0
MIN_SINGLE_EDGE = 0.01  
KELLY_FRACTION = 0.125  
MAX_BET_CAP = 0.01      
TARGET_MIN_ODDS = 1.5
TARGET_MAX_ODDS = 2.05

LEAGUES = ["EPL", "Bundesliga", "LaLiga", "SerieA", "Ligue1", "Eredivisie", "NBA", "EuroLeague", "NCAAB", "WNBA"]

def safe_devig(odds_list):
    if any(o <= 1.0 for o in odds_list):
        return [0.0] * len(odds_list)
    try:
        return shin_devig(odds_list)
    except Exception:
        return [0.0] * len(odds_list)

import difflib

def fuzzy_team(name: str, known: list) -> str:
    for k in known:
        if k.lower() == name.lower(): return k
    matches = difflib.get_close_matches(name, known, n=1, cutoff=0.55)
    if matches:
        return matches[0]
    generic = {"fc", "real", "united", "city", "athletic", "club", "de", "cf", "and", "hove", "albion"}
    name_clean = " ".join([w for w in name.lower().split() if w not in generic])
    if len(name_clean) > 3:
        for k in known:
            k_clean = " ".join([w for w in k.lower().split() if w not in generic])
            if name_clean in k_clean or (len(k_clean)>3 and k_clean in name_clean):
                return k
    return name if not known else None


