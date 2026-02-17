# 🏥 Patient No-Show Prediction - MLOps Demo

Predict patient appointment no-shows using machine learning, deployed with enterprise MLOps practices.

## 🎯 What This Demo Shows

| Capability | Implementation |
|------------|----------------|
| **Model Training** | Logistic Regression on Kaggle healthcare data |
| **Model Registry** | Azure ML Model Registry with versioning |
| **CI/CD Pipeline** | GitHub Actions with self-hosted runner |
| **Deployment** | Online endpoints (staging → production) |
| **Batch Scoring** | Daily batch predictions for next-day appointments |

---

## 📊 Model Overview

**Algorithm:** Logistic Regression (classification)  
**Target:** No-show probability (0-100%)  
**AUC-ROC:** ~0.67

### Features Used
| Feature | Description |
|---------|-------------|
| `age` | Patient age (0-115) |
| `scholarship` | Bolsa Família enrollment (0/1) |
| `hipertension` | Has hypertension (0/1) |
| `diabetes` | Has diabetes (0/1) |
| `alcoholism` | Has alcoholism (0/1) |
| `handcap` | Disability level (0-4) |
| `sms_received` | Got SMS reminder (0/1) |
| `lead_time_days` | Days between scheduling and appointment |
| `day_of_week` | Appointment day (0=Mon, 6=Sun) |
| `chronic_conditions` | Sum of chronic conditions |

### Risk Categories
| Risk Level | Probability | Action |
|------------|------------|--------|
| **Low** | < 30% | Standard reminder |
| **Medium** | 30-50% | Extra reminder |
| **High** | > 50% | Call patient, consider overbooking |

---

## 🚀 Quick Start

### Local Training
```bash
# Install dependencies
pip install -r requirements.txt

# Train model
cd noshow_prediction/training
python train.py --data-path ../../data/KaggleV2-May-2016.csv --output-dir ../../outputs

# Run tests
pytest test_train.py -v
```

### Test the Endpoint
```bash
# Azure CLI
az ml online-endpoint invoke \
  --name noshow-online-endpoint-staging \
  --request-file deployment/sample_requests.json \
  --resource-group rg-ai-hub-citadel-dev-02 \
  --workspace-name AI-WORKSPACE-shark
```

### Sample Predictions

**High Risk Patient** (young, long lead time):
```json
{"age": 15, "scholarship": 0, "hipertension": 0, "diabetes": 0, "alcoholism": 0, "handcap": 0, "sms_received": 1, "lead_time_days": 21, "day_of_week": 2, "chronic_conditions": 0}
```
→ Result: ~65% no-show risk (High)

**Low Risk Patient** (older, short lead time, chronic conditions):
```json
{"age": 65, "scholarship": 0, "hipertension": 1, "diabetes": 1, "alcoholism": 0, "handcap": 0, "sms_received": 1, "lead_time_days": 1, "day_of_week": 2, "chronic_conditions": 2}
```
→ Result: ~25% no-show risk (Low)

---

## 📁 Project Structure

```
noshow-ml-demo/
├── noshow_prediction/           # ML code
│   ├── training/
│   │   ├── train.py             # Training logic
│   │   ├── train_aml.py         # Azure ML entry script
│   │   └── test_train.py        # Unit tests (15 tests)
│   ├── scoring/
│   │   └── score.py             # Scoring script
│   └── conda_dependencies.yml   # Environment spec
│
├── ml_service/                  # Azure ML pipeline
│   └── pipelines/
│       └── noshow_build_train_pipeline.py
│
├── .github/workflows/           # CI/CD
│   └── mlops-ci-cd.yml          # GitHub Actions workflow
│
├── deployment/                  # Endpoint configs
│   ├── online/                  # Real-time endpoint
│   ├── batch/                   # Batch endpoint
│   └── sample_requests.json     # Test payloads
│
├── data/                        # Training data
│   └── KaggleV2-May-2016.csv    # Kaggle dataset
│
├── outputs/                     # Model artifacts
│   ├── model.joblib
│   ├── scaler.joblib
│   └── metrics.json
│
└── notebooks/                   # Experimentation
    └── 01_train_noshow_model.ipynb
```

---

## 🔄 CI/CD Pipeline

```
Push to main
     │
     ▼
┌─────────────────┐
│  🧪 Tests       │  Run pytest
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  🚂 Train       │  Train in Azure ML
└────────┬────────┘  Register model
         │
         ▼
┌─────────────────┐
│  🎭 Staging     │  Deploy to staging endpoint
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  🏭 Production  │  Deploy to production
└─────────────────┘  (with approval gate)
```

### GitHub Environments
| Environment | Secrets | Purpose |
|-------------|---------|---------|
| `staging` | Azure credentials | Test deployments |
| `production` | Azure credentials | Production (requires approval) |

---

## ☁️ Azure Resources

| Resource | Name | Purpose |
|----------|------|---------|
| ML Workspace | `AI-WORKSPACE-shark` | Model registry, endpoints |
| Resource Group | `rg-ai-hub-citadel-dev-02` | Container |
| Compute Cluster | `cpu-cluster` | Training compute (0-2 nodes) |
| Model | `noshow-logreg` | Registered model |
| Data Asset | `noshow-data:1` | Training data in blob store |
| Online Endpoint | `noshow-online-endpoint-staging` | Staging predictions |
| Batch Endpoint | `noshow-batch-endpoint` | Daily batch scoring |

---

## 📈 Business Impact

| Metric | Value | Impact |
|--------|-------|--------|
| No-show rate reduction | 10-20% | Fewer empty slots |
| Revenue recovery | €500K+/year | Better capacity utilization |
| Patient experience | Improved | Proactive outreach for high-risk |

---

## 🔧 Configuration

### GitHub Secrets (Repository level)
```
AZURE_CLIENT_ID
AZURE_CLIENT_SECRET
AZURE_TENANT_ID
AZURE_SUBSCRIPTION_ID
```

### GitHub Variables (Environment level)
```
AZURE_ML_RESOURCE_GROUP=rg-ai-hub-citadel-dev-02
AZURE_ML_WORKSPACE=AI-WORKSPACE-shark
```

---

## 📚 References

- [MLOpsPython Template](https://github.com/microsoft/MLOpsPython)
- [Azure ML Documentation](https://learn.microsoft.com/azure/machine-learning/)
- [Kaggle No-Show Dataset](https://www.kaggle.com/datasets/joniarroba/noshowappointments)
