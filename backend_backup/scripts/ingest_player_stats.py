"""
Ingest Kaggle football player stats CSV into Supabase.

Usage:
    python scripts/ingest_player_stats.py
    python scripts/ingest_player_stats.py --csv path/to/players_data-2025_2026.csv
    python scripts/ingest_player_stats.py --season 24/25 --csv path/to/players_data-2024_2025.csv
"""
import sys
import os
import argparse

# Ensure backend is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.services.player_stats_service import ingest_player_stats
from backend.core.config import ACTIVE_CONFIG
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LEAGUE_NAME = ACTIVE_CONFIG["name"]
LEAGUE_KEY = ACTIVE_CONFIG["fdco_code"].lower()

# Update default path to be league-specific
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_CSV = os.path.join(PROJECT_ROOT, "data", "raw", "ligue1_players_data-2025_2026.csv")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=f"Ingest player stats CSV for {LEAGUE_NAME}"
    )
    parser.add_argument("--csv", default=DEFAULT_CSV, help="Path to the CSV file")
    parser.add_argument("--season", default="25/26", help="Season label e.g. 25/26")
    args = parser.parse_args()

    if not os.path.exists(args.csv):
        print(f"❌ CSV not found: {args.csv}")
        print(f"   League: {LEAGUE_NAME}")
        print(f"   Expected a CSV with Ligue 1 player data")
        print(f"   Download from Kaggle or FBref, then place it at: {DEFAULT_CSV}")
        sys.exit(1)

    logger.info(f"Starting ingestion for {LEAGUE_NAME} season {args.season}")
    count = ingest_player_stats(args.csv, args.season)
    print(f"\n✅ Done! {count} {LEAGUE_NAME} player records saved to Supabase player_stats table")