from fastapi import APIRouter
from backend.services.cache_service import get_cache_status, invalidate_cache
from backend.core.config import ACTIVE_CONFIG
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/cache/status")
def cache_status():
    league = ACTIVE_CONFIG["fdco_code"].lower()  # Should be "f1"
    result = get_cache_status(league)
    
    # FORCE override — guarantees correct league in response
    result["league"] = league
    result["source"] = result.get("source")  # preserve whatever cache_service returns
    
    logger.info(f"CACHE STATUS endpoint: league={league}, result={result}")
    return result


@router.get("/cache/status/all")
def cache_status_all():
    league = ACTIVE_CONFIG["fdco_code"].lower()
    status = get_cache_status(league)
    return {
        "caches": {
            league: {
                "cached": status.get("cached", False),
                "fixture_count": status.get("fixture_count", 0)
            }
        }
    }


@router.post("/cache/invalidate")
def cache_invalidate():
    league = ACTIVE_CONFIG["fdco_code"].lower()
    result = invalidate_cache(league)
    return result


@router.get("/cache/debug")
def cache_debug():
    from backend.core.config import ACTIVE_CONFIG, settings
    return {
        "active_config_fdco": ACTIVE_CONFIG["fdco_code"],
        "active_config_fdco_lower": ACTIVE_CONFIG["fdco_code"].lower(),
        "settings_active_league": settings.ACTIVE_LEAGUE,
        "cache_key_used": f"upcoming_{ACTIVE_CONFIG['fdco_code'].lower()}",
    }

@router.get("/cache/whereami")
def whereami():
    import backend.api.v1.endpoints.cache as mod
    return {
        "file": mod.__file__,
        "has_correct_status": hasattr(mod, 'cache_status'),
    }