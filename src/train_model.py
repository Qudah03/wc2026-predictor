import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from src.data_prep import compute_team_metrics

def train_baseline_model():
    print("Loading raw match data...")
    raw_df = pd.read_csv("data/results.csv")
    raw_df = raw_df.dropna(subset=['home_score', 'away_score'])
    
    print("Engineering historical metrics...")
    processed_df = compute_team_metrics(raw_df)
    
    # Define the features we want our model to learn from
    features = [
        'home_historical_winrate', 
        'away_historical_winrate', 
        'home_avg_goals', 
        'away_avg_goals'
    ]
    
    X = processed_df[features]
    y = processed_df['home_win']
    
    # Split chronologically or randomly. For a baseline, a standard 80/20 split works.
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print(True, f"Training Random Forest Classifier on {len(X_train)} matches...")
    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate the baseline model
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    
    print("\n=== Model Performance ===")
    print(f"Accuracy: {accuracy:.2%}")
    print("\nClassification Report:")
    print(classification_report(y_test, predictions))
    
    # Save the trained model file so the web app can use it later without retraining
    model_path = "src/baseline_model.pkl"
    joblib.dump(model, model_path)
    print(f"\nModel saved successfully to {model_path}")

if __name__ == "__main__":
    train_baseline_model()