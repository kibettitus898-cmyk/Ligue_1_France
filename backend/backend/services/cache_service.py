import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from backend.core.supabase_client import get_supabase
from backend.core.config import ACTIVE_CONFIG

logger = logging.getLogger(__name__)

# L1: in-memory cache (lost on restart, but fast)
_memory_cache: dict[str, dict] = {}

DEFAULT_LEAGUE = ACTIVE_CONFIG["fdco_code"].lower()  # Must be "f1"

def _make_cache_key(league: str) -> str:
    return f"upcoming_{league}"


def _calc_ttl_hours(league: str = DEFAULT_LEAGUE) -> int:
    now = datetime.now(timezone.utc)
    weekday = now.weekday()  # 0=Mon, 5=Sat, 6=Sun
    # Refresh more often on match days (Fri-Sun + Tue-Wed)
    if weekday in (1, 2, 4, 5, 6):
        return 1
    return 6


def get_cached(league: str = DEFAULT_LEAGUE) -> Optional[list]:
    """
    L1 (memory) → L2 (Supabase) fallback.
    Returns list of fixture predictions or None.
    """
    key = _make_cache_key(league)
    now = datetime.now(timezone.utc)

    # ── L1: Memory cache ──────────────────────────────────────────────────────
    if key in _memory_cache:
        entry = _memory_cache[key]
        if entry["expires_at"] > now:
            mins = int((entry["expires_at"] - now).total_seconds() / 60)
            logger.info(f"⚡ Memory cache hit for {key} (expires in {mins} min)")
            return entry["payload"]
        else:
            logger.info(f"⏰ Memory cache expired for {key}")
            del _memory_cache[key]

    # ── L2: Supabase cache ────────────────────────────────────────────────────
    try:
        supabase = get_supabase()
        result = (
            supabase.table("predictions_cache")
            .select("*")
            .eq("cache_key", key)
            .gt("expires_at", now.isoformat())
            .execute()
        )
        if result.data:
            row = result.data[0]
            expires_at = datetime.fromisoformat(row["expires_at"])
            fetched_at = datetime.fromisoformat(row["fetched_at"])

            # Hydrate L1 memory cache
            _memory_cache[key] = {
                "payload": row["payload"],
                "expires_at": expires_at,
                "fetched_at": fetched_at,
            }

            # Increment hit counter
            supabase.table("predictions_cache").update(
                {"hit_count": row["hit_count"] + 1}
            ).eq("cache_key", key).execute()

            mins = int((expires_at - now).total_seconds() / 60)
            logger.info(
                f"🗄️  Supabase cache hit for {key} "
                f"(expires in {mins} min, hit #{row['hit_count'] + 1})"
            )
            return row["payload"]

    except Exception as e:
        logger.warning(f"Cache read failed for {key}: {e}")

    return None


def set_cache(league: str, payload: list) -> None:
    """Write to L1 (memory) + L2 (Supabase)."""
    key = _make_cache_key(league)
    now = datetime.now(timezone.utc)
    ttl_hours = _calc_ttl_hours(league)
    expires_at = now + timedelta(hours=ttl_hours)
    fixture_ids = [str(f.get("fixture_id", "")) for f in payload]

    # L1
    _memory_cache[key] = {
        "payload": payload,
        "expires_at": expires_at,
        "fetched_at": now,
    }

    # L2
    try:
        supabase = get_supabase()
        supabase.table("predictions_cache").upsert(
            {
                "cache_key": key,
                "league": league,
                "payload": payload,
                "fixture_ids": fixture_ids,
                "fetched_at": now.isoformat(),
                "expires_at": expires_at.isoformat(),
                "hit_count": 0,
            },
            on_conflict="cache_key",
        ).execute()

        logger.info(
            f"💾 Cache saved for {key} — {len(payload)} fixtures, "
            f"TTL {ttl_hours}h (expires {expires_at.strftime('%H:%M UTC')})"
        )
    except Exception as e:
        logger.warning(f"Cache write failed for {key}: {e}")


def invalidate_cache(league: str = DEFAULT_LEAGUE) -> dict:
    """Clear L1 + L2 cache for a league."""
    key = _make_cache_key(league)

    # L1
    if key in _memory_cache:
        del _memory_cache[key]

    # L2
    try:
        supabase = get_supabase()
        supabase.table("predictions_cache").delete().eq("cache_key", key).execute()
        logger.info(f"🗑️  Cache invalidated for {key}")
    except Exception as e:
        logger.warning(f"Cache invalidation failed for {key}: {e}")

    return {"status": "ok", "message": f"Cache invalidated for league {league}", "league": league}


def get_cache_status(league: str = DEFAULT_LEAGUE) -> dict:
    """Return cache metadata for a league."""
    key = _make_cache_key(league)
    now = datetime.now(timezone.utc)

    # L1 hit
    if key in _memory_cache:
        entry = _memory_cache[key]
        expires_in = max(0, int((entry["expires_at"] - now).total_seconds() / 60))
        return {
            "league": league,
            "cached": True,
            "source": "memory",
            "fixture_count": len(entry["payload"]),
            "expires_in_mins": expires_in,
            "last_updated": entry["fetched_at"].isoformat(),
        }

    # L2 hit
    try:
        supabase = get_supabase()
        result = (
            supabase.table("predictions_cache")
            .select("fetched_at, expires_at, hit_count, fixture_ids")
            .eq("cache_key", key)
            .execute()
        )
        if result.data:
            row = result.data[0]
            expires_at = datetime.fromisoformat(row["expires_at"])
            is_fresh = expires_at > now
            expires_in = max(0, int((expires_at - now).total_seconds() / 60)) if is_fresh else 0
            return {
                "league": league,
                "cached": is_fresh,
                "source": "supabase" if is_fresh else None,
                "fixture_count": len(row["fixture_ids"]),
                "expires_in_mins": expires_in,
                "last_updated": row["fetched_at"],
                "total_hits": row["hit_count"],
            }
    except Exception as e:
        logger.warning(f"Cache status check failed: {e}")

    # Miss
    return {
        "league": league,
        "cached": False,
        "source": None,
        "fixture_count": 0,
        "expires_in_mins": 0,
        "last_updated": None,
    }