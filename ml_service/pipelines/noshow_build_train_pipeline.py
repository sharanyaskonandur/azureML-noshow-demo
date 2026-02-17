"""
Azure ML Training Job Submitter for No-Show Prediction
=======================================================
Submits a training job to Azure ML compute cluster.
"""

import os
import argparse
from azure.ai.ml import MLClient, command, Input
from azure.ai.ml.entities import Environment, AmlCompute
from azure.ai.ml.constants import AssetTypes
from azure.identity import DefaultAzureCredential


def get_ml_client() -> MLClient:
    """Create ML client from environment configuration."""
    credential = DefaultAzureCredential()
    return MLClient(
        credential=credential,
        subscription_id=os.getenv('SUBSCRIPTION_ID'),
        resource_group_name=os.getenv('RESOURCE_GROUP'),
        workspace_name=os.getenv('WORKSPACE_NAME')
    )


def get_or_create_compute(ml_client: MLClient, compute_name: str) -> str:
    """Get or create compute cluster for training."""
    try:
        ml_client.compute.get(compute_name)
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


def get_environment(ml_client: MLClient, env_name: str) -> str:
    """Always create new environment version to pick up conda changes."""
    print(f"Creating/updating environment: {env_name}")
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    conda_file = os.path.join(repo_root, "noshow_prediction", "conda_dependencies.yml")
    
    env = Environment(
        name=env_name,
        image="mcr.microsoft.com/azureml/openmpi4.1.0-ubuntu20.04:latest",
        conda_file=conda_file,
        description="Environment for no-show prediction training"
    )
    env = ml_client.environments.create_or_update(env)
    print(f"Using environment: {env.name}:{env.version}")
    return f"{env.name}:{env.version}"


def main():
    """Submit training job to Azure ML."""
    parser = argparse.ArgumentParser(description='Submit no-show training job')
    parser.add_argument('--compute-name', type=str, default='cpu-cluster')
    parser.add_argument('--env-name', type=str, default='noshow-training-env')
    parser.add_argument('--dataset-name', type=str, default='noshow-appointments-kaggle')
    args = parser.parse_args()
    
    print("=== Submitting No-Show Training Job ===")
    
    # Get ML client
    ml_client = get_ml_client()
    print(f"Connected to workspace: {ml_client.workspace_name}")
    
    # Get/create compute
    compute_name = get_or_create_compute(ml_client, args.compute_name)
    
    # Get/create environment
    env_id = get_environment(ml_client, args.env_name)
    
    # Get dataset path
    try:
        dataset = ml_client.data.get(args.dataset_name, label="latest")
        print(f"Using dataset: {dataset.name} v{dataset.version}")
        data_path = dataset.path
    except Exception as e:
        print(f"Dataset not found, using default path: {e}")
        data_path = "azureml://datastores/workspaceblobstore/paths/data/KaggleV2-May-2016.csv"
    
    # Get code path
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    code_path = os.path.join(repo_root, "noshow_prediction", "training")
    
    # Create training job
    print("\nSubmitting training job...")
    job = command(
        display_name="noshow-training-job",
        description="Train no-show prediction model",
        compute=compute_name,
        environment=env_id,
        code=code_path,
        command="python train_aml.py --data-path ${{inputs.data}} --output-dir ${{outputs.model}}",
        inputs={
            "data": Input(type=AssetTypes.URI_FILE, path=data_path)
        },
        outputs={
            "model": {"type": "uri_folder", "mode": "rw_mount"}
        },
        experiment_name="noshow-training"
    )
    
    # Submit job
    submitted_job = ml_client.jobs.create_or_update(job)
    print(f"Job submitted: {submitted_job.name}")
    print(f"Monitor at: {submitted_job.studio_url}")
    
    # Wait for completion
    print("\nWaiting for job to complete...")
    ml_client.jobs.stream(submitted_job.name)
    
    print("\n=== Training Job Complete ===")


if __name__ == '__main__':
    main()
