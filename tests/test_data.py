import pandas as pd
import numpy as np
import pytest
import os
from src.data_prep import compute_team_metrics

def test_compute_team_metrics_logic():
    # Create a small chronological dataset
    raw_data = pd.DataFrame({
        'date': ['2026-01-01', '2026-01-02', '2026-01-03'],
        'home_team': ['Argentina', 'France', 'Argentina'],
        'away_team': ['Brazil', 'Italy', 'France'],
        'home_score': [2, 3, 1],
        'away_score': [0, 1, 2]
    })
    
    processed_df = compute_team_metrics(raw_data)
    
    # Assertions
    assert 'home_historical_winrate' in processed_df.columns
    assert 'home_win' in processed_df.columns
    
    # In match 3, Argentina plays France. Argentina's stats should reflect only match 1 (1 game, 1 win -> winrate 1.0)
    arg_row = processed_df.iloc[2]
    assert arg_row['home_historical_winrate'] == 1.0

def test_model_artifact_exclusion():
    # Ensure that our pkl file exists locally but wouldn't be accidentally tracked if missing
    # This is a sanity check for your local training execution
    model_file = "src/baseline_model.pkl"
    if os.path.exists(model_file):
        assert os.path.getsize(model_file) > 0, "Model file exists but is empty. Please check your training script."
    else:
        pytest.skip("Model artifact not found. Please run the training script to generate it before testing.")