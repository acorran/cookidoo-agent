// ---------------------------------------------------------------------------
// Module: container-apps.bicep
// Deploys Container Apps Environment (internal) + 3 Container Apps:
//   - mcp-server (internal only, ports 8001 REST + 8002 SSE)
//   - backend   (external, port 8000)
//   - frontend  (external, port 3000)
// ---------------------------------------------------------------------------

@description('Azure region for the resource')
param location string

@description('Name of the Container Apps Environment')
param containerAppsEnvName string

@description('Subnet ID for the Container Apps Environment')
param containerAppsSubnetId string

@description('Log Analytics workspace ID for diagnostics')
param logAnalyticsWorkspaceId string

@description('ACR login server URL')
param acrLoginServer string

@description('ACR name for role assignment')
param acrName string

@description('Tags to apply')
param tags object = {}

// Service images — set empty string to deploy placeholder
param backendImageName string = ''
param frontendImageName string = ''
param mcpServerImageName string = ''

@secure()
param cookidooEmail string = ''

@secure()
param cookidooPassword string = ''

param keyVaultName string = ''

// ── Managed Identity (shared, for ACR pull + Key Vault access) ──────────────

resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-${containerAppsEnvName}'
  location: location
  tags: tags
}

// ── ACR Pull role assignment ────────────────────────────────────────────────

resource acr 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' existing = {
  name: acrName
}

// AcrPull built-in role
var acrPullRoleId = '7f951dda-4ed3-4680-a7ca-43fe172d538d'

resource acrPullAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acr.id, managedIdentity.id, acrPullRoleId)
  scope: acr
  properties: {
    principalId: managedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleId)
  }
}

// ── Key Vault Secrets User role assignment ──────────────────────────────────

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' existing = if (!empty(keyVaultName)) {
  name: keyVaultName
}

var kvSecretsUserRoleId = '4633458b-17de-408a-b874-0445c86b69e6'

resource kvRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(keyVaultName)) {
  name: guid(keyVault.id, managedIdentity.id, kvSecretsUserRoleId)
  scope: keyVault
  properties: {
    principalId: managedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', kvSecretsUserRoleId)
  }
}

// ── Container Apps Environment (internal only for VNet integration) ─────────

resource containerAppsEnv 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: containerAppsEnvName
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: reference(logAnalyticsWorkspaceId, '2023-09-01').customerId
        sharedKey: listKeys(logAnalyticsWorkspaceId, '2023-09-01').primarySharedKey
      }
    }
    vnetConfiguration: {
      internal: true
      infrastructureSubnetId: containerAppsSubnetId
    }
    workloadProfiles: [
      {
        name: 'Consumption'
        workloadProfileType: 'Consumption'
      }
    ]
  }
}

// ── MCP Server (internal only — not exposed to internet) ────────────────────

var mcpImage = !empty(mcpServerImageName) ? '${acrLoginServer}/${mcpServerImageName}' : 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

resource mcpServerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'ca-mcp-server'
  location: location
  tags: union(tags, { 'azd-service-name': 'mcp-server' })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    workloadProfileName: 'Consumption'
    configuration: {
      ingress: {
        external: false // Internal only — Databricks reaches via VNet
        targetPort: 8001
        transport: 'http'
        additionalPortMappings: [
          {
            external: false
            targetPort: 8002 // MCP SSE protocol
          }
        ]
      }
      registries: [
        {
          server: acrLoginServer
          identity: managedIdentity.id
        }
      ]
      secrets: [
        {
          name: 'cookidoo-email'
          value: cookidooEmail
        }
        {
          name: 'cookidoo-password'
          value: cookidooPassword
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'mcp-server'
          image: mcpImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            { name: 'HOST', value: '0.0.0.0' }
            { name: 'REST_PORT', value: '8001' }
            { name: 'MCP_SSE_PORT', value: '8002' }
            { name: 'COOKIDOO_EMAIL', secretRef: 'cookidoo-email' }
            { name: 'COOKIDOO_PASSWORD', secretRef: 'cookidoo-password' }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 3
      }
    }
  }
}

// ── Backend API (external — serves the API) ─────────────────────────────────

var backendImage = !empty(backendImageName) ? '${acrLoginServer}/${backendImageName}' : 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

resource backendApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'ca-backend'
  location: location
  tags: union(tags, { 'azd-service-name': 'backend' })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    workloadProfileName: 'Consumption'
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        transport: 'http'
        corsPolicy: {
          allowedOrigins: ['*']
          allowedMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
          allowedHeaders: ['*']
        }
      }
      registries: [
        {
          server: acrLoginServer
          identity: managedIdentity.id
        }
      ]
      secrets: [
        {
          name: 'cookidoo-email'
          value: cookidooEmail
        }
        {
          name: 'cookidoo-password'
          value: cookidooPassword
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: backendImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
          env: [
            { name: 'COOKIDOO_EMAIL', secretRef: 'cookidoo-email' }
            { name: 'COOKIDOO_PASSWORD', secretRef: 'cookidoo-password' }
            { name: 'MCP_SSE_URL', value: 'http://ca-mcp-server.internal.${containerAppsEnv.properties.defaultDomain}:8002' }
            { name: 'AZURE_KEY_VAULT_URL', value: !empty(keyVaultName) ? 'https://${keyVaultName}${environment().suffixes.keyvaultDns}' : '' }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 5
      }
    }
  }
}

// ── Frontend (external — serves the React UI) ───────────────────────────────

var frontendImage = !empty(frontendImageName) ? '${acrLoginServer}/${frontendImageName}' : 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

resource frontendApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'ca-frontend'
  location: location
  tags: union(tags, { 'azd-service-name': 'frontend' })
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${managedIdentity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: containerAppsEnv.id
    workloadProfileName: 'Consumption'
    configuration: {
      ingress: {
        external: true
        targetPort: 3000
        transport: 'http'
      }
      registries: [
        {
          server: acrLoginServer
          identity: managedIdentity.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'frontend'
          image: frontendImage
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          env: [
            { name: 'REACT_APP_API_URL', value: 'https://${backendApp.properties.configuration.ingress.fqdn}' }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 3
      }
    }
  }
}

// ── Outputs ─────────────────────────────────────────────────────────────────

output defaultDomain string = containerAppsEnv.properties.defaultDomain
output staticIp string = containerAppsEnv.properties.staticIp

output mcpServerInternalUrl string = 'https://ca-mcp-server.internal.${containerAppsEnv.properties.defaultDomain}'
output backendUrl string = 'https://${backendApp.properties.configuration.ingress.fqdn}'
output frontendUrl string = 'https://${frontendApp.properties.configuration.ingress.fqdn}'

output managedIdentityPrincipalId string = managedIdentity.properties.principalId
output containerAppsEnvId string = containerAppsEnv.id
