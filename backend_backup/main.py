import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.v1.endpoints import matches, predict, pipeline, cache
from backend.api.v1.endpoints.payments import router as payments_router
from backend.core.config import settings, ACTIVE_CONFIG
from backend.services.cache_service import get_cached
import logging

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: warm cache if empty. Shutdown: cleanup."""
    league = ACTIVE_CONFIG["fdco_code"].lower()

    # ── STARTUP ───────────────────────────────────────────────────────────────
    cached = get_cached(league)
    if cached is not None:
        logger.info(f"✅ Startup: cache warm ({len(cached)} fixtures from Supabase)")
    else:
        logger.info("🚀 Startup: cache empty — warming from OddsPapi...")
        try:
            # Run sync prediction logic in thread pool (non-blocking)
            result = await asyncio.to_thread(predict.predict_upcoming, limit=20)
            fixtures = result.get("fixtures", [])
            logger.info(f"✅ Startup: cache warmed with {len(fixtures)} fixtures")
        except Exception as e:
            logger.error(f"❌ Startup cache warm-up failed: {e}")

    yield

    # ── SHUTDOWN ──────────────────────────────────────────────────────────────
    logger.info("👋 Server shutting down")


# Create app with lifespan
app = FastAPI(
    title=f"{ACTIVE_CONFIG['name']} Match Outcome Predictor",
    description=f"Predicts {ACTIVE_CONFIG['name']} match outcomes using ensemble ML + engineered features",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
@app.get("/")
def root():
    return {
        "status": "ok",
        "message": f"{ACTIVE_CONFIG['name']} Predictor API is running",
        "league": ACTIVE_CONFIG["fdco_code"].lower(),
    }

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "league": ACTIVE_CONFIG["name"],
        "league_code": ACTIVE_CONFIG["fdco_code"].lower(),
    }

# Routers
app.include_router(matches.router,  prefix="/api/v1", tags=["Matches"])
app.include_router(predict.router,  prefix="/api/v1", tags=["Predictions"])
app.include_router(pipeline.router, prefix="/api/v1", tags=["Pipeline"])
app.include_router(payments_router, prefix="/api/v1/payments", tags=["Payments"])
app.include_router(cache.router,    prefix="/api/v1", tags=["Cache"])