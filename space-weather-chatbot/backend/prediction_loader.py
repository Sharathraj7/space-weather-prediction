import os
import sys
import pickle
import pandas as pd

# Setup paths so we can use downstrean resources
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
MODEL_PATH = os.path.join(PROJECT_ROOT, "model.pkl")
DATA_PATH = os.path.join(PROJECT_ROOT, "geomagnetic_forecasting_master_dataset.csv")

def get_latest_prediction():
    """
    Loads the pickle model and uses it for prediction.
    """
    try:
        with open(MODEL_PATH, "rb") as f:
            model = pickle.load(f)
            
        df = pd.read_csv(DATA_PATH)
        df = df.sort_values("datetime")
        last_row = df.iloc[-1:] 
        
        remove_cols = ["datetime", "target_1h", "target_3h", "target_6h", "Kp"]
        X = last_row.drop(columns=[c for c in remove_cols if c in last_row.columns], errors="ignore")
        
        prob = model.predict_proba(X)[0][1] 
        
        # We model 3hr natively in pipeline, mapping approximations for the bot requirements
        return {
            "kp_probability_1h": round(max(0.0, prob - 0.05), 4),
            "kp_probability_3h": round(prob, 4),
            "kp_probability_6h": round(min(1.0, prob + 0.1), 4),
            "status": "live"
        }
    except Exception as e:
        print(f"[!] Error computing live prediction. Fallback used: {e}")
        
        # Fallback dictionary if there's any crash in data fetching
        return {
            "kp_probability_1h": 0.25,
            "kp_probability_3h": 0.40,
            "kp_probability_6h": 0.55,
            "status": "mocked"
        }
