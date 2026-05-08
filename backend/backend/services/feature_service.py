"""
Loads all data sources from Supabase, engineers pre-match features,
and returns a model-ready DataFrame saved to data/processed/features.parquet.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from backend.core.config import ACTIVE_CONFIG
from backend.core.supabase_client import get_supabase
from backend.utils.team_utils import canonical_team_or_self, normalise_team


logger = logging.getLogger(__name__)

LEAGUE_KEY = ACTIVE_CONFIG["fdco_code"].lower()
BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
ELO_RATINGS_PATH = BASE_DIR / "models" / "saved" / LEAGUE_KEY / "elo_ratings.json"

ROLLING_WINDOWS = [3, 5, 10]
ELO_K = 32
ELO_DEFAULT = 1500.0

HOME_WIN_RATE = 0.41
DRAW_RATE = 0.29
AWAY_WIN_RATE = 0.30
HOME_EDGE = 0.11

BIG_CLUBS = {"Paris SG", "Marseille", "Lyon", "Monaco", "Lille", "Nice"}


def _normalise_team_name(name: str) -> str:
    return canonical_team_or_self(name)


def _normalise_teams(df: pd.DataFrame, cols: list[str] | None = None) -> pd.DataFrame:
    if df.empty:
        return df
    if cols is None:
        cols = [c for c in ["home_team", "away_team", "team"] if c in df.columns]
    for col in cols:
        df[col] = df[col].apply(lambda x: canonical_team_or_self(x) if pd.notna(x) else x)
    return df


def _load_elo_state() -> dict:
    if ELO_RATINGS_PATH.exists():
        try:
            with open(ELO_RATINGS_PATH, "r", encoding="utf-8") as f:
                state = json.load(f)
            logger.info("✅ Loaded %d Elo ratings from %s", len(state), ELO_RATINGS_PATH)
            return state
        except Exception as e:
            logger.warning("Failed to load Elo ratings from %s: %s", ELO_RATINGS_PATH, e)
            return {}
    logger.warning("Elo ratings file not found at %s; using defaults", ELO_RATINGS_PATH)
    return {}


_ELO_STATE = _load_elo_state()


def reload_elo_state() -> dict:
    global _ELO_STATE
    _ELO_STATE = _load_elo_state()
    return _ELO_STATE


def get_current_elo(team: str, default: float = ELO_DEFAULT) -> float:
    team = _normalise_team_name(team)
    return float(_ELO_STATE.get(team, default))


def _paginated_query(table: str, select: str = "*", order_col: str | None = None) -> list:
    supabase = get_supabase()
    all_rows = []
    page_size = 1000
    offset = 0

    while True:
        q = supabase.table(table).select(select)
        if order_col:
            q = q.order(order_col)

        result = q.range(offset, offset + page_size - 1).execute()
        batch = result.data or []
        if not batch:
            break

        all_rows.extend(batch)
        logger.info("  [%s] fetched %d rows...", table, len(all_rows))
        offset += page_size

        if len(batch) < page_size:
            break

    logger.info("  [%s] ✅ %d total rows", table, len(all_rows))
    return all_rows


def load_matches() -> pd.DataFrame:
    rows = _paginated_query("match_results", "*", order_col="date")
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    df = _normalise_teams(df, cols=["home_team", "away_team"])
    return df.sort_values("date").reset_index(drop=True)


def load_xg() -> pd.DataFrame:
    rows = _paginated_query(
        "xg_data",
        "season,date,home_team,away_team,home_xg,away_xg,home_npxg,away_npxg,xgd",
    )
    df = pd.DataFrame(rows)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df = _normalise_teams(df)
    return df


def load_possession() -> pd.DataFrame:
    rows = _paginated_query(
        "match_stats",
        "date,home_team,away_team,home_possession,away_possession",
    )
    df = pd.DataFrame(rows)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df = _normalise_teams(df)
    return df


def load_squad_strength() -> pd.DataFrame:
    rows = _paginated_query(
        "player_minutes",
        "season,team,minutes,xg,xa,npxg,goals,assists",
    )
    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["season"] = df["season"].astype(str).str.replace(
        r"20(\d{2})/20(\d{2})", r"\1/\2", regex=True
    )
    df = _normalise_teams(df, cols=["team"])
    df = df.sort_values("minutes", ascending=False)
    df = df.groupby(["season", "team"]).head(14)

    squad = df.groupby(["season", "team"]).agg(
        squad_avg_xg=("xg", "mean"),
        squad_avg_xa=("xa", "mean"),
        squad_avg_npxg=("npxg", "mean"),
        squad_total_goals=("goals", "sum"),
        squad_total_ast=("assists", "sum"),
        squad_avg_min=("minutes", "mean"),
    ).reset_index()

    return squad


def _rolling(
    df: pd.DataFrame,
    team_col: str,
    stat_col: str,
    window: int,
    new_name: str,
) -> pd.Series:
    return (
        df.groupby(team_col)[stat_col]
        .transform(lambda x: x.shift(1).rolling(window, min_periods=1).mean())
        .rename(new_name)
    )


def _compute_elo(df: pd.DataFrame) -> pd.DataFrame:
    elo = {}
    home_elos, away_elos = [], []

    for _, row in df.iterrows():
        h, a = row["home_team"], row["away_team"]
        r_h = elo.get(h, ELO_DEFAULT)
        r_a = elo.get(a, ELO_DEFAULT)

        home_elos.append(r_h)
        away_elos.append(r_a)

        e_h = 1 / (1 + 10 ** ((r_a - r_h) / 400))
        s_h = 1.0 if row["ftr"] == "H" else (0.5 if row["ftr"] == "D" else 0.0)

        elo[h] = r_h + ELO_K * (s_h - e_h)
        elo[a] = r_a + ELO_K * ((1 - s_h) - (1 - e_h))

    df["home_elo"] = home_elos
    df["away_elo"] = away_elos
    df["elo_diff"] = df["home_elo"] - df["away_elo"]
    return df


def _compute_pi_ratings(
    df: pd.DataFrame,
    gamma: float = 0.036,
    lam: float = 0.5,
) -> pd.DataFrame:
    pi = {}

    h_hc, h_hd, a_ac, a_ad = [], [], [], []
    h_atk_diff, h_def_diff = [], []

    def get(team):
        return pi.get(team, {"hc": 0.0, "hd": 0.0, "ac": 0.0, "ad": 0.0})

    for _, row in df.iterrows():
        h = row["home_team"]
        a = row["away_team"]
        fthg = float(row.get("fthg") or 0)
        ftag = float(row.get("ftag") or 0)

        rh = get(h)
        ra = get(a)

        h_hc.append(rh["hc"])
        h_hd.append(rh["hd"])
        a_ac.append(ra["ac"])
        a_ad.append(ra["ad"])
        h_atk_diff.append(rh["hc"] - ra["ad"])
        h_def_diff.append(rh["hd"] - ra["ac"])

        exp_h = 10 ** (rh["hc"] - ra["ad"])
        exp_a = 10 ** (ra["ac"] - rh["hd"])

        pi[h] = {
            "hc": rh["hc"] + gamma * (fthg - exp_h),
            "hd": rh["hd"] + gamma * (exp_a - ftag),
            "ac": rh["ac"] + gamma * lam * (fthg - exp_h),
            "ad": rh["ad"] + gamma * lam * (exp_a - ftag),
        }
        pi[a] = {
            "ac": ra["ac"] + gamma * (ftag - exp_a),
            "ad": ra["ad"] + gamma * (exp_h - fthg),
            "hc": ra["hc"] + gamma * lam * (ftag - exp_a),
            "hd": ra["hd"] + gamma * lam * (exp_h - fthg),
        }

    df["h_pi_hc"] = h_hc
    df["h_pi_hd"] = h_hd
    df["a_pi_ac"] = a_ac
    df["a_pi_ad"] = a_ad
    df["pi_atk_diff"] = h_atk_diff
    df["pi_def_diff"] = h_def_diff
    df["pi_total_diff"] = [a - b for a, b in zip(h_atk_diff, h_def_diff)]
    return df


def _add_season_context(df: pd.DataFrame) -> pd.DataFrame:
    def derive_season(d: pd.Timestamp) -> str:
        yr = d.year
        return f"{str(yr)[2:]}/{str(yr + 1)[2:]}" if d.month >= 8 else f"{str(yr - 1)[2:]}/{str(yr)[2:]}"

    df["season_label"] = df["date"].apply(derive_season)
    df["home_matchweek"] = df.groupby(["season_label", "home_team"]).cumcount() + 1
    df["away_matchweek"] = df.groupby(["season_label", "away_team"]).cumcount() + 1
    df["matchweek"] = ((df["home_matchweek"] + df["away_matchweek"]) / 2).round()
    return df


def _compute_h2h(df: pd.DataFrame, window: int = 5) -> pd.Series:
    df = df.reset_index(drop=True)
    df["_pair"] = df.apply(
        lambda r: "__".join(sorted([r["home_team"], r["away_team"]])),
        axis=1,
    )

    h2h_rates = pd.Series(0.5, index=df.index)

    for _, grp in df.groupby("_pair"):
        idx = grp.index.tolist()
        for i, ix in enumerate(idx):
            past = grp.iloc[max(0, i - window): i]
            if past.empty:
                continue

            home = df.at[ix, "home_team"]
            wins = (
                ((past["home_team"] == home) & (past["ftr"] == "H")).sum()
                + ((past["away_team"] == home) & (past["ftr"] == "A")).sum()
            )
            h2h_rates[ix] = wins / len(past)

    df.drop(columns=["_pair"], inplace=True)
    return h2h_rates


def _add_xg_features(df: pd.DataFrame, xg: pd.DataFrame) -> pd.DataFrame:
    if xg.empty:
        logger.warning("xg_data empty — skipping xG features")
        return df

    merged = df.merge(
        xg[["date", "home_team", "away_team", "home_xg", "away_xg", "home_npxg", "away_npxg"]],
        on=["date", "home_team", "away_team"],
        how="left",
    )

    for w in [3, 5]:
        merged[f"h_xg_{w}"] = _rolling(merged, "home_team", "home_xg", w, f"h_xg_{w}")
        merged[f"a_xg_{w}"] = _rolling(merged, "away_team", "away_xg", w, f"a_xg_{w}")
        merged[f"h_npxg_{w}"] = _rolling(merged, "home_team", "home_npxg", w, f"h_npxg_{w}")
        merged[f"a_npxg_{w}"] = _rolling(merged, "away_team", "away_npxg", w, f"a_npxg_{w}")

    merged["xgd_match"] = merged["home_xg"] - merged["away_xg"]
    merged["h_xgd_5"] = _rolling(merged, "home_team", "xgd_match", 5, "h_xgd_5")

    for w in [3, 5]:
        merged[f"h_xg_{w}"] = merged[f"h_xg_{w}"].fillna(merged[f"h_goals_scored_{w}"])
        merged[f"a_xg_{w}"] = merged[f"a_xg_{w}"].fillna(merged[f"a_goals_scored_{w}"])
        merged[f"h_npxg_{w}"] = merged[f"h_npxg_{w}"].fillna(merged[f"h_goals_scored_{w}"])
        merged[f"a_npxg_{w}"] = merged[f"a_npxg_{w}"].fillna(merged[f"a_goals_scored_{w}"])

    merged["h_xgd_5"] = merged["h_xgd_5"].fillna(
        merged["h_goals_scored_5"] - merged["a_goals_scored_5"]
    )

    merged.drop(
        columns=["home_xg", "away_xg", "home_npxg", "away_npxg", "xgd_match"],
        errors="ignore",
        inplace=True,
    )
    return merged


def _add_parity_features(df: pd.DataFrame) -> pd.DataFrame:
    if "h_xg_5" in df.columns and "a_xg_5" in df.columns:
        df["xg_parity_5"] = (
            df["h_xg_5"].fillna(df["h_goals_scored_5"])
            - df["a_xg_5"].fillna(df["a_goals_scored_5"])
        ).abs()

    df["goals_parity_3"] = (df["h_goals_scored_3"] - df["a_goals_scored_3"]).abs()
    df["goals_parity_5"] = (df["h_goals_scored_5"] - df["a_goals_scored_5"]).abs()
    df["def_parity_5"] = df["h_goals_conceded_5"].fillna(0) + df["a_goals_conceded_5"].fillna(0)
    df["form_parity_5"] = (df["h_form_5"] - df["a_form_5"]).abs()

    if "pi_total_diff" in df.columns:
        df["pi_parity"] = df["pi_total_diff"].abs()

    return df


def _add_draw_features(df: pd.DataFrame) -> pd.DataFrame:
    df["_is_draw"] = (df["ftr"] == "D").astype(float)

    df["h_draw_rate_5"] = (
        df.groupby("home_team")["_is_draw"]
        .transform(lambda x: x.shift(1).rolling(5, min_periods=1).mean())
        .fillna(DRAW_RATE)
    )
    df["h_draw_rate_10"] = (
        df.groupby("home_team")["_is_draw"]
        .transform(lambda x: x.shift(1).rolling(10, min_periods=1).mean())
        .fillna(DRAW_RATE)
    )
    df["a_draw_rate_5"] = (
        df.groupby("away_team")["_is_draw"]
        .transform(lambda x: x.shift(1).rolling(5, min_periods=1).mean())
        .fillna(DRAW_RATE)
    )
    df["a_draw_rate_10"] = (
        df.groupby("away_team")["_is_draw"]
        .transform(lambda x: x.shift(1).rolling(10, min_periods=1).mean())
        .fillna(DRAW_RATE)
    )

    df["draw_propensity"] = (df["h_draw_rate_5"] + df["a_draw_rate_5"]) / 2
    df["elo_parity"] = 1 / (1 + df["elo_diff"].abs())

    df["_pair"] = df.apply(
        lambda r: "__".join(sorted([r["home_team"], r["away_team"]])),
        axis=1,
    )

    h2h_draw = pd.Series(DRAW_RATE, index=df.index)
    for _, grp in df.groupby("_pair"):
        idx = grp.index.tolist()
        for i, ix in enumerate(idx):
            past = grp.iloc[max(0, i - 5): i]
            if not past.empty:
                h2h_draw[ix] = (past["ftr"] == "D").mean()

    df["h2h_draw_rate"] = h2h_draw
    df.drop(columns=["_is_draw", "_pair"], inplace=True)
    return df


def _add_possession_features(df: pd.DataFrame, poss: pd.DataFrame) -> pd.DataFrame:
    if poss.empty:
        logger.warning("match_stats empty — skipping possession features")
        return df

    merged = df.merge(
        poss[["date", "home_team", "away_team", "home_possession", "away_possession"]],
        on=["date", "home_team", "away_team"],
        how="left",
    )

    for w in [3, 5]:
        merged[f"h_poss_{w}"] = _rolling(merged, "home_team", "home_possession", w, f"h_poss_{w}")
        merged[f"a_poss_{w}"] = _rolling(merged, "away_team", "away_possession", w, f"a_poss_{w}")

    merged.drop(columns=["home_possession", "away_possession"], errors="ignore", inplace=True)
    return merged


def _add_squad_features(df: pd.DataFrame, squad: pd.DataFrame) -> pd.DataFrame:
    if squad.empty:
        logger.warning("player_minutes empty — skipping squad features")
        return df

    df = df.merge(
        squad.rename(
            columns={
                "team": "home_team",
                "squad_avg_xg": "h_squad_xg",
                "squad_avg_xa": "h_squad_xa",
                "squad_avg_npxg": "h_squad_npxg",
                "squad_total_goals": "h_squad_goals",
                "squad_total_ast": "h_squad_ast",
                "squad_avg_min": "h_squad_min",
            }
        ),
        left_on=["season_label", "home_team"],
        right_on=["season", "home_team"],
        how="left",
    ).drop(columns=["season"], errors="ignore")

    df = df.merge(
        squad.rename(
            columns={
                "team": "away_team",
                "squad_avg_xg": "a_squad_xg",
                "squad_avg_xa": "a_squad_xa",
                "squad_avg_npxg": "a_squad_npxg",
                "squad_total_goals": "a_squad_goals",
                "squad_total_ast": "a_squad_ast",
                "squad_avg_min": "a_squad_min",
            }
        ),
        left_on=["season_label", "away_team"],
        right_on=["season", "away_team"],
        how="left",
    ).drop(columns=["season"], errors="ignore")

    squad_feature_cols = [
        "h_squad_xg", "h_squad_xa", "h_squad_npxg",
        "h_squad_goals", "h_squad_ast", "h_squad_min",
        "a_squad_xg", "a_squad_xa", "a_squad_npxg",
        "a_squad_goals", "a_squad_ast", "a_squad_min",
    ]

    for col in squad_feature_cols:
        if col not in df.columns:
            continue
        df[col] = df.groupby("season_label")[col].transform(lambda x: x.fillna(x.median()))
        df[col] = df[col].fillna(df[col].median())

    df["squad_xg_diff"] = df["h_squad_xg"].fillna(0) - df["a_squad_xg"].fillna(0)
    return df


def _add_home_advantage(df: pd.DataFrame) -> pd.DataFrame:
    df["_home_win"] = (df["ftr"] == "H").astype(float)
    df["_away_win"] = (df["ftr"] == "A").astype(float)

    df["home_win_rate_hist"] = (
        df.groupby("home_team")["_home_win"]
        .transform(lambda x: x.shift(1).expanding().mean())
        .fillna(HOME_WIN_RATE)
    )
    df["away_win_rate_hist"] = (
        df.groupby("away_team")["_away_win"]
        .transform(lambda x: x.shift(1).expanding().mean())
        .fillna(AWAY_WIN_RATE)
    )

    df.drop(columns=["_home_win", "_away_win"], inplace=True)
    return df


def _add_odds_features(df: pd.DataFrame) -> pd.DataFrame:
    logger.info(
        "  Odds debug — b365h in df: %s | b365d in df: %s | sample b365h: %s",
        "b365h" in df.columns,
        "b365d" in df.columns,
        df["b365h"].dropna().head(3).tolist() if "b365h" in df.columns else "N/A",
    )

    if "b365h" not in df.columns:
        return df

    df["b365h"] = pd.to_numeric(df["b365h"], errors="coerce")
    df["b365d"] = pd.to_numeric(df["b365d"], errors="coerce")
    df["b365a"] = pd.to_numeric(df["b365a"], errors="coerce")

    df["odds_impl_h"] = 1 / df["b365h"]
    df["odds_impl_d"] = 1 / df["b365d"]
    df["odds_impl_a"] = 1 / df["b365a"]

    total = df["odds_impl_h"] + df["odds_impl_d"] + df["odds_impl_a"]
    df["odds_fair_h"] = df["odds_impl_h"] / total
    df["odds_fair_d"] = df["odds_impl_d"] / total
    df["odds_fair_a"] = df["odds_impl_a"] / total
    df["odds_home_edge"] = df["odds_fair_h"] - df["odds_fair_a"]

    return df


def build_live_features(home: str, away: str, live_odds: dict) -> pd.DataFrame:
    """
    Build a single-row feature vector using all available Supabase tables.
    """
    sb = get_supabase()

    home = _normalise_team_name(home)
    away = _normalise_team_name(away)

    def fetch_recent(team: str, n: int = 10) -> pd.DataFrame:
        candidates = []
        canonical = normalise_team(team)
        if canonical:
            candidates.append(canonical)
        cleaned = canonical_team_or_self(team)
        if cleaned not in candidates:
            candidates.append(cleaned)

        all_rows = []
        seen = set()

        for candidate in candidates:
            rows = (
                sb.table("match_results")
                .select("*")
                .or_(f"home_team.eq.{candidate},away_team.eq.{candidate}")
                .order("date", desc=True)
                .limit(n)
                .execute()
                .data
            ) or []

            for row in rows:
                key = (
                    row.get("date"),
                    row.get("home_team"),
                    row.get("away_team"),
                    row.get("fthg"),
                    row.get("ftag"),
                )
                if key not in seen:
                    seen.add(key)
                    all_rows.append(row)

        df = pd.DataFrame(all_rows) if all_rows else pd.DataFrame()
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df = _normalise_teams(df, cols=["home_team", "away_team"]).sort_values("date", ascending=False)
        return df

    def compute_match_stats(team: str, prefix: str) -> dict:
        df = fetch_recent(team, 10)
        if df.empty:
            return {}

        stats = {}

        def goals_scored(row):
            return row["fthg"] if row["home_team"] == team else row["ftag"]

        def goals_conceded(row):
            return row["ftag"] if row["home_team"] == team else row["fthg"]

        def form_pts(row):
            r = row.get("ftr")
            if row["home_team"] == team:
                return 1 if r == "H" else (0.5 if r == "D" else 0)
            return 1 if r == "A" else (0.5 if r == "D" else 0)

        df["_scored"] = df.apply(goals_scored, axis=1).fillna(0)
        df["_conceded"] = df.apply(goals_conceded, axis=1).fillna(0)
        df["_form"] = df.apply(form_pts, axis=1)
        df["_draw"] = (df["ftr"] == "D").astype(int)

        for n in [3, 5, 10]:
            s = df.head(n)
            stats[f"{prefix}_goals_scored_{n}"] = round(s["_scored"].mean(), 3)
            stats[f"{prefix}_goals_conceded_{n}"] = round(s["_conceded"].mean(), 3)
            stats[f"{prefix}_form_{n}"] = round(s["_form"].mean(), 3)

        df5 = df.head(5)

        def side_col(home_col, away_col):
            return df5.apply(
                lambda r: r.get(home_col, 0) if r["home_team"] == team else r.get(away_col, 0),
                axis=1,
            ).fillna(0)

        stats[f"{prefix}_sot_5"] = round(side_col("hst", "ast").mean(), 3)
        stats[f"{prefix}_corners_5"] = round(side_col("hc", "ac").mean(), 3)
        stats[f"{prefix}_cards_5"] = round(side_col("hy", "ay").mean(), 3)
        stats[f"{prefix}_draw_rate_5"] = round(df.head(5)["_draw"].mean(), 3)
        stats[f"{prefix}_draw_rate_10"] = round(df["_draw"].mean(), 3)
        return stats

    def compute_xg_stats(team: str, prefix: str) -> dict:
        candidates = []
        canonical = normalise_team(team)
        if canonical:
            candidates.append(canonical)
        cleaned = canonical_team_or_self(team)
        if cleaned not in candidates:
            candidates.append(cleaned)

        all_rows = []
        seen = set()
        for candidate in candidates:
            rows = (
                sb.table("xg_data")
                .select("*")
                .or_(f"home_team.eq.{candidate},away_team.eq.{candidate}")
                .order("date", desc=True)
                .limit(5)
                .execute()
                .data
            ) or []

            for row in rows:
                key = (
                    row.get("date"),
                    row.get("home_team"),
                    row.get("away_team"),
                    row.get("home_xg"),
                    row.get("away_xg"),
                )
                if key not in seen:
                    seen.add(key)
                    all_rows.append(row)

        if not all_rows:
            return {}

        df = pd.DataFrame(all_rows)
        df["date"] = pd.to_datetime(df["date"])
        df = _normalise_teams(df, cols=["home_team", "away_team"]).sort_values("date", ascending=False)

        stats = {}

        def xg_for(row):
            return row["home_xg"] if row["home_team"] == team else row["away_xg"]

        def xg_against(row):
            return row["away_xg"] if row["home_team"] == team else row["home_xg"]

        def npxg_for(row):
            return row["home_npxg"] if row["home_team"] == team else row["away_npxg"]

        df["_xgf"] = df.apply(xg_for, axis=1).fillna(0)
        df["_xga"] = df.apply(xg_against, axis=1).fillna(0)
        df["_npxgf"] = df.apply(npxg_for, axis=1).fillna(0)

        for n in [3, 5]:
            s = df.head(n)
            stats[f"{prefix}_xg_{n}"] = round(s["_xgf"].mean(), 3)
            stats[f"{prefix}_xg_against_{n}"] = round(s["_xga"].mean(), 3)
            stats[f"{prefix}_npxg_{n}"] = round(s["_npxgf"].mean(), 3)

        return stats

    def compute_possession(team: str, prefix: str) -> dict:
        candidates = []
        canonical = normalise_team(team)
        if canonical:
            candidates.append(canonical)
        cleaned = canonical_team_or_self(team)
        if cleaned not in candidates:
            candidates.append(cleaned)

        all_rows = []
        seen = set()
        for candidate in candidates:
            rows = (
                sb.table("match_stats")
                .select("*")
                .or_(f"home_team.eq.{candidate},away_team.eq.{candidate}")
                .order("date", desc=True)
                .limit(5)
                .execute()
                .data
            ) or []

            for row in rows:
                key = (
                    row.get("date"),
                    row.get("home_team"),
                    row.get("away_team"),
                )
                if key not in seen:
                    seen.add(key)
                    all_rows.append(row)

        if not all_rows:
            return {}

        df = pd.DataFrame(all_rows)
        df["date"] = pd.to_datetime(df["date"])
        df = _normalise_teams(df, cols=["home_team", "away_team"]).sort_values("date", ascending=False)

        def poss_for(row):
            return row["home_possession"] if row["home_team"] == team else row["away_possession"]

        df["_poss"] = df.apply(poss_for, axis=1).fillna(50.0)
        return {f"{prefix}_poss_5": round(df["_poss"].mean(), 3)}

    home_elo = get_current_elo(home)
    away_elo = get_current_elo(away)
    elo_diff = round(home_elo - away_elo, 4)
    elo_parity = round(1 / (1 + abs(elo_diff)), 4)

    total = (1 / live_odds["b365h"]) + (1 / live_odds["b365d"]) + (1 / live_odds["b365a"])
    odds_fair_h = round((1 / live_odds["b365h"]) / total, 4)
    odds_fair_d = round((1 / live_odds["b365d"]) / total, 4)
    odds_fair_a = round((1 / live_odds["b365a"]) / total, 4)
    odds_home_edge = round(odds_fair_h - odds_fair_a, 4)

    h_match = compute_match_stats(home, "h")
    a_match = compute_match_stats(away, "a")
    h_xg = compute_xg_stats(home, "h")
    a_xg = compute_xg_stats(away, "a")
    h_poss = compute_possession(home, "h")
    a_poss = compute_possession(away, "a")

    row = {
        **h_match,
        **a_match,
        **h_xg,
        **a_xg,
        **h_poss,
        **a_poss,
        "home_elo": home_elo,
        "away_elo": away_elo,
        "elo_diff": elo_diff,
        "elo_parity": elo_parity,
        "draw_propensity": round(
            (h_match.get("h_draw_rate_5", DRAW_RATE) + a_match.get("a_draw_rate_5", DRAW_RATE)) / 2,
            4,
        ),
        "odds_fair_h": odds_fair_h,
        "odds_fair_d": odds_fair_d,
        "odds_fair_a": odds_fair_a,
        "odds_home_edge": odds_home_edge,
        "matchweek": 0,
        "is_derby": int(home in BIG_CLUBS and away in BIG_CLUBS),
        "home_days_rest": 7,
        "away_days_rest": 7,
        "home_cumpts": 0,
        "away_cumpts": 0,
        "home_win_rate_hist": HOME_WIN_RATE,
        "away_win_rate_hist": AWAY_WIN_RATE,
        "h2h_home_win_rate": 0.5,
        "h2h_draw_rate": DRAW_RATE,
        "h_pi_hc": 0.0,
        "h_pi_hd": 0.0,
        "a_pi_ac": 0.0,
        "a_pi_ad": 0.0,
        "pi_atk_diff": 0.0,
        "pi_def_diff": 0.0,
        "pi_total_diff": 0.0,
        "pi_parity": 0.0,
        "xg_parity_5": round(abs(h_xg.get("h_xg_5", 0) - a_xg.get("a_xg_5", 0)), 4),
        "goals_parity_3": round(abs(h_match.get("h_goals_scored_3", 0) - a_match.get("a_goals_scored_3", 0)), 4),
        "goals_parity_5": round(abs(h_match.get("h_goals_scored_5", 0) - a_match.get("a_goals_scored_5", 0)), 4),
        "def_parity_5": round(h_match.get("h_goals_conceded_5", 0) + a_match.get("a_goals_conceded_5", 0), 4),
        "form_parity_5": round(abs(h_match.get("h_form_5", 0) - a_match.get("a_form_5", 0)), 4),
        "squad_xg_diff": 0.0,
        "cumpts_diff": 0.0,
        "combined_goals_5": round(h_match.get("h_goals_scored_5", 0) + a_match.get("a_goals_scored_5", 0), 4),
        "sot_balance": round(abs(h_match.get("h_sot_5", 0) - a_match.get("a_sot_5", 0)), 4),
    }

    return pd.DataFrame([row])


def engineer_features(df: pd.DataFrame | None = None) -> pd.DataFrame:
    if df is None:
        logger.info("Loading all data sources from Supabase...")
        df = load_matches()
        xg = load_xg()
        poss = load_possession()
        squad = load_squad_strength()
    else:
        logger.info("df provided — loading secondary sources from Supabase...")
        df = _normalise_teams(df.copy(), cols=[c for c in ["home_team", "away_team"] if c in df.columns])
        try:
            xg = load_xg()
        except Exception as e:
            logger.warning("xg_data load failed: %s — xG features will be skipped", e)
            xg = pd.DataFrame()
        try:
            poss = load_possession()
        except Exception as e:
            logger.warning("match_stats load failed: %s — possession features will be skipped", e)
            poss = pd.DataFrame()
        try:
            squad = load_squad_strength()
        except Exception as e:
            logger.warning("player_minutes load failed: %s — squad features will be skipped", e)
            squad = pd.DataFrame()

    df = df.copy()
    logger.info("Base matches loaded: %d rows", len(df))

    df["home_pts"] = df["ftr"].map({"H": 3, "D": 1, "A": 0}).fillna(0)
    df["away_pts"] = df["ftr"].map({"A": 3, "D": 1, "H": 0}).fillna(0)

    for w in ROLLING_WINDOWS:
        df[f"h_goals_scored_{w}"] = _rolling(df, "home_team", "fthg", w, f"h_goals_scored_{w}")
        df[f"h_goals_conceded_{w}"] = _rolling(df, "home_team", "ftag", w, f"h_goals_conceded_{w}")
        df[f"a_goals_scored_{w}"] = _rolling(df, "away_team", "ftag", w, f"a_goals_scored_{w}")
        df[f"a_goals_conceded_{w}"] = _rolling(df, "away_team", "fthg", w, f"a_goals_conceded_{w}")
        df[f"h_form_{w}"] = _rolling(df, "home_team", "home_pts", w, f"h_form_{w}")
        df[f"a_form_{w}"] = _rolling(df, "away_team", "away_pts", w, f"a_form_{w}")

    for w in [5]:
        df[f"h_sot_{w}"] = _rolling(df, "home_team", "hst", w, f"h_sot_{w}")
        df[f"a_sot_{w}"] = _rolling(df, "away_team", "ast", w, f"a_sot_{w}")
        df[f"h_corners_{w}"] = _rolling(df, "home_team", "hc", w, f"h_corners_{w}")
        df[f"a_corners_{w}"] = _rolling(df, "away_team", "ac", w, f"a_corners_{w}")
        df[f"h_cards_{w}"] = _rolling(df, "home_team", "hy", w, f"h_cards_{w}")
        df[f"a_cards_{w}"] = _rolling(df, "away_team", "ay", w, f"a_cards_{w}")

    df = _compute_elo(df)
    df = _compute_pi_ratings(df)
    df = _add_season_context(df)
    df = _add_xg_features(df, xg)
    df = _add_parity_features(df)
    df = _add_draw_features(df)
    df = _add_possession_features(df, poss)
    df = _add_squad_features(df, squad)

    df = df.sort_values("date")

    df["home_days_rest"] = (
        df.groupby("home_team")["date"]
        .transform(lambda x: x.diff().dt.days.shift(1).fillna(7))
    )
    df["away_days_rest"] = (
        df.groupby("away_team")["date"]
        .transform(lambda x: x.diff().dt.days.shift(1).fillna(7))
    )

    df["home_cumpts"] = (
        df.groupby(["season_label", "home_team"])["home_pts"]
        .transform(lambda x: x.cumsum().shift(1).fillna(0))
    )
    df["away_cumpts"] = (
        df.groupby(["season_label", "away_team"])["away_pts"]
        .transform(lambda x: x.cumsum().shift(1).fillna(0))
    )

    df = _add_home_advantage(df)

    df["is_derby"] = (
        df["home_team"].isin(BIG_CLUBS) & df["away_team"].isin(BIG_CLUBS)
    ).astype(int)

    df["h2h_home_win_rate"] = _compute_h2h(df, window=5)
    df = _add_odds_features(df)

    df["cumpts_diff"] = (df["home_cumpts"] - df["away_cumpts"]).abs()
    df["sot_balance"] = (df["h_sot_5"] - df["a_sot_5"]).abs()
    df["combined_goals_5"] = df["h_goals_scored_5"].fillna(0) + df["a_goals_scored_5"].fillna(0)

    rolling_cols = [
        c for c in df.columns
        if any(k in c for k in ["goals_scored", "goals_conceded", "form", "sot", "corners", "cards", "xg", "npxg", "xgd", "poss"])
    ]
    for col in rolling_cols:
        if df[col].isna().any():
            df[col] = df[col].fillna(0)

    parity_cols = [
        "xg_parity_5", "goals_parity_3", "goals_parity_5",
        "form_parity_5", "def_parity_5", "pi_parity",
        "h_draw_rate_5", "a_draw_rate_5",
        "h_draw_rate_10", "a_draw_rate_10",
        "h2h_draw_rate", "draw_propensity", "elo_parity",
    ]
    for col in parity_cols:
        if col in df.columns:
            df[col] = df[col].fillna(DRAW_RATE if "draw" in col or "propensity" in col else 0)

    odds_fill = {
        "odds_fair_h": HOME_WIN_RATE,
        "odds_fair_d": DRAW_RATE,
        "odds_fair_a": AWAY_WIN_RATE,
        "odds_home_edge": HOME_EDGE,
    }
    for col, default in odds_fill.items():
        if col in df.columns:
            df[col] = df[col].fillna(default)

    df = df.dropna(subset=["ftr"])
    logger.info("Feature engineering complete: %d rows × %d columns", len(df), len(df.columns))
    return df


def build_and_save(output_path: str | None = None) -> pd.DataFrame:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out = Path(output_path) if output_path else PROCESSED_DIR / f"features_{LEAGUE_KEY}.parquet"
    df = engineer_features()
    df.to_parquet(out, index=False)
    logger.info("✅ Feature matrix saved → %s  (%d rows × %d cols)", out, len(df), len(df.columns))
    return df