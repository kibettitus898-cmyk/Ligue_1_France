import sys
import os

# Ensure backend is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.services.xg_service import ingest_all_xg
from backend.core.config import ACTIVE_CONFIG
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LEAGUE_NAME = ACTIVE_CONFIG["name"]

if __name__ == "__main__":
    logger.info(f"Starting xG ingestion for {LEAGUE_NAME}")
    try:
        ingest_all_xg()
        logger.info(f"✅ xG data ingested for {LEAGUE_NAME}")
    except Exception as e:
        logger.error(f"❌ xG ingestion failed for {LEAGUE_NAME}: {e}")
        raise