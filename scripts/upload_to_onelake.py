"""
Upload Data to OneLake (Microsoft Fabric Lakehouse)
====================================================
This script uploads the Kaggle no-show dataset to OneLake for the demo.

Prerequisites:
1. Fabric workspace with Lakehouse
2. Azure CLI logged in (az login)
3. Service Principal or user with Fabric access

Usage:
    python upload_to_onelake.py --workspace "YourWorkspace" --lakehouse "YourLakehouse"
"""

import os
import sys
import argparse
import pandas as pd
from datetime import datetime

# Try to import Azure Data Lake Storage Gen2 client
try:
    from azure.identity import DefaultAzureCredential
    from azure.storage.filedatalake import DataLakeServiceClient
except ImportError:
    print("Installing required packages...")
    os.system("pip install azure-identity azure-storage-file-datalake")
    from azure.identity import DefaultAzureCredential
    from azure.storage.filedatalake import DataLakeServiceClient


def get_onelake_client(workspace_id: str):
    """
    Connect to OneLake using Azure credentials.
    
    OneLake endpoint: https://onelake.dfs.fabric.microsoft.com
    """
    credential = DefaultAzureCredential()
    
    # OneLake endpoint
    account_url = "https://onelake.dfs.fabric.microsoft.com"
    
    service_client = DataLakeServiceClient(
        account_url=account_url,
        credential=credential
    )
    
    return service_client


def upload_csv_to_lakehouse(
    service_client: DataLakeServiceClient,
    workspace_id: str,
    lakehouse_name: str,
    local_file_path: str,
    dest_folder: str = "Files/raw"
):
    """
    Upload a CSV file to OneLake Lakehouse.
    
    Args:
        service_client: DataLakeServiceClient instance
        workspace_id: Fabric workspace ID (GUID)
        lakehouse_name: Name of the lakehouse
        local_file_path: Path to local CSV file
        dest_folder: Destination folder in lakehouse (default: Files/raw)
    """
    # Get filesystem client for the workspace
    file_system_client = service_client.get_file_system_client(workspace_id)
    
    # Create directory path: {lakehouse_name}/{dest_folder}
    directory_path = f"{lakehouse_name}.Lakehouse/{dest_folder}"
    directory_client = file_system_client.get_directory_client(directory_path)
    
    # Create directory if not exists
    try:
        directory_client.create_directory()
        print(f"✅ Created directory: {directory_path}")
    except Exception as e:
        if "PathAlreadyExists" in str(e):
            print(f"ℹ️ Directory exists: {directory_path}")
        else:
            print(f"⚠️ Directory issue: {e}")
    
    # Upload file
    file_name = os.path.basename(local_file_path)
    file_client = directory_client.get_file_client(file_name)
    
    print(f"📤 Uploading {file_name}...")
    
    with open(local_file_path, "rb") as f:
        file_client.upload_data(f, overwrite=True)
    
    print(f"✅ Uploaded: {file_name} → {directory_path}/{file_name}")
    
    return f"abfss://{workspace_id}@onelake.dfs.fabric.microsoft.com/{directory_path}/{file_name}"


def prepare_and_upload_kaggle_data(
    workspace_id: str,
    lakehouse_name: str,
    data_path: str = "../data/KaggleV2-May-2016.csv"
):
    """
    Prepare the Kaggle data and upload to OneLake.
    Creates both raw and silver (cleaned) datasets.
    """
    print("=" * 60)
    print("🚀 Uploading No-Show Data to OneLake")
    print("=" * 60)
    
    # Check if data exists
    if not os.path.exists(data_path):
        print(f"❌ Data file not found: {data_path}")
        print("   Run: kaggle datasets download joniarroba/noshowappointments")
        sys.exit(1)
    
    # Connect to OneLake
    print("\n🔐 Connecting to OneLake...")
    service_client = get_onelake_client(workspace_id)
    print("✅ Connected")
    
    # Load and prepare data
    print("\n📂 Loading Kaggle data...")
    df = pd.read_csv(data_path)
    print(f"   Loaded {len(df):,} records")
    
    # Upload raw data
    print("\n📤 Uploading RAW data...")
    raw_path = upload_csv_to_lakehouse(
        service_client,
        workspace_id,
        lakehouse_name,
        data_path,
        dest_folder="Files/raw"
    )
    
    # Prepare silver (cleaned) data
    print("\n🔧 Preparing SILVER data...")
    df.columns = df.columns.str.lower().str.replace('-', '_')
    df['scheduledday'] = pd.to_datetime(df['scheduledday'])
    df['appointmentday'] = pd.to_datetime(df['appointmentday'])
    df['lead_time_days'] = (df['appointmentday'] - df['scheduledday']).dt.days
    df['lead_time_days'] = df['lead_time_days'].clip(lower=0)
    df['day_of_week'] = df['appointmentday'].dt.dayofweek
    df['hour_of_day'] = df['scheduledday'].dt.hour
    df['chronic_conditions'] = df['hipertension'] + df['diabetes'] + df['alcoholism']
    df['no_show'] = (df['no_show'] == 'Yes').astype(int)
    df['age'] = df['age'].clip(lower=0, upper=115)
    
    # Save silver data locally
    silver_path = data_path.replace(".csv", "_silver.parquet")
    df.to_parquet(silver_path, index=False)
    print(f"   Saved silver data locally: {silver_path}")
    
    # Upload silver as parquet
    silver_csv_path = data_path.replace(".csv", "_silver.csv")
    df.to_csv(silver_csv_path, index=False)
    
    print("\n📤 Uploading SILVER data...")
    silver_onelake_path = upload_csv_to_lakehouse(
        service_client,
        workspace_id,
        lakehouse_name,
        silver_csv_path,
        dest_folder="Files/silver/appointments"
    )
    
    print("\n" + "=" * 60)
    print("✅ UPLOAD COMPLETE")
    print("=" * 60)
    print(f"\n📍 OneLake Paths:")
    print(f"   Raw:    {raw_path}")
    print(f"   Silver: {silver_onelake_path}")
    print(f"\n🔗 Access in Fabric:")
    print(f"   1. Go to https://app.fabric.microsoft.com")
    print(f"   2. Open workspace → {lakehouse_name}")
    print(f"   3. Browse Files → raw/ and silver/")
    
    return raw_path, silver_onelake_path


def main():
    parser = argparse.ArgumentParser(description="Upload data to OneLake")
    parser.add_argument("--workspace-id", required=True, help="Fabric Workspace ID (GUID)")
    parser.add_argument("--lakehouse", required=True, help="Lakehouse name")
    parser.add_argument("--data-path", default="../data/KaggleV2-May-2016.csv", help="Path to data file")
    
    args = parser.parse_args()
    
    prepare_and_upload_kaggle_data(
        workspace_id=args.workspace_id,
        lakehouse_name=args.lakehouse,
        data_path=args.data_path
    )


if __name__ == "__main__":
    # Example usage (update with your IDs):
    # python upload_to_onelake.py --workspace-id "abc123-..." --lakehouse "NoShowDemo"
    
    # For quick testing without CLI args:
    if len(sys.argv) == 1:
        print("=" * 60)
        print("OneLake Upload Script")
        print("=" * 60)
        print("\nUsage:")
        print("  python upload_to_onelake.py --workspace-id <GUID> --lakehouse <NAME>")
        print("\nExample:")
        print("  python upload_to_onelake.py --workspace-id \"abc-123-def\" --lakehouse \"NoShowLakehouse\"")
        print("\nTo find your workspace ID:")
        print("  1. Go to https://app.fabric.microsoft.com")
        print("  2. Open your workspace")
        print("  3. Look at the URL: .../groups/<WORKSPACE_ID>/...")
    else:
        main()
