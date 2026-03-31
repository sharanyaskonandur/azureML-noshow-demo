output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.rg.name
}

output "ml_workspace_name" {
  description = "Name of the Azure ML workspace"
  value       = azurerm_machine_learning_workspace.mlw.name
}

output "ml_workspace_id" {
  description = "Resource ID of the Azure ML workspace"
  value       = azurerm_machine_learning_workspace.mlw.id
}

output "ml_workspace_principal_id" {
  description = "System-assigned managed identity principal ID for the Azure ML workspace"
  value       = azurerm_machine_learning_workspace.mlw.identity[0].principal_id
}

output "storage_account_name" {
  description = "Name of the storage account"
  value       = azurerm_storage_account.storage.name
}

output "key_vault_name" {
  description = "Name of the Key Vault"
  value       = azurerm_key_vault.kv.name
}

output "acr_login_server" {
  description = "Login server URL for the container registry"
  value       = azurerm_container_registry.acr.login_server
}

output "application_insights_connection_string" {
  description = "Application Insights connection string"
  value       = azurerm_application_insights.ai.connection_string
  sensitive   = true
}

output "compute_cluster_name" {
  description = "Name of the ML compute cluster"
  value       = azurerm_machine_learning_compute_cluster.cpu_cluster.name
}

output "compute_cluster_principal_id" {
  description = "System-assigned managed identity principal ID for the Azure ML compute cluster"
  value       = azurerm_machine_learning_compute_cluster.cpu_cluster.identity[0].principal_id
}

output "fabric_capacity_id" {
  description = "ID of the Fabric capacity used for the created Fabric workspace, if enabled."
  value       = var.fabric_create_resources ? data.fabric_capacity.capacity[0].id : null
}

output "fabric_workspace_name" {
  description = "Name of the effective Fabric workspace, either created by Terraform or supplied as existing metadata."
  value       = local.fabric_workspace_name_effective
}

output "fabric_workspace_id" {
  description = "ID of the effective Fabric workspace, either created by Terraform or supplied as existing metadata."
  value       = local.fabric_workspace_id_effective
}

output "fabric_workspace_identity_principal_id" {
  description = "System-assigned managed identity principal ID for the created Fabric workspace, if enabled."
  value       = var.fabric_create_resources ? fabric_workspace.fabric[0].identity.service_principal_id : null
}

output "fabric_workspace_identity_application_id" {
  description = "System-assigned managed identity application ID for the created Fabric workspace, if enabled."
  value       = var.fabric_create_resources ? fabric_workspace.fabric[0].identity.application_id : null
}

output "fabric_lakehouse_name" {
  description = "Name of the effective Fabric lakehouse, either created by Terraform or supplied as existing metadata."
  value       = local.fabric_lakehouse_name_effective
}

output "fabric_lakehouse_id" {
  description = "ID of the effective Fabric lakehouse, either created by Terraform or supplied as existing metadata."
  value       = local.fabric_lakehouse_id_effective
}

output "fabric_notebook_connection" {
  description = "Fabric/OneLake values to use from an Azure ML notebook, sourced either from created Fabric resources or from provided existing metadata."
  value = {
    workspace_name   = local.fabric_workspace_name_effective
    workspace_id     = local.fabric_workspace_id_effective
    lakehouse_name   = local.fabric_lakehouse_name_effective
    lakehouse_id     = local.fabric_lakehouse_id_effective
    data_path        = var.fabric_data_path
    onelake_endpoint = local.fabric_onelake_endpoint_effective
    provisioning_note = var.fabric_create_resources ? "Fabric workspace and lakehouse are managed by Terraform in this stack." : "Fabric workspace and lakehouse must already exist in Microsoft Fabric."
    https_uri = local.fabric_workspace_name_effective != null && local.fabric_lakehouse_name_effective != null ? format(
      "https://%s/%s/%s.lakehouse/%s",
      local.fabric_onelake_endpoint_effective,
      local.fabric_workspace_name_effective,
      local.fabric_lakehouse_name_effective,
      trim(var.fabric_data_path, "/")
    ) : null
    abfss_uri = local.fabric_workspace_name_effective != null && local.fabric_lakehouse_name_effective != null ? format(
      "abfss://%s@%s/%s.lakehouse/%s",
      local.fabric_workspace_name_effective,
      local.fabric_onelake_endpoint_effective,
      local.fabric_lakehouse_name_effective,
      trim(var.fabric_data_path, "/")
    ) : null
    https_uri_guid = local.fabric_workspace_id_effective != null && local.fabric_lakehouse_id_effective != null ? format(
      "https://%s/%s/%s/%s",
      local.fabric_onelake_endpoint_effective,
      local.fabric_workspace_id_effective,
      local.fabric_lakehouse_id_effective,
      trim(var.fabric_data_path, "/")
    ) : null
  }
}
