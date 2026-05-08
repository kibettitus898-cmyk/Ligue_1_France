import sys
import os
import logging

# Add project root (parent of backend/) to Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from backend.services.feature_service import build_and_save
from backend.core.config import ACTIVE_CONFIG
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LEAGUE_KEY = ACTIVE_CONFIG["fdco_code"].lower()  # "f1"

if __name__ == "__main__":
    df = build_and_save()
    print(f"\n✅ Features built: {len(df)} rows × {len(df.columns)} columns")
    print(f"   League: {ACTIVE_CONFIG['name']} ({LEAGUE_KEY})")
    print(f"   Saved → data/processed/features_{LEAGUE_KEY}.parquet")
    print(f"\n   Column groups:")
    print(f"   • Rolling match stats : {len([c for c in df.columns if 'goals' in c or 'form' in c or 'sot' in c])}")
    print(f"   • Elo features        : {len([c for c in df.columns if 'elo' in c])}")
    print(f"   • xG features         : {len([c for c in df.columns if 'xg' in c or 'npxg' in c])}")
    print(f"   • Possession features : {len([c for c in df.columns if 'poss' in c])}")
    print(f"   • Squad features      : {len([c for c in df.columns if 'squad' in c])}")
    print(f"   • Contextual features : {len([c for c in df.columns if c in ['home_days_rest','away_days_rest','home_cumpts','away_cumpts','is_derby','h2h_home_win_rate']])}")

    # ── Odds coverage report ─────────────────────────────────────────────
    print(f"\n   Odds features coverage:")
    odds_fills = {
        "odds_fair_h":    ACTIVE_CONFIG.get("home_win_rate", 0.41),
        "odds_fair_d":    ACTIVE_CONFIG.get("draw_rate", 0.29),
        "odds_fair_a":    ACTIVE_CONFIG.get("away_win_rate", 0.30),
        "odds_home_edge": ACTIVE_CONFIG.get("home_edge", 0.11),
    }
    for col, fill_val in odds_fills.items():
        if col in df.columns:
            real_rows = (df[col] != fill_val).sum()
            print(f"   • {col:<20}: {real_rows} rows with real odds  (fill={fill_val})")
        else:
            print(f"   • {col:<20}: ❌ MISSING from parquet")

    # ── Draw feature coverage ────────────────────────────────────────────
    print(f"\n   Draw propensity features coverage:")
    draw_cols = ["h_draw_rate_5", "a_draw_rate_5", "draw_propensity",
                 "h2h_draw_rate", "elo_parity"]
    for col in draw_cols:
        if col in df.columns:
            print(f"   • {col:<20}: ✅ present | mean={df[col].mean():.3f}")
        else:
            print(f"   • {col:<20}: ❌ MISSING")