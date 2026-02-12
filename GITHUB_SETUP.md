# GitHub Repository Setup

## Quick Setup

### 1. Create GitHub Repository
```bash
# Create a new repo on GitHub, then:
cd "c:\Users\skonandur\OneDrive - Microsoft\Documents\ML DEMO\noshow-ml-demo"
git init
git add .
git commit -m "Initial commit: No-show prediction demo"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/noshow-ml-demo.git
git push -u origin main
```

### 2. Configure GitHub Secrets

Go to: **Repository → Settings → Secrets and variables → Actions → Secrets**

Add these secrets:

| Secret Name | Value | How to Get |
|-------------|-------|------------|
| `AZURE_CLIENT_ID` | Service Principal App ID | Azure Portal → App registrations |
| `AZURE_TENANT_ID` | Azure AD Tenant ID | Azure Portal → Azure Active Directory |
| `AZURE_SUBSCRIPTION_ID` | `8a7af4dd-523e-4175-b231-d31d36752280` | Azure Portal → Subscriptions |

### 3. Configure GitHub Variables

Go to: **Repository → Settings → Secrets and variables → Actions → Variables**

Add these variables:

| Variable Name | Value |
|---------------|-------|
| `AZURE_ML_WORKSPACE` | `AI-WORKSPACE-shark` |
| `AZURE_ML_RESOURCE_GROUP` | `rg-ai-hub-citadel-dev-02` |
| `AZURE_SUBSCRIPTION_ID` | `8a7af4dd-523e-4175-b231-d31d36752280` |
| `FABRIC_WORKSPACE_ID` | Your Fabric workspace GUID |
| `FABRIC_LAKEHOUSE` | `NoShowLakehouse` |

### 4. Create Environments

Go to: **Repository → Settings → Environments**

Create two environments:

1. **staging**
   - No protection rules (deploys automatically)

2. **production**
   - ✅ Required reviewers: Add yourself or team lead
   - ✅ Wait timer: 0 minutes (optional: add delay)

### 5. Create Service Principal for GitHub

```bash
# Create service principal
az ad sp create-for-rbac --name "github-noshow-demo" \
  --role contributor \
  --scopes /subscriptions/8a7af4dd-523e-4175-b231-d31d36752280 \
  --json-auth

# Note the output:
# {
#   "clientId": "xxx",        → AZURE_CLIENT_ID
#   "clientSecret": "xxx",    → (not needed for OIDC)
#   "tenantId": "xxx",        → AZURE_TENANT_ID
#   ...
# }
```

### 6. Configure Federated Credentials (OIDC)

For secure, keyless authentication:

1. Go to: Azure Portal → App registrations → Your SP → Certificates & secrets → Federated credentials
2. Add credential:
   - Scenario: GitHub Actions deploying Azure resources
   - Organization: YOUR_GITHUB_USERNAME
   - Repository: noshow-ml-demo
   - Entity: Branch
   - Branch: main

---

## Test the Pipeline

```bash
# Make a small change
echo "# Updated" >> README.md
git add README.md
git commit -m "Test CI/CD pipeline"
git push
```

Then check: https://github.com/YOUR_USERNAME/noshow-ml-demo/actions

---

## File Structure for GitHub

```
noshow-ml-demo/
├── .github/
│   └── workflows/
│       └── mlops.yml          # CI/CD pipeline
├── data/
│   └── prepare_kaggle_data.py # Data prep (optional)
├── deployment/
│   ├── batch/
│   │   ├── batch-endpoint.yml
│   │   ├── batch-deployment.yml
│   │   ├── environment.yml
│   │   └── src/score_batch.py
│   └── online/
│       ├── online-endpoint.yml
│       ├── online-deployment.yml
│       ├── environment.yml
│       └── src/score_online.py
├── notebooks/
│   └── 01_train_noshow_model.ipynb
├── outputs/                    # (gitignored - generated)
├── scripts/
│   └── upload_to_onelake.py
├── tests/
│   └── test_noshow_model.py
├── .gitignore
├── README.md
└── requirements.txt
```
