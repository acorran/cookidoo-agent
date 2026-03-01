"""
Azure Infrastructure Deployment for Cookidoo Agent Assistant.

Deploys the Azure resources needed to connect Azure Databricks to the
MCP server running in Azure Container Apps over a private network.

Architecture:
    ┌───────────────────────────────────────────────────────────┐
    │                    Azure Subscription                      │
    │                                                           │
    │  ┌─────────────────────────────────────────────────────┐  │
    │  │              VNet: cookidoo-vnet (10.0.0.0/16)      │  │
    │  │                                                     │  │
    │  │  ┌─────────────────┐   ┌──────────────────────┐    │  │
    │  │  │  Subnet:        │   │  Subnet:             │    │  │
    │  │  │  databricks-    │   │  container-apps-     │    │  │
    │  │  │  private        │   │  subnet              │    │  │
    │  │  │  10.0.1.0/24    │   │  10.0.3.0/23         │    │  │
    │  │  │                 │   │                      │    │  │
    │  │  │  ┌───────────┐  │   │  ┌────────────────┐  │    │  │
    │  │  │  │ Databricks│  │   │  │ Container Apps │  │    │  │
    │  │  │  │ Workspace │  │   │  │ Environment    │  │    │  │
    │  │  │  │           │  │   │  │                │  │    │  │
    │  │  │  │ Notebooks │──│───│──│─▸ mcp-server   │  │    │  │
    │  │  │  │ (VNet     │  │   │  │   :8001 REST   │  │    │  │
    │  │  │  │  injected)│  │   │  │   :8002 SSE    │  │    │  │
    │  │  │  └───────────┘  │   │  └────────────────┘  │    │  │
    │  │  └─────────────────┘   └──────────────────────┘    │  │
    │  │                                                     │  │
    │  │  ┌─────────────────┐   ┌──────────────────────┐    │  │
    │  │  │  Subnet:        │   │  Private DNS Zone    │    │  │
    │  │  │  databricks-    │   │  azurecontainer      │    │  │
    │  │  │  public         │   │  apps.io             │    │  │
    │  │  │  10.0.2.0/24    │   │  (resolves internal  │    │  │
    │  │  │  (Databricks    │   │   FQDN for           │    │  │
    │  │  │   control plane)│   │   Container Apps)    │    │  │
    │  │  └─────────────────┘   └──────────────────────┘    │  │
    │  └─────────────────────────────────────────────────────┘  │
    │                                                           │
    │  ┌──────────────┐  ┌──────────────┐                      │
    │  │ Key Vault    │  │ Container    │                      │
    │  │ (secrets)    │  │ Registry     │                      │
    │  └──────────────┘  │ (images)     │                      │
    │                    └──────────────┘                      │
    └───────────────────────────────────────────────────────────┘

Usage:
    # Preview what will be created
    python deploy_azure_infrastructure.py --preview

    # Deploy everything
    python deploy_azure_infrastructure.py --deploy

    # Deploy specific components
    python deploy_azure_infrastructure.py --deploy --component networking
    python deploy_azure_infrastructure.py --deploy --component container-apps
    python deploy_azure_infrastructure.py --deploy --component databricks

Prerequisites:
    - Azure CLI installed and logged in (az login)
    - Appropriate Azure RBAC permissions (Contributor + Network Contributor)
    - Python 3.11+
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class AzureConfig:
    """Azure deployment configuration. Override via environment variables."""

    # Subscription & location
    subscription_id: str = os.getenv("AZURE_SUBSCRIPTION_ID", "")
    location: str = os.getenv("AZURE_LOCATION", "uksouth")
    resource_group: str = os.getenv("AZURE_RESOURCE_GROUP", "rg-cookidoo-agent")

    # Naming
    project_name: str = "cookidoo"
    environment: str = os.getenv("AZURE_ENVIRONMENT", "dev")

    # Networking
    vnet_name: str = "cookidoo-vnet"
    vnet_address_space: str = "10.0.0.0/16"
    databricks_private_subnet: str = "10.0.1.0/24"
    databricks_public_subnet: str = "10.0.2.0/24"
    container_apps_subnet: str = "10.0.3.0/23"  # /23 required by ACA

    # Container Apps
    container_registry_name: str = os.getenv(
        "AZURE_CONTAINER_REGISTRY", "crcookidoollm"
    )
    container_apps_env_name: str = "cae-cookidoo-agent"

    # Databricks
    databricks_workspace_name: str = "dbw-cookidoo-agent"
    databricks_sku: str = "premium"  # premium required for VNet injection

    # Key Vault
    key_vault_name: str = os.getenv("AZURE_KEY_VAULT_NAME", "kv-cookidoo-agent")

    # Tags
    tags: Dict[str, str] = field(
        default_factory=lambda: {
            "project": "cookidoo-agent",
            "environment": "dev",
            "managed-by": "deploy-script",
        }
    )

    @property
    def nsg_databricks_name(self) -> str:
        return f"nsg-databricks-{self.environment}"

    @property
    def nsg_container_apps_name(self) -> str:
        return f"nsg-container-apps-{self.environment}"


# ---------------------------------------------------------------------------
# Azure CLI Wrapper
# ---------------------------------------------------------------------------


def az(cmd: str, check: bool = True) -> dict:
    """
    Run an Azure CLI command and return parsed JSON output.

    Args:
        cmd: Azure CLI command (without 'az' prefix).
        check: Raise on non-zero exit code.

    Returns:
        Parsed JSON response or empty dict.
    """
    full_cmd = f"az {cmd} --output json"
    logger.debug(f"Running: {full_cmd}")

    result = subprocess.run(
        full_cmd,
        shell=True,
        capture_output=True,
        text=True,
    )

    if check and result.returncode != 0:
        logger.error(f"Command failed: {full_cmd}")
        logger.error(f"stderr: {result.stderr}")
        raise RuntimeError(f"az command failed: {result.stderr}")

    if result.stdout.strip():
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"raw": result.stdout.strip()}
    return {}


# ---------------------------------------------------------------------------
# Deployment Steps
# ---------------------------------------------------------------------------


def create_resource_group(cfg: AzureConfig) -> None:
    """Create the resource group."""
    logger.info(f"Creating resource group: {cfg.resource_group}")
    tags_str = " ".join(f'"{k}={v}"' for k, v in cfg.tags.items())
    az(
        f"group create "
        f"--name {cfg.resource_group} "
        f"--location {cfg.location} "
        f"--tags {tags_str}"
    )
    logger.info(f"  ✓ Resource group ready")


def create_vnet_and_subnets(cfg: AzureConfig) -> None:
    """Create VNet with subnets for Databricks and Container Apps."""
    logger.info(f"Creating VNet: {cfg.vnet_name}")

    # Create VNet
    az(
        f"network vnet create "
        f"--resource-group {cfg.resource_group} "
        f"--name {cfg.vnet_name} "
        f"--address-prefix {cfg.vnet_address_space} "
        f"--location {cfg.location}"
    )

    # NSG for Databricks (required for VNet injection)
    logger.info("  Creating NSGs...")
    az(
        f"network nsg create "
        f"--resource-group {cfg.resource_group} "
        f"--name {cfg.nsg_databricks_name}"
    )

    # Databricks private subnet (worker nodes)
    logger.info("  Creating Databricks private subnet (10.0.1.0/24)...")
    az(
        f"network vnet subnet create "
        f"--resource-group {cfg.resource_group} "
        f"--vnet-name {cfg.vnet_name} "
        f"--name databricks-private "
        f"--address-prefix {cfg.databricks_private_subnet} "
        f"--network-security-group {cfg.nsg_databricks_name} "
        f"--delegations Microsoft.Databricks/workspaces"
    )

    # Databricks public subnet (NAT gateway / control plane)
    logger.info("  Creating Databricks public subnet (10.0.2.0/24)...")
    az(
        f"network vnet subnet create "
        f"--resource-group {cfg.resource_group} "
        f"--vnet-name {cfg.vnet_name} "
        f"--name databricks-public "
        f"--address-prefix {cfg.databricks_public_subnet} "
        f"--network-security-group {cfg.nsg_databricks_name} "
        f"--delegations Microsoft.Databricks/workspaces"
    )

    # Container Apps subnet (requires /23 minimum)
    logger.info("  Creating Container Apps subnet (10.0.3.0/23)...")
    az(
        f"network vnet subnet create "
        f"--resource-group {cfg.resource_group} "
        f"--vnet-name {cfg.vnet_name} "
        f"--name container-apps-subnet "
        f"--address-prefix {cfg.container_apps_subnet}"
    )

    logger.info("  ✓ VNet and subnets created")


def create_key_vault(cfg: AzureConfig) -> None:
    """Create Azure Key Vault for secrets management."""
    logger.info(f"Creating Key Vault: {cfg.key_vault_name}")
    az(
        f"keyvault create "
        f"--resource-group {cfg.resource_group} "
        f"--name {cfg.key_vault_name} "
        f"--location {cfg.location} "
        f"--sku standard "
        f"--enable-rbac-authorization true"
    )
    logger.info("  ✓ Key Vault created")
    logger.info("  ℹ Store secrets with:")
    logger.info(
        f"    az keyvault secret set --vault-name {cfg.key_vault_name} "
        f"--name cookidoo-email --value <email>"
    )
    logger.info(
        f"    az keyvault secret set --vault-name {cfg.key_vault_name} "
        f"--name cookidoo-password --value <password>"
    )


def create_container_registry(cfg: AzureConfig) -> None:
    """Create Azure Container Registry for Docker images."""
    logger.info(f"Creating Container Registry: {cfg.container_registry_name}")
    az(
        f"acr create "
        f"--resource-group {cfg.resource_group} "
        f"--name {cfg.container_registry_name} "
        f"--sku Basic "
        f"--location {cfg.location} "
        f"--admin-enabled true"
    )
    logger.info("  ✓ Container Registry created")
    logger.info(f"  ℹ Push images with:")
    logger.info(f"    az acr login --name {cfg.container_registry_name}")
    logger.info(
        f"    docker push {cfg.container_registry_name}.azurecr.io/cookidoo-mcp:latest"
    )


def create_container_apps_environment(cfg: AzureConfig) -> str:
    """
    Create Azure Container Apps Environment with VNet integration.

    The internal environment means Container Apps get a private IP
    accessible only within the VNet (and peered subnets like Databricks).

    Returns:
        The default domain of the Container Apps Environment.
    """
    logger.info(f"Creating Container Apps Environment: {cfg.container_apps_env_name}")

    # Get subnet resource ID
    subnet_id_result = az(
        f"network vnet subnet show "
        f"--resource-group {cfg.resource_group} "
        f"--vnet-name {cfg.vnet_name} "
        f"--name container-apps-subnet "
        f"--query id -o tsv",
    )
    subnet_id = subnet_id_result.get("raw", "")

    # Create internal Container Apps Environment
    result = az(
        f"containerapp env create "
        f"--resource-group {cfg.resource_group} "
        f"--name {cfg.container_apps_env_name} "
        f"--location {cfg.location} "
        f"--infrastructure-subnet-resource-id {subnet_id} "
        f"--internal-only true"
    )

    # Get the default domain and static IP
    env_info = az(
        f"containerapp env show "
        f"--resource-group {cfg.resource_group} "
        f"--name {cfg.container_apps_env_name}"
    )

    default_domain = env_info.get("properties", {}).get("defaultDomain", "")
    static_ip = env_info.get("properties", {}).get("staticIp", "")

    logger.info(f"  ✓ Container Apps Environment created (internal-only)")
    logger.info(f"  Default domain: {default_domain}")
    logger.info(f"  Static IP: {static_ip}")

    return default_domain


def create_private_dns_zone(cfg: AzureConfig, default_domain: str) -> None:
    """
    Create Private DNS Zone so Databricks can resolve Container Apps
    internal FQDNs.

    Without this, Databricks clusters cannot resolve
    'mcp-server.internal.<region>.azurecontainerapps.io'.
    """
    logger.info(f"Creating Private DNS Zone: {default_domain}")

    # Create the private DNS zone
    az(
        f"network private-dns zone create "
        f"--resource-group {cfg.resource_group} "
        f"--name {default_domain}"
    )

    # Link DNS zone to the VNet (so Databricks can resolve it)
    az(
        f"network private-dns link vnet create "
        f"--resource-group {cfg.resource_group} "
        f"--zone-name {default_domain} "
        f"--name cookidoo-vnet-link "
        f"--virtual-network {cfg.vnet_name} "
        f"--registration-enabled false"
    )

    # Get the static IP of the Container Apps Environment
    env_info = az(
        f"containerapp env show "
        f"--resource-group {cfg.resource_group} "
        f"--name {cfg.container_apps_env_name}"
    )
    static_ip = env_info.get("properties", {}).get("staticIp", "")

    # Add A record pointing wildcard to the static IP
    if static_ip:
        az(
            f"network private-dns record-set a add-record "
            f"--resource-group {cfg.resource_group} "
            f"--zone-name {default_domain} "
            f"--record-set-name '*' "
            f"--ipv4-address {static_ip}"
        )
        logger.info(f"  ✓ DNS: *.{default_domain} → {static_ip}")

    logger.info("  ✓ Private DNS Zone created and linked to VNet")


def deploy_mcp_container_app(cfg: AzureConfig, default_domain: str) -> str:
    """
    Deploy the MCP server as an Azure Container App.

    Exposes two ports internally:
        - 8001: REST API (target port for ingress)
        - 8002: MCP SSE protocol (additional port)

    Returns:
        The internal FQDN of the MCP server.
    """
    logger.info("Deploying MCP Server Container App...")

    registry_server = f"{cfg.container_registry_name}.azurecr.io"
    image = f"{registry_server}/cookidoo-mcp:latest"

    # Get registry credentials
    creds = az(f"acr credential show --name {cfg.container_registry_name}")
    registry_user = creds.get("username", "")
    registry_pass = creds.get("passwords", [{}])[0].get("value", "")

    # Get Key Vault secrets for Cookidoo credentials
    # (Container App will use these as env vars)
    logger.info("  Retrieving secrets from Key Vault...")

    # Deploy the container app
    az(
        f"containerapp create "
        f"--resource-group {cfg.resource_group} "
        f"--name mcp-server "
        f"--environment {cfg.container_apps_env_name} "
        f"--image {image} "
        f"--registry-server {registry_server} "
        f"--registry-username {registry_user} "
        f"--registry-password {registry_pass} "
        f"--target-port 8001 "
        f"--ingress internal "
        f"--transport auto "
        f"--min-replicas 1 "
        f"--max-replicas 3 "
        f"--cpu 0.5 "
        f"--memory 1.0Gi "
        f"--env-vars "
        f"COOKIDOO_EMAIL=secretref:cookidoo-email "
        f"COOKIDOO_PASSWORD=secretref:cookidoo-password "
        f"MCP_SSE_PORT=8002 "
        f"LOG_LEVEL=INFO"
    )

    # Add the second port for MCP SSE (8002)
    # Container Apps supports additional TCP ports
    az(
        f"containerapp ingress update "
        f"--resource-group {cfg.resource_group} "
        f"--name mcp-server "
        f"--target-port 8001 "
        f"--exposed-port 8001 "
        f"--transport auto "
        f"--type internal"
    )

    mcp_fqdn = f"mcp-server.internal.{default_domain}"
    mcp_rest_url = f"https://mcp-server.{default_domain}"

    logger.info(f"  ✓ MCP Server deployed")
    logger.info(f"  Internal FQDN: {mcp_fqdn}")
    logger.info(f"  REST URL:      {mcp_rest_url}")
    logger.info(f"  SSE URL:       {mcp_rest_url.replace(':8001', ':8002')}")

    return mcp_rest_url


def deploy_backend_container_app(cfg: AzureConfig, mcp_url: str) -> None:
    """Deploy the backend API as an Azure Container App."""
    logger.info("Deploying Backend API Container App...")

    registry_server = f"{cfg.container_registry_name}.azurecr.io"
    image = f"{registry_server}/cookidoo-backend:latest"

    creds = az(f"acr credential show --name {cfg.container_registry_name}")
    registry_user = creds.get("username", "")
    registry_pass = creds.get("passwords", [{}])[0].get("value", "")

    az(
        f"containerapp create "
        f"--resource-group {cfg.resource_group} "
        f"--name backend "
        f"--environment {cfg.container_apps_env_name} "
        f"--image {image} "
        f"--registry-server {registry_server} "
        f"--registry-username {registry_user} "
        f"--registry-password {registry_pass} "
        f"--target-port 8000 "
        f"--ingress external "
        f"--transport auto "
        f"--min-replicas 1 "
        f"--max-replicas 5 "
        f"--cpu 1.0 "
        f"--memory 2.0Gi "
        f"--env-vars "
        f"MCP_SERVER_URL={mcp_url} "
        f"ENV=production "
        f"LOG_LEVEL=INFO"
    )

    logger.info("  ✓ Backend API deployed (external ingress)")


def deploy_frontend_container_app(cfg: AzureConfig) -> None:
    """Deploy the frontend as an Azure Container App."""
    logger.info("Deploying Frontend Container App...")

    registry_server = f"{cfg.container_registry_name}.azurecr.io"
    image = f"{registry_server}/cookidoo-frontend:latest"

    creds = az(f"acr credential show --name {cfg.container_registry_name}")
    registry_user = creds.get("username", "")
    registry_pass = creds.get("passwords", [{}])[0].get("value", "")

    az(
        f"containerapp create "
        f"--resource-group {cfg.resource_group} "
        f"--name frontend "
        f"--environment {cfg.container_apps_env_name} "
        f"--image {image} "
        f"--registry-server {registry_server} "
        f"--registry-username {registry_user} "
        f"--registry-password {registry_pass} "
        f"--target-port 3000 "
        f"--ingress external "
        f"--transport auto "
        f"--min-replicas 1 "
        f"--max-replicas 3 "
        f"--cpu 0.25 "
        f"--memory 0.5Gi"
    )

    logger.info("  ✓ Frontend deployed (external ingress)")


def create_databricks_workspace(cfg: AzureConfig) -> None:
    """
    Create Azure Databricks workspace with VNet injection.

    VNet injection places Databricks worker nodes in the same VNet as
    Container Apps, enabling private network connectivity.
    """
    logger.info(f"Creating Databricks workspace: {cfg.databricks_workspace_name}")

    # Get subnet IDs
    private_subnet_id = az(
        f"network vnet subnet show "
        f"--resource-group {cfg.resource_group} "
        f"--vnet-name {cfg.vnet_name} "
        f"--name databricks-private "
        f"--query id -o tsv"
    ).get("raw", "")

    public_subnet_id = az(
        f"network vnet subnet show "
        f"--resource-group {cfg.resource_group} "
        f"--vnet-name {cfg.vnet_name} "
        f"--name databricks-public "
        f"--query id -o tsv"
    ).get("raw", "")

    # Create Databricks workspace with VNet injection
    az(
        f"databricks workspace create "
        f"--resource-group {cfg.resource_group} "
        f"--name {cfg.databricks_workspace_name} "
        f"--location {cfg.location} "
        f"--sku {cfg.databricks_sku} "
        f"--vnet-address-prefix {cfg.vnet_address_space} "
        f"--private-subnet-name databricks-private "
        f"--public-subnet-name databricks-public "
        f"--public-network-access Enabled "
        f"--required-nsg-rules AllRules"
    )

    # Get workspace URL
    ws_info = az(
        f"databricks workspace show "
        f"--resource-group {cfg.resource_group} "
        f"--name {cfg.databricks_workspace_name}"
    )
    ws_url = ws_info.get("properties", {}).get("workspaceUrl", "")

    logger.info(f"  ✓ Databricks workspace created")
    logger.info(f"  URL: https://{ws_url}")
    logger.info(f"  SKU: {cfg.databricks_sku} (VNet injection enabled)")


def store_mcp_url_in_databricks(cfg: AzureConfig, mcp_url: str) -> None:
    """
    Store the MCP server URL in Databricks secret scope.

    This is the URL that Databricks notebooks use to connect to the
    MCP server. Since both are in the same VNet, this is a private URL.
    """
    logger.info("Storing MCP URL in Databricks secrets...")

    # This requires Databricks CLI configured
    try:
        subprocess.run(
            ["databricks", "secrets", "create-scope", "--scope", "cookidoo-mcp"],
            check=False,
            capture_output=True,
        )
        subprocess.run(
            [
                "databricks",
                "secrets",
                "put-secret",
                "--scope",
                "cookidoo-mcp",
                "--key",
                "mcp-server-url",
                "--string-value",
                mcp_url,
            ],
            check=True,
            capture_output=True,
        )
        logger.info(f"  ✓ Stored mcp-server-url = {mcp_url}")
    except FileNotFoundError:
        logger.warning("  ⚠ Databricks CLI not found. Store manually:")
        logger.warning(f"    databricks secrets create-scope --scope cookidoo-mcp")
        logger.warning(
            f"    databricks secrets put-secret --scope cookidoo-mcp "
            f"--key mcp-server-url --string-value {mcp_url}"
        )


def configure_databricks_key_vault_scope(cfg: AzureConfig) -> None:
    """
    Create a Databricks secret scope backed by Azure Key Vault.

    This lets Databricks notebooks read Cookidoo credentials from
    Key Vault using dbutils.secrets.get().
    """
    logger.info("Configuring Databricks Key Vault secret scope...")

    kv_resource_id = az(
        f"keyvault show "
        f"--resource-group {cfg.resource_group} "
        f"--name {cfg.key_vault_name} "
        f"--query id -o tsv"
    ).get("raw", "")

    kv_dns = f"https://{cfg.key_vault_name}.vault.azure.net/"

    try:
        subprocess.run(
            [
                "databricks",
                "secrets",
                "create-scope",
                "--scope",
                "cookidoo-secrets",
                "--scope-backend-type",
                "AZURE_KEYVAULT",
                "--resource-id",
                kv_resource_id,
                "--dns-name",
                kv_dns,
            ],
            check=True,
            capture_output=True,
        )
        logger.info(f"  ✓ Key Vault scope 'cookidoo-secrets' created")
    except FileNotFoundError:
        logger.warning("  ⚠ Databricks CLI not found. Create manually:")
        logger.warning(
            f"    databricks secrets create-scope --scope cookidoo-secrets "
            f"--scope-backend-type AZURE_KEYVAULT "
            f"--resource-id {kv_resource_id} "
            f"--dns-name {kv_dns}"
        )
    except subprocess.CalledProcessError as e:
        logger.warning(f"  ⚠ Scope may already exist: {e}")


# ---------------------------------------------------------------------------
# Build & Push Docker Images
# ---------------------------------------------------------------------------


def build_and_push_images(cfg: AzureConfig) -> None:
    """Build and push Docker images to Azure Container Registry."""
    logger.info("Building and pushing Docker images...")

    registry = f"{cfg.container_registry_name}.azurecr.io"

    # Login to ACR
    az(f"acr login --name {cfg.container_registry_name}")

    images = [
        ("cookidoo-mcp", "docker/mcp.Dockerfile"),
        ("cookidoo-backend", "docker/backend.Dockerfile"),
        ("cookidoo-frontend", "docker/frontend.Dockerfile"),
    ]

    for image_name, dockerfile in images:
        logger.info(f"  Building {image_name}...")
        subprocess.run(
            [
                "docker",
                "build",
                "-f",
                dockerfile,
                "-t",
                f"{registry}/{image_name}:latest",
                ".",
            ],
            check=True,
        )
        logger.info(f"  Pushing {image_name}...")
        subprocess.run(
            ["docker", "push", f"{registry}/{image_name}:latest"],
            check=True,
        )
        logger.info(f"  ✓ {image_name} pushed to {registry}")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

COMPONENTS = {
    "networking": [
        create_resource_group,
        create_vnet_and_subnets,
        create_key_vault,
        create_container_registry,
    ],
    "container-apps": [
        create_container_apps_environment,
        # create_private_dns_zone called after env creation
        # deploy_mcp_container_app called after DNS
        # deploy_backend_container_app called after MCP
        # deploy_frontend_container_app
    ],
    "databricks": [
        create_databricks_workspace,
        # configure_databricks_key_vault_scope
        # store_mcp_url_in_databricks
    ],
}


def deploy_all(cfg: AzureConfig) -> None:
    """Full deployment of all Azure infrastructure."""
    print("=" * 70)
    print(" Azure Infrastructure Deployment – Cookidoo Agent Assistant")
    print("=" * 70)

    # Phase 1: Networking foundation
    print("\n[Phase 1/4] Networking & Shared Resources")
    create_resource_group(cfg)
    create_vnet_and_subnets(cfg)
    create_key_vault(cfg)
    create_container_registry(cfg)

    # Phase 2: Build and push images
    print("\n[Phase 2/4] Container Images")
    build_and_push_images(cfg)

    # Phase 3: Container Apps
    print("\n[Phase 3/4] Azure Container Apps")
    default_domain = create_container_apps_environment(cfg)
    create_private_dns_zone(cfg, default_domain)
    mcp_url = deploy_mcp_container_app(cfg, default_domain)
    deploy_backend_container_app(cfg, mcp_url)
    deploy_frontend_container_app(cfg)

    # Phase 4: Databricks
    print("\n[Phase 4/4] Azure Databricks")
    create_databricks_workspace(cfg)
    configure_databricks_key_vault_scope(cfg)
    store_mcp_url_in_databricks(cfg, mcp_url)

    # Summary
    print("\n" + "=" * 70)
    print(" Deployment Complete")
    print("=" * 70)
    print(f"Resource Group:     {cfg.resource_group}")
    print(f"Location:           {cfg.location}")
    print(f"VNet:               {cfg.vnet_name}")
    print(f"MCP Server (int):   {mcp_url}")
    print(f"Container Registry: {cfg.container_registry_name}.azurecr.io")
    print(f"Key Vault:          {cfg.key_vault_name}")
    print(f"Databricks:         {cfg.databricks_workspace_name}")
    print()
    print("Databricks can reach the MCP server at:")
    print(f"  REST: {mcp_url}")
    print(f"  SSE:  (configure additional TCP port for 8002)")
    print()
    print("Next steps:")
    print("  1. Store Cookidoo credentials in Key Vault:")
    print(
        f"     az keyvault secret set --vault-name {cfg.key_vault_name} "
        f"--name cookidoo-email --value <email>"
    )
    print(
        f"     az keyvault secret set --vault-name {cfg.key_vault_name} "
        f"--name cookidoo-password --value <password>"
    )
    print("  2. Import notebooks to Databricks workspace")
    print("  3. Run 03_mcp_client_integration notebook to verify connectivity")
    print("  4. Run deploy_infrastructure.py for Databricks catalog/schemas")
    print("=" * 70)


def preview(cfg: AzureConfig) -> None:
    """Show what would be created without deploying."""
    print("=" * 70)
    print(" Deployment Preview (dry run)")
    print("=" * 70)
    print(f"\nSubscription:  {cfg.subscription_id or '(from az login)'}")
    print(f"Location:      {cfg.location}")
    print(f"Resource Group: {cfg.resource_group}")
    print()
    print("Resources to create:")
    print(f"  VNet:                {cfg.vnet_name} ({cfg.vnet_address_space})")
    print(
        f"    Databricks private:  databricks-private ({cfg.databricks_private_subnet})"
    )
    print(
        f"    Databricks public:   databricks-public ({cfg.databricks_public_subnet})"
    )
    print(
        f"    Container Apps:      container-apps-subnet ({cfg.container_apps_subnet})"
    )
    print(
        f"  NSGs:                {cfg.nsg_databricks_name}, {cfg.nsg_container_apps_name}"
    )
    print(f"  Key Vault:           {cfg.key_vault_name}")
    print(f"  Container Registry:  {cfg.container_registry_name}")
    print(f"  Container Apps Env:  {cfg.container_apps_env_name} (internal-only)")
    print(f"    mcp-server:        0.5 vCPU, 1GB (ports 8001, 8002)")
    print(f"    backend:           1.0 vCPU, 2GB (port 8000, external)")
    print(f"    frontend:          0.25 vCPU, 0.5GB (port 3000, external)")
    print(
        f"  Databricks:          {cfg.databricks_workspace_name} ({cfg.databricks_sku})"
    )
    print(f"  Private DNS Zone:    <auto>.azurecontainerapps.io")
    print()
    print("How Databricks→MCP connectivity works:")
    print("  1. Databricks workspace uses VNet injection (databricks-private subnet)")
    print("  2. Container Apps Environment is internal-only (container-apps-subnet)")
    print("  3. Both subnets are in the same VNet (10.0.0.0/16)")
    print("  4. Private DNS Zone resolves Container Apps internal FQDNs")
    print("  5. Databricks notebooks can call: https://mcp-server.<domain>/api/...")
    print()
    print("Estimated monthly cost:")
    print("  Container Apps (3 apps):  ~$30-80/month")
    print("  Databricks (Premium):     ~$0.40/DBU (pay per use)")
    print("  Key Vault:                ~$0.03/10k operations")
    print("  Container Registry:       ~$5/month (Basic)")
    print("  VNet/DNS:                 ~$1/month")
    print("=" * 70)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Deploy Azure infrastructure for Cookidoo Agent Assistant"
    )
    parser.add_argument("--deploy", action="store_true", help="Execute deployment")
    parser.add_argument(
        "--preview", action="store_true", help="Preview resources (dry run)"
    )
    parser.add_argument(
        "--component",
        choices=["networking", "container-apps", "databricks", "images"],
        help="Deploy only a specific component",
    )

    args = parser.parse_args()
    cfg = AzureConfig()

    if not cfg.subscription_id:
        # Try to get from current az login
        try:
            account = az("account show")
            cfg.subscription_id = account.get("id", "")
        except RuntimeError:
            logger.error("Not logged in. Run: az login")
            sys.exit(1)

    if args.preview or (not args.deploy and not args.preview):
        preview(cfg)
    elif args.deploy:
        if args.component == "networking":
            create_resource_group(cfg)
            create_vnet_and_subnets(cfg)
            create_key_vault(cfg)
            create_container_registry(cfg)
        elif args.component == "images":
            build_and_push_images(cfg)
        elif args.component == "container-apps":
            default_domain = create_container_apps_environment(cfg)
            create_private_dns_zone(cfg, default_domain)
            mcp_url = deploy_mcp_container_app(cfg, default_domain)
            deploy_backend_container_app(cfg, mcp_url)
            deploy_frontend_container_app(cfg)
        elif args.component == "databricks":
            create_databricks_workspace(cfg)
            configure_databricks_key_vault_scope(cfg)
            # MCP URL needs to be provided manually for component-only deploy
            mcp_url = os.getenv("MCP_SERVER_URL", "")
            if mcp_url:
                store_mcp_url_in_databricks(cfg, mcp_url)
            else:
                logger.warning(
                    "Set MCP_SERVER_URL env var to store in Databricks secrets"
                )
        else:
            deploy_all(cfg)


if __name__ == "__main__":
    main()
