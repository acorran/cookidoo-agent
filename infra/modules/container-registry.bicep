// ---------------------------------------------------------------------------
// Module: container-registry.bicep
// Deploys Azure Container Registry for Docker images
// ---------------------------------------------------------------------------

@description('Azure region for the resource')
param location string

@description('Name of the Container Registry (must be globally unique, alphanumeric)')
param acrName string

@description('Tags to apply')
param tags object = {}

resource acr 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: acrName
  location: location
  tags: tags
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

output loginServer string = acr.properties.loginServer
output acrName string = acr.name
output acrId string = acr.id
