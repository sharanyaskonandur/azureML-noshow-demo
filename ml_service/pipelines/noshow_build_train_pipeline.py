"""
Azure ML Training Job Submitter for No-Show Prediction
=======================================================
Submits a training job to Azure ML compute cluster using:
- Curated sklearn environment (no conda build required)
- Data asset uploaded to workspace blob store
"""

import os
import argparse
from azure.ai.ml import MLClient, command, Input
from azure.ai.ml.entities import AmlCompute
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


def main():
    """Submit training job to Azure ML."""
    parser = argparse.ArgumentParser(description='Submit no-show training job')
    parser.add_argument('--compute-name', type=str, default='cpu-cluster')
    parser.add_argument('--data-asset', type=str, default='noshow-data:1')
    args = parser.parse_args()
    
    print("=== Submitting No-Show Training Job ===")
    
    # Get ML client
    ml_client = get_ml_client()
    print(f"Connected to workspace: {ml_client.workspace_name}")
    
    # Get/create compute
    compute_name = get_or_create_compute(ml_client, args.compute_name)
    
    # Use curated sklearn environment - no build required!
    env_name = "AzureML-sklearn-1.0-ubuntu20.04-py38-cpu:latest"
    print(f"Using curated environment: {env_name}")
    
    # Get code path
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    code_path = os.path.join(repo_root, "noshow_prediction", "training")
    
    # Create training job using registered data asset
    print("\nSubmitting training job...")
    job = command(
        display_name="noshow-training-job",
        description="Train no-show prediction model",
        compute=compute_name,
        environment=env_name,
        code=code_path,
        command="python train.py --data-path ${{inputs.data}} --output-dir ./outputs",
        inputs={
            "data": Input(type=AssetTypes.URI_FILE, path=f"azureml:{args.data_asset}")
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
    
    # Register model from job outputs
    print("\nRegistering model...")
    model_name = "noshow-logreg"
    
    from azure.ai.ml.entities import Model
    model = Model(
        path=f"azureml://jobs/{submitted_job.name}/outputs/artifacts/paths/outputs/",
        name=model_name,
        type="custom_model",
        description=f"Trained from job {submitted_job.name}"
    )
    registered_model = ml_client.models.create_or_update(model)
    print(f"Model registered: {registered_model.name} v{registered_model.version}")
    
    print("\n=== Training Job Complete ===")


if __name__ == '__main__':
    main()
