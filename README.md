# 🏥 Patient No-Show Prediction Demo

## Deep Technical Demo with Business Focus

**Headline:** *"Train in Fabric. Govern & scale in Azure ML. Operationalize into HiX/BI with monitoring and approvals."*

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [Business Outcomes](#business-outcomes)
3. [Architecture Overview](#architecture-overview)
4. [Prerequisites](#prerequisites)
5. [Demo Setup Guide](#demo-setup-guide)
6. [Demo Script (30-40 minutes)](#demo-script)
7. [Key Talking Points](#key-talking-points)
8. [FAQ & Objection Handling](#faq--objection-handling)

---

## Executive Summary

This demo shows how to move from ML experimentation to production-ready deployment using:

| Component | Purpose |
|-----------|---------|
| **Microsoft Fabric** | Data platform, notebooks, Power BI |
| **Azure ML** | Model registry, endpoints, monitoring |
| **GitHub Actions** | CI/CD with approvals |

**Customer Pain Points Addressed:**
- ❌ "We're stuck in experimentation mode"
- ❌ "How do we productionize sustainably?"
- ❌ "We need governance and audit trails"

---

## Business Outcomes

### Use Case 1: Patient No-Show Prediction
| Metric | Target | Impact |
|--------|--------|--------|
| AUC-ROC | ≥ 0.75 | Reliable risk scoring |
| No-show reduction | 10-20% | €500K+ annual savings |
| Daily processing | By 07:30 | Operational readiness |

### Use Case 2: Multi-Condition Risk (Future)
- Identify complex patients earlier
- Better care coordination
- Reduced readmissions

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     DATA LAYER (Microsoft Fabric)                │
├─────────────────────────────────────────────────────────────────┤
│  Lakehouse          │  Notebooks      │  Power BI               │
│  ├── Bronze (raw)   │  ├── Training   │  ├── Risk Dashboard     │
│  ├── Silver (clean) │  └── EDA        │  └── Operational Views  │
│  └── Gold (curated) │                 │                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ML PLATFORM (Azure ML)                       │
├─────────────────────────────────────────────────────────────────┤
│  Model Registry     │  Endpoints      │  Monitoring             │
│  ├── Versioning     │  ├── Batch      │  ├── Data Drift         │
│  ├── Lineage        │  │   (daily)    │  ├── Model Performance  │
│  └── Tags           │  └── Online     │  └── Alerts             │
│                     │      (real-time)│                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     CI/CD (GitHub Actions)                       │
├─────────────────────────────────────────────────────────────────┤
│  Test → Train → Register → Deploy Staging → [Approval] → Prod   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### Azure Resources
- [ ] Azure ML Workspace (West Europe recommended for NL healthcare)
- [ ] CPU Compute Cluster (`STANDARD_DS3_v2`, 0-2 nodes)
- [ ] Storage Account with Lakehouse access

### Fabric Resources
- [ ] Fabric Workspace with Lakehouse
- [ ] Power BI dataset permissions
- [ ] F64 capacity (or higher)

### GitHub
- [ ] Repository with code
- [ ] OIDC/Service Principal for Azure
- [ ] Protected environments (staging, production)

### Local Development
- [ ] Python 3.10+
- [ ] VS Code with Python extension
- [ ] Azure CLI with ML extension

---

## Demo Setup Guide

### Step 1: Generate Synthetic Data

```bash
cd noshow-ml-demo/data
python synthetic_data_generator.py
```

This creates:
- `patients_silver.parquet` (5,000 patients)
- `appointments_silver.parquet` (25,000 appointments)
- `multi_condition_risk.parquet` (future use case)

### Step 2: Configure Azure ML Connection

Create a `.env` file:

```env
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_RESOURCE_GROUP=your-resource-group
AZURE_ML_WORKSPACE=your-workspace-name
```

### Step 3: Run Training Notebook Locally

1. Open `notebooks/01_train_noshow_model.ipynb`
2. Run all cells
3. Verify model artifacts in `outputs/`

### Step 4: Deploy to Azure ML (Optional for Demo)

```bash
# Login to Azure
az login

# Install ML extension
az extension add -n ml

# Create online endpoint
az ml online-endpoint create -f deployment/online/online-endpoint.yml

# Create deployment
az ml online-deployment create -f deployment/online/online-deployment.yml --all-traffic
```

---

## Demo Script

### Opening (0-3 min)

**Show:** Title slide with outcomes

**Say:**
> "Today I'll show you how to move from ML experimentation—where you already are with Fabric notebooks—to governed production deployment. We'll address your two use cases: no-show prediction and multi-condition risk."

**Key points:**
- ✅ Reduce no-shows → more throughput, lower costs
- ✅ Governed deployment → auditors happy
- ✅ Monitoring → sustainable long-term

---

### Part 1: Train in Fabric Notebook (3-10 min)

**Show:** Open `01_train_noshow_model.ipynb`

**Say:**
> "This notebook runs on CPU—no GPU needed. It's the same environment you're using today with F64."

**Run cells through:**
1. Data loading → "This comes from your Lakehouse"
2. EDA visualizations → "Previous no-shows is the strongest predictor"
3. Model training → "Under 1 second on CPU"
4. Metrics → "AUC above 0.75 is our target"

**Business call-out:**
> "Even with CPU, we hit acceptable accuracy for daily risk lists. We'll monitor and iterate."

---

### Part 2: Register Model to Azure ML (10-15 min)

**Show:** Azure ML Model Registry

**Say:**
> "Everything is versioned. We can prove which model made which decision, when."

**Click through:**
1. Model versions
2. Tags (AUC, build number)
3. Artifacts (model.joblib, scaler.joblib)

**Business call-out:**
> "This is your audit trail. Regulators and compliance teams need this."

---

### Part 3: Deploy Endpoints (15-22 min)

**Show:** Deployment YAML files, then Azure ML Endpoints

#### Batch Endpoint
> "Every morning at 6am, this pipeline scores all upcoming appointments and writes back to your Lakehouse. By 8am, planners see the risk list in Power BI."

#### Online Endpoint
> "This is how you'd integrate with HiX. Low latency, versioned, auditable."

**Demo:** Test online endpoint with curl/Postman

```bash
curl -X POST "https://noshow-online-endpoint.westeurope.inference.ml.azure.com/score" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"distance_km":15,"previous_no_shows":3,"age":55,"medication_count":5,"lead_time_days":21,"day_of_week":0,"hour_of_day":8,"chronic_conditions":2}'
```

---

### Part 4: Power BI Dashboard (22-27 min)

**Show:** Power BI report (mock or real)

**Say:**
> "Frontline planners see the highest-risk patients and can trigger SMS reminders or overbooking adjustments."

**Key views:**
- Today's risk list (sorted by risk)
- Clinic breakdown
- Trend over time

---

### Part 5: CI/CD & Approvals (27-32 min)

**Show:** GitHub Actions workflow

**Say:**
> "Nothing hits production without approval. When Thomas pushes code, it automatically tests, trains, deploys to staging, and waits for approval before production."

**Click through:**
1. Workflow runs
2. Protected environments
3. Approval gates

**Business call-out:**
> "Auditors love this. Full traceability from code change to production."

---

### Part 6: Monitoring (32-36 min)

**Show:** Azure ML Monitoring dashboard

**Say:**
> "We'll know when the model stops working before the business feels it."

**Key metrics:**
- Data drift detection
- Prediction distribution
- Alert configuration

---

### Closing (36-40 min)

**Say:**
> "Let's recap what we've covered..."

| Step | What You Saw | Business Value |
|------|--------------|----------------|
| Train | Fabric notebook on CPU | Works with your current setup |
| Register | Azure ML model registry | Audit trail, versioning |
| Deploy | Batch + Online endpoints | Daily lists + HiX integration |
| Operate | Power BI + GitHub CI/CD | Planners use it, governed changes |
| Monitor | Drift detection + alerts | Sustainable long-term |

**Next steps:**
1. Pilot with 2 clinics (6-8 weeks)
2. Measure no-show reduction
3. Expand if successful

---

## Key Talking Points

### For Thomas (Data Scientist)
- "You can keep using Fabric notebooks"
- "Azure ML handles the deployment complexity"
- "MLflow integration for experiment tracking"

### For Reinier (Infra)
- "Private endpoints available"
- "Managed identity for security"
- "CPU compute keeps costs low"

### For Edwin (BI Lead)
- "Power BI refreshes automatically"
- "Semantic model over predictions table"
- "Self-service analytics on risk data"

### For Sophie (AI Project Lead)
- "Governed deployment with approvals"
- "Clear success metrics"
- "Sustainable, not a one-off"

---

## FAQ & Objection Handling

### "Is Azure ML necessary? Can't we do this in Fabric?"
> "Fabric is great for development. Azure ML adds production-grade deployment, versioning, monitoring, and CI/CD integration. Think of it as the 'ops' in MLOps."

### "What about GDPR/healthcare compliance?"
> "Data stays in your Azure tenant (West Europe). Use pseudonymization for ML features. Managed identities eliminate credential risks. Full audit trail in model registry."

### "We don't have GPU budget."
> "This model runs on CPU. LogisticRegression is fast and interpretable. Start simple, add complexity later if needed."

### "What if the model degrades?"
> "Azure ML monitoring detects data drift and alerts you. Set up automatic retraining triggers or manual review workflows."

### "How long to implement?"
> "Pilot in 6-8 weeks with 2 clinics. You already have the data and Fabric setup. Main work is endpoint deployment and Power BI integration."

---

## File Structure

```
noshow-ml-demo/
├── .github/
│   └── workflows/
│       └── mlops.yml              # CI/CD pipeline
├── data/
│   └── synthetic_data_generator.py # Demo data generation
├── notebooks/
│   └── 01_train_noshow_model.ipynb # Training notebook
├── deployment/
│   ├── batch/
│   │   ├── batch-endpoint.yml
│   │   ├── batch-deployment.yml
│   │   ├── environment.yml
│   │   └── src/
│   │       └── score_batch.py
│   └── online/
│       ├── online-endpoint.yml
│       ├── online-deployment.yml
│       ├── environment.yml
│       └── src/
│           └── score_online.py
├── outputs/                        # Model artifacts (generated)
└── README.md                       # This file
```

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Model AUC | ≥ 0.75 | Azure ML metrics |
| Daily batch SLA | By 07:30 | Pipeline monitoring |
| Planner adoption | ≥ 80% | Power BI usage |
| No-show reduction | 10-20% | A/B test vs control clinics |
| Governance compliance | 100% | All changes via PR + approval |

---

## Contact

**Next meeting:** 18-02 (scheduled by Margot)

**Preparation needed:**
- [ ] Confirm Azure ML workspace access
- [ ] Identify 2 pilot clinics
- [ ] Define success criteria with stakeholders

---

*Demo package created for deep technical demonstration with business focus.*
#   T r i g g e r   C I  
 