"""
Reads B365 odds from football-data CSVs and updates match_results in Supabase.
"""
import sys
import os
import logging
import pandas as pd
from pathlib import Path

# Fix path: add parent directory (backend/) to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.supabase_client import get_supabase
from core.config import ACTIVE_CONFIG
from utils.team_utils import TEAM_NAME_MAP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LEAGUE_CODE = ACTIVE_CONFIG["fdco_code"]  # "F1"

# ABSOLUTE path: go up from scripts/ → backend/ → project root → data/raw/seasons/f1
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CSV_DIR = Path(PROJECT_ROOT) / "data" / "raw" / "seasons" / LEAGUE_CODE.lower()

SEASON_FILES = [
    "1011.csv", "1112.csv", "1213.csv", "1314.csv", "1415.csv",
    "1516.csv", "1617.csv", "1718.csv", "1819.csv", "1920.csv",
    "2021.csv", "2122.csv", "2223.csv", "2324.csv", "2425.csv",
    "2526.csv",
]


def load_csvs() -> pd.DataFrame:
    frames = []

    logger.info(f"Looking for CSVs in: {CSV_DIR}")
    logger.info(f"Directory exists: {CSV_DIR.exists()}")
    if CSV_DIR.exists():
        logger.info(f"Files found: {[f.name for f in CSV_DIR.glob('*.csv')]}")

    for season_file in SEASON_FILES:
        csv_path = CSV_DIR / season_file
        if not csv_path.exists():
            logger.warning(f"  {season_file} — not found at {csv_path}, skipping")
            continue

        try:
            df = pd.read_csv(csv_path, encoding="latin-1", low_memory=False)
            df.columns = df.columns.str.strip().str.lower()

            if "b365h" not in df.columns:
                logger.warning(f"  {season_file} — no B365 cols, skipping")
                continue

            needed = ["date", "hometeam", "awayteam", "b365h", "b365d", "b365a"]
            missing = [c for c in needed if c not in df.columns]
            if missing:
                logger.warning(f"  {season_file} — missing {missing}, skipping")
                continue

            df = df[needed].copy()
            df = df.rename(columns={"hometeam": "home_team", "awayteam": "away_team"})
            df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
            df = df.dropna(subset=["date", "b365h"])

            df["home_team"] = df["home_team"].replace(TEAM_NAME_MAP)
            df["away_team"] = df["away_team"].replace(TEAM_NAME_MAP)

            frames.append(df)
            logger.info(f"  ✅ {season_file} — {len(df)} rows with odds")

        except Exception as e:
            logger.error(f"  ❌ {season_file} — {e}")

    if not frames:
        raise ValueError(f"No CSVs with B365 odds found in {CSV_DIR}")
    return pd.concat(frames, ignore_index=True)


def upload_odds(df: pd.DataFrame) -> None:
    supabase = get_supabase()
    updated = 0
    skipped = 0

    for _, row in df.iterrows():
        date_str = row["date"].strftime("%Y-%m-%d")
        try:
            result = (
                supabase.table("match_results")
                .update({
                    "b365h": float(row["b365h"]),
                    "b365d": float(row["b365d"]),
                    "b365a": float(row["b365a"]),
                })
                .eq("date", date_str)
                .eq("home_team", row["home_team"])
                .eq("away_team", row["away_team"])
                .execute()
            )
            if result.data:
                updated += 1
            else:
                skipped += 1
        except Exception as e:
            logger.warning(f"  Row {date_str} {row['home_team']} v {row['away_team']}: {e}")

    logger.info(f"\n  ✅ Updated : {updated} rows")
    logger.info(f"  ⚠️  Skipped : {skipped} rows (no match found)")


if __name__ == "__main__":
    logger.info(f"Loading B365 odds for {ACTIVE_CONFIG['name']}")
    odds_df = load_csvs()
    logger.info(f"Total rows with odds: {len(odds_df)}")
    logger.info("Uploading to Supabase...")
    upload_odds(odds_df)
    logger.info("Done — re-run build_features.py to regenerate parquet")