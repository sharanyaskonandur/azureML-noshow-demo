"""
Batch Scoring Script for Patient No-Show Prediction
====================================================
This script is used by Azure ML Batch Endpoints to score
appointment data and generate no-show risk predictions.

Input: CSV/Parquet files with appointment data
Output: Scored predictions with risk flags
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime


# Feature configuration (matching training)
FEATURES = [
    'age',
    'scholarship',
    'hipertension',
    'diabetes',
    'alcoholism',
    'handcap',
    'sms_received',
    'lead_time_days',
    'day_of_week',
    'chronic_conditions',
]


def init():
    """Initialize model and scaler. Called once when batch job starts."""
    global model, scaler, prediction_threshold
    
    model_dir = os.getenv("AZUREML_MODEL_DIR", ".")
    
    # Search for model files
    for root, dirs, files in os.walk(model_dir):
        if "model.joblib" in files:
            model = joblib.load(os.path.join(root, "model.joblib"))
            scaler = joblib.load(os.path.join(root, "scaler.joblib"))
            break
    
    prediction_threshold = float(os.getenv("PREDICTION_THRESHOLD", "0.7"))
    print(f"Model initialized. Threshold: {prediction_threshold}")


def run(mini_batch):
    """Score a mini-batch of files."""
    results = []
    
    for file_path in mini_batch:
        try:
            # Read input file
            if file_path.endswith('.parquet'):
                df = pd.read_parquet(file_path)
            else:
                df = pd.read_csv(file_path)
            
            # Prepare features (fill missing with 0)
            X = df[FEATURES].fillna(0) if all(f in df.columns for f in FEATURES) else pd.DataFrame(0, index=df.index, columns=FEATURES)
            
            # Scale and predict
            X_scaled = scaler.transform(X)
            probabilities = model.predict_proba(X_scaled)[:, 1]
            
            # Add predictions
            df['no_show_risk'] = probabilities
            df['risk_flag'] = (probabilities >= prediction_threshold).astype(int)
            df['risk_category'] = pd.cut(probabilities, bins=[0, 0.3, 0.5, 0.7, 1.0], labels=['Low', 'Medium', 'High', 'Very High'])
            df['scored_at'] = datetime.utcnow().isoformat()
            
            results.append(df)
            print(f"Scored {len(df)} records from {os.path.basename(file_path)}")
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    return pd.concat(results, ignore_index=True) if results else pd.DataFrame()
