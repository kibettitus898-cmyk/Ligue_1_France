"""
Run this once to load all historical seasons into Supabase.
"""
import sys
import os
import logging

# Point to the PROJECT ROOT (two levels up from backend/scripts/)
# This makes the 'backend' folder visible as a package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.services.ingest_service import ingest_all
from backend.core.config import ACTIVE_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use .get() to avoid KeyErrors if Ligue 1 config differs slightly
LEAGUE_NAME = ACTIVE_CONFIG.get("name", "Ligue 1")
LEAGUE_CODE = ACTIVE_CONFIG.get("fdco_code", "F1")

if __name__ == "__main__":
    logger.info(f"Starting full historical ingestion for {LEAGUE_NAME} ({LEAGUE_CODE})")
    try:
        ingest_all()
        logger.info(f"✅ All seasons ingested successfully for {LEAGUE_NAME}")
    except Exception as e:
        logger.error(f"❌ Full ingestion failed for {LEAGUE_NAME}: {e}")
        raise