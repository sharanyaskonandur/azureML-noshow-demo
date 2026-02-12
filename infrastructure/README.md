# Infrastructure Setup

This Terraform configuration creates:

| Resource | Purpose |
|----------|---------|
| ADLS Gen2 Storage Account | Data lake for ML data |
| File Systems (containers) | `raw`, `processed`, `ml-data` |
| IAM Role Assignments | Azure ML workspace access to storage |
| Azure ML Datastore | Connect data lake to ML workspace |

## Prerequisites

1. **Terraform** >= 1.5.0
2. **Azure CLI** logged in: `az login`
3. **Permissions**: Owner/Contributor on resource group

## Quick Start

```bash
cd infrastructure

# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Apply (creates resources)
terraform apply
```

## After Deployment

### 1. Upload Data to Data Lake

```bash
# Using azcopy (faster)
azcopy copy "../data/KaggleV2-May-2016.csv" "https://mldemolakeshark.dfs.core.windows.net/ml-data/noshow/"

# Or using Azure CLI
az storage fs file upload \
    --source ../data/KaggleV2-May-2016.csv \
    --path noshow/KaggleV2-May-2016.csv \
    --file-system ml-data \
    --account-name mldemolakeshark \
    --auth-mode login
```

### 2. Use in Notebook

```python
# Load from Azure ML Datastore
from azure.ai.ml import MLClient

# The datastore is automatically registered
datastore = ml_client.datastores.get("noshow_datalake")
data_path = f"azureml://datastores/{datastore.name}/paths/noshow/KaggleV2-May-2016.csv"

# Or load directly from ADLS
df = pd.read_csv("abfss://ml-data@mldemolakeshark.dfs.core.windows.net/noshow/KaggleV2-May-2016.csv",
                 storage_options={"anon": False})
```

## Resources Created

```
Resource Group: rg-ai-hub-citadel-dev-02
├── Storage Account: mldemolakeshark (ADLS Gen2)
│   ├── Container: raw/
│   ├── Container: processed/
│   └── Container: ml-data/
│       └── noshow/  (folder for no-show data)
└── Azure ML Workspace: AI-WORKSPACE-shark
    └── Datastore: noshow_datalake → ml-data container
```

## Clean Up

```bash
terraform destroy
```

## Troubleshooting

**Storage account name taken:**
Change `storage_account_name` in `terraform.tfvars` to a unique name.

**Permission denied:**
Ensure you have Owner/Contributor role on the resource group.

**Azure ML workspace not found:**
Verify the workspace name in `terraform.tfvars` matches exactly.
