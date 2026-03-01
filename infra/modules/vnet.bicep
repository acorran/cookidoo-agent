// ---------------------------------------------------------------------------
// Module: vnet.bicep
// Deploys VNet with subnets for Databricks (private/public) and Container Apps
// ---------------------------------------------------------------------------

@description('Azure region for the resource')
param location string

@description('Name of the Virtual Network')
param vnetName string

@description('Tags to apply')
param tags object = {}

// VNet address space
var vnetAddressPrefix = '10.0.0.0/16'

// Subnet definitions
var subnets = {
  databricksPrivate: {
    name: 'databricks-private'
    addressPrefix: '10.0.1.0/24'
  }
  databricksPublic: {
    name: 'databricks-public'
    addressPrefix: '10.0.2.0/24'
  }
  containerApps: {
    name: 'container-apps'
    addressPrefix: '10.0.3.0/23' // /23 required by Container Apps
  }
}

// ── NSG for Databricks subnets ──────────────────────────────────────────────

resource databricksNsg 'Microsoft.Network/networkSecurityGroups@2023-11-01' = {
  name: 'nsg-databricks-${vnetName}'
  location: location
  tags: tags
  properties: {
    securityRules: [
      // Required by Azure Databricks per docs
      {
        name: 'Microsoft.Databricks-workspaces_UseOnly_databricks-worker-to-worker-inbound'
        properties: {
          description: 'Required for worker nodes communication within a cluster.'
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: 'VirtualNetwork'
          destinationAddressPrefix: 'VirtualNetwork'
          access: 'Allow'
          priority: 100
          direction: 'Inbound'
        }
      }
      {
        name: 'Microsoft.Databricks-workspaces_UseOnly_databricks-worker-to-worker-outbound'
        properties: {
          description: 'Required for worker nodes communication within a cluster.'
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: 'VirtualNetwork'
          destinationAddressPrefix: 'VirtualNetwork'
          access: 'Allow'
          priority: 100
          direction: 'Outbound'
        }
      }
      {
        name: 'Microsoft.Databricks-workspaces_UseOnly_databricks-worker-to-sql'
        properties: {
          description: 'Required for workers communication with Azure SQL services.'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '3306'
          sourceAddressPrefix: 'VirtualNetwork'
          destinationAddressPrefix: 'Sql'
          access: 'Allow'
          priority: 101
          direction: 'Outbound'
        }
      }
      {
        name: 'Microsoft.Databricks-workspaces_UseOnly_databricks-worker-to-storage'
        properties: {
          description: 'Required for workers communication with Azure Storage services.'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '443'
          sourceAddressPrefix: 'VirtualNetwork'
          destinationAddressPrefix: 'Storage'
          access: 'Allow'
          priority: 102
          direction: 'Outbound'
        }
      }
      {
        name: 'Microsoft.Databricks-workspaces_UseOnly_databricks-worker-to-eventhub'
        properties: {
          description: 'Required for log delivery to Event Hub.'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '9093'
          sourceAddressPrefix: 'VirtualNetwork'
          destinationAddressPrefix: 'EventHub'
          access: 'Allow'
          priority: 103
          direction: 'Outbound'
        }
      }
    ]
  }
}

// ── NSG for Container Apps subnet ───────────────────────────────────────────

resource containerAppsNsg 'Microsoft.Network/networkSecurityGroups@2023-11-01' = {
  name: 'nsg-containerApps-${vnetName}'
  location: location
  tags: tags
  properties: {
    securityRules: [
      {
        name: 'AllowVNetInbound'
        properties: {
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: 'VirtualNetwork'
          destinationAddressPrefix: 'VirtualNetwork'
          access: 'Allow'
          priority: 100
          direction: 'Inbound'
        }
      }
    ]
  }
}

// ── Virtual Network ─────────────────────────────────────────────────────────

resource vnet 'Microsoft.Network/virtualNetworks@2023-11-01' = {
  name: vnetName
  location: location
  tags: tags
  properties: {
    addressSpace: {
      addressPrefixes: [
        vnetAddressPrefix
      ]
    }
    subnets: [
      {
        name: subnets.databricksPrivate.name
        properties: {
          addressPrefix: subnets.databricksPrivate.addressPrefix
          networkSecurityGroup: {
            id: databricksNsg.id
          }
          delegations: [
            {
              name: 'databricks-del-private'
              properties: {
                serviceName: 'Microsoft.Databricks/workspaces'
              }
            }
          ]
        }
      }
      {
        name: subnets.databricksPublic.name
        properties: {
          addressPrefix: subnets.databricksPublic.addressPrefix
          networkSecurityGroup: {
            id: databricksNsg.id
          }
          delegations: [
            {
              name: 'databricks-del-public'
              properties: {
                serviceName: 'Microsoft.Databricks/workspaces'
              }
            }
          ]
        }
      }
      {
        name: subnets.containerApps.name
        properties: {
          addressPrefix: subnets.containerApps.addressPrefix
          networkSecurityGroup: {
            id: containerAppsNsg.id
          }
        }
      }
    ]
  }
}

// ── Outputs ─────────────────────────────────────────────────────────────────

output vnetId string = vnet.id
output vnetName string = vnet.name

output containerAppsSubnetId string = vnet.properties.subnets[2].id

output databricksPrivateSubnetName string = subnets.databricksPrivate.name
output databricksPublicSubnetName string = subnets.databricksPublic.name

output databricksNsgId string = databricksNsg.id
