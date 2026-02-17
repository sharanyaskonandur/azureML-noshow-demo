"""
Platform-agnostic training script for Patient No-Show Prediction
================================================================
This script contains the core training logic that can be invoked
locally or from Azure ML pipelines.

Following MLOpsPython template: https://github.com/microsoft/MLOpsPython
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    roc_auc_score,
    brier_score_loss,
    classification_report,
    confusion_matrix
)
import joblib
import json
import os
from datetime import datetime
from typing import Tuple, Dict, Any


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

TARGET = 'no_show'


def load_data(data_path: str) -> pd.DataFrame:
    """
    Load and preprocess the no-show dataset.
    
    Args:
        data_path: Path to the CSV data file
        
    Returns:
        Preprocessed DataFrame
    """
    print(f"Loading data from: {data_path}")
    df = pd.read_csv(data_path)
    
    # Standardize column names
    df.columns = df.columns.str.lower().str.replace('-', '_')
    
    # Parse dates
    df['scheduledday'] = pd.to_datetime(df['scheduledday'])
    df['appointmentday'] = pd.to_datetime(df['appointmentday'])
    
    # Feature engineering
    df['lead_time_days'] = (df['appointmentday'] - df['scheduledday']).dt.days
    df['lead_time_days'] = df['lead_time_days'].clip(lower=0)
    df['day_of_week'] = df['appointmentday'].dt.dayofweek
    df['hour_of_day'] = df['scheduledday'].dt.hour
    
    # Create chronic conditions count
    df['chronic_conditions'] = (
        df['hipertension'].astype(int) +
        df['diabetes'].astype(int) +
        df['alcoholism'].astype(int)
    )
    
    # Convert target: "No" = showed up, "Yes" = no-show
    df['no_show'] = (df['no_show'] == 'Yes').astype(int)
    
    # Clean age
    df['age'] = df['age'].clip(lower=0, upper=115)
    
    print(f"Loaded {len(df):,} records")
    print(f"No-show rate: {df['no_show'].mean():.1%}")
    
    return df


def prepare_data(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, StandardScaler]:
    """
    Prepare features and split data for training.
    
    Args:
        df: Input DataFrame
        test_size: Fraction of data for testing
        random_state: Random seed for reproducibility
        
    Returns:
        X_train, X_test, y_train, y_test, scaler
    """
    # Prepare feature matrix and target
    X = df[FEATURES].fillna(0)
    y = df[TARGET].astype(int)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=y
    )
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print(f"Training samples: {len(X_train):,}")
    print(f"Test samples: {len(X_test):,}")
    
    return X_train_scaled, X_test_scaled, y_train.values, y_test.values, scaler


def train_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    model_params: Dict[str, Any] = None
) -> LogisticRegression:
    """
    Train the logistic regression model.
    
    Args:
        X_train: Scaled training features
        y_train: Training labels
        model_params: Optional model hyperparameters
        
    Returns:
        Trained model
    """
    if model_params is None:
        model_params = {
            'max_iter': 1000,
            'class_weight': 'balanced',
            'random_state': 42,
            'solver': 'lbfgs'
        }
    
    print("Training Logistic Regression model...")
    model = LogisticRegression(**model_params)
    model.fit(X_train, y_train)
    print("Training complete")
    
    return model


def evaluate_model(
    model: LogisticRegression,
    X_test: np.ndarray,
    y_test: np.ndarray
) -> Dict[str, float]:
    """
    Evaluate model performance.
    
    Args:
        model: Trained model
        X_test: Scaled test features
        y_test: Test labels
        
    Returns:
        Dictionary of metrics
    """
    # Generate predictions
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_proba >= 0.5).astype(int)
    
    # Calculate metrics
    auc_score = roc_auc_score(y_test, y_pred_proba)
    brier = brier_score_loss(y_test, y_pred_proba)
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    
    metrics = {
        'auc_roc': float(auc_score),
        'brier_score': float(brier),
        'accuracy': float((tp + tn) / (tp + tn + fp + fn)),
        'precision': float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0,
        'recall': float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0,
        'true_positives': int(tp),
        'true_negatives': int(tn),
        'false_positives': int(fp),
        'false_negatives': int(fn)
    }
    
    print(f"AUC-ROC: {metrics['auc_roc']:.4f}")
    print(f"Brier Score: {metrics['brier_score']:.4f}")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    
    return metrics


def save_model(
    model: LogisticRegression,
    scaler: StandardScaler,
    metrics: Dict[str, float],
    output_dir: str,
    n_train: int,
    n_test: int,
    train_no_show_rate: float,
    test_no_show_rate: float
) -> None:
    """
    Save model artifacts to disk.
    
    Args:
        model: Trained model
        scaler: Fitted scaler
        metrics: Evaluation metrics
        output_dir: Directory to save artifacts
        n_train: Number of training samples
        n_test: Number of test samples
        train_no_show_rate: No-show rate in training data
        test_no_show_rate: No-show rate in test data
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Save model and scaler
    model_path = os.path.join(output_dir, 'model.joblib')
    scaler_path = os.path.join(output_dir, 'scaler.joblib')
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    
    # Save full metrics
    full_metrics = {
        **metrics,
        'training_samples': n_train,
        'test_samples': n_test,
        'features': FEATURES,
        'model_type': 'LogisticRegression',
        'trained_at': datetime.now().isoformat(),
        'no_show_rate_train': train_no_show_rate,
        'no_show_rate_test': test_no_show_rate
    }
    
    metrics_path = os.path.join(output_dir, 'metrics.json')
    with open(metrics_path, 'w') as f:
        json.dump(full_metrics, f, indent=2)
    
    # Save feature config
    feature_config = {
        'features': FEATURES,
        'target': TARGET,
        'prediction_threshold': 0.7
    }
    config_path = os.path.join(output_dir, 'feature_config.json')
    with open(config_path, 'w') as f:
        json.dump(feature_config, f, indent=2)
    
    print(f"Model artifacts saved to: {output_dir}")


def main(
    data_path: str,
    output_dir: str,
    test_size: float = 0.2,
    random_state: int = 42,
    model_params: Dict[str, Any] = None
) -> Dict[str, float]:
    """
    Main training function.
    
    Args:
        data_path: Path to training data CSV
        output_dir: Directory to save model artifacts
        test_size: Fraction of data for testing
        random_state: Random seed
        model_params: Optional model hyperparameters
        
    Returns:
        Dictionary of evaluation metrics
    """
    # Load data
    df = load_data(data_path)
    
    # Prepare data
    X_train, X_test, y_train, y_test, scaler = prepare_data(
        df, test_size, random_state
    )
    
    # Train model
    model = train_model(X_train, y_train, model_params)
    
    # Evaluate model
    metrics = evaluate_model(model, X_test, y_test)
    
    # Save artifacts
    save_model(
        model, scaler, metrics, output_dir,
        n_train=len(y_train),
        n_test=len(y_test),
        train_no_show_rate=float(y_train.mean()),
        test_no_show_rate=float(y_test.mean())
    )
    
    return metrics


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Train no-show prediction model')
    parser.add_argument('--data-path', type=str, required=True,
                        help='Path to training data CSV')
    parser.add_argument('--output-dir', type=str, default='./outputs',
                        help='Directory to save model artifacts')
    parser.add_argument('--test-size', type=float, default=0.2,
                        help='Fraction of data for testing')
    parser.add_argument('--random-state', type=int, default=42,
                        help='Random seed')
    
    args = parser.parse_args()
    
    metrics = main(
        data_path=args.data_path,
        output_dir=args.output_dir,
        test_size=args.test_size,
        random_state=args.random_state
    )
    
    print("\nTraining complete!")
    print(f"AUC-ROC: {metrics['auc_roc']:.4f}")
