import logging
import subprocess
import os
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, HTTPException
from backend.services.ingest_service import ingest_all
from backend.services.feature_service import build_and_save
from backend.services.cache_service import invalidate_cache, get_cache_status
from backend.core.config import LEAGUE_CONFIG

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Existing endpoints — unchanged ────────────────────────────────────────────
@router.post("/pipeline/ingest")
def trigger_ingest(background_tasks: BackgroundTasks):
    background_tasks.add_task(ingest_all)
    return {"message": "Ingestion started in background"}


@router.post("/pipeline/train")
def trigger_train(background_tasks: BackgroundTasks):
    def run():
        try:
            df = build_and_save()
            logger.info(f"✅ Features rebuilt: {df.shape}")

            logger.info("🚀 Starting model training...")
            result = subprocess.run(
                ["python", "scripts/train_model.py"],
                capture_output=True,
                text=True,
                cwd="/home/scop/Betting AI/season specicific/Ligue 1 (France)/Ligue_1"
                # ✅ Updated path to Ligue 1 project directory
            )
            if result.returncode == 0:
                logger.info(f"✅ Model training complete:\n{result.stdout[-500:]}")
                # ── Auto-invalidate cache after retraining ─────────────────
                invalidate_cache("ligue1")  # ✅ Changed from "epl"
                logger.info("🗑️  Cache invalidated after retraining")
            else:
                logger.error(f"❌ Training failed:\n{result.stderr[-500:]}")

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)

    background_tasks.add_task(run)
    return {"message": "Pipeline started — rebuilding features then training model"}


# ── New cache management endpoints ───────────────────────────────────────────
@router.get("/cache/status")
def cache_status(league: str = "ligue1"):  # ✅ Default changed from "epl"
    """Check current cache state for a league."""
    if league not in LEAGUE_CONFIG:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown league '{league}'. Valid: {list(LEAGUE_CONFIG.keys())}"
        )
    return get_cache_status(league)


@router.get("/cache/status/all")
def all_cache_status():
    """Overview of cache state across all configured leagues."""
    return {
        league: get_cache_status(league)
        for league in LEAGUE_CONFIG
    }


@router.post("/cache/invalidate")
def bust_cache(league: str = "ligue1", secret: str = ""):  # ✅ Default changed from "epl"
    """
    Force-bust the predictions cache for a league.
    Requires ADMIN_SECRET env var to prevent abuse.
    Next request to /predict/upcoming will trigger a fresh OddsPapi fetch.
    """
    admin_secret = os.getenv("ADMIN_SECRET", "changeme")
    if secret != admin_secret:
        raise HTTPException(status_code=403, detail="Invalid admin secret")

    if league not in LEAGUE_CONFIG:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown league '{league}'. Valid: {list(LEAGUE_CONFIG.keys())}"
        )

    invalidate_cache(league)
    return {
        "message":  f"Cache invalidated for '{league}'",
        "effect":   "Next /predict/upcoming request will fetch fresh data from OddsPapi",
    }