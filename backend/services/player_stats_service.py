"""
Loads the Kaggle football players stats CSV and ingests Ligue 1 squad data into Supabase.
Dataset: hubertsidorowicz/football-players-stats-2025-2026 (Ligue 1 subset)
"""
import logging
import pandas as pd
import numpy as np
from backend.core.supabase_client import get_supabase

logger = logging.getLogger(__name__)

# Map CSV column names → our clean DB column names
COLUMN_MAP = {
    "Player":                "player",
    "Squad":                 "squad",
    "Comp":                  "comp",
    "Nation":                "nation",
    "Pos":                   "pos",
    "Age":                   "age",
    "MP":                    "mp",
    "Starts":                "starts",
    "Min":                   "min",
    "Gls":                   "goals",
    "Ast":                   "assists",
    "Gls.1":                 "goals_per90",
    "Ast.1":                 "assists_per90",
    "xG":                    "xg",
    "xAG":                   "xag",
    "PrgC":                  "progressive_carries",
    "PrgP":                  "progressive_passes",
    "Tkl":                   "tackles",
    "Int":                   "interceptions",
    "B365H":                 "b365h",
    "B365D":                 "b365d",
    "B365A":                 "b365a",
}

LIGUE1_COMP_NAMES = [
    "fr Ligue 1",
    "Ligue 1",
    "FRA-Ligue 1",
    "French Ligue 1",
]


def load_and_clean(csv_path: str, season: str = "25/26") -> pd.DataFrame:
    df = pd.read_csv(csv_path, encoding="utf-8", on_bad_lines="skip")
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns from CSV")

    # Rename known columns
    rename = {k: v for k, v in COLUMN_MAP.items() if k in df.columns}
    df = df.rename(columns=rename)

    # Keep only columns we need
    keep = list(rename.values())
    df = df[[c for c in keep if c in df.columns]]

    # Add season
    df["season"] = season

    # Filter Ligue 1 only
    if "comp" in df.columns:
        l1_mask = df["comp"].str.contains("Ligue 1", case=False, na=False)
        df_l1 = df[l1_mask].copy()
        logger.info(f"Ligue 1 players after filtering: {len(df_l1)}")
    else:
        df_l1 = df.copy()
        logger.warning("No 'comp' column found — using all rows")

    # Clean numeric columns
    num_cols = ["age","mp","starts","min","goals","assists",
                "goals_per90","assists_per90","xg","xag",
                "progressive_carries","progressive_passes",
                "tackles","interceptions"]
    for col in num_cols:
        if col in df_l1.columns:
            df_l1[col] = pd.to_numeric(df_l1[col], errors="coerce")

    # Convert int columns
    int_cols = ["mp", "starts", "min", "progressive_carries", "progressive_passes"]
    for col in int_cols:
        if col in df_l1.columns:
            df_l1[col] = df_l1[col].apply(
                lambda x: int(x) if pd.notna(x) else None
            )

    # Drop rows with no player or squad
    df_l1 = df_l1.dropna(subset=["player", "squad"])

    # Replace NaN with None for JSON serialization
    df_l1 = df_l1.where(pd.notna(df_l1), None)

    return df_l1


def upsert_player_stats(df: pd.DataFrame):
    supabase = get_supabase()
    records  = df.to_dict(orient="records")

    # Batch upsert in chunks of 500
    batch_size = 500
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        supabase.table("player_stats").upsert(
            batch, on_conflict="season,player,squad"
        ).execute()
        logger.info(f"  Upserted batch {i // batch_size + 1}: {len(batch)} rows")


def ingest_player_stats(csv_path: str, season: str = "25/26"):
    logger.info(f"Loading player stats from: {csv_path}")
    df = load_and_clean(csv_path, season)
    logger.info(f"Ingesting {len(df)} Ligue 1 player records...")
    upsert_player_stats(df)
    logger.info(f"✅ Player stats ingested: {len(df)} players")
    return len(df)