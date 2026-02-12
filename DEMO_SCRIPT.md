# 🎯 Azure ML Platform Demo Script
## Focus: From Fabric Development → Production with Azure ML

**Duration:** 30 minutes  
**Audience:** Thomas (Data Scientist), Reinier (Infra), Edwin (BI), Sophie (AI Lead)  
**Key Message:** *"Azure ML bridges the gap between your Fabric notebooks and production-ready ML operations."*

---

## Pre-Demo Checklist

- [ ] Azure ML Studio open in browser
- [ ] Model already registered (or ready to register live)
- [ ] GitHub repo with workflow visible
- [ ] This script open for reference

---

## Demo Flow

### Opening (2 min)

**Say:**
> "I know you've already built a working no-show prediction model in Fabric. Thomas, you mentioned the challenge is getting it into production sustainably. Today I'll show you how Azure ML solves that exact problem."

**Show:** Architecture slide (if you have one) or draw quickly:
```
Fabric Notebook → Azure ML Registry → Endpoints → Power BI / HiX
                         ↑
                    GitHub CI/CD
```

---

### Part 1: Model Registry (8 min) ⭐ KEY SECTION

**Open:** https://ml.azure.com → Models

**Say:**
> "This is where your model lives once it leaves the notebook. Every version is tracked."

**Show & Click:**
1. **Model list** → "Here's your no-show model"
2. **Version history** → "Every training run creates a new version"
3. **Model details** → Show:
   - Artifacts (model.joblib, scaler.joblib)
   - Tags (AUC score, build number)
   - Description

**Say:**
> "When a regulator asks 'which model made this prediction on January 15th?', you can answer in 10 seconds."

**Business call-out for Sophie:**
> "This is your audit trail. NEN 7510 compliance loves this."

#### Live Demo: Register a Model (Optional)
```bash
az ml model create --name noshow-logreg --path outputs/ --type custom_model
```

---

### Part 2: Batch Endpoint (7 min) ⭐ KEY SECTION

**Say:**
> "You already have batch inference running daily. Let's make it production-grade."

**Open:** Azure ML → Endpoints → Batch endpoints

**Show & Click:**
1. **Create batch endpoint** (or show existing)
2. **Deployment configuration:**
   - Compute cluster (CPU)
   - Scaling (1-4 nodes)
   - Retry settings

**Say:**
> "Every morning at 6am, this pulls tomorrow's appointments from your Lakehouse, scores them, and writes predictions back. By the time planners arrive at 8am, the risk list is ready in Power BI."

**Show the flow:**
```
Lakehouse (appointments) → Batch Endpoint → Lakehouse (predictions) → Power BI
```

**For Reinier (Infra):**
> "This runs on managed compute. No VMs to patch. Auto-scales down to zero when not running."

---

### Part 3: Online Endpoint (5 min)

**Say:**
> "For your HiX integration use case—where you want real-time scoring—here's the online endpoint."

**Open:** Azure ML → Endpoints → Real-time endpoints

**Show:**
1. **Endpoint URL** → "This is a REST API"
2. **Test tab** → Live test with sample JSON:
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

**Say:**
> "Response in under 100ms. This is how middleware calls the model when a patient books an appointment in HiX."

**Show response:**
```json
{
  "no_show_risk": 0.72,
  "risk_category": "Very High",
  "risk_flag": 1
}
```

---

### Part 4: CI/CD with GitHub (5 min) ⭐ KEY SECTION

**Open:** GitHub → Actions tab (or show workflow file)

**Say:**
> "You mentioned you're starting with GitHub. Here's how model deployment becomes part of your DevOps."

**Show the workflow:**
```
Push Code → Run Tests → Train Model → Register → Deploy Staging → [Approval] → Production
```

**Click through:**
1. **Workflow runs** → Show green checkmarks
2. **Protected environment** → "Production requires approval"
3. **Approval gate** → "Sophie or Bas must click approve"

**Say:**
> "Nothing reaches production without human approval. This is governance built into the pipeline."

**For Reinier:**
> "Same patterns you use for database deployments. Infrastructure as code."

---

### Part 5: Monitoring (3 min)

**Open:** Azure ML → Monitoring (or Model details → Monitoring tab)

**Say:**
> "You asked if this is sustainable. Here's how you know the model is still working."

**Show:**
1. **Data drift dashboard** → "Are inputs changing?"
2. **Prediction distribution** → "Is the model behaving differently?"
3. **Alert rules** → "Email/Teams when drift exceeds threshold"

**Say:**
> "You'll know the model needs retraining before the business feels the impact."

---

### Closing (2 min)

**Say:**
> "Let me summarize what Azure ML gives you:"

| Challenge You Have | Azure ML Solution |
|-------------------|-------------------|
| "How to productionize?" | Managed endpoints (batch + online) |
| "Is it sustainable?" | Monitoring + drift detection |
| "Governance?" | Model registry + CI/CD approvals |
| "Integration with HiX?" | REST API (online endpoint) |

**Next steps:**
> "For your April timeline, I'd suggest:
> 1. Register your current model this week
> 2. Deploy batch endpoint for 2 pilot clinics
> 3. Measure impact over 6 weeks
> 4. Add online endpoint for HiX when ready"

---

## Objection Handling

### "Can't we do this in Fabric?"
> "Fabric is excellent for development. Azure ML adds production-grade deployment, versioning, and monitoring. They work together—Fabric for dev, Azure ML for ops."

### "This looks complex"
> "The initial setup takes a few hours. After that, deploying a new model version is one command or one PR merge. Thomas can focus on improving the model, not managing infrastructure."

### "Cost?"
> "Batch endpoints scale to zero when not running. For daily scoring, you're looking at ~€50-100/month compute. Compare that to the €200K+ savings from reducing no-shows."

### "Security for patient data?"
> "Data stays in your Azure tenant. Use managed identities—no credentials in code. Private endpoints available if needed."

---

## Key URLs to Have Open

1. **Azure ML Studio:** https://ml.azure.com
2. **GitHub repo:** (your repo with the workflow)
3. **This script:** For reference

---

## After the Demo

- [ ] Share Azure ML documentation links
- [ ] Offer follow-up session for hands-on setup
- [ ] Send pilot proposal for 2 clinics
- [ ] Schedule next meeting for technical deep-dive with Thomas

---

*Remember: They already understand the use case. Show them the platform.*
