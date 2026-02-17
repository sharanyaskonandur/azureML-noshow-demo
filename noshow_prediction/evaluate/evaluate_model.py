"""
Model Evaluation Script for No-Show Prediction
===============================================
This script compares the performance of a newly trained model
against the current production model to determine if the new
model should be deployed.

Following MLOpsPython template: https://github.com/microsoft/MLOpsPython
"""

import os
import sys
import json
import argparse
import joblib
import pandas as pd
import numpy as np
from sklearn.metrics import roc_auc_score, brier_score_loss
from typing import Tuple, Optional


# Add parent for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from training.train import FEATURES, TARGET


def load_model_and_scaler(model_dir: str) -> Tuple:
    """
    Load model and scaler from directory.
    
    Args:
        model_dir: Directory containing model.joblib and scaler.joblib
        
    Returns:
        (model, scaler) tuple
    """
    model_path = os.path.join(model_dir, 'model.joblib')
    scaler_path = os.path.join(model_dir, 'scaler.joblib')
    
    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    
    return model, scaler


def load_metrics(model_dir: str) -> dict:
    """
    Load metrics from model directory.
    
    Args:
        model_dir: Directory containing metrics.json
        
    Returns:
        Metrics dictionary
    """
    metrics_path = os.path.join(model_dir, 'metrics.json')
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r') as f:
            return json.load(f)
    return {}


def evaluate_on_test_data(
    model,
    scaler,
    test_data: pd.DataFrame
) -> dict:
    """
    Evaluate model on test dataset.
    
    Args:
        model: Trained model
        scaler: Fitted scaler
        test_data: DataFrame with features and target
        
    Returns:
        Dictionary of metrics
    """
    X = test_data[FEATURES].fillna(0)
    y = test_data[TARGET].astype(int)
    
    X_scaled = scaler.transform(X)
    y_pred_proba = model.predict_proba(X_scaled)[:, 1]
    
    return {
        'auc_roc': float(roc_auc_score(y, y_pred_proba)),
        'brier_score': float(brier_score_loss(y, y_pred_proba)),
        'samples': len(y)
    }


def compare_models(
    new_model_metrics: dict,
    production_model_metrics: dict,
    metric_name: str = 'auc_roc',
    threshold: float = 0.0
) -> Tuple[bool, str]:
    """
    Compare new model against production model.
    
    Args:
        new_model_metrics: Metrics from newly trained model
        production_model_metrics: Metrics from current production model
        metric_name: Primary metric for comparison (higher is better)
        threshold: Minimum improvement required
        
    Returns:
        (should_deploy, reason) tuple
    """
    new_metric = new_model_metrics.get(metric_name, 0)
    prod_metric = production_model_metrics.get(metric_name, 0)
    
    improvement = new_metric - prod_metric
    
    if new_metric >= prod_metric + threshold:
        reason = (
            f"New model ({new_metric:.4f}) outperforms production "
            f"({prod_metric:.4f}) by {improvement:.4f}"
        )
        return True, reason
    else:
        reason = (
            f"New model ({new_metric:.4f}) does not significantly "
            f"outperform production ({prod_metric:.4f}). "
            f"Improvement: {improvement:.4f}, Required: {threshold}"
        )
        return False, reason


def main():
    """Main evaluation function."""
    
    parser = argparse.ArgumentParser(description='Evaluate model for deployment')
    parser.add_argument('--new-model-dir', type=str, required=True,
                        help='Directory containing new model artifacts')
    parser.add_argument('--production-model-dir', type=str, default=None,
                        help='Directory containing production model artifacts')
    parser.add_argument('--test-data', type=str, default=None,
                        help='Path to test data for evaluation')
    parser.add_argument('--metric', type=str, default='auc_roc',
                        help='Primary metric for comparison')
    parser.add_argument('--threshold', type=float, default=0.0,
                        help='Minimum improvement threshold')
    parser.add_argument('--output-file', type=str, default='evaluation_result.json',
                        help='Output file for evaluation results')
    
    args = parser.parse_args()
    
    print("=== Model Evaluation ===")
    
    # Load new model metrics
    new_metrics = load_metrics(args.new_model_dir)
    print(f"\nNew model metrics:")
    print(f"  AUC-ROC: {new_metrics.get('auc_roc', 'N/A')}")
    print(f"  Brier:   {new_metrics.get('brier_score', 'N/A')}")
    
    # Load production model metrics if available
    if args.production_model_dir and os.path.exists(args.production_model_dir):
        prod_metrics = load_metrics(args.production_model_dir)
        print(f"\nProduction model metrics:")
        print(f"  AUC-ROC: {prod_metrics.get('auc_roc', 'N/A')}")
        print(f"  Brier:   {prod_metrics.get('brier_score', 'N/A')}")
    else:
        # No production model - first deployment
        prod_metrics = {'auc_roc': 0, 'brier_score': 1.0}
        print("\nNo production model found - first deployment")
    
    # Optional: Evaluate on fresh test data
    if args.test_data and os.path.exists(args.test_data):
        print(f"\nEvaluating on test data: {args.test_data}")
        test_df = pd.read_csv(args.test_data)
        
        # Preprocess test data (same as training)
        test_df.columns = test_df.columns.str.lower().str.replace('-', '_')
        test_df['scheduledday'] = pd.to_datetime(test_df['scheduledday'])
        test_df['appointmentday'] = pd.to_datetime(test_df['appointmentday'])
        test_df['lead_time_days'] = (test_df['appointmentday'] - test_df['scheduledday']).dt.days
        test_df['lead_time_days'] = test_df['lead_time_days'].clip(lower=0)
        test_df['day_of_week'] = test_df['appointmentday'].dt.dayofweek
        test_df['chronic_conditions'] = (
            test_df['hipertension'].astype(int) +
            test_df['diabetes'].astype(int) +
            test_df['alcoholism'].astype(int)
        )
        test_df['no_show'] = (test_df['no_show'] == 'Yes').astype(int)
        test_df['age'] = test_df['age'].clip(lower=0, upper=115)
        
        new_model, new_scaler = load_model_and_scaler(args.new_model_dir)
        new_metrics = evaluate_on_test_data(new_model, new_scaler, test_df)
        print(f"  Fresh evaluation AUC-ROC: {new_metrics['auc_roc']:.4f}")
    
    # Compare models
    print("\n=== Comparison ===")
    should_deploy, reason = compare_models(
        new_metrics,
        prod_metrics,
        metric_name=args.metric,
        threshold=args.threshold
    )
    
    print(f"Decision: {'DEPLOY' if should_deploy else 'SKIP'}")
    print(f"Reason: {reason}")
    
    # Save evaluation result
    result = {
        'should_deploy': should_deploy,
        'reason': reason,
        'new_model_metrics': new_metrics,
        'production_model_metrics': prod_metrics,
        'comparison_metric': args.metric,
        'threshold': args.threshold
    }
    
    with open(args.output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nEvaluation saved to: {args.output_file}")
    
    # Exit with appropriate code
    sys.exit(0 if should_deploy else 1)


if __name__ == '__main__':
    main()
