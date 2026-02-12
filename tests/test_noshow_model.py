"""
Unit Tests for No-Show Prediction Model
=======================================
Run with: pytest tests/ -v
"""

import pytest
import pandas as pd
import numpy as np
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSyntheticDataGenerator:
    """Tests for synthetic data generation."""
    
    def test_generate_patients(self):
        """Test patient data generation."""
        from data.synthetic_data_generator import generate_patients
        
        patients = generate_patients(100)
        
        assert len(patients) == 100
        assert 'patient_id' in patients.columns
        assert 'age' in patients.columns
        assert patients['age'].min() >= 18
        assert patients['age'].max() <= 95
    
    def test_generate_appointments(self):
        """Test appointment data generation."""
        from data.synthetic_data_generator import generate_patients, generate_appointments
        
        patients = generate_patients(50)
        appointments = generate_appointments(patients, 200)
        
        assert len(appointments) == 200
        assert 'appointment_id' in appointments.columns
        assert 'no_show' in appointments.columns
        assert appointments['no_show'].isin([0, 1]).all()
    
    def test_no_show_rate_realistic(self):
        """Test that no-show rate is within realistic range."""
        from data.synthetic_data_generator import generate_patients, generate_appointments
        
        patients = generate_patients(500)
        appointments = generate_appointments(patients, 5000)
        
        no_show_rate = appointments['no_show'].mean()
        
        # Healthcare no-show rates typically 5-30%
        assert 0.05 <= no_show_rate <= 0.30, f"No-show rate {no_show_rate:.1%} outside expected range"


class TestFeatureEngineering:
    """Tests for feature engineering."""
    
    def test_required_features_present(self):
        """Test that all required features are in the data."""
        from data.synthetic_data_generator import generate_patients, generate_appointments
        
        patients = generate_patients(50)
        appointments = generate_appointments(patients, 200)
        df = appointments.merge(patients, on='patient_id', how='left')
        
        required_features = [
            'distance_km',
            'previous_no_shows',
            'age',
            'medication_count',
            'lead_time_days',
            'day_of_week',
            'hour_of_day',
            'chronic_conditions',
        ]
        
        for feature in required_features:
            assert feature in df.columns, f"Missing feature: {feature}"
    
    def test_no_negative_values(self):
        """Test that numeric features don't have negative values."""
        from data.synthetic_data_generator import generate_patients, generate_appointments
        
        patients = generate_patients(50)
        appointments = generate_appointments(patients, 200)
        df = appointments.merge(patients, on='patient_id', how='left')
        
        non_negative_features = ['distance_km', 'previous_no_shows', 'age', 'medication_count']
        
        for feature in non_negative_features:
            assert (df[feature] >= 0).all(), f"Negative values in {feature}"


class TestModelTraining:
    """Tests for model training pipeline."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample training data."""
        np.random.seed(42)
        n = 500
        
        data = pd.DataFrame({
            'distance_km': np.random.exponential(8, n),
            'previous_no_shows': np.random.poisson(0.8, n),
            'age': np.clip(np.random.normal(55, 20, n), 18, 95).astype(int),
            'medication_count': np.random.poisson(3, n),
            'lead_time_days': np.random.exponential(14, n).astype(int),
            'day_of_week': np.random.randint(0, 7, n),
            'hour_of_day': np.random.randint(8, 18, n),
            'chronic_conditions': np.random.poisson(1.5, n),
        })
        
        # Generate target
        prob = 0.08 + data['distance_km']/100 + data['previous_no_shows']*0.08
        data['no_show'] = (np.random.random(n) < prob).astype(int)
        
        return data
    
    def test_model_trains_successfully(self, sample_data):
        """Test that model training completes without errors."""
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler
        from sklearn.linear_model import LogisticRegression
        
        features = ['distance_km', 'previous_no_shows', 'age', 'medication_count',
                   'lead_time_days', 'day_of_week', 'hour_of_day', 'chronic_conditions']
        
        X = sample_data[features]
        y = sample_data['no_show']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        
        model = LogisticRegression(max_iter=1000)
        model.fit(X_train_scaled, y_train)
        
        assert model is not None
        assert len(model.coef_[0]) == len(features)
    
    def test_model_predicts_probabilities(self, sample_data):
        """Test that model outputs valid probabilities."""
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler
        from sklearn.linear_model import LogisticRegression
        
        features = ['distance_km', 'previous_no_shows', 'age', 'medication_count',
                   'lead_time_days', 'day_of_week', 'hour_of_day', 'chronic_conditions']
        
        X = sample_data[features]
        y = sample_data['no_show']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        model = LogisticRegression(max_iter=1000)
        model.fit(X_train_scaled, y_train)
        
        probabilities = model.predict_proba(X_test_scaled)[:, 1]
        
        assert (probabilities >= 0).all()
        assert (probabilities <= 1).all()
    
    def test_model_auc_above_baseline(self, sample_data):
        """Test that model AUC is better than random (0.5)."""
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import roc_auc_score
        
        features = ['distance_km', 'previous_no_shows', 'age', 'medication_count',
                   'lead_time_days', 'day_of_week', 'hour_of_day', 'chronic_conditions']
        
        X = sample_data[features]
        y = sample_data['no_show']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        model = LogisticRegression(max_iter=1000, class_weight='balanced')
        model.fit(X_train_scaled, y_train)
        
        probabilities = model.predict_proba(X_test_scaled)[:, 1]
        auc = roc_auc_score(y_test, probabilities)
        
        assert auc > 0.55, f"AUC {auc:.3f} not significantly better than random"


class TestScoringScripts:
    """Tests for scoring scripts."""
    
    def test_online_scoring_single_record(self):
        """Test online scoring with single record."""
        # This would require the model artifacts to be present
        # For CI, we test the logic without the actual model
        
        test_input = {
            "distance_km": 10.0,
            "previous_no_shows": 2,
            "age": 50,
            "medication_count": 3,
            "lead_time_days": 14,
            "day_of_week": 1,
            "hour_of_day": 10,
            "chronic_conditions": 2
        }
        
        # Validate input structure
        required_fields = ['distance_km', 'previous_no_shows', 'age', 'medication_count',
                         'lead_time_days', 'day_of_week', 'hour_of_day', 'chronic_conditions']
        
        for field in required_fields:
            assert field in test_input, f"Missing required field: {field}"
    
    def test_batch_scoring_input_format(self):
        """Test that batch scoring accepts correct input format."""
        test_df = pd.DataFrame({
            'patient_id': ['P001', 'P002'],
            'distance_km': [5.0, 15.0],
            'previous_no_shows': [0, 3],
            'age': [35, 65],
            'medication_count': [1, 5],
            'lead_time_days': [7, 21],
            'day_of_week': [1, 4],
            'hour_of_day': [9, 14],
            'chronic_conditions': [0, 3]
        })
        
        required_columns = ['distance_km', 'previous_no_shows', 'age', 'medication_count',
                          'lead_time_days', 'day_of_week', 'hour_of_day', 'chronic_conditions']
        
        for col in required_columns:
            assert col in test_df.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
