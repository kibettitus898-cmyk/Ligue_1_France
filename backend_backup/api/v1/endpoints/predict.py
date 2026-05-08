import copy
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException

from backend.core.config import ACTIVE_CONFIG
from backend.ml.features.feature_columns import FEATURE_COLS, LABEL_MAP
from backend.schemas.prediction import PredictionRequest
from backend.services.cache_service import get_cached, set_cache
from backend.services.ev_service import find_value_bets, format_ev_report
from backend.services.feature_service import (
    AWAY_WIN_RATE,
    DRAW_RATE,
    HOME_EDGE,
    HOME_WIN_RATE,
    engineer_features,
    get_current_elo,
    load_matches,
)
from backend.services.odds_service import (
    extract_1x2_odds,
    get_upcoming_fixtures,
    normalise_name,
)
from backend.utils.team_utils import normalise_team


LEAGUE = ACTIVE_CONFIG["fdco_code"].lower()

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
MODELS_DIR = BASE_DIR / "models" / "saved" / LEAGUE
DATA_DIR = BASE_DIR / "data" / "processed"

logger = logging.getLogger(__name__)
router = APIRouter()

_model = _imputer = _feat_names = _feature_df = None

CLASS_TO_RESULT = {v: k for k, v in LABEL_MAP.items()}
OUTCOME_CODE_MAP = {"Home Win": "H", "Draw": "D", "Away Win": "A"}
BIG_CLUBS = {"Paris SG", "Marseille", "Lyon", "Monaco", "Lille", "Nice"}

HOME_SIDE_COLS = {
    "home_elo",
    "home_cumpts",
    "home_days_rest",
    "home_win_rate_hist",
}

AWAY_SIDE_COLS = {
    "away_elo",
    "away_cumpts",
    "away_days_rest",
    "away_win_rate_hist",
}

try:
    _model = joblib.load(MODELS_DIR / "ensemble.pkl")
    _imputer = joblib.load(MODELS_DIR / "imputer.pkl")
    _feat_names = joblib.load(MODELS_DIR / "feature_names.pkl")
    logger.info("✅ Models loaded successfully from %s", MODELS_DIR)
except FileNotFoundError as e:
    logger.error("❌ Model file missing: %s. Run: python backend/scripts/train_model.py", e)
except Exception as e:
    logger.error("❌ Unexpected error loading models: %s", e)


def _canonical_team_name(team: str) -> str:
    if not team:
        return ""
    odds_name = normalise_name(team) or team
    return normalise_team(odds_name) or odds_name


def _team_candidates(team: str) -> list[str]:
    candidates = []
    for value in [
        team,
        normalise_name(team) if team else None,
        normalise_team(team) if team else None,
        _canonical_team_name(team),
    ]:
        if value and value not in candidates:
            candidates.append(value)
    return candidates


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def _get_feature_frame() -> pd.DataFrame:
    global _feature_df

    if _feature_df is not None:
        return _feature_df

    parquet = DATA_DIR / f"features_{LEAGUE}.parquet"
    if parquet.exists():
        _feature_df = pd.read_parquet(parquet)
        logger.info("✅ Loaded feature parquet from %s", parquet)
    else:
        logger.info("Parquet not found — building features from Supabase...")
        df = load_matches()
        _feature_df = engineer_features(df)

    return _feature_df


def _latest_team_row(df: pd.DataFrame, team: str, side: str) -> pd.DataFrame:
    candidates = _team_candidates(team)
    primary_col = "home_team" if side == "home" else "away_team"

    primary = df[df[primary_col].isin(candidates)]
    if not primary.empty:
        return primary.tail(1).copy()

    logger.warning("'%s' not found as %s team — using league fallback row", team, side)
    row = df.tail(1).copy()
    row[primary_col] = _canonical_team_name(team)
    return row


def _pair_history(df: pd.DataFrame, home_team: str, away_team: str) -> tuple[float, float]:
    home_candidates = _team_candidates(home_team)
    away_candidates = _team_candidates(away_team)

    pair_df = df[
        (
            df["home_team"].isin(home_candidates)
            & df["away_team"].isin(away_candidates)
        )
        | (
            df["home_team"].isin(away_candidates)
            & df["away_team"].isin(home_candidates)
        )
    ].sort_values("date")

    if pair_df.empty:
        return 0.5, DRAW_RATE

    recent = pair_df.tail(5)
    home_wins = (
        (
            recent["home_team"].isin(home_candidates)
            & (recent["ftr"] == "H")
        )
        | (
            recent["away_team"].isin(home_candidates)
            & (recent["ftr"] == "A")
        )
    ).mean()
    draw_rate = (recent["ftr"] == "D").mean()

    return round(float(home_wins), 4), round(float(draw_rate), 4)


def _map_probabilities(proba: np.ndarray) -> dict:
    probs = {"H": 0.0, "D": 0.0, "A": 0.0}
    classes = getattr(_model, "classes_", None)

    if classes is None or len(classes) != len(proba):
        for label, p in zip(["H", "D", "A"], proba):
            probs[label] = round(float(p), 4)
        return probs

    for cls, p in zip(classes, proba):
        key = None

        if cls in probs:
            key = cls
        elif cls in CLASS_TO_RESULT:
            key = CLASS_TO_RESULT[cls]
        else:
            try:
                key = CLASS_TO_RESULT[int(cls)]
            except Exception:
                key = None

        if key in probs:
            probs[key] = round(float(p), 4)

    if sum(probs.values()) == 0:
        for label, p in zip(["H", "D", "A"], proba):
            probs[label] = round(float(p), 4)

    return probs


def _normalise_ev_payload(ev_result: dict | None) -> dict | None:
    if not ev_result:
        return None

    ev = copy.deepcopy(ev_result)

    for section in ("all_outcomes", "value_bets"):
        for item in ev.get(section, []):
            if "kelly_%" in item and "kelly_pct" not in item:
                item["kelly_pct"] = item["kelly_%"]
            if "outcome" in item and "outcome_code" not in item:
                item["outcome_code"] = OUTCOME_CODE_MAP.get(item["outcome"], item["outcome"])

    best_bet = ev.get("best_bet")
    if best_bet:
        if "kelly_%" in best_bet and "kelly_pct" not in best_bet:
            best_bet["kelly_pct"] = best_bet["kelly_%"]
        if "outcome" in best_bet and "outcome_code" not in best_bet:
            best_bet["outcome_code"] = OUTCOME_CODE_MAP.get(best_bet["outcome"], best_bet["outcome"])

    return ev


def _assemble_feature_row(
    df: pd.DataFrame,
    home_team: str,
    away_team: str,
    home_odd: float | None = None,
    draw_odd: float | None = None,
    away_odd: float | None = None,
) -> dict:
    home_norm = _canonical_team_name(home_team)
    away_norm = _canonical_team_name(away_team)

    home_row = _latest_team_row(df, home_norm, side="home")
    away_row = _latest_team_row(df, away_norm, side="away")

    home_vals = home_row.iloc[0]
    away_vals = away_row.iloc[0]

    home_elo = get_current_elo(home_norm)
    away_elo = get_current_elo(away_norm)

    feat_cols = _feat_names if _feat_names else FEATURE_COLS
    row = {}

    for col in feat_cols:
        if col.startswith("h_") or col in HOME_SIDE_COLS:
            row[col] = home_vals.get(col, np.nan)
        elif col.startswith("a_") or col in AWAY_SIDE_COLS:
            row[col] = away_vals.get(col, np.nan)
        else:
            row[col] = home_vals.get(col, np.nan)

    row["home_elo"] = home_elo
    row["away_elo"] = away_elo

    row["elo_diff"] = round(home_elo - away_elo, 4)
    row["elo_parity"] = round(1 / (1 + abs(row["elo_diff"])), 4)

    row["pi_atk_diff"] = round(
        _safe_float(row.get("h_pi_hc")) - _safe_float(row.get("a_pi_ad")),
        4,
    )
    row["pi_def_diff"] = round(
        _safe_float(row.get("h_pi_hd")) - _safe_float(row.get("a_pi_ac")),
        4,
    )
    row["pi_total_diff"] = round(row["pi_atk_diff"] - row["pi_def_diff"], 4)
    row["pi_parity"] = round(abs(row["pi_total_diff"]), 4)

    row["xg_parity_5"] = round(
        abs(_safe_float(row.get("h_xg_5")) - _safe_float(row.get("a_xg_5"))),
        4,
    )
    row["goals_parity_3"] = round(
        abs(_safe_float(row.get("h_goals_scored_3")) - _safe_float(row.get("a_goals_scored_3"))),
        4,
    )
    row["goals_parity_5"] = round(
        abs(_safe_float(row.get("h_goals_scored_5")) - _safe_float(row.get("a_goals_scored_5"))),
        4,
    )
    row["def_parity_5"] = round(
        _safe_float(row.get("h_goals_conceded_5")) + _safe_float(row.get("a_goals_conceded_5")),
        4,
    )
    row["form_parity_5"] = round(
        abs(_safe_float(row.get("h_form_5")) - _safe_float(row.get("a_form_5"))),
        4,
    )
    row["draw_propensity"] = round(
        (
            _safe_float(row.get("h_draw_rate_5"), DRAW_RATE)
            + _safe_float(row.get("a_draw_rate_5"), DRAW_RATE)
        ) / 2,
        4,
    )
    row["squad_xg_diff"] = round(
        _safe_float(row.get("h_squad_xg")) - _safe_float(row.get("a_squad_xg")),
        4,
    )
    row["cumpts_diff"] = round(
        abs(_safe_float(row.get("home_cumpts")) - _safe_float(row.get("away_cumpts"))),
        4,
    )
    row["combined_goals_5"] = round(
        _safe_float(row.get("h_goals_scored_5")) + _safe_float(row.get("a_goals_scored_5")),
        4,
    )
    row["sot_balance"] = round(
        abs(_safe_float(row.get("h_sot_5")) - _safe_float(row.get("a_sot_5"))),
        4,
    )

    h2h_home_win_rate, h2h_draw_rate = _pair_history(df, home_norm, away_norm)
    row["h2h_home_win_rate"] = h2h_home_win_rate
    row["h2h_draw_rate"] = h2h_draw_rate
    row["is_derby"] = int(home_norm in BIG_CLUBS and away_norm in BIG_CLUBS)

    if home_odd and draw_odd and away_odd:
        total = (1 / home_odd) + (1 / draw_odd) + (1 / away_odd)
        row["odds_fair_h"] = round((1 / home_odd) / total, 4)
        row["odds_fair_d"] = round((1 / draw_odd) / total, 4)
        row["odds_fair_a"] = round((1 / away_odd) / total, 4)
    else:
        row["odds_fair_h"] = _safe_float(row.get("odds_fair_h"), HOME_WIN_RATE)
        row["odds_fair_d"] = _safe_float(row.get("odds_fair_d"), DRAW_RATE)
        row["odds_fair_a"] = _safe_float(row.get("odds_fair_a"), AWAY_WIN_RATE)

    row["odds_home_edge"] = round(row["odds_fair_h"] - row["odds_fair_a"], 4)

    if "matchweek" in feat_cols:
        home_mw = _safe_float(home_vals.get("matchweek"), np.nan)
        away_mw = _safe_float(away_vals.get("matchweek"), np.nan)
        if np.isnan(home_mw) and np.isnan(away_mw):
            row["matchweek"] = 0
        elif np.isnan(home_mw):
            row["matchweek"] = away_mw
        elif np.isnan(away_mw):
            row["matchweek"] = home_mw
        else:
            row["matchweek"] = round((home_mw + away_mw) / 2, 2)

    row["home_days_rest"] = _safe_float(row.get("home_days_rest"), 7.0)
    row["away_days_rest"] = _safe_float(row.get("away_days_rest"), 7.0)
    row["home_win_rate_hist"] = _safe_float(row.get("home_win_rate_hist"), HOME_WIN_RATE)
    row["away_win_rate_hist"] = _safe_float(row.get("away_win_rate_hist"), AWAY_WIN_RATE)

    return row


def _run_prediction(
    home_team: str,
    away_team: str,
    home_odd: float = None,
    draw_odd: float = None,
    away_odd: float = None,
) -> dict:
    if _model is None or _imputer is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Run: python backend/scripts/train_model.py",
        )

    df = _get_feature_frame()
    feat_cols = _feat_names if _feat_names else FEATURE_COLS

    row = _assemble_feature_row(
        df=df,
        home_team=home_team,
        away_team=away_team,
        home_odd=home_odd,
        draw_odd=draw_odd,
        away_odd=away_odd,
    )

    X = pd.DataFrame([row])
    for col in feat_cols:
        if col not in X.columns:
            X[col] = np.nan
    X = X[feat_cols]

    X_imp = pd.DataFrame(_imputer.transform(X), columns=feat_cols)

    proba_raw = _model.predict_proba(X_imp)[0]
    probs = _map_probabilities(proba_raw)

    predicted = max(probs, key=probs.get)
    confidence = round(probs[predicted] * 100, 2)

    ev_result = None
    if home_odd and draw_odd and away_odd:
        ev_result = find_value_bets(
            model_probs=probs,
            home_odd=home_odd,
            draw_odd=draw_odd,
            away_odd=away_odd,
        )
        ev_result = _normalise_ev_payload(ev_result)

    return {
        "probabilities": probs,
        "predicted": predicted,
        "label": {"H": "Home Win", "D": "Draw", "A": "Away Win"}[predicted],
        "confidence": confidence,
        "ev_analysis": ev_result,
    }


@router.post("/predict")
def predict(req: PredictionRequest):
    try:
        result = _run_prediction(
            home_team=req.home_team,
            away_team=req.away_team,
            home_odd=req.home_odd,
            draw_odd=req.draw_odd,
            away_odd=req.away_odd,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if req.home_odd and req.draw_odd and req.away_odd and result["ev_analysis"]:
        logger.info(format_ev_report(result["ev_analysis"], req.home_team, req.away_team))

    return {
        "home_team": _canonical_team_name(req.home_team),
        "away_team": _canonical_team_name(req.away_team),
        **result,
    }


@router.get("/predict/upcoming")
def predict_upcoming(limit: int = 20):
    if _model is None or _imputer is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Run: python backend/scripts/train_model.py",
        )

    cached = get_cached(LEAGUE)
    if cached is not None:
        logger.info("⚡ Serving %d fixtures from cache", len(cached))
        return {"source": "cache", "fixtures": cached[:limit]}

    logger.info("📡 Cache miss — fetching from OddsPapi...")

    try:
        fixtures = get_upcoming_fixtures()
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch fixtures from OddsPapi: {e}",
        )

    logger.info("Fetched %d raw fixtures from OddsPapi", len(fixtures))

    results = []

    for fix in fixtures[:limit]:
        fixture_id = fix.get("id") or fix.get("fixtureId")
        if not fixture_id:
            logger.warning("Fixture missing ID, skipping: %s", fix)
            continue

        home_raw = fix.get("participant1Name", "")
        away_raw = fix.get("participant2Name", "")
        home_team = _canonical_team_name(home_raw)
        away_team = _canonical_team_name(away_raw)
        date = fix.get("startTime") or fix.get("startDate") or fix.get("date", "")

        if not home_team or not away_team:
            logger.warning(
                "Skipping fixture %s: missing team names (home='%s', away='%s')",
                fixture_id,
                home_team,
                away_team,
            )
            continue

        odds = extract_1x2_odds(fix, bookmaker="pinnacle")
        if not odds:
            logger.warning(
                "No odds for %s vs %s (fixture %s) — skipping",
                home_team,
                away_team,
                fixture_id,
            )
            continue

        try:
            result = _run_prediction(
                home_team=home_team,
                away_team=away_team,
                home_odd=odds["b365h"],
                draw_odd=odds["b365d"],
                away_odd=odds["b365a"],
            )

            results.append(
                {
                    "fixture_id": fixture_id,
                    "date": date,
                    "home_team": home_team,
                    "away_team": away_team,
                    "b365": {
                        "h": odds["b365h"],
                        "d": odds["b365d"],
                        "a": odds["b365a"],
                    },
                    "probabilities": result["probabilities"],
                    "predicted": result["predicted"],
                    "label": result["label"],
                    "confidence": result["confidence"],
                    "ev_analysis": result["ev_analysis"],
                }
            )
        except ValueError as e:
            logger.warning("Skipping %s vs %s: %s", home_team, away_team, e)
            continue
        except Exception as e:
            logger.error("Unexpected error for %s vs %s: %s", home_team, away_team, e)
            continue

    if results:
        set_cache(LEAGUE, results)
        logger.info("💾 Cached %d fixtures", len(results))

    return {"source": "live", "fixtures": results}