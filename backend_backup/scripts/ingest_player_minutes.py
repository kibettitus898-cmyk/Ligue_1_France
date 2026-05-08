import sys
import os

# Ensure backend is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.services.understat_player_service import ingest_all_player_minutes
from backend.core.config import ACTIVE_CONFIG
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LEAGUE_NAME = ACTIVE_CONFIG["name"]

if __name__ == "__main__":
    logger.info(f"Starting Understat player minutes ingestion for {LEAGUE_NAME}")
    try:
        ingest_all_player_minutes()
        logger.info(f"✅ All player minutes ingested from Understat for {LEAGUE_NAME}")
    except Exception as e:
        logger.error(f"❌ Player minutes ingestion failed: {e}")
        raise