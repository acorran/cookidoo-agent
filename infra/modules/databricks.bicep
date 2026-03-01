// ---------------------------------------------------------------------------
// Module: databricks.bicep
// Deploys Azure Databricks workspace with VNet injection (Premium SKU)
// ---------------------------------------------------------------------------

@description('Azure region for the resource')
param location string

@description('Databricks workspace name')
param workspaceName string

@description('Databricks pricing tier')
@allowed(['premium', 'standard', 'trial'])
param sku string = 'premium'

@description('ID of the VNet for injection')
param vnetId string

@description('Name of the private (backend) subnet for Databricks')
param privateSubnetName string

@description('Name of the public (frontend) subnet for Databricks')
param publicSubnetName string

@description('ID of the NSG attached to Databricks subnets')
param nsgId string

@description('Tags to apply')
param tags object = {}

// Databricks requires a managed resource group for its control plane resources
var managedResourceGroupName = 'databricks-rg-${workspaceName}'

resource databricksWorkspace 'Microsoft.Databricks/workspaces@2024-05-01' = {
  name: workspaceName
  location: location
  tags: tags
  sku: {
    name: sku
  }
  properties: {
    managedResourceGroupId: subscriptionResourceId('Microsoft.Resources/resourceGroups', managedResourceGroupName)
    parameters: {
      customVirtualNetworkId: {
        value: vnetId
      }
      customPrivateSubnetName: {
        value: privateSubnetName
      }
      customPublicSubnetName: {
        value: publicSubnetName
      }
      enableNoPublicIp: {
        value: true // Secure cluster connectivity (no public IPs on workers)
      }
    }
  }
}

// ── Outputs ─────────────────────────────────────────────────────────────────

output workspaceUrl string = 'https://${databricksWorkspace.properties.workspaceUrl}'
output workspaceId string = databricksWorkspace.id
output workspaceName string = databricksWorkspace.name
output managedResourceGroupId string = databricksWorkspace.properties.managedResourceGroupId
