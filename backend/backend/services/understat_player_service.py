"""
Fetches Ligue 1 player-level minutes and xG data from Understat.
Used for:
  1. Player form ratings (rolling xG, minutes over last 5 matches)
  2. Injury inference (sudden drop to 0 minutes = injured/suspended)
"""
import logging
import time
import pandas as pd
from understatapi import UnderstatClient
from backend.core.supabase_client import get_supabase

logger = logging.getLogger(__name__)

# Understat start-year → season label
SEASONS = {
    "2014": "14/15", "2015": "15/16", "2016": "16/17",
    "2017": "17/18", "2018": "18/19", "2019": "19/20",
    "2020": "20/21", "2021": "21/22", "2022": "22/23",
    "2023": "23/24", "2024": "24/25",
}

# Understat Ligue 1 team names → football-data.co.uk short names
TEAM_NAME_MAP = {
    "Paris Saint-Germain":  "Paris SG",
    "Paris Saint Germain":  "Paris SG",
    "PSG":                  "Paris SG",
    "Olympique Lyonnais":   "Lyon",
    "Olympique de Marseille": "Marseille",
    "Marseille":            "Marseille",
    "AS Monaco":            "Monaco",
    "Lille OSC":            "Lille",
    "LOSC Lille":           "Lille",
    "OGC Nice":             "Nice",
    "Stade Rennais":        "Rennes",
    "Stade Rennais FC":     "Rennes",
    "RC Lens":              "Lens",
    "Stade de Reims":       "Reims",
    "Montpellier HSC":      "Montpellier",
    "Montpellier":          "Montpellier",
    "RC Strasbourg Alsace": "Strasbourg",
    "Strasbourg":           "Strasbourg",
    "FC Nantes":            "Nantes",
    "Nantes":               "Nantes",
    "Le Havre AC":          "Le Havre",
    "Le Havre":             "Le Havre",
    "Stade Brestois 29":    "Brest",
    "Stade Brestois":       "Brest",
    "Brest":                "Brest",
    "Toulouse FC":          "Toulouse",
    "Toulouse":             "Toulouse",
    "AJ Auxerre":           "Auxerre",
    "Auxerre":              "Auxerre",
    "Angers SCO":           "Angers",
    "Angers":               "Angers",
    "AS Saint-Étienne":     "St Etienne",
    "AS Saint-Etienne":     "St Etienne",
    "Saint-Étienne":        "St Etienne",
    "Saint-Etienne":        "St Etienne",
    "FC Metz":              "Metz",
    "Metz":                 "Metz",
    "FC Lorient":           "Lorient",
    "Lorient":              "Lorient",
    "Clermont Foot":        "Clermont",
    "Clermont Foot 63":     "Clermont",
    "Clermont":             "Clermont",
    "ESTAC Troyes":         "Troyes",
    "Troyes":               "Troyes",
}

KEEP_COLS = [
    "id", "player_name", "team_title", "games", "time",
    "goals", "assists", "xG", "xA", "npxG",
    "xGChain", "xGBuildup", "yellow_cards", "red_cards",
]


def fetch_player_season(understat_year: str) -> pd.DataFrame:
    with UnderstatClient() as client:
        data = client.league(league="Ligue_1").get_player_data(season=understat_year)
    df = pd.DataFrame(data)
    # Keep only available columns
    df = df[[c for c in KEEP_COLS if c in df.columns]]
    return df


def clean_player_df(df: pd.DataFrame, season_label: str) -> list[dict]:
    df = df.copy()
    df["season"] = season_label

    # Normalize team names to football-data.co.uk format
    if "team_title" in df.columns:
        df["team_title"] = df["team_title"].replace(TEAM_NAME_MAP)

    rename = {
        "id":           "player_id",
        "player_name":  "player_name",
        "team_title":   "team",
        "games":        "matches",
        "time":         "minutes",
        "goals":        "goals",
        "assists":      "assists",
        "xG":           "xg",
        "xA":           "xa",
        "npg":          "npg",
        "npxG":         "npxg",
        "xGChain":      "xg_chain",
        "xGBuildup":    "xg_buildup",
        "yellow_cards": "yellow",
        "red_cards":    "red",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    # ── SAFETY: only keep columns that exist in our DB schema ──
    DB_COLS = [
        "player_id", "player_name", "team", "season",
        "matches", "minutes", "goals", "assists",
        "xg", "xa", "npg", "npxg",
        "xg_chain", "xg_buildup", "yellow", "red",
    ]
    df = df[[c for c in DB_COLS if c in df.columns]]

    # Numeric casting
    float_cols = ["goals","assists","xg","xa","npg","npxg","xg_chain","xg_buildup"]
    int_cols   = ["matches","minutes","yellow","red"]

    for col in float_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in int_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: int(x) if pd.notna(x) else None)

    df = df.where(pd.notna(df), None)
    return df.to_dict(orient="records")


def upsert_players(records: list[dict]):
    if not records:
        return
    supabase = get_supabase()
    for i in range(0, len(records), 500):
        batch = records[i:i+500]
        supabase.table("player_minutes").upsert(
            batch, on_conflict="season,player_id,team"
        ).execute()


def ingest_all_player_minutes():
    for year, label in SEASONS.items():
        logger.info(f"Fetching Ligue 1 player minutes: {label}...")
        try:
            raw  = fetch_player_season(year)
            recs = clean_player_df(raw, label)
            upsert_players(recs)
            logger.info(f"  ✅ {label}: {len(recs)} players")
        except Exception as e:
            logger.error(f"  ❌ {label} failed: {e}")
        time.sleep(1.5)  # respectful delay


def get_squad_form_features(team: str, season: str) -> dict:
    """
    Returns pre-match squad strength features for a given team.
    Used by feature_service.py when building prediction features.
    """
    supabase = get_supabase()
    result = (
        supabase.table("player_minutes")
        .select("player_name,minutes,xg,npxg,xa,goals,assists")
        .eq("team", team)
        .eq("season", season)
        .order("minutes", desc=True)
        .limit(14)   # first-choice squad (11 starters + 3 bench)
        .execute()
    )
    players = result.data
    if not players:
        return {}

    df = pd.DataFrame(players)
    return {
        "squad_avg_xg":      round(df["xg"].mean(), 4)    if "xg"      in df else None,
        "squad_avg_npxg":    round(df["npxg"].mean(), 4)  if "npxg"    in df else None,
        "squad_avg_xa":      round(df["xa"].mean(), 4)    if "xa"      in df else None,
        "squad_total_goals": df["goals"].sum()             if "goals"   in df else None,
        "squad_total_ast":   df["assists"].sum()           if "assists" in df else None,
        "squad_avg_minutes": round(df["minutes"].mean(), 1),
    }