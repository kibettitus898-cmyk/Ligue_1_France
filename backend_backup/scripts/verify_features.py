"""
Verifies the feature matrix is healthy after the NaN fixes.
Focused exclusively on Ligue 1 (F1).
Run: python backend/scripts/verify_features.py
"""
import sys
import os
import pandas as pd
from pathlib import Path

# Adjust path to account for 'backend' folder rename
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# Import from 'backend' instead of 'app'
from backend.ml.features.feature_columns import FEATURE_COLS, TARGET_COL, LABEL_MAP

# Ensure this path points to your Ligue 1 processed data
# If you store multiple leagues in one parquet, we will filter below.
FEATURES_PATH = Path("data/processed/ligue1_features.parquet")

if not FEATURES_PATH.exists():
    print(f"❌ Error: Feature file not found at {FEATURES_PATH}")
    sys.exit(1)

df = pd.read_parquet(FEATURES_PATH)

# --- Ligue 1 Specific Filter ---
# Usually 'div' or 'league' column exists if the pipeline handles multiple
if 'div' in df.columns:
    df = df[df['div'] == 'F1'].copy()
elif 'league' in df.columns:
    df = df[df['league'].str.lower().contains('ligue1|france')].copy()

date_col = "date" if "date" in df.columns else "match_date"
df = df.sort_values(date_col).reset_index(drop=True)

print("=" * 60)
print(f"  LIGUE 1 FEATURE MATRIX AUDIT (F1)")
print("=" * 60)
print(f"  Total rows in parquet        : {len(df)}")

# ── Target validity ──────────────────────────────────────────────
y = df[TARGET_COL].map(LABEL_MAP)
valid_target = y.notna().sum()
print(f"  Rows with valid target       : {valid_target}")
print(f"  Rows with missing target     : {y.isna().sum()}  ← should be 0")

# ── Available declared features ──────────────────────────────────
available = [c for c in FEATURE_COLS if c in df.columns]
missing   = [c for c in FEATURE_COLS if c not in df.columns]
print(f"\n  Declared FEATURE_COLS        : {len(FEATURE_COLS)}")
print(f"  Found in parquet             : {len(available)}")
print(f"  Missing (will be skipped)    : {len(missing)}")
if missing:
    print(f"  Missing cols: {missing}")

# ── NaN audit on feature matrix ───────────────────────────────────
X = df[available].copy()
nan_by_col = X.isna().sum().sort_values(ascending=False)
nan_cols   = nan_by_col[nan_by_col > 0]

print(f"\n  Columns with NaN             : {len(nan_cols)} / {len(available)}")
rows_with_nan = X.isna().any(axis=1).sum()
print(f"  Rows with ≥1 NaN feature     : {rows_with_nan}  ({rows_with_nan/len(X)*100:.1f}%)")
print(f"  Rows lost if dropna()        : {len(X) - len(X.dropna())}")

if not nan_cols.empty:
    print(f"\n  Top NaN columns (Ligue 1 Context):")
    print(f"  {'Column':<45} {'NaNs':>6}  {'Rate':>6}")
    print(f"  {'-'*60}")
    for col, count in nan_cols.head(20).items():
        flag = " ⚠️ " if count / len(X) > 0.10 else ""
        print(f"  {col:<45} {count:>6}  ({count/len(X)*100:>5.1f}%){flag}")

# ── Season coverage ──────────────────────────────────────────────
if "season_label" in df.columns:
    season_counts = df["season_label"].value_counts().sort_index()
    print(f"\n  Ligue 1 Rows per season:")
    for season, count in season_counts.items():
        bar = "█" * (count // 20) # Adjusted bar scale for Ligue 1 (380 matches/season)
        print(f"  {season}  {count:>4}  {bar}")

# ── Feature group NaN rates ──────────────────────────────────────
groups = {
    "Rolling stats" : [c for c in available if any(k in c for k in ["goals","form","sot","corners","cards"])],
    "xG features"   : [c for c in available if "xg" in c or "npxg" in c],
    "Elo features"  : [c for c in available if "elo" in c],
    "Pi-ratings"    : [c for c in available if "pi_" in c],
    "Possession"    : [c for c in available if "poss" in c],
    "Squad"         : [c for c in available if "squad" in c],
    "H2H"           : [c for c in available if "h2h" in c],
    "Odds"          : [c for c in available if "odds" in c or "b365" in c],
    "Contextual"    : [c for c in available if c in [
        "home_days_rest","away_days_rest","home_cumpts","away_cumpts","is_derby",
        "home_win_rate_hist","away_win_rate_hist"
    ]],
}
print(f"\n  Ligue 1 NaN rate by feature group:")
print(f"  {'Group':<20} {'Cols':>5}  {'Max NaN%':>9}  {'Status':>8}")
print(f"  {'-'*50}")
for group, cols in groups.items():
    if not cols:
        continue
    max_nan = X[cols].isna().max().max() if cols else 0
    pct = max_nan / len(X) * 100 if len(X) > 0 else 0
    status = "✅" if pct == 0 else ("⚠️ " if pct < 10 else "❌")
    print(f"  {group:<20} {len(cols):>5}  {pct:>8.1f}%  {status:>8}")

# ── Final verdict ────────────────────────────────────────────────
print("\n" + "=" * 60)
if rows_with_nan == 0:
    print("  ✅ CLEAN: Ligue 1 dataset has 0 NaN rows.")
elif rows_with_nan / len(X) < 0.15: # Slightly more lenient for smaller leagues
    print(f"  ✅ HEALTHY: {rows_with_nan} rows have NaNs (Imputer will handle)")
else:
    print(f"  ❌ WARNING: {rows_with_nan/len(X)*100:.1f}% rows still have NaNs")
print("=" * 60)