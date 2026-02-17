"""
Online Scoring Script for Patient No-Show Prediction
====================================================
Real-time scoring for HiX integration and operational apps.
"""

import os
import json
import joblib
import numpy as np
from datetime import datetime

FEATURES = ['age', 'scholarship', 'hipertension', 'diabetes', 'alcoholism', 
            'handcap', 'sms_received', 'lead_time_days', 'day_of_week', 'chronic_conditions']


def init():
    """Initialize model. Called once when endpoint starts."""
    global model, scaler, threshold
    
    model_dir = os.getenv("AZUREML_MODEL_DIR", ".")
    for root, dirs, files in os.walk(model_dir):
        if "model.joblib" in files:
            model = joblib.load(os.path.join(root, "model.joblib"))
            scaler = joblib.load(os.path.join(root, "scaler.joblib"))
            break
    
    threshold = float(os.getenv("PREDICTION_THRESHOLD", "0.7"))


def run(raw_data):
    """Score appointment(s) for no-show risk."""
    data = json.loads(raw_data)
    records = data.get("data", [data])
    
    results = []
    for record in records:
        features = [float(record.get(f, 0) or 0) for f in FEATURES]
        X_scaled = scaler.transform([features])
        prob = model.predict_proba(X_scaled)[0, 1]
        
        results.append({
            "no_show_risk": round(float(prob), 4),
            "no_show_risk_pct": round(float(prob) * 100, 1),
            "risk_category": "Very High" if prob >= 0.7 else "High" if prob >= 0.5 else "Medium" if prob >= 0.3 else "Low",
            "risk_flag": int(prob >= threshold),
            "scored_at": datetime.utcnow().isoformat()
        })
    
    return json.dumps(results[0] if len(records) == 1 else {"predictions": results})
