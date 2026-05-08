"""
Derives squad availability (injured + suspended count) per team
before each matchday and stores it for use as a training feature.
"""
import logging
from datetime import date
from backend.core.supabase_client import get_supabase
from backend.services.transfermarkt_service import get_team_injury_count
from backend.core.config import ACTIVE_CONFIG

logger = logging.getLogger(__name__)

# Ligue 1 teams (18) — football-data.co.uk short names
# Update this list each season if promotion/relegation changes
LIGUE1_TEAMS = [
    "Paris SG",
    "Marseille",
    "Lyon",
    "Monaco",
    "Lille",
    "Nice",
    "Rennes",
    "Lens",
    "Reims",
    "Montpellier",
    "Strasbourg",
    "Nantes",
    "Le Havre",
    "Brest",
    "Toulouse",
    "Auxerre",
    "Angers",
    "St Etienne",
]

N_TEAMS = ACTIVE_CONFIG["teams_count"]  # 18


def build_squad_availability_snapshot():
    """
    Call this before each matchday (e.g. via /pipeline/refresh endpoint).
    Saves injury counts for all Ligue 1 teams into squad_availability table.
    """
    supabase = get_supabase()
    today    = date.today().isoformat()
    records  = []

    for team in LIGUE1_TEAMS:
        try:
            counts = get_team_injury_count(team)
            records.append({
                "date":             today,
                "team":             team,
                "league":           ACTIVE_CONFIG["fdco_code"].lower(),
                "injured_count":    counts["injured_count"],
                "suspended_count":  counts["suspended_count"],
                "total_missing":    counts["total_missing"],
            })
        except Exception as e:
            logger.warning(f"Failed to fetch injury data for {team}: {e}")

    if records:
        supabase.table("squad_availability").upsert(
            records, on_conflict="date,team"
        ).execute()
        logger.info(f"✅ Squad availability snapshot saved for {today} — {len(records)}/{N_TEAMS} teams")
    return records


def get_availability_feature(team: str, match_date: str) -> int:
    """
    Looks up total_missing for a team on or before a given date.
    Returns 0 if no data available (safe default).
    """
    supabase = get_supabase()
    result   = (
        supabase.table("squad_availability")
        .select("total_missing")
        .eq("team", team)
        .lte("date", match_date)
        .order("date", desc=True)
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0]["total_missing"]
    return 0