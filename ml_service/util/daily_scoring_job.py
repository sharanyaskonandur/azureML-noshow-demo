"""
Daily Batch Scoring Job Scheduler
=================================
This script can be scheduled (Azure Logic Apps, Azure Data Factory, or Fabric Pipeline)
to invoke the batch endpoint daily at 6am.

For Edwin's Power BI dashboard: Lakehouse → Score → Lakehouse → Power BI
"""

import os
from datetime import datetime, timedelta
from azure.identity import DefaultAzureCredential
from azure.ai.ml import MLClient
from azure.ai.ml.entities import BatchEndpoint

# Configuration
SUBSCRIPTION_ID = "8a7af4dd-523e-4175-b231-d31d36752280"
RESOURCE_GROUP = "rg-ai-hub-citadel-dev-02"
WORKSPACE_NAME = "AI-WORKSPACE-shark"
BATCH_ENDPOINT_NAME = "noshow-batch-endpoint"

# Fabric Lakehouse paths (OneLake)
LAKEHOUSE_BASE = "https://onelake.dfs.fabric.microsoft.com"
WORKSPACE_ID = "your-fabric-workspace-guid"
LAKEHOUSE_NAME = "your-lakehouse-name"

def get_tomorrow_date():
    """Get tomorrow's date for file naming."""
    return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")


def invoke_daily_scoring():
    """
    Invoke batch endpoint to score tomorrow's appointments.
    
    Flow:
    1. Read appointments from Fabric Lakehouse
    2. Score with Azure ML batch endpoint
    3. Write predictions back to Lakehouse
    4. Power BI refreshes and shows results
    """
    
    # Connect to Azure ML
    credential = DefaultAzureCredential()
    ml_client = MLClient(credential, SUBSCRIPTION_ID, RESOURCE_GROUP, WORKSPACE_NAME)
    
    tomorrow = get_tomorrow_date()
    
    # Input: Tomorrow's appointments from Fabric Lakehouse
    input_path = f"{LAKEHOUSE_BASE}/{WORKSPACE_ID}/{LAKEHOUSE_NAME}.Lakehouse/Files/appointments/{tomorrow}.parquet"
    
    # Output: Predictions folder in Lakehouse
    output_path = f"{LAKEHOUSE_BASE}/{WORKSPACE_ID}/{LAKEHOUSE_NAME}.Lakehouse/Files/predictions/{tomorrow}/"
    
    print(f"🚀 Starting daily scoring for {tomorrow}")
    print(f"   Input:  {input_path}")
    print(f"   Output: {output_path}")
    
    # Invoke the batch endpoint
    job = ml_client.batch_endpoints.invoke(
        endpoint_name=BATCH_ENDPOINT_NAME,
        input=input_path,
        output_path=output_path
    )
    
    print(f"✅ Batch job submitted: {job.name}")
    print(f"   Monitor at: https://ml.azure.com")
    
    return job


def main():
    """Main entry point for scheduled execution."""
    print(f"📅 Daily scoring job started at {datetime.now().isoformat()}")
    
    try:
        job = invoke_daily_scoring()
        print(f"✅ Job submitted successfully")
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
