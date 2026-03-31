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
  --resource-group <your-resource-group> \
  --workspace-name <your-workspace-name>
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
│   └── training/
│       ├── train.py             # Training logic
│       └── test_train.py        # Unit tests (15 tests)
│
├── ml_service/                  # Azure ML pipeline
│   └── pipelines/
│       └── noshow_build_train_pipeline.py
│
├── .github/workflows/           # CI/CD
│   └── mlops-ci-cd.yml          # GitHub Actions workflow
│
├── deployment/                  # Endpoint configs
│   ├── online/                  # Real-time scoring scripts
│   ├── batch/                   # Batch scoring scripts
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
├── notebooks/                   # Experimentation
│   ├── 01_train_noshow_model.ipynb
│   └── 02_connect_fabric_onelake_demo.ipynb
│
└── terraform/                   # Infrastructure as Code
    ├── main.tf                  # Azure ML + optional Fabric resources
    ├── variables.tf             # Input variables
    ├── outputs.tf               # Terraform outputs
    └── terraform.tfvars.example # Sample variable values
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
| ML Workspace | `<your-workspace-name>` | Model registry, endpoints |
| Resource Group | `<your-resource-group>` | Container |
| Compute Cluster | `cpu-cluster` | Training compute (0-2 nodes) |
| Model | `noshow-logreg` | Registered model |
| Data Asset | `noshow-data:1` | Training data in blob store |
| Online Endpoint | `noshow-online-endpoint-staging` | Staging predictions |
| Batch Endpoint | `noshow-batch-endpoint` | Daily batch scoring |

---

## � Microsoft Fabric Integration

This solution integrates with **Microsoft Fabric** for enterprise data management:

```
┌─────────────────────────────────────────────────────────────┐
│              MICROSOFT FABRIC LAKEHOUSE                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Bronze Layer │─▶│ Silver Layer │─▶│ Gold Layer   │      │
│  │ Raw HiX data │  │ Cleaned data │  │ ML-ready     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                              │              │
│  OneLake: abfss://lakehouse@onelake.dfs...  │              │
└──────────────────────────────────────────────┼──────────────┘
                                               │
                      Read from OneLake ───────┘
                                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    AZURE ML WORKSPACE                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Training Job │─▶│ Model        │─▶│ Endpoints    │      │
│  │ (cpu-cluster)│  │ Registry     │  │ batch/online │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────────────────────────┬──────────────┘
                                               │
              Predictions written back ────────┘
                                               ▼
┌─────────────────────────────────────────────────────────────┐
│              FABRIC LAKEHOUSE (Predictions)                 │
│  predictions/noshow_risk/2026-02-18/predictions.parquet    │
└──────────────────────────────────────────────┬──────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    POWER BI DASHBOARD                       │
│  "Today's High-Risk Appointments" (DirectLake mode)        │
└─────────────────────────────────────────────────────────────┘
```

### Integration Points

| Component | Role | Connection |
|-----------|------|------------|
| **Fabric Lakehouse** | Data storage | Appointments in Gold layer |
| **Azure ML Training** | Model training | Reads from OneLake via ADLS Gen2 |
| **Azure ML Batch** | Daily scoring | Reads/writes from OneLake |
| **Azure ML Online** | Real-time | HiX calls API on booking |
| **Power BI** | Visualization | DirectLake on predictions |

### Azure ML Notebook Connection Flow

The Terraform in this repo provisions Azure ML infrastructure and can optionally create a Microsoft Fabric workspace and lakehouse when Fabric provider access is configured. If you keep Fabric creation disabled, the Fabric workspace and lakehouse must already exist before you use the notebook connection flow below.

For the first integration demo step, use [notebooks/02_connect_fabric_onelake_demo.ipynb](notebooks/02_connect_fabric_onelake_demo.ipynb). It covers:

1. **OneLake Datastore** — Create or update Azure ML OneLake datastores (Files and Tables) and build `azureml://datastores/.../paths/...` URIs.
2. **Direct OneLake Reads** — Read CSV/Parquet files directly from OneLake via `azure-storage-file-datalake`.
3. **Fabric SQL Endpoint (pyodbc)** — Connect to the lakehouse SQL analytics endpoint using ODBC Driver 18 with Azure AD token auth.
4. **Fabric SQL Endpoint (mssql-python)** — Connect using Microsoft's new `mssql-python` driver with Entra ID auth (no ODBC Driver Manager needed).
5. **Azure ML Connection** — Register the SQL endpoint as an Azure ML workspace connection for use in pipelines and jobs.

For this repo, the recommended step-1 demo path is:

1. Provision Azure ML with Terraform and populate the optional Fabric variables in [terraform/terraform.tfvars.example](terraform/terraform.tfvars.example).
2. Use Terraform outputs to share the Azure ML workspace or compute managed identity with your Fabric admin.
3. Grant that principal read access to the Fabric workspace or lakehouse that contains the training file.
4. Open [notebooks/02_connect_fabric_onelake_demo.ipynb](notebooks/02_connect_fabric_onelake_demo.ipynb) to create OneLake datastores, validate direct reads, and optionally connect via SQL.
5. Use the datastore URI or SQL connection in notebooks, jobs, or data assets.

### Cost Model

| Resource | Billing | Est. Cost |
|----------|---------|-----------|
| `cpu-cluster` | Per job (~5 min) | ~$0.02/job |
| Online endpoint | Always-on | ~$137/month |
| Batch endpoint | Per batch run | ~$0.10/run |

> **Tip:** Delete online endpoints when not demoing. Use batch + cpu-cluster for scheduled scoring (scales to 0 when idle).

---

## �📈 Business Impact

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
AZURE_ML_RESOURCE_GROUP=<your-resource-group>
AZURE_ML_WORKSPACE=<your-workspace-name>
```

---

## 🎓 Learning Resources for New Azure ML Users

### Getting Started
| Resource | Description |
|----------|-------------|
| [Azure ML Quickstart](https://learn.microsoft.com/azure/machine-learning/quickstart-create-resources) | Create your first workspace and resources |
| [Azure ML Studio Tour](https://learn.microsoft.com/azure/machine-learning/overview-what-is-azure-machine-learning) | Overview of Azure ML capabilities |
| [Free Azure Account](https://azure.microsoft.com/free/) | $200 credit for 30 days + free tier services |

### Hands-On Tutorials
| Tutorial | What You'll Learn |
|----------|-------------------|
| [Train your first model](https://learn.microsoft.com/azure/machine-learning/tutorial-train-model) | End-to-end training workflow |
| [Deploy a model](https://learn.microsoft.com/azure/machine-learning/tutorial-deploy-model) | Online endpoints and inference |
| [AutoML Tutorial](https://learn.microsoft.com/azure/machine-learning/tutorial-first-experiment-automated-ml) | No-code ML with AutoML |
| [MLOps with GitHub Actions](https://learn.microsoft.com/azure/machine-learning/how-to-github-actions-machine-learning) | CI/CD for ML |

### Learning Paths (Microsoft Learn)
- [Azure Data Scientist Associate](https://learn.microsoft.com/credentials/certifications/azure-data-scientist/) - DP-100 certification path
- [Build AI solutions with Azure ML](https://learn.microsoft.com/training/paths/build-ai-solutions-with-azure-ml-service/) - Comprehensive learning path
- [MLOps Fundamentals](https://learn.microsoft.com/training/paths/introduction-machine-learn-operations/) - Production ML best practices

### Sample Repositories
| Repo | Description |
|------|-------------|
| [Azure ML Examples](https://github.com/Azure/azureml-examples) | Official samples for SDK v2, CLI v2 |
| [MLOpsPython](https://github.com/microsoft/MLOpsPython) | Production MLOps template |
| [Azure ML Cheat Sheet](https://azure.github.io/azureml-cheatsheets/) | Quick reference for common tasks |

### Key Concepts to Explore
1. **Workspaces** - Central hub for all ML assets
2. **Compute** - Training clusters, compute instances, serverless
3. **Data Assets** - Versioned, governed data references
4. **Environments** - Reproducible Python/Docker environments
5. **Pipelines** - Orchestrated ML workflows
6. **Endpoints** - Real-time and batch inference
7. **MLflow** - Experiment tracking and model registry

### Useful Azure CLI Commands
```bash
# List workspaces you have access to
az ml workspace list --output table

# Show workspace details
az ml workspace show --name <workspace-name> -g <resource-group>

# List registered models
az ml model list --workspace-name <workspace-name> -g <resource-group>

# List endpoints
az ml online-endpoint list --workspace-name <workspace-name> -g <resource-group>
```

---

## 📚 References

- [MLOpsPython Template](https://github.com/microsoft/MLOpsPython)
- [Azure ML Documentation](https://learn.microsoft.com/azure/machine-learning/)
- [Kaggle No-Show Dataset](https://www.kaggle.com/datasets/joniarroba/noshowappointments)
