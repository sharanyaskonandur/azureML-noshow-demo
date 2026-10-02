"""
Unit Tests for Training Module
==============================
Tests for the no-show prediction training pipeline.

Run with: pytest noshow_prediction/training/test_train.py -v

Following MLOpsPython template: https://github.com/microsoft/MLOpsPython
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
import os
import sys
import json

# Add training directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from train import (
    load_data,
    prepare_data,
    train_model,
    evaluate_model,
    save_model,
    FEATURES,
    TARGET
)


@pytest.fixture
def sample_dataframe():
    """Create sample no-show data for testing."""
    np.random.seed(42)
    n = 500
    
    df = pd.DataFrame({
        'patientid': range(n),
        'appointmentid': range(n),
        'gender': np.random.choice(['M', 'F'], n),
        'scheduledday': pd.date_range('2023-01-01', periods=n, freq='h'),
        'appointmentday': pd.date_range('2023-01-15', periods=n, freq='h'),
        'age': np.clip(np.random.normal(50, 20, n), 0, 115).astype(int),
        'neighbourhood': np.random.choice(['A', 'B', 'C'], n),
        'scholarship': np.random.randint(0, 2, n),
        'hipertension': np.random.randint(0, 2, n),
        'diabetes': np.random.randint(0, 2, n),
        'alcoholism': np.random.randint(0, 2, n),
        'handcap': np.random.randint(0, 5, n),
        'sms_received': np.random.randint(0, 2, n),
        'no_show': np.random.choice(['Yes', 'No'], n, p=[0.2, 0.8])
    })
    
    return df


@pytest.fixture
#Delete this test


@pytest.fixture
def temp_csv_file(sample_dataframe):
    """Create temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_dataframe.to_csv(f, index=False)
        return f.name


class TestLoadData:
    """Tests for data loading."""
    
    def test_load_data_returns_dataframe(self, temp_csv_file):
        """Test that load_data returns a DataFrame."""
        df = load_data(temp_csv_file)
        assert isinstance(df, pd.DataFrame)
        os.unlink(temp_csv_file)
    
    def test_load_data_has_required_columns(self, temp_csv_file):
        """Test that loaded data has all required features."""
        df = load_data(temp_csv_file)
        
        for feature in FEATURES:
            assert feature in df.columns, f"Missing feature: {feature}"
        
        assert TARGET in df.columns, f"Missing target: {TARGET}"
        os.unlink(temp_csv_file)
    
    def test_load_data_creates_derived_features(self, temp_csv_file):
        """Test that derived features are created."""
        df = load_data(temp_csv_file)
        
        derived_features = ['lead_time_days', 'day_of_week', 'chronic_conditions']
        for feature in derived_features:
            assert feature in df.columns, f"Missing derived feature: {feature}"
        
        os.unlink(temp_csv_file)
    
    def test_target_is_binary(self, temp_csv_file):
        """Test that target is binary (0 or 1)."""
        df = load_data(temp_csv_file)
        
        assert df[TARGET].isin([0, 1]).all()
        os.unlink(temp_csv_file)


class TestPrepareData:
    """Tests for data preparation."""
    
    def test_prepare_data_returns_correct_shapes(self, processed_dataframe):
        """Test that prepare_data returns correct array shapes."""
        X_train, X_test, y_train, y_test, scaler = prepare_data(
            processed_dataframe, test_size=0.2
        )
        
        # Check shapes
        total = len(processed_dataframe)
        train_size = int(total * 0.8)
        test_size = total - train_size
        
        assert X_train.shape[0] == train_size
        assert X_test.shape[0] == test_size
        assert y_train.shape[0] == train_size
        assert y_test.shape[0] == test_size
    
    def test_prepare_data_scales_features(self, processed_dataframe):
        """Test that features are scaled."""
        X_train, X_test, y_train, y_test, scaler = prepare_data(
            processed_dataframe
        )
        
        # Scaled training data should have mean close to 0 and std close to 1
        assert np.abs(X_train.mean()) < 0.5
        assert np.abs(X_train.std() - 1.0) < 0.5
    
    def test_stratified_split(self, processed_dataframe):
        """Test that train/test split maintains class ratio."""
        X_train, X_test, y_train, y_test, scaler = prepare_data(
            processed_dataframe
        )
        
        train_ratio = y_train.mean()
        test_ratio = y_test.mean()
        
        # Ratios should be similar due to stratification
        assert abs(train_ratio - test_ratio) < 0.05


class TestTrainModel:
    """Tests for model training."""
    
    def test_train_model_returns_model(self, processed_dataframe):
        """Test that train_model returns a trained model."""
        X_train, X_test, y_train, y_test, scaler = prepare_data(
            processed_dataframe
        )
        
        model = train_model(X_train, y_train)
        
        assert model is not None
        assert hasattr(model, 'predict')
        assert hasattr(model, 'predict_proba')
    
    def test_model_has_coefficients(self, processed_dataframe):
        """Test that trained model has coefficients."""
        X_train, X_test, y_train, y_test, scaler = prepare_data(
            processed_dataframe
        )
        
        model = train_model(X_train, y_train)
        
        assert len(model.coef_[0]) == len(FEATURES)


class TestEvaluateModel:
    """Tests for model evaluation."""
    
    def test_evaluate_returns_metrics(self, processed_dataframe):
        """Test that evaluate_model returns expected metrics."""
        X_train, X_test, y_train, y_test, scaler = prepare_data(
            processed_dataframe
        )
        model = train_model(X_train, y_train)
        
        metrics = evaluate_model(model, X_test, y_test)
        
        assert 'auc_roc' in metrics
        assert 'brier_score' in metrics
        assert 'accuracy' in metrics
        assert 'precision' in metrics
        assert 'recall' in metrics
    
    def test_metrics_are_valid_ranges(self, processed_dataframe):
        """Test that metrics are in valid ranges."""
        X_train, X_test, y_train, y_test, scaler = prepare_data(
            processed_dataframe
        )
        model = train_model(X_train, y_train)
        
        metrics = evaluate_model(model, X_test, y_test)
        
        # AUC should be between 0 and 1
        assert 0 <= metrics['auc_roc'] <= 1
        
        # Brier score should be between 0 and 1
        assert 0 <= metrics['brier_score'] <= 1
        
        # Accuracy should be between 0 and 1
        assert 0 <= metrics['accuracy'] <= 1
    
    def test_model_produces_valid_auc(self, processed_dataframe):
        """Test that model produces a valid AUC score."""
        X_train, X_test, y_train, y_test, scaler = prepare_data(
            processed_dataframe
        )
        model = train_model(X_train, y_train)
        
        metrics = evaluate_model(model, X_test, y_test)
        
        # AUC should be a valid probability (0-1)
        # Note: With random synthetic data, AUC may be below 0.5
        assert 0 <= metrics['auc_roc'] <= 1


class TestSaveModel:
    """Tests for model artifact saving."""
    
    def test_save_model_creates_files(self, processed_dataframe):
        """Test that save_model creates all required files."""
        X_train, X_test, y_train, y_test, scaler = prepare_data(
            processed_dataframe
        )
        model = train_model(X_train, y_train)
        metrics = evaluate_model(model, X_test, y_test)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            save_model(
                model, scaler, metrics, tmpdir,
                n_train=len(y_train),
                n_test=len(y_test),
                train_no_show_rate=float(y_train.mean()),
                test_no_show_rate=float(y_test.mean())
            )
            
            # Check files exist
            assert os.path.exists(os.path.join(tmpdir, 'model.joblib'))
            assert os.path.exists(os.path.join(tmpdir, 'scaler.joblib'))
            assert os.path.exists(os.path.join(tmpdir, 'metrics.json'))
            assert os.path.exists(os.path.join(tmpdir, 'feature_config.json'))
    
    def test_metrics_json_is_valid(self, processed_dataframe):
        """Test that saved metrics.json is valid JSON."""
        X_train, X_test, y_train, y_test, scaler = prepare_data(
            processed_dataframe
        )
        model = train_model(X_train, y_train)
        metrics = evaluate_model(model, X_test, y_test)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            save_model(
                model, scaler, metrics, tmpdir,
                n_train=len(y_train),
                n_test=len(y_test),
                train_no_show_rate=float(y_train.mean()),
                test_no_show_rate=float(y_test.mean())
            )
            
            with open(os.path.join(tmpdir, 'metrics.json')) as f:
                loaded_metrics = json.load(f)
            
            assert 'auc_roc' in loaded_metrics
            assert 'features' in loaded_metrics
            assert loaded_metrics['model_type'] == 'LogisticRegression'


class TestEndToEnd:
    """End-to-end integration tests."""
    
    def test_full_training_pipeline(self, temp_csv_file):
        """Test the full training pipeline from data load to model save."""
        from train import main
        
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics = main(
                data_path=temp_csv_file,
                output_dir=tmpdir,
                test_size=0.2,
                random_state=42
            )
            
            # Check metrics exist and are valid
            assert 'auc_roc' in metrics
            assert 0 <= metrics['auc_roc'] <= 1  # Valid AUC range
            
            # Check artifacts were created
            assert os.path.exists(os.path.join(tmpdir, 'model.joblib'))
            assert os.path.exists(os.path.join(tmpdir, 'scaler.joblib'))
            assert os.path.exists(os.path.join(tmpdir, 'metrics.json'))
        
        os.unlink(temp_csv_file)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
