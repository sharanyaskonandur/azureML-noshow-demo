"""
Kaggle Medical Appointment No-Show Data Preparation
====================================================
Downloads and prepares the Kaggle dataset for the Azure ML demo.

Dataset: https://www.kaggle.com/datasets/joniarroba/noshowappointments
File: KaggleV2-May-2016.csv (110,527 records)

Usage:
    1. Download KaggleV2-May-2016.csv from Kaggle
    2. Place in this folder (data/)
    3. Run: python prepare_kaggle_data.py
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

# Input/output paths
INPUT_FILE = "KaggleV2-May-2016.csv"
OUTPUT_FILE = "appointments_silver.csv"
OUTPUT_PARQUET = "appointments_silver.parquet"


def load_and_clean_kaggle_data(filepath: str) -> pd.DataFrame:
    """Load and clean the Kaggle no-show dataset."""
    
    print(f"📂 Loading {filepath}...")
    df = pd.read_csv(filepath)
    
    print(f"   Raw records: {len(df):,}")
    print(f"   Columns: {list(df.columns)}")
    
    # Standardize column names (lowercase, underscores)
    df.columns = df.columns.str.lower().str.replace('-', '_')
    
    # Parse dates
    df['scheduledday'] = pd.to_datetime(df['scheduledday'])
    df['appointmentday'] = pd.to_datetime(df['appointmentday'])
    
    # Calculate lead_time_days (days between scheduling and appointment)
    df['lead_time_days'] = (df['appointmentday'] - df['scheduledday']).dt.days
    # Cap negative values (data quality - appointment before scheduling)
    df['lead_time_days'] = df['lead_time_days'].clip(lower=0)
    
    # Extract time features
    df['day_of_week'] = df['appointmentday'].dt.dayofweek  # 0=Monday
    df['hour_of_day'] = df['scheduledday'].dt.hour  # Hour when scheduled
    
    # Convert target: "No" means they showed up, "Yes" means no-show
    # We want 1 = no-show (positive class for risk prediction)
    df['no_show'] = (df['no_show'] == 'Yes').astype(int)
    
    # Clean age (remove negative values)
    df['age'] = df['age'].clip(lower=0, upper=115)
    
    # Create chronic_conditions count (sum of health indicators)
    df['chronic_conditions'] = (
        df['hipertension'].astype(int) + 
        df['diabetes'].astype(int) + 
        df['alcoholism'].astype(int)
    )
    
    # Rename for consistency with our model features
    df = df.rename(columns={
        'handcap': 'handicap',
        'sms_received': 'sms_reminder'
    })
    
    print(f"✅ Cleaned {len(df):,} records")
    return df


def create_feature_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Create the feature dataset for ML training."""
    
    # Select and order features for ML
    feature_cols = [
        'patientid',
        'appointmentid',
        'gender',
        'age',
        'neighbourhood',
        'scholarship',
        'hipertension',
        'diabetes',
        'alcoholism',
        'handicap',
        'sms_reminder',
        'chronic_conditions',
        'lead_time_days',
        'day_of_week',
        'hour_of_day',
        'scheduledday',
        'appointmentday',
        'no_show'  # Target
    ]
    
    df_features = df[feature_cols].copy()
    
    # Print feature statistics
    print("\n📊 Feature Statistics:")
    print(f"   No-show rate: {df_features['no_show'].mean():.1%}")
    print(f"   Age range: {df_features['age'].min()} - {df_features['age'].max()}")
    print(f"   Lead time: {df_features['lead_time_days'].median():.0f} days (median)")
    print(f"   SMS reminder rate: {df_features['sms_reminder'].mean():.1%}")
    print(f"   Neighborhoods: {df_features['neighbourhood'].nunique()}")
    
    return df_features


def main():
    """Main processing pipeline."""
    
    print("=" * 60)
    print("Kaggle No-Show Data Preparation")
    print("=" * 60)
    
    # Check input file exists
    if not os.path.exists(INPUT_FILE):
        print(f"\n❌ ERROR: {INPUT_FILE} not found!")
        print("\nTo download:")
        print("1. Go to: https://www.kaggle.com/datasets/joniarroba/noshowappointments")
        print("2. Click 'Download' (requires Kaggle account)")
        print("3. Extract KaggleV2-May-2016.csv to this folder")
        print(f"\nOr use kaggle CLI:")
        print(f"   kaggle datasets download joniarroba/noshowappointments")
        print(f"   unzip noshowappointments.zip")
        return
    
    # Load and clean
    df = load_and_clean_kaggle_data(INPUT_FILE)
    
    # Create feature dataset
    df_features = create_feature_dataset(df)
    
    # Save outputs
    print(f"\n💾 Saving to {OUTPUT_FILE}...")
    df_features.to_csv(OUTPUT_FILE, index=False)
    
    print(f"💾 Saving to {OUTPUT_PARQUET}...")
    df_features.to_parquet(OUTPUT_PARQUET, index=False)
    
    print("\n✅ Done! Files created:")
    print(f"   - {OUTPUT_FILE}")
    print(f"   - {OUTPUT_PARQUET}")
    print("\nNext: Open notebooks/01_train_noshow_model.ipynb and run it!")


if __name__ == "__main__":
    main()
