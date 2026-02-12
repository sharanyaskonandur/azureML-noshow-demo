# =============================================================================
# GitHub Self-Hosted Runner on Azure Container Instance
# =============================================================================
# This creates a self-hosted runner that can execute GitHub Actions workflows

variable "github_runner_token" {
  description = "GitHub runner registration token (get from repo Settings → Actions → Runners)"
  type        = string
  sensitive   = true
}

variable "github_repo_url" {
  description = "GitHub repository URL"
  type        = string
  default     = "https://github.com/skonandur_microsoft/azure-ml-repo"
}

variable "runner_name" {
  description = "Name for the runner"
  type        = string
  default     = "azure-ml-runner"
}

# Container Instance for GitHub Runner
resource "azurerm_container_group" "github_runner" {
  name                = "github-runner"
  location            = var.location
  resource_group_name = data.azurerm_resource_group.rg.name
  os_type             = "Linux"
  restart_policy      = "Always"

  container {
    name   = "github-runner"
    image  = "myoung34/github-runner:latest"
    cpu    = "2"
    memory = "4"

    environment_variables = {
      RUNNER_NAME_PREFIX = var.runner_name
      RUNNER_WORKDIR     = "/home/runner/work"
      REPO_URL           = var.github_repo_url
      RUNNER_SCOPE       = "repo"
      LABELS             = "azure,self-hosted,linux"
    }

    secure_environment_variables = {
      ACCESS_TOKEN = var.github_runner_token
    }

    ports {
      port     = 80
      protocol = "TCP"
    }
  }

  tags = {
    environment = var.environment
    purpose     = "github-runner"
  }
}

output "runner_status" {
  value = "GitHub runner deployed. Check repo Settings → Actions → Runners"
}
