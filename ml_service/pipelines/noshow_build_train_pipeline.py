"""
Azure ML Training Pipeline Builder for No-Show Prediction
==========================================================
This script creates and publishes the training pipeline in Azure ML.
The pipeline performs: data preparation → training → evaluation → registration.

Following MLOpsPython template: https://github.com/microsoft/MLOpsPython
"""

import os
import sys
import argparse
from azure.ai.ml import MLClient, Input, Output, command, dsl
from azure.ai.ml.entities import (
    Environment,
    BuildContext,
    AmlCompute,
    Data,
    Model
)
from azure.ai.ml.constants import AssetTypes, InputOutputModes
from azure.identity import DefaultAzureCredential


def get_workspace_config() -> dict:
    """Get workspace configuration from environment variables."""
    return {
        'subscription_id': os.getenv('SUBSCRIPTION_ID'),
        'resource_group': os.getenv('RESOURCE_GROUP'),
        'workspace_name': os.getenv('WORKSPACE_NAME'),
    }


def get_ml_client() -> MLClient:
    """Create ML client from environment configuration."""
    config = get_workspace_config()
    credential = DefaultAzureCredential()
    
    return MLClient(
        credential=credential,
        subscription_id=config['subscription_id'],
        resource_group_name=config['resource_group'],
        workspace_name=config['workspace_name']
    )


def get_or_create_compute(ml_client: MLClient, compute_name: str) -> str:
    """Get or create compute cluster for training."""
    try:
        compute = ml_client.compute.get(compute_name)
        print(f"Using existing compute: {compute_name}")
    except Exception:
        print(f"Creating compute cluster: {compute_name}")
        compute = AmlCompute(
            name=compute_name,
            size="STANDARD_DS3_v2",
            min_instances=0,
            max_instances=2,
            idle_time_before_scale_down=300
        )
        ml_client.compute.begin_create_or_update(compute).result()
    
    return compute_name


def get_environment(ml_client: MLClient, env_name: str) -> Environment:
    """Get or create training environment."""
    try:
        env = ml_client.environments.get(env_name, label="latest")
        print(f"Using existing environment: {env_name}")
    except Exception:
        print(f"Creating environment: {env_name}")
        conda_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "noshow_prediction",
            "conda_dependencies.yml"
        )
        env = Environment(
            name=env_name,
            image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu20.04:latest",
            conda_file=conda_file,
            description="Environment for no-show prediction training"
        )
        env = ml_client.environments.create_or_update(env)
    
    return env


def create_train_step(env: Environment, compute_name: str):
    """Create training step component."""
    
    @command(
        display_name="Train No-Show Model",
        description="Train logistic regression model for no-show prediction",
        environment=env,
        compute=compute_name,
        code="../noshow_prediction/training",
    )
    def train_step(
        data_path: Input(type=AssetTypes.URI_FILE),
        output_dir: Output(type=AssetTypes.URI_FOLDER),
        test_size: float = 0.2,
        random_state: int = 42
    ):
        return f"""
        python train_aml.py \
            --data-path ${{inputs.data_path}} \
            --output-dir ${{outputs.output_dir}} \
            --test-size {test_size} \
            --random-state {random_state}
        """
    
    return train_step


def create_evaluate_step(env: Environment, compute_name: str):
    """Create evaluation step component."""
    
    @command(
        display_name="Evaluate Model",
        description="Evaluate and compare model performance",
        environment=env,
        compute=compute_name,
        code="../noshow_prediction/evaluate",
    )
    def evaluate_step(
        model_dir: Input(type=AssetTypes.URI_FOLDER),
        evaluation_output: Output(type=AssetTypes.URI_FOLDER)
    ):
        return f"""
        python evaluate_model.py \
            --new-model-dir ${{inputs.model_dir}} \
            --output-file ${{outputs.evaluation_output}}/evaluation_result.json
        """
    
    return evaluate_step


@dsl.pipeline(
    name="noshow-training-pipeline",
    description="End-to-end training pipeline for no-show prediction model",
    default_compute="cpu-cluster"
)
def noshow_training_pipeline(
    training_data: Input,
    test_size: float = 0.2,
    random_state: int = 42
):
    """
    Create the training pipeline.
    
    Pipeline steps:
    1. Train model
    2. Evaluate model
    
    Args:
        training_data: Path to training data
        test_size: Test split ratio
        random_state: Random seed
    """
    # Training step
    train_job = train_step(
        data_path=training_data,
        test_size=test_size,
        random_state=random_state
    )
    
    # Evaluation step
    evaluate_job = evaluate_step(
        model_dir=train_job.outputs.output_dir
    )
    
    return {
        "model_output": train_job.outputs.output_dir,
        "evaluation_output": evaluate_job.outputs.evaluation_output
    }


def main():
    """Build and publish training pipeline."""
    
    parser = argparse.ArgumentParser(description='Build no-show training pipeline')
    parser.add_argument('--compute-name', type=str, default='cpu-cluster',
                        help='Compute cluster name')
    parser.add_argument('--env-name', type=str, default='noshow-training-env',
                        help='Environment name')
    parser.add_argument('--dataset-name', type=str, default='noshow-appointments-kaggle',
                        help='Training dataset name')
    parser.add_argument('--publish', action='store_true',
                        help='Publish pipeline after building')
    
    args = parser.parse_args()
    
    print("=== Building No-Show Training Pipeline ===")
    
    # Get ML client
    ml_client = get_ml_client()
    print(f"Connected to workspace: {ml_client.workspace_name}")
    
    # Get/create compute
    compute_name = get_or_create_compute(ml_client, args.compute_name)
    
    # Get/create environment
    env = get_environment(ml_client, args.env_name)
    
    # Get dataset
    try:
        dataset = ml_client.data.get(args.dataset_name, label="latest")
        print(f"Using dataset: {dataset.name} v{dataset.version}")
        data_input = Input(type=AssetTypes.URI_FILE, path=dataset.path)
    except Exception as e:
        print(f"Warning: Dataset not found, using default path: {e}")
        data_input = Input(
            type=AssetTypes.URI_FILE,
            path="azureml://datastores/workspaceblobstore/paths/data/KaggleV2-May-2016.csv"
        )
    
    # Build pipeline
    print("\nBuilding pipeline...")
    pipeline = noshow_training_pipeline(
        training_data=data_input
    )
    
    # Submit or publish
    if args.publish:
        print("\nPublishing pipeline...")
        published_pipeline = ml_client.jobs.create_or_update(pipeline)
        print(f"Pipeline published: {published_pipeline.name}")
    else:
        print("\nSubmitting pipeline job...")
        pipeline_job = ml_client.jobs.create_or_update(pipeline)
        print(f"Pipeline job submitted: {pipeline_job.name}")
        print(f"Monitor at: {pipeline_job.studio_url}")
    
    print("\n=== Pipeline Build Complete ===")


if __name__ == '__main__':
    main()
