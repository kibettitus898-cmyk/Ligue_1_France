import sys
import os

# Ensure backend is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.services.transfermarkt_service import ingest_live_injuries
from backend.services.squad_availability_service import build_squad_availability_snapshot
from backend.core.config import ACTIVE_CONFIG
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LEAGUE_NAME = ACTIVE_CONFIG["name"]

if __name__ == "__main__":
    logger.info(f"Refreshing injuries + squad availability for {LEAGUE_NAME}")
    try:
        ingest_live_injuries()
        logger.info("  ✅ Live injuries ingested from Transfermarkt")
    except Exception as e:
        logger.error(f"  ❌ Injury ingestion failed: {e}")

    try:
        build_squad_availability_snapshot()
        logger.info("  ✅ Squad availability snapshot built")
    except Exception as e:
        logger.error(f"  ❌ Squad availability snapshot failed: {e}")

    print(f"✅ Injuries + squad availability refreshed for {LEAGUE_NAME}")