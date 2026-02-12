# Azure ML Platform Quick Reference
## For Live Demo

## 🔗 Quick URLs

| Resource | URL |
|----------|-----|
| Azure ML Studio | https://ml.azure.com |
| Azure Portal | https://portal.azure.com |
| GitHub Actions | https://github.com/{your-repo}/actions |

---

## 📋 CLI Commands Cheat Sheet

### Model Operations
```powershell
# List models
az ml model list -g $RG -w $WS -o table

# Register model
az ml model create --name noshow-logreg --path outputs/ --type custom_model -g $RG -w $WS

# Show model details
az ml model show --name noshow-logreg --version 1 -g $RG -w $WS
```

### Online Endpoint Operations
```powershell
# List endpoints
az ml online-endpoint list -g $RG -w $WS -o table

# Create endpoint
az ml online-endpoint create --file deployment/online/online-endpoint.yml -g $RG -w $WS

# Create deployment
az ml online-deployment create --file deployment/online/online-deployment.yml --all-traffic -g $RG -w $WS

# Test endpoint
az ml online-endpoint invoke --name noshow-online-endpoint --request-file deployment/sample_requests.json -g $RG -w $WS

# Get endpoint URL
az ml online-endpoint show --name noshow-online-endpoint --query scoring_uri -o tsv -g $RG -w $WS
```

### Batch Endpoint Operations
```powershell
# Create batch endpoint
az ml batch-endpoint create --file deployment/batch/batch-endpoint.yml -g $RG -w $WS

# Create batch deployment
az ml batch-deployment create --file deployment/batch/batch-deployment.yml --set-default -g $RG -w $WS

# Invoke batch job
az ml batch-endpoint invoke --name noshow-batch-endpoint --input azureml://datastores/workspaceblobstore/paths/data/ -g $RG -w $WS
```

### Monitoring
```powershell
# List jobs (to show history)
az ml job list -g $RG -w $WS -o table --max-results 10

# Show specific job
az ml job show --name <job-name> -g $RG -w $WS
```

---

## 🧪 Test Payloads

### Single Prediction (copy-paste ready)
```json
{"age":25,"scholarship":1,"hipertension":0,"diabetes":0,"alcoholism":0,"handcap":0,"sms_received":0,"lead_time_days":21,"day_of_week":4,"chronic_conditions":0}
```

### Low Risk Patient
```json
{"age":45,"scholarship":0,"hipertension":1,"diabetes":0,"alcoholism":0,"handcap":0,"sms_received":1,"lead_time_days":5,"day_of_week":2,"chronic_conditions":1}
```

### High Risk Patient
```json
{"age":22,"scholarship":1,"hipertension":0,"diabetes":0,"alcoholism":1,"handcap":0,"sms_received":0,"lead_time_days":28,"day_of_week":0,"chronic_conditions":1}
```

---

## 🎯 Key Points to Emphasize

### For Thomas (Data Scientist)
- "You keep using Fabric notebooks for development"
- "Azure ML handles deployment complexity"
- "One command to update production model"

### For Reinier (Infra)
- "Managed compute - no VMs to patch"
- "Private endpoints available"
- "Managed identity - no credentials in code"

### For Edwin (BI)
- "Predictions land in Lakehouse automatically"
- "Power BI refreshes with daily risk list"
- "No change to your semantic models"

### For Sophie (AI Lead)
- "Full audit trail in model registry"
- "Approval gates before production"
- "Monitoring proves model reliability"

---

## ⚠️ Common Demo Issues & Fixes

| Issue | Quick Fix |
|-------|-----------|
| Endpoint not responding | Check deployment status: `az ml online-deployment show` |
| 401 Unauthorized | Refresh API key: `az ml online-endpoint get-credentials` |
| Model not found | Check model name/version: `az ml model list` |
| Slow response | First call is cold start (~10s), subsequent calls fast |

---

## 📊 Talking Points by Persona

### "Why not just Fabric?"
> "Fabric = Development. Azure ML = Production. They complement each other."

### "What about cost?"
> "Batch endpoint: ~€50-100/month (scales to zero). Compare to €217K saved from 10% no-show reduction."

### "Timeline?"
> "Register model: 1 hour. Deploy endpoint: 2 hours. Set up CI/CD: 1 day. Pilot: 6-8 weeks."

### "Security?"
> "Data stays in your tenant. West Europe region. Managed identity. Private endpoints optional."
