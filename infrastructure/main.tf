# =============================================================================
# Azure ML Demo Infrastructure
# Creates: ADLS Gen2 + Azure ML Workspace Data Connection
# =============================================================================

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.80"
    }
  }
  required_version = ">= 1.5.0"
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
  tenant_id       = var.tenant_id
}

# =============================================================================
# VARIABLES
# =============================================================================

variable "subscription_id" {
  description = "Azure Subscription ID"
  type        = string
  default     = "8a7af4dd-523e-4175-b231-d31d36752280"
}

variable "tenant_id" {
  description = "Azure Tenant ID"
  type        = string
  default     = "9ca9b358-1044-426c-abf5-94ea79276525"
}

variable "resource_group_name" {
  description = "Resource group for ML demo"
  type        = string
  default     = "rg-ai-hub-citadel-dev-02"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "swedencentral"
}

variable "storage_account_name" {
  description = "Storage account name (must be globally unique)"
  type        = string
  default     = "mldemolakeshark"  # Change if taken
}

variable "ml_workspace_name" {
  description = "Azure ML Workspace name"
  type        = string
  default     = "AI-WORKSPACE-shark"
}

variable "environment" {
  description = "Environment tag"
  type        = string
  default     = "demo"
}

# =============================================================================
# DATA SOURCES
# =============================================================================

# Reference existing resource group
data "azurerm_resource_group" "rg" {
  name = var.resource_group_name
}

# Reference existing Azure ML workspace
data "azurerm_machine_learning_workspace" "ml" {
  name                = var.ml_workspace_name
  resource_group_name = var.resource_group_name
}

# =============================================================================
# STORAGE ACCOUNT (ADLS Gen2)
# =============================================================================

resource "azurerm_storage_account" "datalake" {
  name                     = var.storage_account_name
  resource_group_name      = data.azurerm_resource_group.rg.name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  
  # Enable hierarchical namespace for ADLS Gen2
  is_hns_enabled = true
  
  # Security settings
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false
  shared_access_key_enabled       = true

  blob_properties {
    versioning_enabled = true
    
    delete_retention_policy {
      days = 7
    }
    
    container_delete_retention_policy {
      days = 7
    }
  }

  tags = {
    environment = var.environment
    project     = "noshow-ml-demo"
    purpose     = "ml-data-lake"
  }
}

# =============================================================================
# DATA LAKE CONTAINERS (File Systems)
# =============================================================================

resource "azurerm_storage_data_lake_gen2_filesystem" "raw" {
  name               = "raw"
  storage_account_id = azurerm_storage_account.datalake.id
}

resource "azurerm_storage_data_lake_gen2_filesystem" "processed" {
  name               = "processed"
  storage_account_id = azurerm_storage_account.datalake.id
}

resource "azurerm_storage_data_lake_gen2_filesystem" "ml-data" {
  name               = "ml-data"
  storage_account_id = azurerm_storage_account.datalake.id
}

# Create folder structure in ml-data container
resource "azurerm_storage_data_lake_gen2_path" "noshow_folder" {
  path               = "noshow"
  filesystem_name    = azurerm_storage_data_lake_gen2_filesystem.ml-data.name
  storage_account_id = azurerm_storage_account.datalake.id
  resource           = "directory"
}

# =============================================================================
# IAM - Grant Azure ML Workspace access to Storage
# =============================================================================

# Storage Blob Data Contributor for Azure ML managed identity
resource "azurerm_role_assignment" "ml_storage_contributor" {
  scope                = azurerm_storage_account.datalake.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = data.azurerm_machine_learning_workspace.ml.identity[0].principal_id
}

# Storage Blob Data Reader (for read-only scenarios)
resource "azurerm_role_assignment" "ml_storage_reader" {
  scope                = azurerm_storage_account.datalake.id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = data.azurerm_machine_learning_workspace.ml.identity[0].principal_id
}

# =============================================================================
# AZURE ML DATASTORE CONNECTION
# =============================================================================

resource "azurerm_machine_learning_datastore_datalake_gen2" "noshow_data" {
  name                 = "noshow_datalake"
  workspace_id         = data.azurerm_machine_learning_workspace.ml.id
  storage_container_id = azurerm_storage_data_lake_gen2_filesystem.ml-data.id
  
  # Use workspace managed identity (no keys needed)
  # This requires the role assignments above
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "storage_account_name" {
  description = "Storage account name"
  value       = azurerm_storage_account.datalake.name
}

output "storage_account_id" {
  description = "Storage account ID"
  value       = azurerm_storage_account.datalake.id
}

output "datalake_endpoint" {
  description = "ADLS Gen2 DFS endpoint"
  value       = azurerm_storage_account.datalake.primary_dfs_endpoint
}

output "ml_data_container_url" {
  description = "ML data container URL"
  value       = "abfss://ml-data@${azurerm_storage_account.datalake.name}.dfs.core.windows.net/"
}

output "datastore_name" {
  description = "Azure ML Datastore name"
  value       = azurerm_machine_learning_datastore_datalake_gen2.noshow_data.name
}

output "upload_command" {
  description = "Command to upload data"
  value       = "azcopy copy './data/KaggleV2-May-2016.csv' 'https://${azurerm_storage_account.datalake.name}.dfs.core.windows.net/ml-data/noshow/'"
}
