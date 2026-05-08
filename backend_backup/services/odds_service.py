from __future__ import annotations

import os
import logging
from typing import Any

import requests
from dotenv import load_dotenv

from backend.core.config import ACTIVE_CONFIG, settings
from backend.core.supabase_client import get_supabase
from backend.utils.team_utils import canonical_team_or_self, normalise_team


load_dotenv()
logger = logging.getLogger(__name__)

ODDSPAPI_KEY = os.getenv("ODDSPAPI_KEY") or settings.ODDSPAPI_KEY
BASE_URL = "https://api.oddspapi.io/v4"
TOURNAMENT_ID = ACTIVE_CONFIG.get("tournament_id", 34)

logger.info("OddsPapi configured: BASE_URL=%s, TOURNAMENT_ID=%s", BASE_URL, TOURNAMENT_ID)


def normalise_name(name: str) -> str:
    if not name:
        return ""
    return canonical_team_or_self(name)


def _load_participant_cache() -> dict[int, str]:
    try:
        supabase = get_supabase()
        result = supabase.table("participant_names").select("id,name").execute()
        if result.data:
            mapping = {int(row["id"]): row["name"] for row in result.data}
            logger.info("🗄️  Loaded %d participants from Supabase", len(mapping))
            return mapping
    except Exception as e:
        logger.warning("Supabase participant load failed: %s", e)
    return {}


def _save_participants_to_supabase(mapping: dict[int, str], tournament_id: int | None = None) -> None:
    if not mapping:
        return
    try:
        supabase = get_supabase()
        rows = [
            {
                "id": int(pid),
                "name": name,
                "tournament_id": tournament_id,
                "updated_at": "now()",
            }
            for pid, name in mapping.items()
        ]
        supabase.table("participant_names").upsert(rows, on_conflict="id").execute()
        logger.info("💾 Saved %d participants to Supabase", len(rows))
    except Exception as e:
        logger.warning("Supabase participant save failed: %s", e)


def _fetch_participants_from_fixtures() -> dict[int, str]:
    mapping: dict[int, str] = {}

    try:
        resp = requests.get(
            f"{BASE_URL}/fixtures",
            params={"apiKey": ODDSPAPI_KEY, "tournamentId": TOURNAMENT_ID},
            timeout=15,
        )

        if resp.status_code == 200:
            fixtures = resp.json()
            if isinstance(fixtures, list):
                for f in fixtures:
                    p1_id = f.get("participant1Id")
                    p2_id = f.get("participant2Id")
                    p1_name = normalise_name(f.get("participant1Name", "").strip())
                    p2_name = normalise_name(f.get("participant2Name", "").strip())

                    if p1_id and p1_name:
                        mapping[int(p1_id)] = p1_name
                    if p2_id and p2_name:
                        mapping[int(p2_id)] = p2_name

                if mapping:
                    logger.info("🔍 Auto-discovered %d participants from /fixtures", len(mapping))
                    return mapping
        else:
            logger.warning("/fixtures returned %s: %s", resp.status_code, resp.text[:200])
    except Exception as e:
        logger.warning("Auto-discovery via /fixtures failed: %s", e)

    return mapping


PARTICIPANT_ID_MAP = _load_participant_cache()

if not PARTICIPANT_ID_MAP:
    api_map = _fetch_participants_from_fixtures()
    if api_map:
        PARTICIPANT_ID_MAP.update(api_map)
        _save_participants_to_supabase(api_map, tournament_id=TOURNAMENT_ID)

logger.info("Participant map ready: %d teams", len(PARTICIPANT_ID_MAP))


def _enrich_fixture_names(fixture: dict[str, Any]) -> dict[str, Any]:
    p1_id = fixture.get("participant1Id")
    p2_id = fixture.get("participant2Id")

    p1_name = fixture.get("participant1Name", "").strip()
    p2_name = fixture.get("participant2Name", "").strip()

    if not p1_name and p1_id and p1_id in PARTICIPANT_ID_MAP:
        p1_name = PARTICIPANT_ID_MAP[p1_id]
    if not p2_name and p2_id and p2_id in PARTICIPANT_ID_MAP:
        p2_name = PARTICIPANT_ID_MAP[p2_id]

    p1_name = normalise_name(p1_name)
    p2_name = normalise_name(p2_name)

    fixture["participant1Name"] = p1_name
    fixture["participant2Name"] = p2_name

    if p1_id and p1_name and p1_id not in PARTICIPANT_ID_MAP:
        PARTICIPANT_ID_MAP[p1_id] = p1_name
    if p2_id and p2_name and p2_id not in PARTICIPANT_ID_MAP:
        PARTICIPANT_ID_MAP[p2_id] = p2_name

    if p1_id and not p1_name:
        logger.warning("Unknown participant1Id: %s", p1_id)
    if p2_id and not p2_name:
        logger.warning("Unknown participant2Id: %s", p2_id)

    return fixture


def get_upcoming_fixtures() -> list[dict]:
    url = f"{BASE_URL}/odds-by-tournaments"
    params = {
        "apiKey": ODDSPAPI_KEY,
        "bookmaker": "pinnacle",
        "tournamentIds": TOURNAMENT_ID,
    }

    logger.info("Fetching: %s with tournamentIds=%s", url, TOURNAMENT_ID)
    resp = requests.get(url, params=params, timeout=15)

    if resp.status_code != 200:
        logger.error("OddsPapi error %s: %s", resp.status_code, resp.text[:500])
        resp.raise_for_status()

    data = resp.json()
    fixtures = []

    if isinstance(data, list):
        fixtures = data
    elif isinstance(data, dict):
        for key in ("fixtures", "data", "results", "events"):
            if key in data and isinstance(data[key], list):
                fixtures = data[key]
                break
        if not fixtures:
            for val in data.values():
                if isinstance(val, list):
                    fixtures = val
                    break

    logger.info("Fixtures returned: %d found", len(fixtures))

    new_discoveries = {}
    enriched = []

    for fix in fixtures:
        fix = _enrich_fixture_names(fix)

        p1_id = fix.get("participant1Id")
        p2_id = fix.get("participant2Id")
        p1_name = fix.get("participant1Name", "")
        p2_name = fix.get("participant2Name", "")

        if p1_id and p1_name and p1_id not in PARTICIPANT_ID_MAP:
            new_discoveries[p1_id] = p1_name
            PARTICIPANT_ID_MAP[p1_id] = p1_name

        if p2_id and p2_name and p2_id not in PARTICIPANT_ID_MAP:
            new_discoveries[p2_id] = p2_name
            PARTICIPANT_ID_MAP[p2_id] = p2_name

        enriched.append(fix)

    if new_discoveries:
        _save_participants_to_supabase(new_discoveries, tournament_id=TOURNAMENT_ID)
        logger.info("🔍 Auto-discovered %d new participants", len(new_discoveries))

    return enriched


def extract_1x2_odds(fixture: dict, bookmaker: str = "pinnacle") -> dict | None:
    try:
        bm_odds = fixture["bookmakerOdds"][bookmaker]
        markets = bm_odds["markets"]
    except (KeyError, TypeError):
        return None

    market_101 = markets.get("101", {})
    outcomes = market_101.get("outcomes", {})
    if outcomes and len(outcomes) >= 3:
        prices = {}
        outcome_map = {"101": "b365h", "102": "b365d", "103": "b365a"}
        for outcome_key, price_key in outcome_map.items():
            try:
                price = float(outcomes[outcome_key]["players"]["0"]["price"])
                if price > 1.0:
                    prices[price_key] = price
            except (KeyError, TypeError, ValueError, IndexError):
                continue
        if len(prices) == 3:
            return prices

    for market_id, market_data in markets.items():
        try:
            outs = market_data.get("outcomes", {})
            if len(outs) == 3:
                prices = {}
                keys = list(outs.keys())
                mapping = {keys[0]: "b365h", keys[1]: "b365d", keys[2]: "b365a"}

                for ok, pk in mapping.items():
                    price = float(outs[ok]["players"]["0"]["price"])
                    if price > 1.0:
                        prices[pk] = price

                if len(prices) == 3:
                    logger.debug("Extracted odds from market %s: %s", market_id, prices)
                    return prices
        except Exception:
            continue

    logger.warning("Could not extract 3 valid prices for fixture %s", fixture.get("fixtureId") or fixture.get("id"))
    return None


def get_b365_odds(fixture_id: str) -> dict | None:
    logger.warning("get_b365_odds() is deprecated — use extract_1x2_odds() on fixture object")
    return None


def calculate_ev(model_prob: float, decimal_odd: float) -> float:
    return round((model_prob * decimal_odd) - 1, 4)