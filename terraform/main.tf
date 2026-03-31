terraform {
  required_version = ">= 1.8.0, < 2.0.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
    fabric = {
      source  = "microsoft/fabric"
      version = "1.4.0"
    }
  }

  backend "local" {}
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = false
    }
  }
}

provider "fabric" {}

# -----------------------------------------------------------------------------
# Data sources
# -----------------------------------------------------------------------------
data "azurerm_client_config" "current" {}

data "fabric_capacity" "capacity" {
  count        = var.fabric_create_resources ? 1 : 0
  display_name = var.fabric_capacity_name

  lifecycle {
    postcondition {
      condition     = self.state == "Active"
      error_message = "Fabric Capacity is not in Active state."
    }
  }
}

locals {
  fabric_workspace_name_effective = var.fabric_create_resources ? fabric_workspace.fabric[0].display_name : var.fabric_workspace_name
  fabric_workspace_id_effective   = var.fabric_create_resources ? fabric_workspace.fabric[0].id : var.fabric_workspace_id
  fabric_lakehouse_name_effective = var.fabric_create_resources ? fabric_lakehouse.fabric[0].display_name : var.fabric_lakehouse_name
  fabric_lakehouse_id_effective   = var.fabric_create_resources ? fabric_lakehouse.fabric[0].id : var.fabric_lakehouse_id
  fabric_onelake_endpoint_effective = var.fabric_create_resources ? replace(
    fabric_workspace.fabric[0].onelake_endpoints.dfs_endpoint,
    "https://",
    ""
  ) : var.fabric_onelake_endpoint
}

# -----------------------------------------------------------------------------
# Resource Group
# -----------------------------------------------------------------------------
resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}

# -----------------------------------------------------------------------------
# Log Analytics Workspace (required by Application Insights)
# -----------------------------------------------------------------------------
resource "azurerm_log_analytics_workspace" "law" {
  name                = "${var.prefix}-law"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = var.tags
}

# -----------------------------------------------------------------------------
# Application Insights
# -----------------------------------------------------------------------------
resource "azurerm_application_insights" "ai" {
  name                = "${var.prefix}-ai"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  workspace_id        = azurerm_log_analytics_workspace.law.id
  application_type    = "web"
  local_authentication_disabled = true
  tags                = var.tags
}

# -----------------------------------------------------------------------------
# Storage Account (for ML workspace default storage)
# -----------------------------------------------------------------------------
resource "azurerm_storage_account" "storage" {
  name                     = var.storage_account_name
  location                 = azurerm_resource_group.rg.location
  resource_group_name      = azurerm_resource_group.rg.name
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"
  tags                     = var.tags
}


# -----------------------------------------------------------------------------
# Key Vault
# -----------------------------------------------------------------------------
resource "azurerm_key_vault" "kv" {
  name                     = "${var.prefix}-kv"
  location                 = azurerm_resource_group.rg.location
  resource_group_name      = azurerm_resource_group.rg.name
  tenant_id                = data.azurerm_client_config.current.tenant_id
  sku_name                 = "standard"
  purge_protection_enabled = true
  tags                     = var.tags
}

# -----------------------------------------------------------------------------
# Azure Container Registry (for custom scoring environments)
# -----------------------------------------------------------------------------
resource "azurerm_container_registry" "acr" {
  name                = var.acr_name
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "Basic"
  admin_enabled       = false
  tags                = var.tags
}

# -----------------------------------------------------------------------------
# Azure Machine Learning Workspace
# -----------------------------------------------------------------------------
resource "azurerm_machine_learning_workspace" "mlw" {
  name                          = "${var.prefix}-mlw"
  location                      = azurerm_resource_group.rg.location
  resource_group_name           = azurerm_resource_group.rg.name
  application_insights_id       = azurerm_application_insights.ai.id
  key_vault_id                  = azurerm_key_vault.kv.id
  storage_account_id            = azurerm_storage_account.storage.id
  container_registry_id         = azurerm_container_registry.acr.id
  public_network_access_enabled = true

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

# -----------------------------------------------------------------------------
# Compute Cluster for training (scales to 0 when idle)
# -----------------------------------------------------------------------------
resource "azurerm_machine_learning_compute_cluster" "cpu_cluster" {
  name                          = "cpu-cluster"
  location                      = azurerm_resource_group.rg.location
  machine_learning_workspace_id = azurerm_machine_learning_workspace.mlw.id
  vm_priority                   = "Dedicated"
  vm_size                       = var.compute_vm_size

  scale_settings {
    min_node_count                       = 0
    max_node_count                       = var.compute_max_nodes
    scale_down_nodes_after_idle_duration = "PT5M"
  }

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

# -----------------------------------------------------------------------------
# Microsoft Fabric resources (optional)
# -----------------------------------------------------------------------------
resource "fabric_workspace" "fabric" {
  count        = var.fabric_create_resources ? 1 : 0
  display_name = var.fabric_workspace_display_name
  description  = var.fabric_workspace_description
  capacity_id  = data.fabric_capacity.capacity[0].id

  identity = {
    type = "SystemAssigned"
  }
}

resource "fabric_lakehouse" "fabric" {
  count        = var.fabric_create_resources ? 1 : 0
  display_name = var.fabric_lakehouse_display_name
  description  = var.fabric_lakehouse_description
  workspace_id = fabric_workspace.fabric[0].id

  configuration = {
    enable_schemas = var.fabric_lakehouse_enable_schemas
  }
}
