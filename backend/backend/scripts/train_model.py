"""
Trains a Ligue 1 match outcome classifier using the full feature matrix.

Pipeline:
  1. Load features_f1.parquet
  2. Encode target H/D/A → 0/1/2
  3. TimeSeriesSplit cross-validation
  4. Train CatBoost + Random Forest + XGBoost ensemble
  5. Evaluate on held-out final season
  6. Save models → backend/models/saved/<league>/
  7. Save evaluation report → backend/models/saved/<league>/eval_report.json
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import pandas as pd

from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import (
    accuracy_score,
    log_loss,
    classification_report,
    confusion_matrix,
)

from catboost import CatBoostClassifier

from backend.ml.features.feature_columns import FEATURE_COLS, TARGET_COL, LABEL_MAP, N_TEAMS
from backend.ml.utils import impute
from backend.ml.models.xgb_model import build_xgb
from backend.ml.stacking import train_stacking_ensemble
from backend.core.config import ACTIVE_CONFIG


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────────────────────

LEAGUE_KEY = ACTIVE_CONFIG["fdco_code"].lower()
BACKEND_ROOT = PROJECT_ROOT / "backend"
DATA_DIR = BACKEND_ROOT / "data" / "processed"
MODELS_DIR = BACKEND_ROOT / "models" / "saved" / LEAGUE_KEY
FEATURES_PATH = DATA_DIR / f"features_{LEAGUE_KEY}.parquet"

MODELS_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def first_existing_column(df: pd.DataFrame, *names: str) -> str | None:
    for name in names:
        if name in df.columns:
            return name
    return None


def warn_high_nan(nan_by_col: pd.Series, n_rows: int, threshold: float = 0.30):
    if n_rows == 0:
        return

    groups = {
        "xG": [c for c in nan_by_col.index if "xg" in c.lower() or "npxg" in c.lower()],
        "Elo": [c for c in nan_by_col.index if "elo" in c.lower()],
        "H2H": [c for c in nan_by_col.index if "h2h" in c.lower()],
        "Squad": [c for c in nan_by_col.index if "squad" in c.lower()],
        "Rolling": [c for c in nan_by_col.index if "rolling" in c.lower() or "form" in c.lower()],
    }

    for group, cols in groups.items():
        if not cols:
            continue
        worst_count = nan_by_col[cols].max()
        worst_rate = worst_count / n_rows
        if worst_rate > threshold:
            logger.warning(
                f"⚠️ High NaN rate in [{group}] features "
                f"(worst: {worst_rate * 100:.0f}%) — check feature engineering defaults"
            )


def evaluate(name: str, model, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)
    y_proba = y_proba / y_proba.sum(axis=1, keepdims=True)

    acc = round(accuracy_score(y_test, y_pred), 4)
    ll = round(log_loss(y_test, y_proba), 4)
    cr = classification_report(
        y_test,
        y_pred,
        target_names=["Home Win", "Draw", "Away Win"],
        output_dict=True,
    )

    logger.info(f"\n{'=' * 50}")
    logger.info(f"  {name}")
    logger.info(f"  Accuracy : {acc:.4f}")
    logger.info(f"  Log Loss : {ll:.4f}")
    logger.info(
        "\n" + classification_report(
            y_test,
            y_pred,
            target_names=["Home Win", "Draw", "Away Win"],
        )
    )

    cm = confusion_matrix(y_test, y_pred)
    logger.info(f"Confusion Matrix:\n{cm}")

    return {
        "model": name,
        "accuracy": acc,
        "log_loss": ll,
        "classification": cr,
        "confusion_matrix": cm.tolist(),
    }


def cross_validate(model, X: pd.DataFrame, y: pd.Series, name: str, n_splits: int = 5, n_jobs: int = -1) -> float:
    tscv = TimeSeriesSplit(n_splits=n_splits)
    scores = cross_val_score(model, X, y, cv=tscv, scoring="accuracy", n_jobs=n_jobs)
    logger.info(
        f"{name} CV accuracy: {scores.mean():.4f} ± {scores.std():.4f} "
        f"| folds: {[round(s, 4) for s in scores]}"
    )
    return float(scores.mean())


def log_feature_importance(model, feature_names: list[str], top_n: int = 20):
    if hasattr(model, "feature_importances_"):
        imp = pd.Series(model.feature_importances_, index=feature_names)
    elif hasattr(model, "get_feature_importance"):
        imp = pd.Series(model.get_feature_importance(), index=feature_names)
    else:
        return

    top = imp.nlargest(top_n)
    logger.info(f"\nTop {top_n} features:\n{top.to_string()}")
    imp.sort_values(ascending=False).to_csv(
        MODELS_DIR / "feature_importance.csv",
        header=["importance"],
    )


# ─────────────────────────────────────────────────────────────────────────────
# LOAD & PREPARE
# ─────────────────────────────────────────────────────────────────────────────

def load_data() -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    logger.info(f"PROJECT_ROOT   : {PROJECT_ROOT}")
    logger.info(f"BACKEND_ROOT   : {BACKEND_ROOT}")
    logger.info(f"FEATURES_PATH  : {FEATURES_PATH}")
    logger.info(f"MODELS_DIR     : {MODELS_DIR}")

    if not FEATURES_PATH.exists():
        raise FileNotFoundError(
            f"Feature matrix not found at {FEATURES_PATH}. "
            f"Build it first with the feature pipeline."
        )

    df = pd.read_parquet(FEATURES_PATH)
    logger.info(f"Loaded feature matrix: {len(df)} rows × {len(df.columns)} columns")
    logger.info(
        f"League: {ACTIVE_CONFIG['name']} | Teams: {N_TEAMS} | "
        f"Matchweeks/season: {(N_TEAMS - 1) * 2}"
    )

    date_col = first_existing_column(df, "date", "match_date")
    if date_col:
        df = df.sort_values(date_col).reset_index(drop=True)
        logger.info(f"Sorted by {date_col} ✅")
    else:
        logger.warning("⚠️ No date column found — order not guaranteed")

    available = [c for c in FEATURE_COLS if c in df.columns]
    missing = [c for c in FEATURE_COLS if c not in df.columns]
    if missing:
        logger.warning(f"Missing {len(missing)} declared features (skipped): {missing}")

    if not available:
        raise ValueError("No declared feature columns found in the feature matrix.")

    if TARGET_COL not in df.columns:
        raise KeyError(f"Target column '{TARGET_COL}' not found in feature matrix.")

    X = df[available].copy()
    y = df[TARGET_COL].map(LABEL_MAP)

    valid = y.notna()
    n_dropped_target = int((~valid).sum())
    if n_dropped_target:
        logger.warning(f"Dropped {n_dropped_target} rows with missing target (unmapped result)")

    X = X[valid].copy()
    y = y[valid].astype(int)
    df_full = df.loc[valid].reset_index(drop=True)
    X = X.reset_index(drop=True)
    y = y.reset_index(drop=True)

    nan_by_col = X.isna().sum().sort_values(ascending=False)
    nan_cols = nan_by_col[nan_by_col > 0]

    if nan_cols.empty:
        logger.info("No NaN values in feature matrix ✅")
    else:
        logger.info(f"NaN audit — {len(nan_cols)} columns have missing values:")
        for col, count in nan_cols.head(20).items():
            pct = count / len(X) * 100
            logger.info(f"   {col:<45} {count:>5} NaNs  ({pct:.1f}%)")
        if len(nan_cols) > 20:
            logger.info(f"   ... and {len(nan_cols) - 20} more columns")

    rows_with_nan = int(X.isna().any(axis=1).sum())
    logger.info(
        f"Rows with ≥1 NaN feature: {rows_with_nan} "
        f"({rows_with_nan / len(X) * 100:.1f}%) → will be imputed, NOT dropped"
    )

    odds_cols = ["odds_fair_h", "odds_fair_d", "odds_fair_a", "odds_home_edge"]
    for col in odds_cols:
        if col in df.columns:
            coverage = df[col].notna().mean()
            logger.info(f"  {col}: {coverage * 100:.1f}% coverage")
        else:
            logger.warning(f"  {col}: MISSING from feature matrix")

    warn_high_nan(nan_by_col, n_rows=len(X), threshold=0.30)

    dist = y.value_counts().rename({0: "H", 1: "D", 2: "A"}).sort_index()
    logger.info(f"Target distribution:\n{dist.to_string()}")
    logger.info(f"Final usable rows: {len(X)}")

    return X, y, df_full


# ─────────────────────────────────────────────────────────────────────────────
# MODELS
# ─────────────────────────────────────────────────────────────────────────────

def build_rf() -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=500,
        max_depth=12,
        min_samples_split=20,
        min_samples_leaf=10,
        max_features="sqrt",
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )


def build_catboost() -> CatBoostClassifier:
    return CatBoostClassifier(
        iterations=600,
        learning_rate=0.05,
        depth=5,
        loss_function="MultiClass",
        eval_metric="Accuracy",
        class_weights=[1.0, 1.3, 1.0],
        random_seed=42,
        verbose=0,
    )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN TRAINING PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

def train():
    logger.info("=" * 60)
    logger.info(f"  {ACTIVE_CONFIG['name'].upper()} MATCH OUTCOME TRAINER")
    logger.info("=" * 60)

    X, y, df_full = load_data()

    season_col = first_existing_column(df_full, "season_label", "seasonlabel")
    holdout_min = (N_TEAMS - 1) * N_TEAMS

    if season_col and "24/25" in set(df_full[season_col].astype(str).unique()):
        holdout_mask = df_full[season_col].astype(str) == "24/25"
        if holdout_mask.sum() < 100:
            logger.warning(f"24/25 holdout has <100 rows — using last {holdout_min} rows instead")
            holdout_mask = pd.Series(False, index=df_full.index)
            holdout_mask.iloc[-holdout_min:] = True
    else:
        logger.warning("season_label column missing or 24/25 not found — using last full season rows")
        holdout_mask = pd.Series(False, index=df_full.index)
        holdout_mask.iloc[-holdout_min:] = True

    X_train, X_test = X[~holdout_mask], X[holdout_mask]
    y_train, y_test = y[~holdout_mask], y[holdout_mask]

    logger.info(f"Train: {len(X_train)} rows | Holdout: {len(X_test)} rows")

    X_train_imp, X_test_imp, imputer = impute(X_train, X_test)

    rf = build_rf()
    cb = build_catboost()
    xgb = build_xgb()

    logger.info(
        "Class distribution (no SMOTE): "
        f"{pd.Series(y_train).value_counts().rename({0: 'H', 1: 'D', 2: 'A'}).to_dict()}"
    )

    logger.info("\nRunning TimeSeriesSplit cross-validation (5 folds)...")
    rf_cv = cross_validate(rf, X_train_imp, y_train, "RandomForest")
    cb_cv = cross_validate(cb, X_train_imp, y_train, "CatBoost")
    xgb_cv = cross_validate(xgb, X_train_imp, y_train, "XGBoost")

    logger.info("\nFitting final models on full training set...")
    rf.fit(X_train_imp, y_train)
    xgb.fit(X_train_imp, y_train)
    cb.fit(X_train_imp, y_train)

    ensemble = VotingClassifier(
        estimators=[("rf", rf), ("xgb", xgb), ("cb", cb)],
        voting="soft",
        weights=[0.50, 0.30, 0.20],
    )
    ensemble.fit(X_train_imp, y_train)

    logger.info("\n" + "=" * 60)
    logger.info("  HOLDOUT EVALUATION")
    logger.info("=" * 60)

    results = []
    for name, model in [
        ("RandomForest", rf),
        ("XGBoost", xgb),
        ("CatBoost", cb),
        ("Ensemble", ensemble),
    ]:
        res = evaluate(name, model, X_test_imp, y_test)
        res["cv_accuracy"] = (
            rf_cv if name == "RandomForest"
            else xgb_cv if name == "XGBoost"
            else cb_cv if name == "CatBoost"
            else None
        )
        results.append(res)

    logger.info("\nBuilding OOF Stacking Ensemble...")
    base_models = {
        "RF": build_rf(),
        "XGB": build_xgb(),
        "CB": build_catboost(),
    }
    stack_result = train_stacking_ensemble(
        base_models=base_models,
        X_train=X_train_imp,
        y_train=y_train,
        X_test=X_test_imp,
        y_test=y_test,
        n_splits=7,
    )

    logger.info("\nSaving models...")
    joblib.dump(rf, MODELS_DIR / "random_forest.pkl")
    joblib.dump(xgb, MODELS_DIR / "xgboost.pkl")
    joblib.dump(cb, MODELS_DIR / "catboost.pkl")
    joblib.dump(ensemble, MODELS_DIR / "ensemble.pkl")
    joblib.dump(stack_result["meta_model"], MODELS_DIR / "stacking_meta.pkl")
    joblib.dump(stack_result["base_models"], MODELS_DIR / "stacking_base_models.pkl")
    joblib.dump(imputer, MODELS_DIR / "imputer.pkl")
    joblib.dump(list(X_train_imp.columns), MODELS_DIR / "feature_names.pkl")

    logger.info(f"✅ Models saved → {MODELS_DIR}")

    log_feature_importance(rf, list(X_train_imp.columns))

    report = {
        "trained_at": datetime.now().isoformat(),
        "league": ACTIVE_CONFIG["name"],
        "league_code": LEAGUE_KEY,
        "train_rows": len(X_train),
        "holdout_rows": len(X_test),
        "features_used": len(X_train_imp.columns),
        "models": [{k: v for k, v in r.items() if k != "confusion_matrix"} for r in results],
    }

    with open(MODELS_DIR / "eval_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)

    logger.info(f"✅ Eval report saved → {MODELS_DIR / 'eval_report.json'}")

    home_team_col = first_existing_column(df_full, "home_team", "hometeam")
    away_team_col = first_existing_column(df_full, "away_team", "awayteam")
    home_elo_col = first_existing_column(df_full, "home_elo", "homeelo")
    away_elo_col = first_existing_column(df_full, "away_elo", "awayelo")

    final_elo = {}
    if home_team_col and away_team_col and home_elo_col and away_elo_col:
        teams = pd.unique(pd.concat([df_full[home_team_col], df_full[away_team_col]], ignore_index=True))
        for team in teams:
            home_mask = df_full[home_team_col] == team
            away_mask = df_full[away_team_col] == team
            if home_mask.any():
                final_elo[team] = float(df_full.loc[home_mask, home_elo_col].iloc[-1])
            elif away_mask.any():
                final_elo[team] = float(df_full.loc[away_mask, away_elo_col].iloc[-1])

        elo_path = MODELS_DIR / "elo_ratings.json"
        with open(elo_path, "w") as f:
            json.dump(final_elo, f, indent=2)
        logger.info(f"✅ ELO ratings saved → {elo_path} ({len(final_elo)} teams)")
    else:
        logger.warning("⚠️ ELO/team columns not found — elo_ratings.json not saved")

    stack_entry = {
        "model": "StackingEnsemble",
        "accuracy": float(stack_result.get("test_accuracy", stack_result.get("accuracy", 0.0))),
        "log_loss": float(stack_result.get("log_loss", stack_result.get("test_log_loss", 0.0))),
    }

    all_results = results + [stack_entry]
    best = max(all_results, key=lambda r: r["accuracy"])

    logger.info("\n" + "=" * 60)
    logger.info(f"  BEST MODEL   : {best['model']}")
    logger.info(f"  ACCURACY     : {best['accuracy']:.4f} ({best['accuracy'] * 100:.1f}%)")
    logger.info(f"  LOG LOSS     : {best['log_loss']:.4f}")
    logger.info("=" * 60)

    target_met = best["accuracy"] >= 0.62
    logger.info(f"  62% TARGET   : {'✅ MET' if target_met else '❌ NOT YET'}")

    return float(best["accuracy"])


if __name__ == "__main__":
    acc = train()
    sys.exit(0 if acc >= 0.60 else 1)