// ---------------------------------------------------------------------------
// Main Bicep orchestrator for Cookidoo Agent Assistant
// Provisions: VNet, ACR, Key Vault, Container Apps, Databricks, DNS
// Deploy via: azd up
// ---------------------------------------------------------------------------

targetScope = 'subscription'

// ── Parameters ──────────────────────────────────────────────────────────────

@minLength(1)
@maxLength(64)
@description('Name of the environment (e.g. dev, staging, prod)')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Tags applied to all resources')
param tags object = {}

// Service image names — injected by azd after docker build+push
param backendImageName string = ''
param frontendImageName string = ''
param mcpServerImageName string = ''

// Cookidoo credentials (set via: azd env set COOKIDOO_EMAIL <value>)
@secure()
param cookidooEmail string = ''
@secure()
param cookidooPassword string = ''

// Databricks SKU — Premium required for VNet injection
@allowed(['premium', 'standard', 'trial'])
param databricksSku string = 'premium'

// Optional: skip Databricks deployment for cost savings during dev
param deployDatabricks bool = true

// ── Variables ───────────────────────────────────────────────────────────────

var abbrs = loadJsonContent('./abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))

// Resource names using Azure abbreviation conventions
var resourceGroupName = '${abbrs.resourcesResourceGroups}${environmentName}'
var vnetName = '${abbrs.networkVirtualNetworks}${resourceToken}'
var acrName = '${abbrs.containerRegistryRegistries}${resourceToken}'
var keyVaultName = '${abbrs.keyVaultVaults}${resourceToken}'
var containerAppsEnvName = '${abbrs.appManagedEnvironments}${resourceToken}'
var logAnalyticsName = '${abbrs.operationalInsightsWorkspaces}${resourceToken}'
var databricksWorkspaceName = '${abbrs.databricksWorkspaces}${resourceToken}'

// Merge default tags with environment name
var defaultTags = union(tags, {
  'azd-env-name': environmentName
  'project': 'cookidoo-agent'
})

// ── Resource Group ──────────────────────────────────────────────────────────

resource rg 'Microsoft.Resources/resourceGroups@2022-09-01' = {
  name: resourceGroupName
  location: location
  tags: defaultTags
}

// ── Monitoring ──────────────────────────────────────────────────────────────

module monitoring './modules/monitoring.bicep' = {
  name: 'monitoring'
  scope: rg
  params: {
    location: location
    logAnalyticsName: logAnalyticsName
    tags: defaultTags
  }
}

// ── Networking ──────────────────────────────────────────────────────────────

module vnet './modules/vnet.bicep' = {
  name: 'vnet'
  scope: rg
  params: {
    location: location
    vnetName: vnetName
    tags: defaultTags
  }
}

// ── Container Registry ──────────────────────────────────────────────────────

module acr './modules/container-registry.bicep' = {
  name: 'acr'
  scope: rg
  params: {
    location: location
    acrName: acrName
    tags: defaultTags
  }
}

// ── Key Vault ───────────────────────────────────────────────────────────────

module keyVault './modules/key-vault.bicep' = {
  name: 'keyVault'
  scope: rg
  params: {
    location: location
    keyVaultName: keyVaultName
    tags: defaultTags
    cookidooEmail: cookidooEmail
    cookidooPassword: cookidooPassword
  }
}

// ── Container Apps Environment (internal, VNet-integrated) ──────────────────

module containerApps './modules/container-apps.bicep' = {
  name: 'containerApps'
  scope: rg
  params: {
    location: location
    containerAppsEnvName: containerAppsEnvName
    containerAppsSubnetId: vnet.outputs.containerAppsSubnetId
    logAnalyticsWorkspaceId: monitoring.outputs.logAnalyticsWorkspaceId
    acrLoginServer: acr.outputs.loginServer
    acrName: acrName
    tags: defaultTags

    // Service images
    backendImageName: backendImageName
    frontendImageName: frontendImageName
    mcpServerImageName: mcpServerImageName

    // MCP server config
    cookidooEmail: cookidooEmail
    cookidooPassword: cookidooPassword

    // Key Vault reference
    keyVaultName: keyVaultName
  }
}

// ── Private DNS Zone (Databricks → Container Apps resolution) ───────────────

module dns './modules/dns.bicep' = {
  name: 'dns'
  scope: rg
  params: {
    defaultDomain: containerApps.outputs.defaultDomain
    staticIp: containerApps.outputs.staticIp
    vnetId: vnet.outputs.vnetId
    tags: defaultTags
  }
}

// ── Azure Databricks (VNet-injected, Premium SKU) ───────────────────────────

module databricks './modules/databricks.bicep' = if (deployDatabricks) {
  name: 'databricks'
  scope: rg
  params: {
    location: location
    workspaceName: databricksWorkspaceName
    sku: databricksSku
    vnetId: vnet.outputs.vnetId
    privateSubnetName: vnet.outputs.databricksPrivateSubnetName
    publicSubnetName: vnet.outputs.databricksPublicSubnetName
    nsgId: vnet.outputs.databricksNsgId
    tags: defaultTags
  }
}

// ── Outputs (used by azd for wiring services) ───────────────────────────────

// azd uses these outputs to configure service endpoints and env vars
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = acr.outputs.loginServer
output AZURE_CONTAINER_REGISTRY_NAME string = acrName
output AZURE_KEY_VAULT_NAME string = keyVaultName
output AZURE_KEY_VAULT_ENDPOINT string = keyVault.outputs.vaultUri

// Container Apps URLs
output SERVICE_BACKEND_URI string = containerApps.outputs.backendUrl
output SERVICE_FRONTEND_URI string = containerApps.outputs.frontendUrl
output SERVICE_MCP_SERVER_URI string = containerApps.outputs.mcpServerInternalUrl

// Databricks
output DATABRICKS_WORKSPACE_URL string = deployDatabricks ? databricks.outputs.workspaceUrl : ''
output DATABRICKS_WORKSPACE_ID string = deployDatabricks ? databricks.outputs.workspaceId : ''

// Networking
output VNET_NAME string = vnet.outputs.vnetName
output MCP_SERVER_INTERNAL_FQDN string = containerApps.outputs.mcpServerInternalUrl
