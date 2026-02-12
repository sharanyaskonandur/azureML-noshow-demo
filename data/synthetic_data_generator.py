"""
Synthetic Data Generator for Healthcare No-Show Demo
=====================================================
Generates realistic but fully synthetic patient and appointment data.
NO REAL PHI - Safe for demos and testing.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

np.random.seed(42)
random.seed(42)

def generate_patients(n_patients: int = 5000) -> pd.DataFrame:
    """Generate synthetic patient demographics."""
    
    patient_ids = [f"P{str(i).zfill(6)}" for i in range(1, n_patients + 1)]
    
    # Age distribution (realistic healthcare distribution)
    ages = np.clip(np.random.normal(55, 20, n_patients), 18, 95).astype(int)
    
    # Sex distribution
    sex = np.random.choice(['M', 'F'], n_patients, p=[0.45, 0.55])
    
    # Chronic conditions (0-5, higher for older patients)
    base_conditions = np.random.poisson(1.5, n_patients)
    age_factor = (ages - 40) / 50  # older = more conditions
    chronic_conditions = np.clip(base_conditions + (age_factor * np.random.uniform(0, 2, n_patients)), 0, 8).astype(int)
    
    # Medication count (correlated with conditions)
    medication_count = np.clip(chronic_conditions * np.random.uniform(1, 3, n_patients) + np.random.poisson(1, n_patients), 0, 15).astype(int)
    
    # Insurance type
    insurance_type = np.random.choice(
        ['Basisverzekering', 'Aanvullend', 'Onverzekerd'], 
        n_patients, 
        p=[0.70, 0.25, 0.05]
    )
    
    # Postal code (NL format, fictional)
    postal_codes = [f"{random.randint(1000, 9999)}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}" for _ in range(n_patients)]
    
    return pd.DataFrame({
        'patient_id': patient_ids,
        'age': ages,
        'sex': sex,
        'chronic_conditions': chronic_conditions,
        'medication_count': medication_count,
        'insurance_type': insurance_type,
        'postal_code': postal_codes,
        'registration_date': [datetime(2020, 1, 1) + timedelta(days=random.randint(0, 1500)) for _ in range(n_patients)]
    })


def generate_appointments(patients_df: pd.DataFrame, n_appointments: int = 25000) -> pd.DataFrame:
    """Generate synthetic appointment data with realistic no-show patterns."""
    
    patient_ids = patients_df['patient_id'].tolist()
    patient_ages = patients_df.set_index('patient_id')['age'].to_dict()
    patient_conditions = patients_df.set_index('patient_id')['chronic_conditions'].to_dict()
    
    appointments = []
    
    specialties = ['Huisarts', 'Cardiologie', 'Orthopedie', 'Dermatologie', 'Neurologie', 'Interne Geneeskunde', 'Radiologie']
    specialty_weights = [0.35, 0.15, 0.12, 0.10, 0.10, 0.12, 0.06]
    
    clinics = ['Kliniek Noord', 'Kliniek Zuid', 'Kliniek Centrum', 'Kliniek Oost']
    
    for i in range(n_appointments):
        appt_id = f"A{str(i).zfill(8)}"
        patient_id = random.choice(patient_ids)
        
        # Appointment datetime (last 18 months)
        appt_date = datetime(2024, 7, 1) + timedelta(
            days=random.randint(0, 540),
            hours=random.randint(8, 17),
            minutes=random.choice([0, 15, 30, 45])
        )
        
        specialty = random.choices(specialties, weights=specialty_weights)[0]
        clinic = random.choice(clinics)
        
        # Distance to clinic (km) - affects no-show
        distance_km = np.clip(np.random.exponential(8), 0.5, 50)
        
        # Previous no-shows for this patient (0-5)
        previous_no_shows = min(5, np.random.poisson(0.8))
        
        # Lead time (days between scheduling and appointment)
        lead_time_days = max(1, int(np.random.exponential(14)))
        
        # Day of week (0=Monday, 6=Sunday)
        day_of_week = appt_date.weekday()
        
        # Hour of day
        hour_of_day = appt_date.hour
        
        # Calculate no-show probability based on realistic factors
        base_prob = 0.08  # 8% baseline no-show rate
        
        # Distance factor (further = more no-shows)
        distance_factor = min(0.15, distance_km / 100)
        
        # Previous no-shows factor (strongest predictor)
        history_factor = previous_no_shows * 0.08
        
        # Age factor (very young and very old = slightly more no-shows)
        age = patient_ages.get(patient_id, 50)
        age_factor = 0.03 if age < 25 or age > 80 else 0
        
        # Lead time factor (longer lead time = more no-shows)
        lead_factor = min(0.10, lead_time_days / 150)
        
        # Monday morning / Friday afternoon factor
        time_factor = 0.03 if (day_of_week == 0 and hour_of_day < 10) or (day_of_week == 4 and hour_of_day > 15) else 0
        
        # Weather proxy (winter months slightly higher)
        month = appt_date.month
        weather_factor = 0.02 if month in [11, 12, 1, 2] else 0
        
        no_show_prob = base_prob + distance_factor + history_factor + age_factor + lead_factor + time_factor + weather_factor
        no_show_prob = min(0.60, no_show_prob)  # cap at 60%
        
        no_show = 1 if random.random() < no_show_prob else 0
        
        appointments.append({
            'appointment_id': appt_id,
            'patient_id': patient_id,
            'appointment_datetime': appt_date,
            'specialty': specialty,
            'clinic': clinic,
            'distance_km': round(distance_km, 2),
            'previous_no_shows': previous_no_shows,
            'lead_time_days': lead_time_days,
            'day_of_week': day_of_week,
            'hour_of_day': hour_of_day,
            'no_show': no_show
        })
    
    return pd.DataFrame(appointments)


def generate_multi_condition_risk(patients_df: pd.DataFrame) -> pd.DataFrame:
    """Generate multi-condition risk scores for the second use case."""
    
    risk_data = []
    conditions = ['Diabetes', 'Hypertensie', 'COPD', 'Hartfalen', 'Nierziekte', 'Depressie']
    
    for _, patient in patients_df.iterrows():
        patient_risks = {'patient_id': patient['patient_id']}
        
        # Base risk influenced by age and existing conditions
        base_risk = (patient['age'] / 100) * 0.3 + (patient['chronic_conditions'] / 8) * 0.4
        
        for condition in conditions:
            # Add some randomness but keep it realistic
            risk = np.clip(base_risk + np.random.normal(0, 0.15), 0, 1)
            patient_risks[f'{condition.lower()}_risk'] = round(risk, 3)
        
        # Overall complexity score
        patient_risks['complexity_score'] = round(np.mean([patient_risks[f'{c.lower()}_risk'] for c in conditions]), 3)
        patient_risks['high_risk_flag'] = 1 if patient_risks['complexity_score'] > 0.5 else 0
        
        risk_data.append(patient_risks)
    
    return pd.DataFrame(risk_data)


def save_data(output_dir: str = '.'):
    """Generate and save all synthetic datasets."""
    
    print("🏥 Generating synthetic healthcare data for demo...")
    
    # Generate patients
    print("  → Generating patient demographics...")
    patients_df = generate_patients(5000)
    
    # Generate appointments
    print("  → Generating appointment history...")
    appointments_df = generate_appointments(patients_df, 25000)
    
    # Join for silver layer
    print("  → Creating silver layer (joined data)...")
    appointments_silver = appointments_df.merge(patients_df, on='patient_id', how='left')
    
    # Generate multi-condition risk
    print("  → Generating multi-condition risk scores...")
    multi_condition_df = generate_multi_condition_risk(patients_df)
    
    # Save as parquet (preferred for Fabric)
    print(f"  → Saving to {output_dir}...")
    
    patients_df.to_parquet(f'{output_dir}/patients_silver.parquet', index=False)
    appointments_df.to_parquet(f'{output_dir}/appointments_raw.parquet', index=False)
    appointments_silver.to_parquet(f'{output_dir}/appointments_silver.parquet', index=False)
    multi_condition_df.to_parquet(f'{output_dir}/multi_condition_risk.parquet', index=False)
    
    # Also save as CSV for easy viewing
    patients_df.to_csv(f'{output_dir}/patients_silver.csv', index=False)
    appointments_silver.to_csv(f'{output_dir}/appointments_silver.csv', index=False)
    multi_condition_df.to_csv(f'{output_dir}/multi_condition_risk.csv', index=False)
    
    print("\n✅ Data generation complete!")
    print(f"   Patients: {len(patients_df):,}")
    print(f"   Appointments: {len(appointments_df):,}")
    print(f"   No-show rate: {appointments_df['no_show'].mean():.1%}")
    print(f"   High-risk patients: {multi_condition_df['high_risk_flag'].sum():,}")
    
    return patients_df, appointments_silver, multi_condition_df


if __name__ == "__main__":
    save_data('.')
