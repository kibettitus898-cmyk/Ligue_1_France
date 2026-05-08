import logging
import os
import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException

from backend.core.config import LEAGUE_CONFIG
from backend.services.cache_service import get_cache_status, invalidate_cache
from backend.services.feature_service import build_and_save
from backend.services.ingest_service import ingest_all


logger = logging.getLogger(__name__)
router = APIRouter()

PROJECT_ROOT = Path(__file__).resolve().parents[4]
TRAIN_SCRIPT = PROJECT_ROOT / "backend" / "scripts" / "train_model.py"


@router.post("/pipeline/ingest")
def trigger_ingest(background_tasks: BackgroundTasks):
    background_tasks.add_task(ingest_all)
    return {"message": "Ingestion started in background"}


@router.post("/pipeline/train")
def trigger_train(background_tasks: BackgroundTasks):
    def run():
        try:
            logger.info(f"PROJECT_ROOT resolved to: {PROJECT_ROOT}")
            logger.info(f"TRAIN_SCRIPT resolved to: {TRAIN_SCRIPT}")

            if not TRAIN_SCRIPT.exists():
                raise FileNotFoundError(f"Training script not found: {TRAIN_SCRIPT}")

            df = build_and_save()
            logger.info(f"✅ Features rebuilt: {df.shape}")

            logger.info("🚀 Starting model training...")
            result = subprocess.run(
                [sys.executable, str(TRAIN_SCRIPT)],
                capture_output=True,
                text=True,
                cwd=str(PROJECT_ROOT),
            )

            if result.returncode == 0:
                stdout_tail = result.stdout[-2000:] if result.stdout else ""
                logger.info(f"✅ Model training complete:\n{stdout_tail}")

                invalidate_cache("ligue1")
                logger.info("🗑️ Cache invalidated after retraining")
            else:
                stderr_tail = result.stderr[-4000:] if result.stderr else ""
                stdout_tail = result.stdout[-2000:] if result.stdout else ""
                logger.error(f"❌ Training failed.\nSTDOUT:\n{stdout_tail}\nSTDERR:\n{stderr_tail}")

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)

    background_tasks.add_task(run)
    return {"message": "Pipeline started — rebuilding features then training model"}


@router.get("/cache/status")
def cache_status(league: str = "ligue1"):
    if league not in LEAGUE_CONFIG:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown league '{league}'. Valid: {list(LEAGUE_CONFIG.keys())}",
        )
    return get_cache_status(league)


@router.get("/cache/status/all")
def all_cache_status():
    return {
        league: get_cache_status(league)
        for league in LEAGUE_CONFIG
    }


@router.post("/cache/invalidate")
def bust_cache(league: str = "ligue1", secret: str = ""):
    admin_secret = os.getenv("ADMIN_SECRET", "changeme")
    if secret != admin_secret:
        raise HTTPException(status_code=403, detail="Invalid admin secret")

    if league not in LEAGUE_CONFIG:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown league '{league}'. Valid: {list(LEAGUE_CONFIG.keys())}",
        )

    invalidate_cache(league)
    return {
        "message": f"Cache invalidated for '{league}'",
        "effect": "Next /predict/upcoming request will fetch fresh data from OddsPapi",
    }