"""
Online Scoring Script for Patient No-Show Prediction
=====================================================
Real-time scoring endpoint for HiX integration and operational apps.
Returns no-show risk scores for individual appointments.

Input: JSON with appointment features
Output: Risk score, category, and flag
"""

import os
import json
import joblib
import numpy as np
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Feature configuration (matching Kaggle dataset)
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
    
    # List all files in model directory for debugging
    logger.info("Listing model directory contents:")
    for root, dirs, files in os.walk(model_dir):
        for f in files:
            logger.info(f"  {os.path.join(root, f)}")
    
    # Try different possible paths for the model files
    possible_paths = [
        model_dir,
        os.path.join(model_dir, "outputs"),
        os.path.join(model_dir, "noshow-logreg"),
        os.path.join(model_dir, "noshow-logreg", "1"),
        os.path.join(model_dir, "noshow-logreg", "2"),
    ]
    
    # Also search recursively for model.joblib
    for root, dirs, files in os.walk(model_dir):
        if "model.joblib" in files:
            possible_paths.insert(0, root)
            break
    
    model_path = None
    scaler_path = None
    
    for path in possible_paths:
        test_model = os.path.join(path, "model.joblib")
        test_scaler = os.path.join(path, "scaler.joblib")
        if os.path.exists(test_model) and os.path.exists(test_scaler):
            model_path = test_model
            scaler_path = test_scaler
            logger.info(f"Found model at: {path}")
            break
    
    if model_path is None:
        # List directory contents for debugging
        logger.error(f"Model not found. AZUREML_MODEL_DIR={model_dir}")
        raise FileNotFoundError(f"Could not find model.joblib in {model_dir}")
    
    # Load model and scaler
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    
    # Get prediction threshold from environment
    prediction_threshold = float(os.getenv("PREDICTION_THRESHOLD", "0.7"))
    
    logger.info(f"✅ Model initialized with threshold: {prediction_threshold}")


def run(raw_data: str) -> str:
    """
    Score a single appointment or batch of appointments.
    
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
            # Batch input
            records = data["data"]
            is_batch = True
        else:
            # Single input
            records = [data]
            is_batch = False
        
        results = []
        
        for record in records:
            # Extract features (with defaults for missing values)
            features = []
            for feat in FEATURES:
                value = record.get(feat, 0)
                features.append(float(value) if value is not None else 0.0)
            
            # Scale features
            X = np.array([features])
            X_scaled = scaler.transform(X)
            
            # Generate prediction
            probability = float(model.predict_proba(X_scaled)[0, 1])
            
            # Determine risk category
            if probability < 0.3:
                risk_category = "Low"
            elif probability < 0.5:
                risk_category = "Medium"
            elif probability < 0.7:
                risk_category = "High"
            else:
                risk_category = "Very High"
            
            # Create result
            result = {
                "no_show_risk": round(probability, 4),
                "no_show_risk_pct": round(probability * 100, 1),
                "risk_category": risk_category,
                "risk_flag": int(probability >= prediction_threshold),
                "threshold_used": prediction_threshold,
                "scored_at": datetime.utcnow().isoformat() + "Z",
                "model_version": os.getenv("MODEL_VERSION", "v1")
            }
            
            # Include patient_id if provided
            if "patient_id" in record:
                result["patient_id"] = record["patient_id"]
            if "appointment_id" in record:
                result["appointment_id"] = record["appointment_id"]
            
            results.append(result)
        
        # Log prediction
        avg_risk = np.mean([r["no_show_risk"] for r in results])
        logger.info(f"Scored {len(results)} records. Avg risk: {avg_risk:.2%}")
        
        # Return single result or batch
        if is_batch:
            return json.dumps({"predictions": results})
        else:
            return json.dumps(results[0])
            
    except Exception as e:
        logger.error(f"Scoring error: {str(e)}")
        return json.dumps({
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })


# =============================================================================
# Local Testing
# =============================================================================
if __name__ == "__main__":
    print("🧪 Running local test...")
    
    # Initialize (for local testing, set paths)
    os.environ["AZUREML_MODEL_DIR"] = "../../outputs"
    init()
    
    # Test single prediction
    test_single = json.dumps({
        "patient_id": "P12345",
        "appointment_id": "A00001",
        "age": 55,
        "scholarship": 0,
        "hipertension": 1,
        "diabetes": 1,
        "alcoholism": 0,
        "handcap": 0,
        "sms_received": 1,
        "lead_time_days": 21,
        "day_of_week": 4,
        "chronic_conditions": 2
    })
    
    print("\n📋 Single Prediction Test:")
    result = run(test_single)
    print(json.dumps(json.loads(result), indent=2))
    
    # Test batch prediction
    test_batch = json.dumps({
        "data": [
            {
                "patient_id": "P001",
                "age": 35,
                "scholarship": 0,
                "hipertension": 0,
                "diabetes": 0,
                "alcoholism": 0,
                "handcap": 0,
                "sms_received": 1,
                "lead_time_days": 7,
                "day_of_week": 1,
                "chronic_conditions": 0
            },
            {
                "patient_id": "P002",
                "age": 70,
                "scholarship": 1,
                "hipertension": 1,
                "diabetes": 1,
                "alcoholism": 0,
                "handcap": 1,
                "sms_received": 0,
                "lead_time_days": 30,
                "day_of_week": 0,
                "chronic_conditions": 2
            }
        ]
    })
    
    print("\n📋 Batch Prediction Test:")
    result = run(test_batch)
    print(json.dumps(json.loads(result), indent=2))
