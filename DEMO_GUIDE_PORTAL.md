# 🎯 Azure ML Demo Guide
## OneLake + GitHub + Portal Flow

**Duration:** 30-40 minutes  
**Focus:** Production readiness, sustainability, governance

---

## Pre-Demo Setup Checklist

### 1. OneLake Data Setup
- [ ] Fabric Workspace created
- [ ] Lakehouse created (e.g., `NoShowLakehouse`)
- [ ] Data uploaded via `scripts/upload_to_onelake.py`:
  ```bash
  python scripts/upload_to_onelake.py \
    --workspace-id "YOUR_WORKSPACE_GUID" \
    --lakehouse "NoShowLakehouse"
  ```
- [ ] Verify data in Fabric portal: https://app.fabric.microsoft.com

### 2. GitHub Repository
- [ ] Repo pushed to GitHub
- [ ] GitHub Secrets configured:
  - `AZURE_CLIENT_ID`
  - `AZURE_TENANT_ID`
  - `AZURE_SUBSCRIPTION_ID`
- [ ] GitHub Variables configured:
  - `AZURE_ML_WORKSPACE` = AI-WORKSPACE-shark
  - `AZURE_ML_RESOURCE_GROUP` = rg-ai-hub-citadel-dev-02
  - `AZURE_SUBSCRIPTION_ID` = 8a7af4dd-523e-4175-b231-d31d36752280
  - `FABRIC_WORKSPACE_ID` = (your Fabric workspace GUID)
  - `FABRIC_LAKEHOUSE` = NoShowLakehouse
- [ ] Environments created: `staging`, `production` (with approval)

### 3. Azure ML Portal
- [ ] Workspace URL ready: https://ml.azure.com
- [ ] Model registered: `noshow-logreg`
- [ ] Endpoint deployed: `noshow-online-endpoint`

---

## Demo Flow

### Part 1: Data in OneLake (5 min)

**Open:** https://app.fabric.microsoft.com → Your Workspace

**Say:**
> "The data lives in Microsoft Fabric's OneLake. This is your unified data layer - same data for BI, Data Science, and ML."

**Show:**
1. **Lakehouse** → `NoShowLakehouse`
2. **Files** → `raw/KaggleV2-May-2016.csv`
3. **Files** → `silver/appointments/` (cleaned data)

**Business call-out:**
> "Your data platform team manages this. ML team reads from it. No data duplication."

---

### Part 2: GitHub CI/CD (8 min)

**Open:** https://github.com/YOUR_REPO/actions

**Say:**
> "Every code change triggers this automated pipeline. Nothing reaches production without tests, training, and approval."

**Show the workflow:**
```
Push Code → Tests → Train → Register → Deploy Staging → [Approval] → Production
```

**Click through:**
1. **Actions tab** → Show workflow runs
2. **Workflow file** → `.github/workflows/mlops.yml`
3. **Environments** → Show `staging` and `production` with protection rules

**Demo: Trigger a workflow**
```
Click "Run workflow" → Watch the pipeline start
```

**For Infra team:**
> "Same patterns you use for app deployments. Infrastructure as code. Everything in Git."

---

### Part 3: Azure ML Portal - Model Registry (7 min)

**Open:** https://ml.azure.com → Models

**Say:**
> "Every model version is tracked here. This is your audit trail."

**Show:**
1. **Model list** → `noshow-logreg`
2. **Versions** → "Each CI run creates a new version"
3. **Model details**:
   - Artifacts (model.joblib, scaler.joblib)
   - Tags (AUC score, build number, git commit)
   - Description

**Business call-out:**
> "When auditors ask 'what model made this prediction?', you answer in 10 seconds."

---

### Part 4: Azure ML Portal - Endpoints (8 min)

**Open:** https://ml.azure.com → Endpoints

#### Online Endpoint (Real-time API)
**Show:**
1. **Endpoint overview** → `noshow-online-endpoint`
2. **Deployments** → Blue deployment
3. **Test tab** → Live test:
```json
{
  "age": 25,
  "scholarship": 1,
  "hipertension": 0,
  "diabetes": 0,
  "alcoholism": 0,
  "handcap": 0,
  "sms_received": 0,
  "lead_time_days": 21,
  "day_of_week": 4,
  "chronic_conditions": 0
}
```

4. **Consume tab** → Show:
   - REST endpoint URL
   - API key
   - Sample code (Python, C#, curl)

**Say:**
> "This is a REST API. HiX calls this when a patient books. Response in under 100ms."

---

### Part 5: Monitoring & Cost (5 min)

**Open:** https://ml.azure.com → Endpoints → noshow-online-endpoint → Metrics

**Show:**
1. **Request count** → Traffic volume
2. **Latency** → Response times
3. **Errors** → Error rate

**Then:** Azure Portal → Cost Management

**Filter by:**
- Resource group: `rg-ai-hub-citadel-dev-02`
- Tag: `ml.azure.com`

**Say:**
> "Online endpoint: ~€50-100/month for single instance. Scales automatically under load."

---

### Part 6: Closing - Why Azure ML? (3 min)

**Summary slide:**

| They Asked | We Showed |
|------------|-----------|
| "Is it sustainable?" | Monitoring, auto-scaling, managed compute |
| "Why not just Fabric?" | Fabric = data + dev. Azure ML = production ops |
| "Can it run in production?" | Live endpoint, CI/CD, approval gates |
| "Governance?" | Model registry + GitHub + audit trail |

**Next steps:**
1. **Week 1:** Upload production data to OneLake
2. **Week 2:** Deploy pilot endpoint
3. **Week 4-8:** Measure no-show reduction
4. **Decision:** Expand or iterate

---

## Quick Commands

### Test the endpoint (curl)
```bash
curl -X POST "https://noshow-online-endpoint.swedencentral.inference.ml.azure.com/score" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"age":25,"scholarship":1,"hipertension":0,"diabetes":0,"alcoholism":0,"handcap":0,"sms_received":0,"lead_time_days":21,"day_of_week":4,"chronic_conditions":0}'
```

### Test the endpoint (PowerShell)
```powershell
$headers = @{
    "Authorization" = "Bearer YOUR_API_KEY"
    "Content-Type" = "application/json"
}
$body = '{"age":25,"scholarship":1,"hipertension":0,"diabetes":0,"alcoholism":0,"handcap":0,"sms_received":0,"lead_time_days":21,"day_of_week":4,"chronic_conditions":0}'

Invoke-RestMethod -Uri "https://noshow-online-endpoint.swedencentral.inference.ml.azure.com/score" -Method Post -Headers $headers -Body $body
```

### Trigger GitHub workflow
```bash
gh workflow run mlops.yml
```

---

## Talking Points

### "Why can't we do this in Fabric?"
> "Fabric is excellent for data and notebooks. Azure ML adds:
> - Managed endpoints (no infra to manage)
> - Model versioning (audit trail)
> - Monitoring & drift detection
> - CI/CD integration
> 
> They complement each other. Fabric for dev, Azure ML for production."

### "What about cost?"
> "Online endpoint: ~€50-100/month for Standard_DS3_v2. 
> Compare to €200K+ annual cost of no-shows.
> Compute scales to zero when not used."

### "Security?"
> - Data stays in your tenant (West Europe)
> - Managed identity (no credentials in code)
> - Private endpoints available
> - Full RBAC integration

---

## URLs to Have Open

| Resource | URL |
|----------|-----|
| Fabric | https://app.fabric.microsoft.com |
| GitHub | https://github.com/YOUR_REPO |
| Azure ML | https://ml.azure.com |
| Azure Portal | https://portal.azure.com |

---

*Demo guide for OneLake + GitHub + Portal flow*
