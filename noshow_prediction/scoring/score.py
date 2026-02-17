"""
Real-time Scoring Script for Patient No-Show Prediction
========================================================
This script is used by Azure ML real-time endpoints (ACI/AKS)
to score individual appointments and return no-show risk.

Following MLOpsPython template: https://github.com/microsoft/MLOpsPython
"""

import os
import json
import joblib
import numpy as np
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Feature configuration (matching training)
FEATURES = [
    'age',                  # Patient age
    'scholarship',          # Bolsa Família welfare indicator
    'hipertension',         # Has hypertension (0/1)
    'diabetes',             # Has diabetes (0/1)
    'alcoholism',           # Alcoholism indicator (0/1)
    'handcap',              # Disability level (0-4)
    'sms_received',         # Received SMS reminder (0/1)
    'lead_time_days',       # Days between scheduling and appointment
    'day_of_week',          # Day of week (0=Mon)
    'chronic_conditions',   # Sum of health conditions
]


def init():
    """
    Initialize the model and scaler.
    Called once when the endpoint starts.
    """
    global model, scaler, prediction_threshold
    
    # Get model path from Azure ML
    model_dir = os.getenv("AZUREML_MODEL_DIR", ".")
    
    logger.info(f"AZUREML_MODEL_DIR = {model_dir}")
    
    # Search for model files
    possible_paths = [
        model_dir,
        os.path.join(model_dir, "outputs"),
        os.path.join(model_dir, "noshow-logreg"),
    ]
    
    # Also search recursively
    for root, dirs, files in os.walk(model_dir):
        if "model.joblib" in files:
            possible_paths.insert(0, root)
            logger.info(f"Found model at: {root}")
            break
    
    model_path = None
    scaler_path = None
    
    for path in possible_paths:
        test_model = os.path.join(path, "model.joblib")
        test_scaler = os.path.join(path, "scaler.joblib")
        if os.path.exists(test_model) and os.path.exists(test_scaler):
            model_path = test_model
            scaler_path = test_scaler
            break
    
    if model_path is None:
        raise FileNotFoundError(f"Could not find model files in {model_dir}")
    
    # Load model and scaler
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    
    # Get prediction threshold from environment
    prediction_threshold = float(os.getenv("PREDICTION_THRESHOLD", "0.7"))
    
    logger.info(f"Model initialized with threshold: {prediction_threshold}")


def run(raw_data: str) -> str:
    """
    Score appointments for no-show risk.
    
    Input JSON format (single):
    {
        "age": 45,
        "scholarship": 0,
        "hipertension": 1,
        "diabetes": 0,
        "alcoholism": 0,
        "handcap": 0,
        "sms_received": 1,
        "lead_time_days": 14,
        "day_of_week": 1,
        "chronic_conditions": 1
    }
    
    Input JSON format (batch):
    {
        "data": [
            { ... appointment 1 ... },
            { ... appointment 2 ... }
        ]
    }
    
    Returns:
        JSON with risk score, category, and flag
    """
    try:
        # Parse input
        data = json.loads(raw_data)
        
        # Handle batch vs single input
        if "data" in data:
            records = data["data"]
            is_batch = True
        else:
            records = [data]
            is_batch = False
        
        results = []
        
        for record in records:
            # Extract features
            features = []
            for feat in FEATURES:
                value = record.get(feat, 0)
                features.append(float(value) if value is not None else 0.0)
            
            # Scale features
            X = np.array([features])
            X_scaled = scaler.transform(X)
            
            # Generate prediction
            probability = model.predict_proba(X_scaled)[0, 1]
            
            # Classify risk
            if probability >= 0.7:
                risk_category = "Very High"
            elif probability >= 0.5:
                risk_category = "High"
            elif probability >= 0.3:
                risk_category = "Medium"
            else:
                risk_category = "Low"
            
            # Build result
            result = {
                "no_show_risk": round(float(probability), 4),
                "no_show_risk_pct": round(float(probability) * 100, 1),
                "risk_category": risk_category,
                "risk_flag": int(probability >= prediction_threshold),
                "threshold_used": prediction_threshold,
                "scored_at": datetime.utcnow().isoformat(),
                "model_version": os.getenv("MODEL_VERSION", "v1")
            }
            
            results.append(result)
        
        # Return single or batch result
        if is_batch:
            return json.dumps({"predictions": results})
        else:
            return json.dumps(results[0])
            
    except Exception as e:
        logger.error(f"Scoring error: {str(e)}")
        return json.dumps({
            "error": str(e),
            "scored_at": datetime.utcnow().isoformat()
        })


if __name__ == "__main__":
    # Local testing
    print("Testing scoring script...")
    
    # Set test model directory
    os.environ["AZUREML_MODEL_DIR"] = "./outputs"
    
    # Initialize
    init()
    
    # Test single prediction
    test_input = json.dumps({
        "age": 25,
        "scholarship": 1,
        "hipertension": 0,
        "diabetes": 0,
        "alcoholism": 0,
        "handcap": 0,
        "sms_received": 0,
        "lead_time_days": 21,
        "day_of_week": 4,
        "chronic_conditions": 0
    })
    
    result = run(test_input)
    print(f"Result: {result}")
    
    # Test batch prediction
    test_batch = json.dumps({
        "data": [
            {"age": 25, "scholarship": 1, "sms_received": 0, "lead_time_days": 21},
            {"age": 65, "scholarship": 0, "sms_received": 1, "lead_time_days": 3}
        ]
    })
    
    batch_result = run(test_batch)
    print(f"Batch result: {batch_result}")
