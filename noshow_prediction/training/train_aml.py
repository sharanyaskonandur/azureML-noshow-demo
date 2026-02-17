"""
Azure ML Entry Script for Training Pipeline
============================================
This script is the entry point for Azure ML pipeline steps.
It invokes the training functions from train.py and handles
Azure ML logging and data assets.

Following MLOpsPython template: https://github.com/microsoft/MLOpsPython
"""

import os
import sys
import json
import argparse
import mlflow
from azureml.core import Run

# Add paths for imports - works from both repo root and training directory
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)  # For direct train.py imports
sys.path.insert(0, os.path.dirname(script_dir))  # For noshow_prediction package

from train import (
    load_data,
    prepare_data,
    train_model,
    evaluate_model,
    save_model,
    FEATURES,
    TARGET
)


def load_parameters(parameters_file: str) -> dict:
    """
    Load training parameters from JSON file.
    
    Args:
        parameters_file: Path to parameters.json
        
    Returns:
        Dictionary of parameters
    """
    if os.path.exists(parameters_file):
        with open(parameters_file, 'r') as f:
            return json.load(f)
    return {}


def main():
    """Main entry point for Azure ML training step."""
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='Train no-show prediction model in Azure ML')
    parser.add_argument('--data-path', type=str, required=True,
                        help='Path to training data (CSV or Azure ML Dataset mount)')
    parser.add_argument('--output-dir', type=str, default='./outputs',
                        help='Directory to save model artifacts')
    parser.add_argument('--parameters-file', type=str, default='parameters.json',
                        help='Path to training parameters JSON')
    parser.add_argument('--test-size', type=float, default=0.2,
                        help='Test split ratio')
    parser.add_argument('--random-state', type=int, default=42,
                        help='Random seed')
    
    args = parser.parse_args()
    
    # Get Azure ML run context
    run = Run.get_context()
    is_offline = run.id.startswith('OfflineRun')
    
    if not is_offline:
        print(f"Azure ML Run ID: {run.id}")
        mlflow.start_run()
    
    # Load parameters
    params = load_parameters(args.parameters_file)
    test_size = params.get('test_size', args.test_size)
    random_state = params.get('random_state', args.random_state)
    model_params = params.get('model_params', {
        'max_iter': 1000,
        'class_weight': 'balanced',
        'random_state': random_state,
        'solver': 'lbfgs'
    })
    
    print(f"Parameters: test_size={test_size}, random_state={random_state}")
    
    # Handle data path (could be file or mounted dataset)
    data_path = args.data_path
    if os.path.isdir(data_path):
        # If it's a directory (mounted dataset), look for CSV files
        csv_files = [f for f in os.listdir(data_path) if f.endswith('.csv')]
        if csv_files:
            data_path = os.path.join(args.data_path, csv_files[0])
            print(f"Found CSV in mounted dataset: {data_path}")
    
    # Load and prepare data
    print("\n=== Loading Data ===")
    df = load_data(data_path)
    
    print("\n=== Preparing Features ===")
    X_train, X_test, y_train, y_test, scaler = prepare_data(
        df, test_size, random_state
    )
    
    # Log data statistics
    if not is_offline:
        run.log('training_samples', len(y_train))
        run.log('test_samples', len(y_test))
        run.log('no_show_rate_train', float(y_train.mean()))
        run.log('no_show_rate_test', float(y_test.mean()))
        run.log('features_count', len(FEATURES))
    
    # Train model
    print("\n=== Training Model ===")
    model = train_model(X_train, y_train, model_params)
    
    # Evaluate model
    print("\n=== Evaluating Model ===")
    metrics = evaluate_model(model, X_test, y_test)
    
    # Log metrics to Azure ML
    if not is_offline:
        for metric_name, metric_value in metrics.items():
            if isinstance(metric_value, (int, float)):
                run.log(metric_name, metric_value)
                mlflow.log_metric(metric_name, metric_value)
        
        # Log parameters
        mlflow.log_param('test_size', test_size)
        mlflow.log_param('random_state', random_state)
        mlflow.log_param('model_type', 'LogisticRegression')
        mlflow.log_param('features', ','.join(FEATURES))
    
    # Print metrics summary
    print("\n=== Metrics Summary ===")
    print(f"AUC-ROC:     {metrics['auc_roc']:.4f}")
    print(f"Brier Score: {metrics['brier_score']:.4f}")
    print(f"Accuracy:    {metrics['accuracy']:.4f}")
    print(f"Precision:   {metrics['precision']:.4f}")
    print(f"Recall:      {metrics['recall']:.4f}")
    
    # Save artifacts
    print("\n=== Saving Artifacts ===")
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)
    
    save_model(
        model, scaler, metrics, output_dir,
        n_train=len(y_train),
        n_test=len(y_test),
        train_no_show_rate=float(y_train.mean()),
        test_no_show_rate=float(y_test.mean())
    )
    
    # Upload artifacts to Azure ML
    if not is_offline:
        # Log model artifacts
        mlflow.sklearn.log_model(model, 'model')
        
        # Upload outputs folder
        for filename in os.listdir(output_dir):
            filepath = os.path.join(output_dir, filename)
            run.upload_file(name=f'outputs/{filename}', path_or_stream=filepath)
        
        mlflow.end_run()
    
    print("\n=== Training Complete ===")
    print(f"Model artifacts saved to: {output_dir}")
    
    return metrics


if __name__ == '__main__':
    main()
