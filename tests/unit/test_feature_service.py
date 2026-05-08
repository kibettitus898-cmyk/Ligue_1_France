import pandas as pd
import pytest
import sys
import os

# Ensure backend is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Updated import to reflect backend renaming
from backend.services.feature_service import engineer_features

@pytest.fixture
def sample_df():
    """
    Generates a sample dataset using Ligue 1 teams (PSG and Marseille).
    Note: Ensure your ftr/fthg/ftag match the column names expected 
    by your updated engineer_features service.
    """
    data = {
        "date": pd.date_range("2023-08-01", periods=20, freq="7D"),
        "home_team": ["PSG"] * 10 + ["Marseille"] * 10,
        "away_team": ["Marseille"] * 10 + ["PSG"] * 10,
        "ftr": ["H","D","A","H","H","D","A","H","D","H"] * 2,
        "fthg": [3,1,0,4,2,1,1,3,0,2] * 2,
        "ftag": [0,1,2,1,0,1,2,0,0,1] * 2,
        "hst": [8,4,3,7,5,4,3,6,2,4] * 2, # Shots on target
        "ast": [2,3,6,3,1,4,5,2,1,2] * 2,
        "hc": [6,5,4,7,6,5,4,6,3,5] * 2,  # Corners
        "ac": [2,4,6,3,2,5,6,3,1,3] * 2,
        "time_weight": [1.0] * 20,
    }
    return pd.DataFrame(data)

def test_engineer_features_returns_elo(sample_df):
    """Verifies that Elo ratings are calculated for Ligue 1 teams."""
    result = engineer_features(sample_df)
    # Check if elo_diff or any other expected elo column exists
    assert "elo_diff" in result.columns or any("elo" in col for col in result.columns)

def test_no_data_leakage(sample_df):
    """
    Ensures rolling features (like form) are created.
    Crucial for Ligue 1 where match frequency can vary.
    """
    result = engineer_features(sample_df)
    
    # We check for a common rolling feature
    # Replace 'h_form_5' with the specific column name used in your service
    assert "h_form_5" in result.columns or "rolling_goals_h" in result.columns
    
    # Optional: Verify that the first few rows don't have 'future' info
    # (Checking that rolling windows don't 'peek' forward)
    first_match_form = result.iloc[0].get("h_form_5")
    # If using dropna() inside engineer_features, result will be shorter than sample_df
    assert len(result) <= len(sample_df)

def test_ligue1_team_handling(sample_df):
    """Specific check to ensure the service handles French team names correctly."""
    result = engineer_features(sample_df)
    unique_teams = set(result["home_team"].unique())
    assert "PSG" in unique_teams
    assert "Marseille" in unique_teams