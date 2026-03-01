// ---------------------------------------------------------------------------
// Module: monitoring.bicep
// Deploys Log Analytics Workspace (required by Container Apps Environment)
// ---------------------------------------------------------------------------

@description('Azure region for the resource')
param location string

@description('Name of the Log Analytics workspace')
param logAnalyticsName string

@description('Tags to apply')
param tags object = {}

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

output logAnalyticsWorkspaceId string = logAnalyticsWorkspace.id
output logAnalyticsWorkspaceName string = logAnalyticsWorkspace.name
