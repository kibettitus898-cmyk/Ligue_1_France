import logging
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.services.odds_service import (
    get_upcoming_fixtures, get_b365_odds, calculate_ev, normalise_name
)
from backend.services.feature_service import build_live_features
from backend.services.model_service import load_model, predict_proba
from backend.services.cache_service import get_cached, set_cache, get_cache_status
from backend.core.config import ACTIVE_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LEAGUE = ACTIVE_CONFIG["fdco_code"].lower()  # "f1"

# ── Check cache first — avoids burning API quota on every run ─────────────────
status = get_cache_status(LEAGUE)
if status.get("cached"):
    print(f"\n⚡ Serving from cache "
          f"({status['source']}, "
          f"expires in {status.get('expires_in_mins', '?')} min, "
          f"{status.get('fixture_count', '?')} fixtures)\n")

    cached_results = get_cached(LEAGUE)
    if cached_results:
        for fix in cached_results:
            probs = fix["probabilities"]
            odds  = fix["b365"]
            ev    = fix["ev_analysis"]

            ev_h = next((o["ev"] for o in ev["all_outcomes"] if o["outcome"] == "H"), 0)
            ev_d = next((o["ev"] for o in ev["all_outcomes"] if o["outcome"] == "D"), 0)
            ev_a = next((o["ev"] for o in ev["all_outcomes"] if o["outcome"] == "A"), 0)

            print(f"\n{'='*50}")
            print(f"  {fix['home_team']}  vs  {fix['away_team']}  ({fix['date']})")
            print(f"  Model:  H={probs['H']:.1%}  D={probs['D']:.1%}  A={probs['A']:.1%}")
            print(f"  B365:   H={odds['h']}  D={odds['d']}  A={odds['a']}")
            print(f"  EV:     H={ev_h:+.3f}  D={ev_d:+.3f}  A={ev_a:+.3f}")

            if ev["has_value"] and ev["best_bet"]:
                bb = ev["best_bet"]
                print(f"  🟢 VALUE BET → {bb['outcome']}  "
                      f"EV={bb['ev']:+.3f}  Kelly={bb['kelly_pct']}%")
            else:
                print("  🔴 No value — skip")

        sys.exit(0)

# ── Cache miss — fetch fresh from OddsPapi ────────────────────────────────────
print(f"\n📡 Cache miss — fetching live data from OddsPapi for {ACTIVE_CONFIG['name']}...\n")

model = load_model()
print("✅ Ensemble model loaded")

fixtures = get_upcoming_fixtures()
logger.info(f"Found {len(fixtures)} upcoming {ACTIVE_CONFIG['name']} fixtures")

results = []

for fix in fixtures:
    fixture_id = fix.get("id") or fix.get("fixtureId")
    if not fixture_id:
        logger.warning(f"Fixture missing ID, skipping: {fix}")
        continue

    home       = normalise_name(fix.get("participant1Name", str(fix.get("participant1Id", ""))))
    away       = normalise_name(fix.get("participant2Name", str(fix.get("participant2Id", ""))))
    start_time = fix.get("startTime") or fix.get("startDate", "")

    odds = get_b365_odds(fixture_id)

    if not odds:
        logger.warning(f"  ⚠️  No 1X2 odds for fixture {fixture_id}, skipping")
        continue

    print(f"\n{home} vs {away}  ({start_time})")
    print(f"  B365: H={odds['b365h']}  D={odds['b365d']}  A={odds['b365a']}")

    features = build_live_features(home, away, odds)
    probs    = predict_proba(model, features)   # [p_home, p_draw, p_away]

    ev_h = calculate_ev(probs[0], odds["b365h"])
    ev_d = calculate_ev(probs[1], odds["b365d"])
    ev_a = calculate_ev(probs[2], odds["b365a"])

    all_outcomes = [
        {"outcome": "H", "model_prob": round(probs[0], 4),
         "decimal_odd": odds["b365h"], "ev": round(ev_h, 4),
         "kelly_pct": round(max(((probs[0]*odds["b365h"]-1)/(odds["b365h"]-1))*100, 0), 2),
         "is_value": ev_h > 0.05},
        {"outcome": "D", "model_prob": round(probs[1], 4),
         "decimal_odd": odds["b365d"], "ev": round(ev_d, 4),
         "kelly_pct": round(max(((probs[1]*odds["b365d"]-1)/(odds["b365d"]-1))*100, 0), 2),
         "is_value": ev_d > 0.05},
        {"outcome": "A", "model_prob": round(probs[2], 4),
         "decimal_odd": odds["b365a"], "ev": round(ev_a, 4),
         "kelly_pct": round(max(((probs[2]*odds["b365a"]-1)/(odds["b365a"]-1))*100, 0), 2),
         "is_value": ev_a > 0.05},
    ]
    value_bets = [o for o in all_outcomes if o["is_value"]]
    best_bet   = max(value_bets, key=lambda x: x["ev"]) if value_bets else None

    print(f"\n{'='*50}")
    print(f"  {home}  vs  {away}")
    print(f"  Model:  H={probs[0]:.1%}  D={probs[1]:.1%}  A={probs[2]:.1%}")
    print(f"  B365:   H={odds['b365h']}  D={odds['b365d']}  A={odds['b365a']}")
    print(f"  EV:     H={ev_h:+.3f}  D={ev_d:+.3f}  A={ev_a:+.3f}")

    if best_bet:
        print(f"  🟢 VALUE BET → {best_bet['outcome']}  EV={best_bet['ev']:+.3f}")
    else:
        print("  🔴 No value — skip")

    results.append({
        "fixture_id":    fixture_id,
        "date":          start_time,
        "league":        LEAGUE,
        "home_team":     home,
        "away_team":     away,
        "b365":          {"h": odds["b365h"], "d": odds["b365d"], "a": odds["b365a"]},
        "probabilities": {
            "H": round(probs[0], 4),
            "D": round(probs[1], 4),
            "A": round(probs[2], 4)
        },
        "ev_analysis": {
            "has_value":    len(value_bets) > 0,
            "best_bet":     best_bet,
            "value_bets":   value_bets,
            "all_outcomes": all_outcomes,
        },
    })

# ── Save to cache so API and future runs serve from cache ─────────────────────
if results:
    set_cache(LEAGUE, results)
    print(f"\n💾 {len(results)} fixtures cached — next run serves instantly")