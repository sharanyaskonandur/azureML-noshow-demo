# 🎯 Azure ML Platform Demo Script

**Duration:** 20-30 minutes  
**Key Message:** *"From code to production with governance, monitoring, and CI/CD"*

---

## Pre-Demo Checklist

- [ ] Azure ML Studio open: https://ml.azure.com
- [ ] GitHub repo open: Actions tab visible
- [ ] Terminal ready for endpoint testing
- [ ] This script open for reference

### Azure Resources (Already Deployed)
| Resource | Name |
|----------|------|
| Workspace | `AI-WORKSPACE-shark` |
| Resource Group | `rg-ai-hub-citadel-dev-02` |
| Model | `noshow-logreg` (v5+) |
| Compute | `cpu-cluster` |
| Batch Endpoint | `noshow-batch-endpoint` |
| Online Endpoint | `noshow-online-endpoint-staging` |

---

## Demo Flow

### Part 1: Model Registry (5 min) ⭐

**Open:** Azure ML Studio → Models → `noshow-logreg`

**Show:**
1. **Version history** - Every training creates a new version
2. **Artifacts** - `model.joblib`, `scaler.joblib`, `metrics.json`
3. **Metrics** - AUC-ROC score, training date

**Say:**
> "Every model version is tracked. When compliance asks 'which model made this prediction?', you answer in seconds."

---

### Part 2: Online Endpoint (8 min) ⭐

**Open:** Azure ML → Endpoints → Real-time → `noshow-online-endpoint-staging`

**Show:**
1. Endpoint URL (REST API)
2. Deployment details
3. Test tab

**Live Test - High Risk Patient:**
```json
{"age": 15, "scholarship": 0, "hipertension": 0, "diabetes": 0, "alcoholism": 0, "handcap": 0, "sms_received": 1, "lead_time_days": 21, "day_of_week": 2, "chronic_conditions": 0}
```

**Expected Response:** ~65% risk (High)
```json
{"no_show_risk": 0.65, "risk_category": "High", "risk_flag": 1}
```

**Live Test - Low Risk Patient:**
```json
{"age": 65, "scholarship": 0, "hipertension": 1, "diabetes": 1, "alcoholism": 0, "handcap": 0, "sms_received": 1, "lead_time_days": 1, "day_of_week": 2, "chronic_conditions": 2}
```

**Expected Response:** ~25% risk (Low)
```json
{"no_show_risk": 0.25, "risk_category": "Low", "risk_flag": 0}
```

**Say:**
> "Response in under 100ms. This is how your EHR system calls the model when a patient books."

**Key Factors:**
- Long lead time → Higher risk
- Young age → Higher risk
- No chronic conditions → Higher risk
- Short lead time + older + chronic conditions → Lower risk

---

### Part 3: Batch Endpoint (5 min)

**Open:** Azure ML → Endpoints → Batch → `noshow-batch-endpoint`

**Show:**
1. Endpoint configuration
2. Deployment (`noshow-batch-v1`)
3. Compute cluster (`cpu-cluster` - scales 0-2)

**Say:**
> "Every morning, this scores tomorrow's appointments. By 8am, the risk list is ready in Power BI. Compute scales to zero when not running - you only pay for what you use."

---

### Part 4: CI/CD Pipeline (7 min) ⭐

**Open:** GitHub → Actions tab

**Show the workflow:** `mlops-ci-cd.yml`

```
Push to main
     │
     ▼
┌─────────────────┐
│  🧪 Tests       │  pytest (15 unit tests)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  🚂 Train       │  Submit to Azure ML
└────────┬────────┘  Register model
         │
         ▼
┌─────────────────┐
│  🎭 Staging     │  Deploy to staging
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  🏭 Production  │  Deploy to production
└─────────────────┘  (approval required)
```

**Click through:**
1. Recent workflow runs → Green checkmarks
2. Jobs breakdown → Test, Train, Deploy
3. Environment protection → Production requires approval

**Say:**
> "Nothing reaches production without human approval. This is governance built into the pipeline."

---

### Part 5: Code Walkthrough (Optional, 3 min)

**Open:** VS Code / GitHub → `noshow_prediction/training/train.py`

**Show:**
- Logistic Regression model
- Feature engineering
- Evaluation metrics (AUC-ROC, precision, recall)

**Say:**
> "Simple, interpretable model. Data scientists focus on improving the model, not managing infrastructure."

---

## Live Demo Commands

### Test Endpoint via CLI
```bash
# Test staging endpoint
az ml online-endpoint invoke \
  --name noshow-online-endpoint-staging \
  --request-file deployment/sample_requests.json \
  --resource-group rg-ai-hub-citadel-dev-02 \
  --workspace-name AI-WORKSPACE-shark
```

### Trigger CI/CD
```bash
# Make a small change and push
git add .
git commit -m "Trigger CI/CD demo"
git push
```

Then show GitHub Actions running.

---

## Sample Test Payloads

### High Risk Examples
```json
{"age": 18, "scholarship": 1, "hipertension": 0, "diabetes": 0, "alcoholism": 0, "handcap": 0, "sms_received": 0, "lead_time_days": 30, "day_of_week": 5, "chronic_conditions": 0}
```

```json
{"age": 22, "scholarship": 0, "hipertension": 0, "diabetes": 0, "alcoholism": 1, "handcap": 0, "sms_received": 0, "lead_time_days": 14, "day_of_week": 1, "chronic_conditions": 0}
```

### Low Risk Examples
```json
{"age": 72, "scholarship": 0, "hipertension": 1, "diabetes": 1, "alcoholism": 0, "handcap": 0, "sms_received": 1, "lead_time_days": 1, "day_of_week": 2, "chronic_conditions": 2}
```

```json
{"age": 55, "scholarship": 0, "hipertension": 1, "diabetes": 0, "alcoholism": 0, "handcap": 0, "sms_received": 1, "lead_time_days": 0, "day_of_week": 3, "chronic_conditions": 1}
```

---

## Key Talking Points

| Question | Answer |
|----------|--------|
| "What model?" | Logistic Regression - interpretable, fast, ~67% AUC |
| "What features?" | Age, lead time, chronic conditions, SMS reminder |
| "How to integrate?" | REST API for real-time, batch for daily scoring |
| "Governance?" | Model registry + CI/CD approvals |
| "Cost?" | ~€50-100/month (scales to zero) |

---

## Closing

**Summary:**
> "You now have:
> - ✅ Model versioning & audit trail
> - ✅ Real-time API for EHR integration
> - ✅ Batch scoring for daily operations
> - ✅ CI/CD with approval gates
> - ✅ Self-hosted runner for security"

**Next Steps:**
1. Pilot with 2 clinics
2. Measure no-show reduction over 6 weeks
3. Expand to full deployment

---

## Troubleshooting

### Endpoint not responding
```bash
az ml online-endpoint show --name noshow-online-endpoint-staging \
  --resource-group rg-ai-hub-citadel-dev-02 \
  --workspace-name AI-WORKSPACE-shark
```

### Check deployment status
```bash
az ml online-deployment list --endpoint-name noshow-online-endpoint-staging \
  --resource-group rg-ai-hub-citadel-dev-02 \
  --workspace-name AI-WORKSPACE-shark
```

### View recent jobs
```bash
az ml job list --resource-group rg-ai-hub-citadel-dev-02 \
  --workspace-name AI-WORKSPACE-shark --max-results 5
```
