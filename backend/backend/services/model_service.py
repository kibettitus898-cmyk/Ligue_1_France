import joblib
import numpy as np
import pandas as pd
from pathlib import Path

from backend.core.config import ACTIVE_CONFIG

LEAGUE_CODE = ACTIVE_CONFIG["fdco_code"].lower()  # e.g. "f1"

# Resolve path relative to THIS file: backend/services/ → backend/
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "models" / "saved" / LEAGUE_CODE


def load_model():
    """Load the main ensemble model."""
    path = MODEL_DIR / "ensemble.pkl"
    if not path.exists():
        raise FileNotFoundError(
            f"Model not found at {path}. Run: python backend/scripts/train_model.py"
        )
    return joblib.load(path)


def load_imputer():
    """Load the feature imputer."""
    path = MODEL_DIR / "imputer.pkl"
    if not path.exists():
        raise FileNotFoundError(
            f"Imputer not found at {path}. Run: python backend/scripts/train_model.py"
        )
    return joblib.load(path)


def load_feature_names() -> list:
    """Load expected feature names in correct order."""
    path = MODEL_DIR / "feature_names.pkl"
    if not path.exists():
        raise FileNotFoundError(
            f"Feature names not found at {path}. Run: python backend/scripts/train_model.py"
        )
    return joblib.load(path)


def predict_proba(model, features: pd.DataFrame) -> list[float]:
    imputer       = load_imputer()
    feature_names = load_feature_names()
    features      = features.reindex(columns=feature_names)
    
    # ✅ Keep as DataFrame with column names — fixes sklearn warning
    features_imputed = pd.DataFrame(
        imputer.transform(features),
        columns=feature_names
    )
    probs = model.predict_proba(features_imputed)[0]
    return probs.tolist()