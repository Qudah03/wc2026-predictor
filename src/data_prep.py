import pandas as pd
import numpy as np

def compute_team_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes progressive historical metrics for home and away teams.
    """
    # Ensure date is sorted chronologically
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    # Initialize dictionary to keep track of running stats for each team
    # Format: { team_name: { 'games': 0, 'wins': 0, 'goals_scored': 0, 'goals_conceded': 0 } }
    team_stats = {}
    
    # Lists to store our newly engineered features
    home_win_rates = []
    away_win_rates = []
    home_attack_rem = []
    away_attack_rem = []
    
    # Target variable: 1 if home win, 0 otherwise (Draw or Away win)
    df['home_win'] = (df['home_score'] > df['away_score']).astype(int)
    
    for idx, row in df.iterrows():
        h_team = row['home_team']
        a_team = row['away_team']
        
        # Initialize team if they don't exist in our dictionary yet
        for team in [h_team, a_team]:
            if team not in team_stats:
                team_stats[team] = {'games': 0, 'wins': 0, 'goals_scored': 0, 'goals_conceded': 0}
        
        # Extract stats *before* this match happened
        h_games = team_stats[h_team]['games']
        a_games = team_stats[a_team]['games']
        
        # Calculate features (avoid dividing by zero for a team's first ever game)
        home_win_rates.append(team_stats[h_team]['wins'] / h_games if h_games > 0 else 0.33)
        away_win_rates.append(team_stats[a_team]['wins'] / a_games if a_games > 0 else 0.33)
        
        home_attack_rem.append(team_stats[h_team]['goals_scored'] / h_games if h_games > 0 else 1.0)
        away_attack_rem.append(team_stats[a_team]['goals_scored'] / a_games if a_games > 0 else 1.0)
        
        # Update our running dictionary totals with the results of *this* match for future rows
        team_stats[h_team]['games'] += 1
        team_stats[a_team]['games'] += 1
        
        team_stats[h_team]['goals_scored'] += row['home_score']
        team_stats[h_team]['goals_conceded'] += row['away_score']
        team_stats[a_team]['goals_scored'] += row['away_score']
        team_stats[a_team]['goals_conceded'] += row['home_score']
        
        if row['home_score'] > row['away_score']:
            team_stats[h_team]['wins'] += 1
        elif row['away_score'] > row['home_score']:
            team_stats[a_team]['wins'] += 1

    # Add the engineered arrays back into our main dataframe
    df['home_historical_winrate'] = home_win_rates
    df['away_historical_winrate'] = away_win_rates
    df['home_avg_goals'] = home_attack_rem
    df['away_avg_goals'] = away_attack_rem
    
    return df

if __name__ == "__main__":
    # Test execution
    raw_df = pd.read_csv("data/results.csv")
    # Clean missing records
    raw_df = raw_df.dropna(subset=['home_score', 'away_score'])
    processed_df = compute_team_metrics(raw_df)
    print("Features engineered successfully!")
    print(processed_df[['date', 'home_team', 'away_team', 'home_historical_winrate', 'home_win']].tail())