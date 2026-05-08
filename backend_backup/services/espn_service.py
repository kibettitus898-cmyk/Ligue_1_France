"""
Fetches possession % from ESPN API for Ligue 1 fixtures.
Fast approach: uses actual Ligue 1 matchweek dates instead of scanning every calendar day.
"""
import logging
import time
import requests
from datetime import date, timedelta
from backend.core.supabase_client import get_supabase
from backend.core.config import ACTIVE_CONFIG


logger = logging.getLogger(__name__)


# ESPN API uses 'fra.1' for Ligue 1
LEAGUE_SLUG = "fra.1"
ESPN_SCOREBOARD = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{LEAGUE_SLUG}/scoreboard"
ESPN_SUMMARY    = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{LEAGUE_SLUG}/summary"


# Ligue 1 seasons: Aug–May (18 teams, 34 matchweeks)
# Maps season_year → (start_date, end_date, season_label)
SEASON_DATE_RANGES = {
    2019: ("2019-08-09", "2020-03-07", "19/20"),   # COVID-aborted
    2020: ("2020-08-21", "2021-05-23", "20/21"),
    2021: ("2021-08-06", "2022-05-21", "21/22"),
    2022: ("2022-08-05", "2023-06-03", "22/23"),   # World Cup extended
    2023: ("2023-08-11", "2024-05-19", "23/24"),
    2024: ("2024-08-16", "2025-05-17", "24/25"),
}


def fetch_events_for_date(match_date: str) -> list[dict]:
    """Fetch all Ligue 1 events for YYYY-MM-DD. Returns [] silently if none."""
    try:
        r = requests.get(
            ESPN_SCOREBOARD,
            params={"dates": match_date.replace("-", "")},
            timeout=10
        )
        if r.status_code != 200:
            return []
        data = r.json()
        events = []
        for event in data.get("events", []):
            try:
                comp   = event["competitions"][0]
                home   = next(t for t in comp["competitors"] if t["homeAway"] == "home")
                away   = next(t for t in comp["competitors"] if t["homeAway"] == "away")
                status = comp.get("status", {}).get("type", {}).get("completed", False)
                if not status:
                    continue  # skip unplayed fixtures
                events.append({
                    "event_id":  event["id"],
                    "date":      event["date"][:10],
                    "home_team": home["team"]["displayName"],
                    "away_team": away["team"]["displayName"],
                })
            except (KeyError, StopIteration):
                continue
        return events
    except Exception as e:
        logger.debug(f"Scoreboard failed {match_date}: {e}")
        return []


def fetch_possession(event_id: str) -> dict:
    """Fetch possession % from ESPN match summary."""
    try:
        r = requests.get(ESPN_SUMMARY, params={"event": event_id}, timeout=10)
        if r.status_code != 200:
            return {}
        data  = r.json()
        teams = data.get("boxscore", {}).get("teams", [])
        result = {}
        for team in teams:
            side = "home" if team.get("homeAway") == "home" else "away"
            for stat in team.get("statistics", []):
                if stat.get("name") == "possessionPct":
                    try:
                        result[f"{side}_possession"] = float(
                            stat.get("displayValue", "0").replace("%", "").strip()
                        )
                    except ValueError:
                        result[f"{side}_possession"] = None
        return result
    except Exception as e:
        logger.debug(f"Summary failed event {event_id}: {e}")
        return {}


def get_match_dates(start_str: str, end_str: str) -> list[str]:
    """
    Only return Fri–Wed dates (core Ligue 1 matchdays).
    Thu excluded as Ligue 1 rarely plays Thursdays.
    """
    start, end = date.fromisoformat(start_str), date.fromisoformat(end_str)
    dates, cur = [], start
    while cur <= end:
        # 4=Fri, 5=Sat, 6=Sun, 0=Mon, 1=Tue, 2=Wed
        if cur.weekday() in [4, 5, 6, 0, 1, 2]:
            dates.append(cur.isoformat())
        cur += timedelta(days=1)
    return dates


def upsert_possession(records: list[dict]):
    if not records:
        return
    get_supabase().table("match_stats").upsert(
        records, on_conflict="date,home_team,away_team"
    ).execute()


def ingest_possession_season(season_year: int):
    if season_year not in SEASON_DATE_RANGES:
        logger.error(f"Season {season_year} not configured")
        return

    # ── FIX: Unpack season_label from the config tuple ──
    start, end, season_label = SEASON_DATE_RANGES[season_year]
    all_dates  = get_match_dates(start, end)
    total      = len(all_dates)

    logger.info(f"Ligue 1 Season {season_year}/{season_year+1} ({season_label}): scanning {total} dates...")

    records            = []
    dates_with_matches = 0
    total_events       = 0

    for i, match_date in enumerate(all_dates, 1):
        if i % 20 == 0 or i == 1:
            logger.info(f"  Progress: {i}/{total} dates | "
                        f"matchdays found: {dates_with_matches} | "
                        f"events: {total_events} | "
                        f"possession records: {len(records)}")

        events = fetch_events_for_date(match_date)
        if not events:
            time.sleep(0.15)
            continue

        dates_with_matches += 1
        total_events       += len(events)
        logger.info(f"  [{match_date}] {len(events)} matches found")

        for ev in events:
            poss = fetch_possession(ev["event_id"])
            if poss:
                records.append({
                    "season":          season_label,        # ← FIX: season now populated
                    "date":            ev["date"],
                    "home_team":       ev["home_team"],
                    "away_team":       ev["away_team"],
                    "home_possession": poss.get("home_possession"),
                    "away_possession": poss.get("away_possession"),
                })
            time.sleep(0.2)

        time.sleep(0.3)

    # Final upsert
    upsert_possession(records)
    logger.info(
        f"✅ Ligue 1 Season {season_year} ({season_label}): {dates_with_matches} matchdays | "
        f"{total_events} fixtures | {len(records)} possession records saved"
    )
    return len(records)