"""
Batch Scoring Script for Patient No-Show Prediction
====================================================
This script is used by Azure ML Batch Endpoints to score
appointment data and generate no-show risk predictions.

Input: Parquet files with appointment data
Output: Scored predictions with risk flags
"""

import os
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List


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
    Called once when the batch job starts.
    """
    global model, scaler, prediction_threshold
    
    # Get model path from Azure ML
    model_path = os.path.join(os.getenv("AZUREML_MODEL_DIR", "."), "model.joblib")
    scaler_path = os.path.join(os.getenv("AZUREML_MODEL_DIR", "."), "scaler.joblib")
    
    # Load model and scaler
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    
    # Get prediction threshold from environment
    prediction_threshold = float(os.getenv("PREDICTION_THRESHOLD", "0.7"))
    
    print(f"✅ Model initialized")
    print(f"   Prediction threshold: {prediction_threshold}")


def run(mini_batch: List[str]) -> pd.DataFrame:
    """
    Score a mini-batch of files.
    
    Args:
        mini_batch: List of file paths to process
        
    Returns:
        DataFrame with predictions
    """
    results = []
    
    for file_path in mini_batch:
        try:
            # Read the input file
            if file_path.endswith('.parquet'):
                df = pd.read_parquet(file_path)
            elif file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                print(f"⚠️ Unsupported file format: {file_path}")
                continue
            
            # Prepare features
            X = df[FEATURES].fillna(0)
            
            # Scale features
            X_scaled = scaler.transform(X)
            
            # Generate predictions
            probabilities = model.predict_proba(X_scaled)[:, 1]
            
            # Add predictions to dataframe
            df['no_show_risk'] = probabilities
            df['no_show_risk_pct'] = (probabilities * 100).round(1)
            df['risk_flag'] = (probabilities >= prediction_threshold).astype(int)
            df['risk_category'] = pd.cut(
                probabilities,
                bins=[0, 0.3, 0.5, 0.7, 1.0],
                labels=['Low', 'Medium', 'High', 'Very High']
            )
            
            # Add metadata
            df['scored_at'] = datetime.utcnow().isoformat()
            df['model_version'] = os.getenv("MODEL_VERSION", "v1")
            df['source_file'] = os.path.basename(file_path)
            
            results.append(df)
            print(f"✅ Processed {len(df)} records from {os.path.basename(file_path)}")
            
        except Exception as e:
            print(f"❌ Error processing {file_path}: {str(e)}")
            continue
    
    # Combine all results
    if results:
        combined = pd.concat(results, ignore_index=True)
        
        # Log summary statistics
        high_risk_count = (combined['risk_flag'] == 1).sum()
        total_count = len(combined)
        print(f"📊 Batch Summary: {high_risk_count}/{total_count} high-risk ({high_risk_count/total_count:.1%})")
        
        return combined
    else:
        return pd.DataFrame()


if __name__ == "__main__":
    # Local testing
    print("🧪 Running local test...")
    init()
    
    # Test with sample data
    test_data = pd.DataFrame({
        'patient_id': ['P001', 'P002', 'P003'],
        'distance_km': [5.0, 15.0, 25.0],
        'previous_no_shows': [0, 2, 4],
        'age': [35, 55, 75],
        'medication_count': [1, 5, 10],
        'lead_time_days': [7, 14, 30],
        'day_of_week': [1, 4, 0],
        'hour_of_day': [9, 14, 8],
        'chronic_conditions': [0, 2, 4],
    })
    
    # Save test file
    test_data.to_parquet('test_input.parquet', index=False)
    
    # Run scoring
    result = run(['test_input.parquet'])
    print("\n📋 Test Results:")
    print(result[['patient_id', 'no_show_risk', 'risk_category', 'risk_flag']])
    
    # Cleanup
    os.remove('test_input.parquet')
