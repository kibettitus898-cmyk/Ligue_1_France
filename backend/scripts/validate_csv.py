"""
Validate local CSV files before uploading to Supabase.
Updated for 'backend' folder structure and multi-league support.

Usage: 
    python backend/scripts/validate_csv.py data/raw/seasons/epl
    python backend/scripts/validate_csv.py data/raw/seasons/laliga
"""
import sys
import os
import pandas as pd
from pathlib import Path

# Ensure the root directory is in the path so we can find 'backend'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

try:
    # Renamed from app.services to backend.services
    from backend.services.ingest_service import COLUMN_MAP
except ImportError:
    print("❌ Error: Could not find 'backend.services'. Ensure you have renamed your folder to 'backend' and are running from the project root.")
    sys.exit(1)

def validate(folder: str):
    folder_path = Path(folder)
    if not folder_path.exists():
        print(f"❌ Error: Folder '{folder}' does not exist.")
        return

    csvs = list(folder_path.glob("*.csv"))
    print(f"--- CSV Validation Report ---")
    print(f"Target Folder: {folder}")
    print(f"Found {len(csvs)} files\n")

    for f in sorted(csvs):
        try:
            # Using latin-1 as football-data.co.uk CSVs often use it
            df = pd.read_csv(f, on_bad_lines="skip", encoding="latin-1")
            
            # Clean column names (strip whitespace and lowercase for comparison)
            df_cols = [str(c).strip().lower() for c in df.columns]
            
            # Match against your defined COLUMN_MAP keys
            present = [c for c in COLUMN_MAP if c.lower() in df_cols]
            missing = [c for c in COLUMN_MAP if c.lower() not in df_cols]
            
            status = "✅ PASS" if not missing else "⚠️  INCOMPLETE"
            
            print(f"[{status}] {f.name}")
            print(f"    Rows: {len(df)}")
            print(f"    Columns Matched: {len(present)}/{len(COLUMN_MAP)}")
            
            if missing:
                print(f"    ❌ Missing Required: {missing}")
            print("-" * 30)
            
        except Exception as e:
            print(f"❌ Error reading {f.name}: {e}")

if __name__ == "__main__":
    # Default to a generic path, but allow command line override
    target_folder = sys.argv[1] if len(sys.argv) > 1 else "data/raw/seasons"
    validate(target_folder)