import sys
import os

# Ensure backend is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.services.espn_service import ingest_possession_season
from backend.core.config import ACTIVE_CONFIG
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LEAGUE_NAME = ACTIVE_CONFIG["name"]

if __name__ == "__main__":
    logger.info(f"Starting ESPN possession ingestion for {LEAGUE_NAME}")
    # Start with just 2024 to verify it works, then backfill
    for year in [2024, 2023, 2022, 2021, 2020, 2019]:
        logger.info(f"  → Ingesting {year}...")
        try:
            count = ingest_possession_season(year)
            logger.info(f"    ✅ {year}: {count} records")
        except Exception as e:
            logger.error(f"    ❌ {year} failed: {e}")
    print(f"✅ ESPN possession ingestion complete for {LEAGUE_NAME}")