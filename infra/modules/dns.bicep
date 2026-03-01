// ---------------------------------------------------------------------------
// Module: dns.bicep
// Deploys Private DNS Zone for Container Apps default domain
// Links to VNet so Databricks workers can resolve internal Container App FQDNs
// ---------------------------------------------------------------------------

@description('Container Apps Environment default domain (e.g. nicedesert-abc123.uksouth.azurecontainerapps.io)')
param defaultDomain string

@description('Static IP of the Container Apps Environment load balancer')
param staticIp string

@description('VNet ID to link the DNS zone to')
param vnetId string

@description('Tags to apply')
param tags object = {}

// ── Private DNS Zone (matches Container Apps default domain) ────────────────

resource privateDnsZone 'Microsoft.Network/privateDnsZones@2024-06-01' = {
  name: defaultDomain
  location: 'global'
  tags: tags
}

// ── Link DNS zone to VNet ───────────────────────────────────────────────────

resource vnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2024-06-01' = {
  parent: privateDnsZone
  name: 'vnet-link'
  location: 'global'
  tags: tags
  properties: {
    virtualNetwork: {
      id: vnetId
    }
    registrationEnabled: false
  }
}

// ── Wildcard A record → Container Apps static IP ────────────────────────────
// All *.{defaultDomain} queries will resolve to the internal load balancer

resource wildcardRecord 'Microsoft.Network/privateDnsZones/A@2024-06-01' = {
  parent: privateDnsZone
  name: '*'
  properties: {
    ttl: 300
    aRecords: [
      {
        ipv4Address: staticIp
      }
    ]
  }
}

// ── Outputs ─────────────────────────────────────────────────────────────────

output dnsZoneName string = privateDnsZone.name
output dnsZoneId string = privateDnsZone.id
