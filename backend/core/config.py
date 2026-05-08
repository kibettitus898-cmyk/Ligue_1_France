from pydantic_settings import BaseSettings
from pathlib import Path

# Resolve .env relative to this file: backend/core/ → project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"   # backend/.env

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_KEY: str
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    ODDSPAPI_KEY: str = ""
    ODDSPAPI_BASE_URL: str = "https://api.oddspapi.io/v4"
    ODDSPAPI_VERSION: str = "v4"
    ACTIVE_LEAGUE: str = "ligue1"

    class Config:
        env_file = str(ENV_FILE)
        case_sensitive = True
        extra = "forbid"


settings = Settings()


# ── League registry ────────────────────────────────────────────────────────────
LEAGUE_CONFIG = {
    "ligue1": {
        "name":           "Ligue 1",
        "fdco_code":      "F1",
        "tournament_id":  34,              # ✅ FIXED: confirmed from your curl result
        "supabase_table": "match_results",
        "models_dir":     "models/saved/f1",
        "season_format":  "aug_may",
        "teams_count":    18,
        "understat_slug": "ligue_1",
    },
    # Bonus: other French leagues now available if you ever need them
    "ligue2": {
        "name":           "Ligue 2",
        "fdco_code":      "F2",
        "tournament_id":  182,             # confirmed from your curl result
        "supabase_table": "match_results",
        "models_dir":     "models/saved/f2",
        "season_format":  "aug_may",
        "teams_count":    20,
        "understat_slug": "ligue_2",
    },
    "france_national": {
        "name":           "National",
        "fdco_code":      "F3",
        "tournament_id":  183,             # confirmed from your curl result
        "supabase_table": "match_results",
        "models_dir":     "models/saved/f3",
        "season_format":  "aug_may",
        "teams_count":    18,
        "understat_slug": "national",
    },
}


# ── Active league helper ───────────────────────────────────────────────────────
ACTIVE_CONFIG = LEAGUE_CONFIG[settings.ACTIVE_LEAGUE]