"""
League-agnostic feature definitions for the active league (currently: Ligue 1).
All columns are generic football metrics — no league-specific hardcoding.
"""

from backend.core.config import ACTIVE_CONFIG  # pulls ligue1 config

# ── Feature column definitions ────────────────────────────────────────────────
FEATURE_COLS = [
    # ── Rolling goals ─────────────────────────────────────────────────────────
    "h_goals_scored_3",   "h_goals_scored_5",   "h_goals_scored_10",
    "h_goals_conceded_3", "h_goals_conceded_5", "h_goals_conceded_10",
    "a_goals_scored_3",   "a_goals_scored_5",   "a_goals_scored_10",
    "a_goals_conceded_3", "a_goals_conceded_5", "a_goals_conceded_10",
    # ── Rolling form ──────────────────────────────────────────────────────────
    "h_form_3", "h_form_5", "h_form_10",
    "a_form_3", "a_form_5", "a_form_10",
    # ── Rolling shots / corners / cards ───────────────────────────────────────
    "h_sot_5",     "a_sot_5",
    "h_corners_5", "a_corners_5",
    "h_cards_5",   "a_cards_5",
    # ── Elo ───────────────────────────────────────────────────────────────────
    "home_elo", "away_elo", "elo_diff",
    # ── Pi-ratings ────────────────────────────────────────────────────────────
    "h_pi_hc", "h_pi_hd",
    "a_pi_ac", "a_pi_ad",
    "pi_atk_diff", "pi_def_diff", "pi_total_diff",
    # ── xG rolling ────────────────────────────────────────────────────────────
    "h_xg_3", "h_xg_5",
    "a_xg_3", "a_xg_5",
    "h_npxg_3", "h_npxg_5",
    "a_npxg_3", "a_npxg_5",
    "h_xgd_5",
    # ── Parity / draw signal ──────────────────────────────────────────────────
    "xg_parity_5",
    "goals_parity_3", "goals_parity_5",
    "def_parity_5",   "form_parity_5",
    "pi_parity",
    # ── Draw propensity features ──────────────────────────────────────────────
    "h_draw_rate_5",
    "a_draw_rate_5",
    "h_draw_rate_10",
    "a_draw_rate_10",
    "h2h_draw_rate",
    "draw_propensity",
    "elo_parity",
    # ── Squad strength ────────────────────────────────────────────────────────
    "h_squad_xg",   "h_squad_xa",   "h_squad_npxg",
    "h_squad_goals","h_squad_ast",  "h_squad_min",
    "a_squad_xg",   "a_squad_xa",   "a_squad_npxg",
    "a_squad_goals","a_squad_ast",  "a_squad_min",
    "squad_xg_diff",
    # ── Contextual ────────────────────────────────────────────────────────────
    "home_days_rest",    "away_days_rest",
    "home_cumpts",       "away_cumpts",
    "is_derby",          "h2h_home_win_rate",
    "matchweek",
    # ── Home advantage ────────────────────────────────────────────────────────
    "home_win_rate_hist","away_win_rate_hist",
    "cumpts_diff",
    "combined_goals_5",
    "sot_balance",
    # ── Bookmaker odds (market wisdom) ────────────────────────────────────────
    "odds_fair_h",
    "odds_fair_d",
    "odds_fair_a",
    "odds_home_edge",
]

TARGET_COL = "ftr"
LABEL_MAP  = {"H": 0, "D": 1, "A": 2}

# ── League-aware helpers ──────────────────────────────────────────────────────
# Use these in your services instead of hardcoding league assumptions
N_TEAMS = ACTIVE_CONFIG["teams_count"]          # 18 for Ligue 1
N_MATCHWEEKS = (N_TEAMS - 1) * 2                # 34 for Ligue 1
LEAGUE_NAME = ACTIVE_CONFIG["name"]             # "Ligue 1"