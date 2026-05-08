"""
Loads raw CSV seasons from football-data.co.uk, cleans them,
applies time-decay weights, and upserts into Supabase match_results table.
"""
import logging
import math
import json
import numpy as np
import pandas as pd
import requests
from io import StringIO
from backend.core.supabase_client import get_supabase
from backend.core.config import ACTIVE_CONFIG


logger = logging.getLogger(__name__)


LEAGUE_CODE = ACTIVE_CONFIG["fdco_code"]  # "F1" for Ligue 1


SEASONS = [
    "1011", "1112", "1213", "1314", "1415", "1516",
    "1617", "1718", "1819", "1920", "2021", "2122", "2223", "2324", "2425",
]


BASE_URL = f"https://www.football-data.co.uk/mmz4281/{{season}}/{LEAGUE_CODE}.csv"


COLUMN_MAP = {
    "Date": "date", "HomeTeam": "home_team", "AwayTeam": "away_team",
    "FTR": "ftr", "FTHG": "fthg", "FTAG": "ftag",
    "HTHG": "hthg", "HTAG": "htag",
    "HS": "hs", "AS": "as_", "HST": "hst", "AST": "ast",
    "HC": "hc", "AC": "ac", "HY": "hy", "AY": "ay",
    "HR": "hr", "AR": "ar", "Referee": "referee", "HF": "hf", "AF": "af",
}


INT_COLS = [
    "fthg", "ftag", "hthg", "htag",
    "hs", "as_", "hst", "ast",
    "hc", "ac", "hy", "ay", "hr", "ar", "hf", "af"
]


class SafeEncoder(json.JSONEncoder):
    """Converts all non-JSON-safe types (NaN, pd.NA, numpy types) to JSON-safe equivalents."""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return None if np.isnan(obj) else float(obj)
        if isinstance(obj, float) and math.isnan(obj):
            return None
        try:
            if pd.isna(obj):
                return None
        except Exception:
            pass
        return super().default(obj)


def _get_season_label(season_code: str) -> str:
    """'2425' → '24/25'"""
    return f"{season_code[:2]}/{season_code[2:]}"


def _time_weight(season_code: str, total: int) -> float:
    idx = SEASONS.index(season_code)
    return round(math.exp(-0.15 * (total - 1 - idx)), 4)


def fetch_season(season_code: str) -> pd.DataFrame:
    url = BASE_URL.format(season=season_code)
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    df = pd.read_csv(StringIO(response.text), on_bad_lines="skip")
    return df


def clean_season(df: pd.DataFrame, season_code: str) -> pd.DataFrame:
    df = df.rename(columns=COLUMN_MAP)
    df = df[[c for c in COLUMN_MAP.values() if c in df.columns]]
    df["season"] = _get_season_label(season_code)
    df["time_weight"] = _time_weight(season_code, len(SEASONS))
    df["date"] = pd.to_datetime(df["date"], format="mixed", dayfirst=True, errors="coerce")
    df = df.dropna(subset=["date", "home_team", "away_team"])
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    for col in INT_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    return df


def upsert_season(df: pd.DataFrame):
    supabase = get_supabase()
    records = df.to_dict(orient="records")
    # Round-trip through SafeEncoder to flush out NaN, pd.NA, numpy types → JSON-safe Python
    records = json.loads(json.dumps(records, cls=SafeEncoder))
    supabase.table("match_results").upsert(
        records, on_conflict="season,date,home_team,away_team"
    ).execute()
    logger.info(f"  Upserted {len(records)} rows")


def ingest_all():
    logger.info(f"Starting ingestion for {ACTIVE_CONFIG['name']} ({LEAGUE_CODE})")
    for code in SEASONS:
        logger.info(f"Ingesting season {code}...")
        try:
            raw = fetch_season(code)
            clean = clean_season(raw, code)
            upsert_season(clean)
            logger.info(f"  ✅ {code}: {len(clean)} matches")
        except Exception as e:
            logger.error(f"  ❌ {code} failed: {e}")