from fastapi import APIRouter, HTTPException
from backend.core.supabase_client import get_supabase

router = APIRouter()


def _normalize_season(season: str) -> str:
    """
    Convert user-friendly season formats to football-data.co.uk short format.
    Examples:
        "2021-2022" → "21/22"
        "2021/2022" → "21/22"
        "21/22"     → "21/22"  (pass-through)
    """
    season = season.strip()
    
    # Already short format (e.g. "21/22") — just ensure separator is "/"
    if len(season) == 5 and season[2] in ("/", "-"):
        return f"{season[:2]}/{season[3:]}"
    
    # Long format with dash or slash (e.g. "2021-2022" or "2021/2022")
    if len(season) == 9 and season[4] in ("/", "-"):
        return f"{season[2:4]}/{season[7:9]}"
    
    # Fallback: return as-is and let Supabase handle it
    return season


@router.get("/matches")
def get_matches(season: str | None = None, limit: int = 50):
    supabase = get_supabase()
    query = supabase.table("match_results").select("*").limit(limit)
    
    if season:
        normalized = _normalize_season(season)
        query = query.eq("season", normalized)
    
    result = query.execute()
    return {"count": len(result.data), "data": result.data}


@router.get("/matches/seasons")
def get_seasons():
    supabase = get_supabase()
    result = supabase.table("match_results").select("season").execute()
    seasons = sorted(set(r["season"] for r in result.data))
    return {"seasons": seasons}