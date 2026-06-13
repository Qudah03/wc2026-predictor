import os
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="WC 2026 Prediction API")

# Enable CORS so your Angular app (running on port 4200) can communicate with it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load your existing trained model path relative to backend/main.py
MODEL_PATH = os.path.join(os.path.dirname(__file__), "src", "baseline_model.pkl")

try:
    model = joblib.load(MODEL_PATH)
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

class MatchPredictionRequest(BaseModel):
    home_team: str
    away_team: str

@app.post("/api/predict")
async def predict_match(payload: MatchPredictionRequest):
    if model is None:
        raise HTTPException(status_code=500, detail="ML Model not loaded on server.")
    
    try:
        # Replace this placeholder DataFrame with your exact data_prep feature extraction logic
        # mapping payload.home_team and payload.away_team to historical stats.
        input_features = pd.DataFrame([[0.5, 0.5, 1.2, 1.1]], columns=[
            'home_historical_winrate', 'away_historical_winrate', 
            'home_avg_goals', 'away_avg_goals'
        ])
        
        prediction = model.predict(input_features)[0]
        winner = payload.home_team if prediction == 1 else payload.away_team
        
        return {"winner": winner}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))