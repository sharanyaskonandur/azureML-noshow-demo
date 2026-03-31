variable "prefix" {
  description = "Prefix used for naming all resources (e.g. noshow-demo)"
  type        = string
  default     = "noshow-demo"
}

variable "resource_group_name" {
  description = "Name of the Azure resource group to create"
  type        = string
}

variable "location" {
  description = "Azure region for all resources"
  type        = string
  default     = "swedencentral"
}

variable "storage_account_name" {
  description = "Globally unique name for the storage account (lowercase, no hyphens, 3-24 chars)"
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9]{3,24}$", var.storage_account_name))
    error_message = "Storage account name must be 3-24 lowercase alphanumeric characters."
  }
}

variable "acr_name" {
  description = "Globally unique name for the Azure Container Registry (alphanumeric, 5-50 chars)"
  type        = string

  validation {
    condition     = can(regex("^[a-zA-Z0-9]{5,50}$", var.acr_name))
    error_message = "ACR name must be 5-50 alphanumeric characters."
  }
}

variable "compute_vm_size" {
  description = "VM size for the Azure ML compute cluster"
  type        = string
  default     = "Standard_DS3_v2"
}

variable "compute_max_nodes" {
  description = "Maximum number of nodes in the ML compute cluster"
  type        = number
  default     = 2
}

variable "fabric_create_resources" {
  description = "Create a Microsoft Fabric workspace and lakehouse through the Fabric Terraform provider. Requires Fabric licensing, provider authentication, and an existing active Fabric capacity."
  type        = bool
  default     = false
}

variable "fabric_capacity_name" {
  description = "Display name of an existing active Fabric capacity used when fabric_create_resources is true."
  type        = string
  default     = null
}

variable "fabric_workspace_display_name" {
  description = "Display name for the Fabric workspace to create when fabric_create_resources is true."
  type        = string
  default     = "noshow fabric workspace"
}

variable "fabric_workspace_description" {
  description = "Description for the Fabric workspace to create."
  type        = string
  default     = "Fabric workspace for the no-show ML demo"
}

variable "fabric_lakehouse_display_name" {
  description = "Display name for the Fabric lakehouse to create when fabric_create_resources is true."
  type        = string
  default     = "noshow_fabric_lakehouse"
}

variable "fabric_lakehouse_description" {
  description = "Description for the Fabric lakehouse to create."
  type        = string
  default     = "Lakehouse for the no-show ML demo"
}

variable "fabric_lakehouse_enable_schemas" {
  description = "Create a schema-enabled Fabric lakehouse."
  type        = bool
  default     = true
}

variable "fabric_workspace_name" {
  description = "Optional existing Fabric workspace name used for OneLake access from Azure ML notebooks when fabric_create_resources is false."
  type        = string
  default     = null
}

variable "fabric_workspace_id" {
  description = "Optional existing Fabric workspace GUID. Prefer this when the workspace name contains spaces or special characters, or when fabric_create_resources is false."
  type        = string
  default     = null
}

variable "fabric_lakehouse_name" {
  description = "Optional existing Fabric lakehouse name used for OneLake access from Azure ML notebooks when fabric_create_resources is false."
  type        = string
  default     = null
}

variable "fabric_lakehouse_id" {
  description = "Optional existing Fabric lakehouse GUID. Prefer this when using GUID-based OneLake paths, or when fabric_create_resources is false."
  type        = string
  default     = null
}

variable "fabric_data_path" {
  description = "Relative path inside an existing Fabric lakehouse item, for example Files/noshow/KaggleV2-May-2016.csv"
  type        = string
  default     = "Files/noshow/KaggleV2-May-2016.csv"
}

variable "fabric_onelake_endpoint" {
  description = "OneLake DFS endpoint for an existing Fabric tenant. Override with a regional endpoint if data residency requires it."
  type        = string
  default     = "onelake.dfs.fabric.microsoft.com"
}

variable "tags" {
  description = "Tags applied to all resources"
  type        = map(string)
  default = {
    project         = "noshow-ml-demo"
    environment     = "dev"
    managed_by      = "terraform"
    SecurityControl = "Ignore"
  }
}
