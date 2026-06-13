import pandas as pd

def clean_match_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans raw match data: Drops rows with missing goals 
    and adds a target column 'home_win' (1 if home team won, 0 otherwise).
    """
    # Drop rows where goals are missing
    df = df.dropna(subset=['home_score', 'away_score'])
    
    # Create target column for the ML model
    df['home_win'] = (df['home_score'] > df['away_score']).astype(int)
    
    return df