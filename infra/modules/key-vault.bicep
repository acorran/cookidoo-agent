// ---------------------------------------------------------------------------
// Module: key-vault.bicep
// Deploys Azure Key Vault with RBAC and stores Cookidoo credentials
// ---------------------------------------------------------------------------

@description('Azure region for the resource')
param location string

@description('Name of the Key Vault')
param keyVaultName string

@description('Tags to apply')
param tags object = {}

@secure()
@description('Cookidoo platform email')
param cookidooEmail string = ''

@secure()
@description('Cookidoo platform password')
param cookidooPassword string = ''

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    enablePurgeProtection: false // Allow purge for dev environments
  }
}

// ── Store Cookidoo secrets ──────────────────────────────────────────────────

resource secretEmail 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = if (!empty(cookidooEmail)) {
  parent: keyVault
  name: 'cookidoo-email'
  properties: {
    value: cookidooEmail
  }
}

resource secretPassword 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = if (!empty(cookidooPassword)) {
  parent: keyVault
  name: 'cookidoo-password'
  properties: {
    value: cookidooPassword
  }
}

// ── Outputs ─────────────────────────────────────────────────────────────────

output vaultUri string = keyVault.properties.vaultUri
output keyVaultName string = keyVault.name
output keyVaultId string = keyVault.id
