"""
Environment Variables Configuration
===================================
Utility for loading environment configuration for Azure ML.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class MLEnvironmentConfig:
    """Azure ML environment configuration."""
    subscription_id: str
    resource_group: str
    workspace_name: str
    compute_name: str = "cpu-cluster"
    dataset_name: str = "noshow-appointments-kaggle"
    model_name: str = "noshow-logreg"
    endpoint_name: str = "noshow-online-endpoint"
    

def get_environment_config() -> MLEnvironmentConfig:
    """
    Load configuration from environment variables.
    
    Required env vars:
        SUBSCRIPTION_ID
        RESOURCE_GROUP
        WORKSPACE_NAME
        
    Optional env vars:
        COMPUTE_NAME
        DATASET_NAME
        MODEL_NAME
        ENDPOINT_NAME
    """
    required = ['SUBSCRIPTION_ID', 'RESOURCE_GROUP', 'WORKSPACE_NAME']
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        raise ValueError(f"Missing required environment variables: {missing}")
    
    return MLEnvironmentConfig(
        subscription_id=os.environ['SUBSCRIPTION_ID'],
        resource_group=os.environ['RESOURCE_GROUP'],
        workspace_name=os.environ['WORKSPACE_NAME'],
        compute_name=os.getenv('COMPUTE_NAME', 'cpu-cluster'),
        dataset_name=os.getenv('DATASET_NAME', 'noshow-appointments-kaggle'),
        model_name=os.getenv('MODEL_NAME', 'noshow-logreg'),
        endpoint_name=os.getenv('ENDPOINT_NAME', 'noshow-online-endpoint'),
    )


def print_config():
    """Print current configuration."""
    try:
        config = get_environment_config()
        print("Azure ML Configuration:")
        print(f"  Subscription: {config.subscription_id}")
        print(f"  Resource Group: {config.resource_group}")
        print(f"  Workspace: {config.workspace_name}")
        print(f"  Compute: {config.compute_name}")
        print(f"  Dataset: {config.dataset_name}")
        print(f"  Model: {config.model_name}")
        print(f"  Endpoint: {config.endpoint_name}")
    except ValueError as e:
        print(f"Configuration error: {e}")


if __name__ == '__main__':
    print_config()
