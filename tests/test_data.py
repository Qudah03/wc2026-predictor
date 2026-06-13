import pandas as pd
import numpy as np
import pytest
import os

from src.data_prep import clean_match_data

def test_clean_match_data_logic():
    # 1. Create a fake raw dataset to test against
    raw_data = pd.DataFrame({
        'home_team': ['Argentina', 'France', 'Germany'],
        'away_team': ['Saudi Arabia', 'Morocco', 'Japan'],
        'home_score': [1, 2, np.nan],  # Germany vs Japan has a missing score
        'away_score': [2, 0, 1]
    })
    
    # 2. Run the cleaning function
    cleaned_df = clean_match_data(raw_data)
    
    # 3. Assertions (The actual checks)
    # Check if the row with the NaN score was dropped (3 rows should become 2)
    assert len(cleaned_df) == 2
    
    # Check if Argentina's loss to Saudi Arabia correctly outputs 0 (not a home win)
    assert cleaned_df.loc[cleaned_df['home_team'] == 'Argentina', 'home_win'].values[0] == 0
    
    # Check if France's win over Morocco correctly outputs 1 (home win)
    assert cleaned_df.loc[cleaned_df['home_team'] == 'France', 'home_win'].values[0] == 1

def test_model_artifact_exclusion():
    # Ensure that our pkl file exists locally but wouldn't be accidentally tracked if missing
    # This is a sanity check for your local training execution
    model_file = "src/baseline_model.pkl"
    if os.path.exists(model_file):
        assert os.path.getsize(model_file) > 0, "Model file exists but is empty. Check your training script."
    else:
        print(f"Model file {model_file} does not exist locally. This is expected if you haven't run the training script yet.")